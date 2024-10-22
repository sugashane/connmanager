import getpass
import json

from connmanager.connection_handler import (
    ConnectionHandlerException,
    RDPHandler,
    SSHHandler,
    VMRCHandler,
    VNCHandler,
)
from connmanager.print_table import print_json_as_table

PROTOCOLS = ["ssh", "rdp", "vnc", "vmrc"]


class ConnectionService:
    def __init__(self, database):
        self.database = database

    def password_comparison(self):
        password1 = getpass.getpass("Enter the password: ")
        password2 = getpass.getpass("Re-enter the password: ")
        if password1 == password2:
            return password1
        else:
            print("Passwords do not match. Please try again.")
            return self.password_comparison()

    def is_ipv6(self, ip):
        if ":" in ip:
            return True
        return False

    def add_connection(self):
        while True:
            alias = input("Enter a unique alias for the connection: ")
            # Check if the alias already exists
            if alias.isdigit():
                print(
                    "Invalid alias. The alias cannot be only digits. Please try again."
                )
            elif self.database.alias_exists(alias):
                print("This alias already exists. Please choose a different one.")
            else:
                break

        while True:
            protocol = input(f"Enter the protocol (e.g. {', '.join(PROTOCOLS)}): ")
            if protocol not in PROTOCOLS:
                print(f"Invalid protocol. Please enter {', '.join(PROTOCOLS)}.")
            else:
                break

        if protocol.casefold() == "vmrc":
            host_or_ip = input(
                "Enter vmrc URL (e.g. vmrc://<esxi-host>/?moid=<vmid>): "
            )
            port = None
            username = None
        else:
            while True:
                host_or_ip = input("Enter the hostname or IP address: ")
                if not host_or_ip:
                    print("Invalid hostname or IP address. Please try again.")
                else:
                    break

            port = input("Enter the port (press Enter for default): ") or None
            username = (
                input("Enter the username (press Enter if not applicable): ") or None
            )
        password = None
        ssh_key_path = None
        domain = None
        resolution = None
        tag = None

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
                ssh_key_path = (
                    input(
                        "Enter path to SSH private key (default is ~/.ssh/id_rsa): "
                    ).strip()
                    or "~/.ssh/id_rsa"
                )
            else:
                password = self.password_comparison()
        elif protocol.casefold() == "rdp":
            if (
                self.is_ipv6(host_or_ip)
                and not host_or_ip.startswith("[")
                and not host_or_ip.endswith("]")
            ):
                host_or_ip = f"[{host_or_ip}]"
            password = self.password_comparison()
            domain = input("Enter the domain (press Enter if not applicable): ") or None
            resolution = input("Enter the resolution (e.g., 1920x1080): ") or None
        # Add other protocol-specific fields as needed

        while True:
            tag = input("Enter an optional tag (i.e lab, tools, personal): ") or None
            if tag in PROTOCOLS:
                print("Invalid tag. Unable to use protocol as a tag.")
            else:
                break

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
                "tag": tag,
                "extras": extras,
            }
            # Filter out None values, as they are not needed
            connection_details = {
                k: v for k, v in connection_details.items() if v is not None
            }

            self.database.add_connection(**connection_details)
            print("Connection added successfully.")
        except Exception as e:
            print(f"Error adding connection: {e}")
        finally:
            self.database.close()

    def edit_connection(self, alias_or_id):
        try:
            # Retrieve the existing connection details
            connection = self.database.get_connection(alias_or_id)
            if not connection:
                print(f"No connection found with alias or ID '{alias_or_id}'.")
                return

            print("Editing connection. Press Enter to keep the current value.")

            # Display current values and prompt for new values
            alias = input(f"Alias [{connection['alias']}]: ") or connection["alias"]
            protocol = (
                input(f"Protocol [{connection['protocol']}]: ")
                or connection["protocol"]
            )
            host_or_ip = (
                input(f"Hostname or IP [{connection['host_or_ip']}]: ")
                or connection["host_or_ip"]
            )
            port = input(f"Port [{connection.get('port', '')}]: ") or connection.get(
                "port", None
            )
            username = input(
                f"Username [{connection.get('username', '')}]: "
            ) or connection.get("username", None)
            password = None
            ssh_key_path = None
            domain = None
            resolution = None

            # Protocol-specific fields
            if protocol.casefold() == "ssh":
                auth_method = input(
                    f"Authentication method (password/key) [{connection.get('ssh_key_path', 'password')}]: "
                ).strip().lower() or (
                    "key" if connection.get("ssh_key_path") else "password"
                )
                if auth_method == "key":
                    ssh_key_path = input(
                        f"SSH key path [{connection.get('ssh_key_path', '')}]: "
                    ).strip() or connection.get("ssh_key_path", None)
                else:
                    password = getpass.getpass(
                        "Enter the password (press Enter to keep current): "
                    ) or connection.get("password", None)
            elif protocol.casefold() == "rdp":
                password = getpass.getpass(
                    "Enter the password (press Enter to keep current): "
                ) or connection.get("password", None)
                domain = input(
                    f"Domain [{connection.get('domain', '')}]: "
                ) or connection.get("domain", None)
                resolution = input(
                    f"Resolution [{connection.get('resolution', '')}]: "
                ) or connection.get("resolution", None)
            # Add other protocol-specific fields as needed
            # Collect extras
            extras = connection.get("extras", {})
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
                self.database.update_connection(alias_or_id, **connection_details)
                print("Connection updated successfully.")
            except Exception as e:
                print(f"Error updating connection: {e}")
            finally:
                self.database.close()
        except Exception as e:
            print(f"An error occurred while editing connection: {e}")

    def delete_connection(self, alias_or_id):
        try:
            # Delete the connection from the database
            self.database.delete_connection(alias_or_id)
            print(f"Connection '{alias_or_id}' deleted successfully.")
        except Exception as e:
            print(f"An error occurred while deleting connection: {e}")
        finally:
            self.database.close()

    def get_connections_summary(self, protocol_or_tag):
        try:
            connections = self.database.get_connection_summary()
            if protocol_or_tag:
                if protocol_or_tag in PROTOCOLS:
                    connections = [
                        x for x in connections if x["protocol"] == protocol_or_tag
                    ]
                else:
                    connections = [
                        x for x in connections if x["tag"] == protocol_or_tag
                    ]
            if connections:
                print_json_as_table(connections)
            else:
                print("No connections found.")
        except Exception as e:
            print(f"An error occurred while getting connections {e}")
        finally:
            self.database.close()

    def search_connections(self, search_info):
        try:
            # Search for connections in the database
            results = self.database.search_connections(search_info)
            if results:
                print_json_as_table(results, title="Search Results")
            else:
                print("No connections found matching the search criteria.")
        except Exception as e:
            print(f"An error occurred while searching for connections: {e}")
        finally:
            self.database.close()

    def connect_to_alias_or_id(self, alias_or_id):
        try:
            if alias_or_id.isdigit():
                connection_details = self.database.get_connection_by_id(
                    int(alias_or_id)
                )
            else:
                connection_details = self.database.get_connection_by_alias(alias_or_id)
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
                    ssh_handler = SSHHandler(
                        host_or_ip, username, password, ssh_key_path
                    )
                    ssh_handler.connect()
                except ConnectionHandlerException:
                    print("SSH connection failed/timed out")
            elif protocol.casefold() == "rdp":
                try:
                    rdp_handler = RDPHandler(
                        host_or_ip, username, password, domain, resolution
                    )
                    rdp_handler.connect()
                except ConnectionHandlerException:
                    print(f"RDP connection failed/timed out")
            elif protocol.casefold() == "vmrc":
                try:
                    vmrc_handler = VMRCHandler(host_or_ip)
                    vmrc_handler.connect()
                except ConnectionHandlerException as e:
                    print(f"VMRC connection failed/timed out")
            elif protocol.casefold() == "vnc":
                try:
                    vnc_handler = VNCHandler(host_or_ip, username, password)
                    vnc_handler.connect()
                except ConnectionHandlerException as e:
                    print(f"VNC: Error establishing connection: {e}")
            else:
                print(f"Unsupported protocol: {protocol}")

        except Exception as e:
            print(f"An error occurred while connecting: {e}")
        finally:
            self.database.close()

    def import_connections(self, json_file):
        try:
            with open(json_file, "r") as file:
                connections = json.load(file)
                for connection in connections:
                    # Remove the 'id' field if it exists
                    connection.pop("id", None)
                    alias = connection.get("alias")
                    if self.database.alias_exists(alias):
                        choice = (
                            input(
                                f"Alias '{alias}' already exists. Do you want to overwrite it? (y/n): "
                            )
                            .strip()
                            .lower()
                        )
                        if choice == "y":
                            self.database.update_connection(alias, **connection)
                            print(f"Connection '{alias}' overwritten.")
                        else:
                            print(f"Connection '{alias}' skipped.")
                    else:
                        self.database.add_connection(**connection)
                        print(f"Connection '{alias}' added.")
            print(f"Connections imported successfully from {json_file}.")
        except Exception as e:
            print(f"An error occurred while importing connections: {e}")
        finally:
            self.database.close()

    def export_connections(self, json_file):
        try:
            connections = self.database.get_all_connections()
            for connection in connections:
                connection.pop("id", None)
            with open(json_file, "w") as file:
                json.dump(connections, file, indent=4)
            print(f"Connections exported successfully to {json_file}.")
        except Exception as e:
            print(f"An error occurred while exporting connections: {e}")
        finally:
            self.database.close()
