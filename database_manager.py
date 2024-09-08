import json
from getpass import getpass

from print_table import print_json_as_table


class DatabaseManager:
    def __init__(self):
        pass

    def add_connection(self, database):
        while True:
            alias = input("Enter a unique alias for the connection: ")
            # Check if the alias already exists
            if alias.isdigit():
                print(
                    "Invalid alias. The alias cannot be only digits. Please try again."
                )
            elif database.alias_exists(alias):
                print("This alias already exists. Please choose a different one.")
            else:
                break

        while True:
            protocol = input("Enter the protocol (e.g., ssh, rdp, vnc): ")
            if protocol.lower() not in ("ssh", "rdp", "vnc"):
                print("Invalid protocol. Please enter 'ssh', 'rdp', or 'vnc'.")
            else:
                break

        while True:
            host_or_ip = input("Enter the hostname or IP address: ")
            if host_or_ip == "":
                print("Invalid hostname or IP address. Please try again.")
            else:
                break

        protocol = input("Enter the protocol (e.g., ssh, rdp, vnc): ")
        host_or_ip = input("Enter the hostname or IP address: ")
        port = input("Enter the port (press Enter for default): ") or None
        username = input("Enter the username (press Enter if not applicable): ") or None
        password = None
        ssh_key_path = None
        domain = None
        resolution = None

        # Protocol-specific fields
        if protocol.casefold() == "ssh":
            auth_method = (
                input(
                    "Choose authentication method, password or key (default: password): "
                )
                .strip()
                .lower()
            )
            if auth_method == "key":
                ssh_key_path = input(
                    "Enter the path to the SSH private key file: "
                ).strip()
            else:
                password = (
                    getpass("Enter the password (press Enter if not applicable): ")
                    or None
                )
        elif protocol.casefold() == "rdp":
            password = (
                getpass("Enter the password (press Enter if not applicable): ") or None
            )
            domain = input("Enter the domain (press Enter if not applicable): ") or None
            resolution = input("Enter the resolution (e.g., 1920x1080): ") or None
        # Add other protocol-specific fields as needed

        # Collect extras
        extras = {}
        print("Enter extra options (key=value). Type 'done' when finished:")
        while True:
            extra = input().strip()
            if extra.lower() == "done":
                break
            try:
                key, value = extra.split("=")
                extras[key.strip()] = value.strip()
            except ValueError:
                print(
                    "Invalid format for extra options. Please use 'key=value' format."
                )
        try:
            # Use a dictionary to pass only relevant fields based on the protocol
            connection_details = {
                "alias": alias,
                "protocol": protocol,
                "host_or_ip": host_or_ip,
                "port": port,
                "username": username,
                "password": password,
                "ssh_key_path": ssh_key_path,
                "domain": domain,
                "resolution": resolution,
                "extras": extras,
            }

            # Filter out None values, as they are not needed
            connection_details = {
                k: v for k, v in connection_details.items() if v is not None
            }

            database.add_connection(**connection_details)
            print("Connection added successfully.")
        except Exception as e:
            print(f"Error adding connection: {e}")
        finally:
            database.close()

    def delete_connection(self, database, alias):
        try:
            # Delete the connection from the database
            database.delete_connection(alias)
            print(f"Connection '{alias}' deleted successfully.")
        except Exception as e:
            print(f"An error occurred while deleting connection: {e}")
        finally:
            database.close()

    def edit_connection(self, database, alias_or_id):
        # Implement the logic to edit a connection
        # current_data = database.get_connection_by_protocol(alias, protocol)
        if alias_or_id.isdigit():
            connection_details = database.get_connection_by_id(int(alias_or_id))
        else:
            connection_details = database.get_connection_by_alias(alias_or_id)
        if not connection_details:
            print(f"No connection found with alias or ID of: '{alias_or_id}'.")
            return

        print(f"Editing connection '{alias_or_id}'")
        pass

    def get_connections_by_protocol(self, database, protocol, detail_level):
        try:
            # Fetch the connections from the database
            connections = database.get_connections_by_protocol(protocol)

            if detail_level == "summary":
                # Print a summary (e.g., just the aliases)
                print(f"List of '{protocol}' connections:")
                for connection in connections:
                    print(connection["alias"])
            elif detail_level == "all":
                # Print full details of each connection
                print(f"Full details of '{protocol}' connections:")
                print_json_as_table(
                    json.dumps(connections), f"{protocol.upper()} Connections"
                )
                # for connection in connections:
                #     print(json.dumps(connection, indent=4))
        except Exception as e:
            print(f"An error occurred while listing connections: {e}")
        finally:
            database.close()

    def get_connections_summary(self, database, protocol):
        try:
            connections = database.get_connection_summary()
            if protocol:
                proto_connections = [
                    x for x in connections if x["protocol"] == protocol
                ]
                print_json_as_table(proto_connections)
            else:
                print_json_as_table(connections)
        except Exception as e:
            print(f"An error occurred while getting connections {e}")
        finally:
            database.close()

    def find_connection(self, database, protocol, alias):
        # Implement the logic to find a connection by alias
        pass

    def connect_to_alias_or_id(self, database, alias_or_id):
        if alias_or_id.isdigit():
            connection_details = database.get_connection_by_id(int(alias_or_id))
        else:
            connection_details = database.get_connection_by_alias(alias_or_id)
        if not connection_details:
            print(f"No connection found with alias or ID of: '{alias_or_id}'.")
            return

        # Extract common connection parameters
        host_or_ip = connection_details["host_or_ip"]
        username = connection_details["username"]
        password = connection_details["password"]
        protocol = connection_details["protocol"]
        domain = connection_details["domain"]
        resolution = connection_details["resolution"]
        ssh_key_path = connection_details["ssh_key_path"]

        # Determine the protocol and create the appropriate handler
        if protocol.casefold() == "ssh":
            try:
                ssh_handler = SSHHandler(host_or_ip, username, password, ssh_key_path)
                ssh_handler.connect()
                print("SSH: Connection Established")
            except ConnectionHandlerException as e:
                print(f"SSH: Error establishing connection: {e}")
        if protocol.casefold() == "rdp":
            try:
                rdp_handler = RDPHandler(
                    host_or_ip, username, password, domain, resolution
                )
                rdp_handler.connect()
                print("RDP: Connection Established")
            except ConnectionHandlerException as e:
                print(f"RDP: Error establishing connection: {e}")
        # Handle other protocols similarly...

        # Don't forget to close your database connection when done
        database.close()
