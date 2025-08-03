
"""
Database connection and management for remote connection manager.
Handles CRUD operations and conversion to ConnectionDetails dataclass.
"""

import json
import sqlite3
import logging
from typing import Optional, Dict, Any, List, Union
from connmanager.connection_prompter import ConnectionDetails

# Set up logging
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Handles all database operations for connection management.
    """
    def __init__(self, db_path: str):
        """
        Initialize the database connection and create the table if needed.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self) -> None:
        """
        Create the connections table if it does not exist.
        """
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY,
                alias TEXT UNIQUE NOT NULL,
                protocol TEXT NOT NULL,
                host_or_ip TEXT NOT NULL,
                port INTEGER,
                username TEXT,
                password TEXT,
                ssh_key_path TEXT,
                domain TEXT,
                resolution TEXT,
                tag TEXT,
                extras TEXT
            )
        """
        )
        self.conn.commit()

    def add_connection(
        self,
        alias: str,
        protocol: str,
        host_or_ip: str,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        ssh_key_path: Optional[str] = None,
        domain: Optional[str] = None,
        resolution: Optional[str] = None,
        tag: Optional[str] = None,
        extras: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Add a new connection to the database.
        """
        extras_json = json.dumps(extras) if extras else "{}"
        try:
            self.cursor.execute(
            """
            INSERT INTO connections (alias, protocol, host_or_ip, port, username, password, ssh_key_path, domain, resolution, tag, extras)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                alias,
                protocol,
                host_or_ip,
                port,
                username,
                password,
                ssh_key_path,
                domain,
                resolution,
                tag,
                extras_json,
            ),
        )
            self.conn.commit()
            logger.info(f"Added connection '{alias}' to database.")
        except Exception as e:
            logger.error(f"Error adding connection '{alias}': {e}")
            self.conn.rollback()

    def delete_connection(self, alias_or_id: Union[str, int]) -> None:
        """
        Delete a connection by alias or id.
        """
        try:
            query = "DELETE FROM connections WHERE alias = ? OR id = ?"
            self.cursor.execute(query, (alias_or_id, alias_or_id))
            self.conn.commit()
            logger.info(f"Deleted connection '{alias_or_id}' from database.")
        except Exception as e:
            logger.error(f"An error occurred while deleting the connection: {e}")
            self.conn.rollback()

    def edit_connection(
        self,
        connection_id: int,
        protocol: str,
        host_or_ip: str,
        port: Optional[int],
        username: Optional[str],
        password: Optional[str],
    ) -> None:
        """
        Edit an existing connection by id.
        """
        try:
            self.cursor.execute(
                """
                UPDATE connections
                SET protocol=?, host_or_ip=?, port=?, username=?, password=?
                WHERE id=?
            """,
                (protocol, host_or_ip, port, username, password, connection_id),
            )
            self.conn.commit()
            logger.info(f"Edited connection id '{connection_id}'.")
        except Exception as e:
            logger.error(f"Error editing connection id '{connection_id}': {e}")
            self.conn.rollback()

    def search_connections(self, search_info: str) -> List[Dict[str, Any]]:
        """
        Search for connections matching the search_info string.
        """
        try:
            query = """
            SELECT id, alias, protocol, host_or_ip, tag FROM connections
            WHERE alias LIKE ? OR host_or_ip LIKE ? OR username LIKE ? OR protocol LIKE ? OR tag LIKE ?
            """
            search_pattern = f"%{search_info}%"
            self.cursor.execute(
                query,
                (
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    search_pattern,
                ),
            )
            results = self.cursor.fetchall()
            if results:
                columns = [column[0] for column in self.cursor.description]
                logger.debug(f"Found {len(results)} search results for '{search_info}'.")
                return [dict(zip(columns, result)) for result in results]
            logger.info(f"No connections found for search '{search_info}'.")
            return []
        except Exception as e:
            logger.error(f"An error occurred while searching for connections: {e}")
            return []

    def get_connections_by_protocol(self, protocol: str) -> List[Dict[str, Any]]:
        """
        Get all connections for a given protocol.
        """
        try:
            self.cursor.execute(
                "SELECT * FROM connections WHERE protocol = ?", (protocol,)
            )
            results = [dict(row) for row in self.cursor.fetchall()]
            logger.debug(f"Found {len(results)} connections for protocol '{protocol}'.")
            return results
        except sqlite3.Error as e:
            logger.error(f"An error occurred: {e}")
            return []

    def get_connection_summary(self) -> List[Dict[str, Any]]:
        """
        Get a summary of all connections.
        """
        try:
            self.cursor.execute(
                "SELECT id, alias, protocol, host_or_ip, tag FROM connections ORDER BY id"
            )
            results = [dict(row) for row in self.cursor.fetchall()]
            logger.debug(f"Returning summary for {len(results)} connections.")
            return results
        except sqlite3.Error as e:
            logger.error(f"An error occurred: {e}")
            return []

    def get_connection_by_alias(self, alias: str) -> ConnectionDetails:
        """
        Get a connection by its alias.
        """
        self.cursor.execute("SELECT * FROM connections WHERE alias = ?", (alias,))
        row = self.cursor.fetchone()
        if row:
            logger.debug(f"Found connection for alias '{alias}'.")
            return self._row_to_connection_details(row)
        else:
            logger.info(f"Connection with alias '{alias}' not found.")
            raise ValueError(f"Connection with alias '{alias}' not found")

    def get_connection_by_id(self, id: int) -> ConnectionDetails:
        """
        Get a connection by its id.
        """
        self.cursor.execute("SELECT * FROM connections WHERE id = ?", (id,))
        row = self.cursor.fetchone()
        if row:
            logger.debug(f"Found connection for id '{id}'.")
            return self._row_to_connection_details(row)
        else:
            logger.info(f"Connection with id '{id}' not found.")
            raise ValueError(f"Connection with id '{id}' not found")

    def get_connection(self, alias_or_id: Union[str, int]) -> Optional[ConnectionDetails]:
        """
        Get a connection by alias or id.
        """
        try:
            query = "SELECT * FROM connections WHERE alias = ? OR id = ?"
            self.cursor.execute(query, (alias_or_id, alias_or_id))
            result = self.cursor.fetchone()
            if result:
                logger.debug(f"Found connection for '{alias_or_id}'.")
                return self._row_to_connection_details(result)
            logger.info(f"Connection '{alias_or_id}' not found.")
            return None
        except Exception as e:
            logger.error(f"An error occurred while retrieving the connection: {e}")
            return None

    def update_connection(self, alias_or_id: Union[str, int], **connection_details) -> None:
        """
        Update a connection by alias or id.
        """
        try:
            # Serialize 'extras' dict to JSON string if present
            if 'extras' in connection_details and isinstance(connection_details['extras'], dict):
                connection_details['extras'] = json.dumps(connection_details['extras'])
            set_clause = ", ".join([f"{key} = ?" for key in connection_details.keys()])
            query = f"UPDATE connections SET {set_clause} WHERE alias = ? OR id = ?"
            params = list(connection_details.values()) + [alias_or_id, alias_or_id]
            self.cursor.execute(query, params)
            self.conn.commit()
            logger.info(f"Updated connection '{alias_or_id}'.")
        except Exception as e:
            logger.error(f"An error occurred while updating the connection: {e}")
            self.conn.rollback()

    def get_all_connections(self) -> List[Dict[str, Any]]:
        """
        Get all connections in the database.
        """
        try:
            self.cursor.execute("SELECT * FROM connections")
            results = self.cursor.fetchall()
            if results:
                columns = [column[0] for column in self.cursor.description]
                logger.debug(f"Returning all {len(results)} connections.")
                return [dict(zip(columns, result)) for result in results]
            logger.info("No connections found in database.")
            return []
        except Exception as e:
            logger.error(f"An error occurred while retrieving all connections: {e}")
            return []

    def alias_exists(self, alias: str) -> bool:
        """
        Check if a connection alias exists in the database.
        """
        query = "SELECT COUNT(*) FROM connections WHERE alias = ?"
        self.cursor.execute(query, (alias,))
        exists = self.cursor.fetchone()[0] > 0
        logger.debug(f"Alias '{alias}' exists: {exists}")
        return exists

    def close(self) -> None:
        """
        Close the database connection and cursor.
        """
        self.cursor.close()
        self.conn.close()

    def _row_to_connection_details(self, row: sqlite3.Row) -> ConnectionDetails:
        """
        Convert a DB row to a ConnectionDetails dataclass, handling JSON for extras and str for port.
        """
        data = dict(row)
        alias = data.get("alias") or ""
        protocol = data.get("protocol") or ""
        host_or_ip = data.get("host_or_ip") or ""
        port = data.get("port")
        if port is not None and port != "":
            port = str(port)
        else:
            port = None
        extras = data.get("extras")
        if isinstance(extras, str):
            try:
                extras = json.loads(extras)
            except Exception:
                extras = {}
        elif not extras:
            extras = {}
        return ConnectionDetails(
            alias=alias,
            protocol=protocol,
            host_or_ip=host_or_ip,
            port=port,
            username=data.get("username"),
            password=data.get("password"),
            ssh_key_path=data.get("ssh_key_path"),
            domain=data.get("domain"),
            resolution=data.get("resolution"),
            tag=data.get("tag"),
            extras=extras,
        )
