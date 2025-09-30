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
        if self.search_mode:
            # Show what user is currently typing
            search_text = f"Search: {self.search_input}_"
            stdscr.addstr(y, 0, search_text[:width-10])
            # Show search mode indicator
            stdscr.addstr(y, min(len(search_text), width-10), "[TYPING]", curses.color_pair(6))
        else:
            # Show current applied search filter
            search_text = f"Search: {self.search_query}" if self.search_query else "Search: (press / to search)"
            stdscr.addstr(y, 0, search_text[:width-1])
    
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
        
        # Calculate dynamic column widths based on terminal width
        col_widths = self._calculate_column_widths(width)
        
        # Draw column headers
        headers = f"{'ID':<{col_widths['id']}} {'Alias':<{col_widths['alias']}} {'Protocol':<{col_widths['protocol']}} {'Host/IP':<{col_widths['host']}} {'Tag':<{col_widths['tag']}}"
        stdscr.addstr(start_y, 0, headers[:width-1], curses.A_BOLD)
        
        # Draw connections
        for i in range(visible_start, visible_end):
            conn = self.filtered_connections[i]
            y = start_y + 1 + (i - visible_start)
            
            # Format connection line with truncation
            conn_id = str(conn.get('id', 0))
            alias = self._truncate_text(conn.get('alias', ''), col_widths['alias'])
            protocol = self._truncate_text(conn.get('protocol', ''), col_widths['protocol'])
            host = self._truncate_text(conn.get('host_or_ip', ''), col_widths['host'])
            tag = self._truncate_text(conn.get('tag', '') or '', col_widths['tag'])
            
            line = f"{conn_id:<{col_widths['id']}} {alias:<{col_widths['alias']}} {protocol:<{col_widths['protocol']}} {host:<{col_widths['host']}} {tag:<{col_widths['tag']}}"
            
            # Highlight selected line with reverse video (works better with themes)
            if i == self.current_selection:
                attr = curses.A_REVERSE | curses.A_BOLD
            else:
                attr = 0
            stdscr.addstr(y, 0, line[:width-1], attr)
    
    def _calculate_column_widths(self, terminal_width: int) -> Dict[str, int]:
        """
        Calculate optimal column widths based on terminal width.
        """
        # Minimum widths for each column
        min_widths = {
            'id': 4,
            'alias': 12,
            'protocol': 8,
            'host': 15,
            'tag': 8
        }
        
        # Account for spaces between columns (4 spaces)
        spacing = 4
        available_width = terminal_width - spacing - 1  # -1 for safety margin
        
        # If terminal is too narrow, use minimum widths
        min_total = sum(min_widths.values())
        if available_width <= min_total:
            return min_widths
        
        # Distribute extra space, prioritizing host column since it tends to be longest
        extra_space = available_width - min_total
        
        # Give most extra space to host, some to alias, a bit to tag
        widths = min_widths.copy()
        
        # Distribute extra space: 50% to host, 30% to alias, 20% to tag
        host_extra = int(extra_space * 0.5)
        alias_extra = int(extra_space * 0.3)
        tag_extra = extra_space - host_extra - alias_extra
        
        widths['host'] += host_extra
        widths['alias'] += alias_extra
        widths['tag'] += tag_extra
        
        return widths
    
    def _truncate_text(self, text: str, max_width: int) -> str:
        """
        Truncate text to fit within max_width, adding ellipsis if needed.
        """
        if len(text) <= max_width:
            return text
        
        if max_width <= 3:
            return text[:max_width]
        
        # Use ellipsis for truncated text
        return text[:max_width-3] + "..."
    
    def draw_footer(self, stdscr, y: int, width: int) -> None:
        """
        Draw the footer with key bindings.
        """
        controls = "↑↓:Navigate | Enter:Exit&Connect | a:Add | e:Edit | d:Delete | /:Search | c:Clear | r:Refresh | h:Help | q:Quit"
        stdscr.addstr(y, 0, controls[:width-1], curses.color_pair(6))
    
    def draw_help_screen(self, stdscr) -> None:
        """
        Draw the help screen.
        """
        height, width = stdscr.getmaxyx()
        
        help_text = [
            "Connection Manager TUI - Help",
            "",
            "NAVIGATION:",
            "  ↑/k, ↓/j     Navigate up/down",
            "  Home/g       Go to first connection",
            "  End/G        Go to last connection",
            "",
            "ACTIONS:",
            "  Enter        Exit TUI and connect to selected connection",
            "  a            Add new connection",
            "  e            Edit selected connection", 
            "  d            Delete selected connection",
            "  r            Refresh connections list",
            "",
            "SEARCH:",
            "  /            Enter search mode (real-time filtering)",
            "  [typing]     Filter connections as you type",
            "  Enter        Apply search and exit search mode",
            "  Esc          Clear search and exit search mode",
            "  Ctrl+U       Clear search input (stay in search mode)",
            "  c            Clear active search (from main view)",
            "",
            "OTHER:",
            "  h, ?         Show/hide this help",
            "  q, Ctrl+C    Quit application",
            "",
            "Press any key to return to main screen..."
        ]
        
        # Left-align help text with some padding
        start_y = max(1, (height - len(help_text)) // 2)
        left_margin = 4
        
        for i, line in enumerate(help_text):
            if start_y + i < height - 1:
                if line and not line.startswith(" "):
                    # Section headers - bold and slightly indented
                    attr = curses.A_BOLD | curses.color_pair(1)
                    x = left_margin
                elif line.startswith("  "):
                    # Command descriptions - normal text, more indented
                    attr = 0
                    x = left_margin + 2
                else:
                    # Empty lines or other text
                    attr = 0
                    x = left_margin
                
                stdscr.addstr(start_y + i, x, line[:width-x-1], attr)
    
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
        elif key == ord('c') and self.search_query:  # Clear search (only if there's an active search)
            self.search_query = ""
            self.search_input = ""
            self.apply_search_filter()
            self.status_message = "Search cleared"
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
        if key == 27:  # Escape - clear search and exit search mode
            self.search_mode = False
            self.search_input = ""
            self.search_query = ""
            self.apply_search_filter()
        elif key == 21:  # Ctrl+U - clear current input but stay in search mode
            self.search_input = ""
            self.search_query = ""
            self.apply_search_filter()
        elif key in [ord('\n'), ord('\r'), curses.KEY_ENTER, 10, 13]:
            self.search_mode = False
            self.search_query = self.search_input
            self.apply_search_filter()
        elif key in [curses.KEY_BACKSPACE, 127, 8]:
            self.search_input = self.search_input[:-1]
            # Apply filter in real-time as user types
            self.search_query = self.search_input
            self.apply_search_filter()
        elif 32 <= key <= 126:  # Printable characters
            self.search_input += chr(key)
            # Apply filter in real-time as user types
            self.search_query = self.search_input
            self.apply_search_filter()
        
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
            # Use TUI-safe add connection that doesn't close database
            self._tui_add_connection()
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
    
    def _tui_add_connection(self) -> None:
        """
        TUI-safe version of add_connection that doesn't close the database.
        """
        try:
            connection_details = self.service.prompter.prompt_connection_fields()
            self.service.database.add_connection(**asdict(connection_details))
            logger.info("Connection added successfully.")
        except Exception as e:
            logger.error(f"Error adding connection: {e}")
            raise
    
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
            # Use TUI-safe edit connection that doesn't close database
            self._tui_edit_connection(alias_or_id)
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
    
    def _tui_edit_connection(self, alias_or_id: str) -> None:
        """
        TUI-safe version of edit_connection that doesn't close the database.
        """
        try:
            connection = self.service.database.get_connection(alias_or_id)
            if not connection:
                logger.info(f"No connection found with alias or ID '{alias_or_id}'.")
                return
            logger.info("Editing connection. Press Enter to keep the current value.")
            connection_details = self.service.prompter.prompt_connection_fields(existing=connection)
            try:
                self.service.database.update_connection(connection_details.alias, **asdict(connection_details))
                logger.info("Connection updated successfully.")
            except Exception as e:
                logger.error(f"Error updating connection: {e}")
                raise
        except Exception as e:
            logger.error(f"An error occurred while editing connection: {e}")
            raise
    
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
                # Use TUI-safe delete that doesn't close database
                self._tui_delete_connection(alias_or_id)
                self.refresh_connections()
                self.status_message = f"Connection {alias} deleted successfully"
            else:
                self.status_message = "Delete cancelled"
        except Exception as e:
            self.status_message = f"Error deleting connection: {str(e)}"
        finally:
            stdscr.keypad(True)
            curses.curs_set(0)
    
    def _tui_delete_connection(self, alias_or_id: str) -> None:
        """
        TUI-safe version of delete_connection that doesn't close the database.
        """
        try:
            self.service.database.delete_connection(alias_or_id)
            logger.info(f"Connection with alias or ID '{alias_or_id}' deleted successfully.")
        except Exception as e:
            logger.error(f"An error occurred while deleting connection: {e}")
            raise


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
