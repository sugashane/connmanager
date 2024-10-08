import json
import sqlite3


class DatabaseConnection:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Set the row_factory to sqlite3.Row
        self.cursor = self.conn.cursor()  # Initialize the cursor
        self.create_table()

    def create_table(self):
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
        alias,
        protocol,
        host_or_ip,
        port=None,
        username=None,
        password=None,
        ssh_key_path=None,
        domain=None,
        resolution=None,
        tag=None,
        extras=None,
    ):
        # Convert extras dictionary to a JSON string
        extras_json = json.dumps(extras) if extras else "{}"
        # cursor = self.conn.cursor()
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

    def delete_connection(self, alias_or_id):
        try:
            query = "DELETE FROM connections WHERE alias = ? OR id = ?"
            self.cursor.execute(query, (alias_or_id, alias_or_id))
            self.conn.commit()
        except Exception as e:
            print(f"An error occurred while deleting the connection: {e}")
            self.conn.rollback()

    def edit_connection(
        self, connection_id, protocol, host_or_ip, port, username, password
    ):
        # cursor = self.conn.cursor()
        self.cursor.execute(
            """
            UPDATE connections
            SET protocol=?, host_or_ip=?, port=?, username=?, password=?
            WHERE id=?
        """,
            (protocol, host_or_ip, port, username, password, connection_id),
        )
        self.conn.commit()

    def search_connections(self, search_info):
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
                return [dict(zip(columns, result)) for result in results]
            return []
        except Exception as e:
            print(f"An error occurred while searching for connections: {e}")
            return []

    def get_connections_by_protocol(self, protocol):
        try:
            self.cursor.execute(
                "SELECT * FROM connections WHERE protocol = ?", (protocol,)
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return []

    def get_connection_summary(self):
        try:
            self.cursor.execute(
                "SELECT id, alias, protocol, host_or_ip, tag FROM connections ORDER BY id"
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return []

    def get_connection_by_alias(self, alias):
        self.cursor.execute("SELECT * FROM connections WHERE alias = ?", (alias,))
        row = self.cursor.fetchone()
        if row:
            return dict(row)
        else:
            raise ValueError(f"Connection with alias '{alias}' not found")

    def get_connection_by_id(self, id):
        self.cursor.execute("SELECT * FROM connections WHERE id = ?", (id,))
        row = self.cursor.fetchone()
        if row:
            return dict(row)
        else:
            raise ValueError(f"Connection with id '{id}' not found")

    def get_connection(self, alias_or_id):
        try:
            query = "SELECT * FROM connections WHERE alias = ? OR id = ?"
            self.cursor.execute(query, (alias_or_id, alias_or_id))
            result = self.cursor.fetchone()
            if result:
                columns = [column[0] for column in self.cursor.description]
                return dict(zip(columns, result))
            return None
        except Exception as e:
            print(f"An error occurred while retrieving the connection: {e}")
            return None

    def update_connection(self, alias_or_id, **connection_details):
        try:
            # Construct the update query
            set_clause = ", ".join([f"{key} = ?" for key in connection_details.keys()])
            query = f"UPDATE connections SET {set_clause} WHERE alias = ? OR id = ?"
            params = list(connection_details.values()) + [alias_or_id, alias_or_id]

            # Execute the update query
            self.cursor.execute(query, params)
            self.conn.commit()
        except Exception as e:
            print(f"An error occurred while updating the connection: {e}")
            self.conn.rollback()

    def get_all_connections(self):
        try:
            self.cursor.execute("SELECT * FROM connections")
            results = self.cursor.fetchall()
            if results:
                columns = [column[0] for column in self.cursor.description]
                return [dict(zip(columns, result)) for result in results]
            return []
        except Exception as e:
            print(f"An error occurred while retrieving all connections: {e}")
            return []

    def alias_exists(self, alias):
        query = "SELECT COUNT(*) FROM connections WHERE alias = ?"
        # cursor = self.conn.cursor()
        self.cursor.execute(query, (alias,))
        return self.cursor.fetchone()[0] > 0

    def close(self):
        self.cursor.close()  # Close the cursor
        self.conn.close()  # Close the connection
