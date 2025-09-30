#!/usr/bin/env python3

"""
Curses-based Text User Interface for the Connection Manager.
Provides an interactive interface to view, search, add, edit, delete, and connect to connections.
"""

import curses
import logging
from typing import List, Optional, Dict, Any
from dataclasses import asdict

from connmanager.connection_service import ConnectionService
from connmanager.connection_prompter import ConnectionPrompter, ConnectionDetails, PROTOCOLS
from connmanager.database_connection import DatabaseConnection

logger = logging.getLogger(__name__)


class ConnectionManagerTUI:
    """
    Curses-based TUI for the Connection Manager.
    """
    
    def __init__(self, connection_service: ConnectionService):
        self.service = connection_service
        self.connections: List[Dict[str, Any]] = []
        self.filtered_connections: List[Dict[str, Any]] = []
        self.current_selection = 0
        self.search_query = ""
        self.status_message = ""
        self.show_help = False
        
        # UI state
        self.search_mode = False
        self.search_input = ""
        
        # Connection request (set when user wants to connect)
        self.connection_requested = None
        
    def run(self, stdscr) -> None:
        """
        Main TUI loop.
        """
        # Initialize curses
        curses.curs_set(0)  # Hide cursor
        stdscr.keypad(True)  # Enable special keys
        
        # Initialize colors if available
        if curses.has_colors():
            curses.start_color()
            
            try:
                curses.use_default_colors()  # Use terminal's default colors
                # Define color pairs that work well with dark themes
                curses.init_pair(1, curses.COLOR_CYAN, -1)      # Header - cyan on default
                curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)   # Selected - black on cyan
                curses.init_pair(3, curses.COLOR_GREEN, -1)     # Success - green on default
                curses.init_pair(4, curses.COLOR_RED, -1)       # Error - red on default
                curses.init_pair(5, curses.COLOR_YELLOW, -1)    # Warning - yellow on default
                curses.init_pair(6, curses.COLOR_BLUE, -1)      # Info - blue on default
            except:
                # Fallback for terminals that don't support default colors
                curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Header
                curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Selected
                curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Success
                curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)     # Error
                curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Warning
                curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLACK)    # Info
        
        # Load initial connections
        self.refresh_connections()
        
        while True:
            try:
                self.draw_screen(stdscr)
                key = stdscr.getch()
                
                if self.handle_key(stdscr, key):
                    break  # Exit requested
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.status_message = f"Error: {str(e)}"
                logger.error(f"TUI error: {e}")
    
    def refresh_connections(self) -> None:
        """
        Refresh the connections list from the database.
        """
        try:
            self.connections = self.service.database.get_all_connections()
            self.apply_search_filter()
            self.status_message = f"Loaded {len(self.connections)} connections"
        except Exception as e:
            self.status_message = f"Error loading connections: {str(e)}"
            self.connections = []
            self.filtered_connections = []
    
    def apply_search_filter(self) -> None:
        """
        Apply search filter to connections.
        """
        if not self.search_query:
            self.filtered_connections = self.connections.copy()
        else:
            query_lower = self.search_query.lower()
            self.filtered_connections = [
                conn for conn in self.connections
                if (query_lower in conn.get('alias', '').lower() or
                    query_lower in conn.get('host_or_ip', '').lower() or
                    query_lower in conn.get('protocol', '').lower() or
                    query_lower in conn.get('tag', '').lower())
            ]
        
        # Reset selection if it's out of bounds
        if self.current_selection >= len(self.filtered_connections):
            self.current_selection = max(0, len(self.filtered_connections) - 1)
    
    def draw_screen(self, stdscr) -> None:
        """
        Draw the main screen.
        """
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        if self.show_help:
            self.draw_help_screen(stdscr)
            return
        
        # Draw header
        self.draw_header(stdscr, width)
        
        # Draw search bar
        search_y = 2
        self.draw_search_bar(stdscr, search_y, width)
        
        # Draw connections list
        list_start_y = 4
        list_height = height - 7  # Leave space for header, search, and footer
        self.draw_connections_list(stdscr, list_start_y, list_height, width)
        
        # Draw footer with controls
        self.draw_footer(stdscr, height - 2, width)
        
        # Draw status message
        if self.status_message:
            stdscr.addstr(height - 1, 0, self.status_message[:width-1], 
                         curses.color_pair(3) if "Error" not in self.status_message else curses.color_pair(4))
        
        stdscr.refresh()
    
    def draw_header(self, stdscr, width: int) -> None:
        """
        Draw the header bar.
        """
        title = "Connection Manager TUI"
        count_text = f"({len(self.filtered_connections)}/{len(self.connections)} connections)"
        header_text = f"{title} {count_text}"
        
        # Center the header
        x = max(0, (width - len(header_text)) // 2)
        stdscr.addstr(0, x, header_text, curses.color_pair(1) | curses.A_BOLD)
    
    def draw_search_bar(self, stdscr, y: int, width: int) -> None:
        """
        Draw the search bar.
        """
        search_text = f"Search: {self.search_query}"
        if self.search_mode:
            search_text += "_"  # Show cursor
        
        stdscr.addstr(y, 0, search_text[:width-1])
        
        if self.search_mode:
            # Show search mode indicator
            stdscr.addstr(y, min(len(search_text), width-10), "[SEARCH]", curses.color_pair(6))
    
    def draw_connections_list(self, stdscr, start_y: int, height: int, width: int) -> None:
        """
        Draw the connections list.
        """
        if not self.filtered_connections:
            stdscr.addstr(start_y + height//2, (width - 20)//2, "No connections found", curses.color_pair(5))
            return
        
        # Calculate visible range
        visible_start = max(0, self.current_selection - height//2)
        visible_end = min(len(self.filtered_connections), visible_start + height)
        
        # Draw column headers
        headers = f"{'ID':<4} {'Alias':<20} {'Protocol':<8} {'Host/IP':<25} {'Tag':<15}"
        stdscr.addstr(start_y, 0, headers[:width-1], curses.A_BOLD)
        
        # Draw connections
        for i in range(visible_start, visible_end):
            conn = self.filtered_connections[i]
            y = start_y + 1 + (i - visible_start)
            
            # Format connection line
            line = f"{conn.get('id', 0):<4} {conn.get('alias', ''):<20} {conn.get('protocol', ''):<8} {conn.get('host_or_ip', ''):<25} {conn.get('tag', '') or '':<15}"
            
            # Highlight selected line with reverse video (works better with themes)
            if i == self.current_selection:
                attr = curses.A_REVERSE | curses.A_BOLD
            else:
                attr = 0
            stdscr.addstr(y, 0, line[:width-1], attr)
    
    def draw_footer(self, stdscr, y: int, width: int) -> None:
        """
        Draw the footer with key bindings.
        """
        controls = "↑↓:Navigate | Enter:Exit&Connect | a:Add | e:Edit | d:Delete | /:Search | r:Refresh | h:Help | q:Quit"
        stdscr.addstr(y, 0, controls[:width-1], curses.color_pair(6))
    
    def draw_help_screen(self, stdscr) -> None:
        """
        Draw the help screen.
        """
        height, width = stdscr.getmaxyx()
        
        help_text = [
            "Connection Manager TUI - Help",
            "",
            "Navigation:",
            "  ↑/k        - Move up",
            "  ↓/j        - Move down", 
            "  Home/g     - Go to first connection",
            "  End/G      - Go to last connection",
            "",
            "Actions:",
            "  Enter      - Exit TUI and connect to selected connection",
            "  a          - Add new connection",
            "  e          - Edit selected connection", 
            "  d          - Delete selected connection",
            "  r          - Refresh connections list",
            "",
            "Search:",
            "  /          - Enter search mode",
            "  Esc        - Exit search mode",
            "  Ctrl+C     - Clear search",
            "",
            "Other:",
            "  h/?        - Show/hide this help",
            "  q/Ctrl+C   - Quit application",
            "",
            "Press any key to return..."
        ]
        
        # Center the help text
        start_y = max(0, (height - len(help_text)) // 2)
        for i, line in enumerate(help_text):
            if start_y + i < height - 1:
                x = max(0, (width - len(line)) // 2)
                attr = curses.A_BOLD if i == 0 else 0
                stdscr.addstr(start_y + i, x, line[:width-1], attr)
    
    def handle_key(self, stdscr, key: int) -> bool:
        """
        Handle keyboard input. Returns True if should exit.
        """
        if self.show_help:
            self.show_help = False
            return False
        
        if self.search_mode:
            return self.handle_search_key(key)
        
        # Navigation keys
        if key in [curses.KEY_UP, ord('k')]:
            self.current_selection = max(0, self.current_selection - 1)
        elif key in [curses.KEY_DOWN, ord('j')]:
            self.current_selection = min(len(self.filtered_connections) - 1, self.current_selection + 1)
        elif key in [curses.KEY_HOME, ord('g')]:
            self.current_selection = 0
        elif key in [curses.KEY_END, ord('G')]:
            self.current_selection = max(0, len(self.filtered_connections) - 1)
        
        # Action keys
        elif key in [ord('\n'), ord('\r'), curses.KEY_ENTER, 10, 13]:
            self.connect_to_selected()
            if self.connection_requested:
                return True  # Exit TUI to connect
        elif key == ord('a'):
            self.add_connection(stdscr)
        elif key == ord('e'):
            self.edit_selected_connection(stdscr)
        elif key == ord('d'):
            self.delete_selected_connection(stdscr)
        elif key == ord('r'):
            self.refresh_connections()
        elif key == ord('/'):
            self.search_mode = True
            self.search_input = ""
        elif key in [ord('h'), ord('?')]:
            self.show_help = True
        elif key in [ord('q'), 3]:  # 'q' or Ctrl+C
            return True
        
        # Clear status message after navigation/action keys
        if key not in [ord('/'), ord('h'), ord('?')]:
            self.status_message = ""
        return False
    
    def handle_search_key(self, key: int) -> bool:
        """
        Handle keyboard input in search mode.
        """
        if key == 27:  # Escape
            self.search_mode = False
            self.search_input = ""
        elif key == 3:  # Ctrl+C
            self.search_mode = False
            self.search_input = ""
            self.search_query = ""
            self.apply_search_filter()
        elif key in [ord('\n'), curses.KEY_ENTER]:
            self.search_mode = False
            self.search_query = self.search_input
            self.apply_search_filter()
        elif key in [curses.KEY_BACKSPACE, 127, 8]:
            self.search_input = self.search_input[:-1]
        elif 32 <= key <= 126:  # Printable characters
            self.search_input += chr(key)
        
        return False
    
    def connect_to_selected(self) -> None:
        """
        Request connection to the currently selected connection.
        This will exit the TUI and return the connection alias/id.
        """
        if not self.filtered_connections or self.current_selection >= len(self.filtered_connections):
            self.status_message = "No connection selected"
            return
        
        conn = self.filtered_connections[self.current_selection]
        alias_or_id = conn.get('alias') or str(conn.get('id'))
        
        # Set the connection request and exit TUI
        self.connection_requested = alias_or_id
        self.status_message = f"Exiting TUI to connect to {alias_or_id}..."
    
    def add_connection(self, stdscr) -> None:
        """
        Add a new connection using a form interface.
        """
        try:
            # Temporarily exit curses mode for the prompter
            curses.endwin()
            self.service.add_connection()
            # Re-initialize curses
            stdscr.refresh()
            self.refresh_connections()
            self.status_message = "Connection added successfully"
        except Exception as e:
            self.status_message = f"Error adding connection: {str(e)}"
        finally:
            # Ensure curses is re-initialized
            stdscr.keypad(True)
            curses.curs_set(0)
    
    def edit_selected_connection(self, stdscr) -> None:
        """
        Edit the currently selected connection.
        """
        if not self.filtered_connections or self.current_selection >= len(self.filtered_connections):
            self.status_message = "No connection selected"
            return
        
        conn = self.filtered_connections[self.current_selection]
        alias_or_id = conn.get('alias') or str(conn.get('id'))
        
        try:
            # Temporarily exit curses mode for the prompter
            curses.endwin()
            self.service.edit_connection(alias_or_id)
            # Re-initialize curses
            stdscr.refresh()
            self.refresh_connections()
            self.status_message = f"Connection {alias_or_id} updated successfully"
        except Exception as e:
            self.status_message = f"Error editing connection: {str(e)}"
        finally:
            # Ensure curses is re-initialized
            stdscr.keypad(True)
            curses.curs_set(0)
    
    def delete_selected_connection(self, stdscr) -> None:
        """
        Delete the currently selected connection with confirmation.
        """
        if not self.filtered_connections or self.current_selection >= len(self.filtered_connections):
            self.status_message = "No connection selected"
            return
        
        conn = self.filtered_connections[self.current_selection]
        alias = conn.get('alias', 'Unknown')
        
        # Simple confirmation (in a real implementation, you might want a proper dialog)
        try:
            curses.endwin()
            confirm = input(f"Delete connection '{alias}'? (y/N): ").strip().lower()
            stdscr.refresh()
            
            if confirm == 'y':
                alias_or_id = conn.get('alias') or str(conn.get('id'))
                self.service.delete_connection(alias_or_id)
                self.refresh_connections()
                self.status_message = f"Connection {alias} deleted successfully"
            else:
                self.status_message = "Delete cancelled"
        except Exception as e:
            self.status_message = f"Error deleting connection: {str(e)}"
        finally:
            stdscr.keypad(True)
            curses.curs_set(0)


def run_tui(connection_service: ConnectionService) -> Optional[str]:
    """
    Run the TUI application.
    Returns the alias/id of a connection to connect to, or None if no connection was requested.
    """
    tui = ConnectionManagerTUI(connection_service)
    try:
        curses.wrapper(tui.run)
        return tui.connection_requested
    except KeyboardInterrupt:
        return None
    except Exception as e:
        logger.error(f"TUI error: {e}")
        print(f"TUI error: {e}")
        return None
