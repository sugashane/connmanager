import getpass
import json
import logging
import sys
from dataclasses import asdict
from typing import Any, Optional

from connmanager.connection_prompter import ConnectionPrompter, ConnectionDetails, PROTOCOLS
from connmanager.connection_handler import ConnectionHandlerException, connection_handler_factory
from connmanager.print_table import print_json_as_table

logger = logging.getLogger(__name__)


class ConnectionService:
    """
    Service layer for managing connections and delegating to the database and prompter.
    """

    def __init__(self, database: Any) -> None:
        """
        Initialize the service with a database and prompter.
        """
        self.database = database
        self.prompter = ConnectionPrompter(database)

    def add_connection(self) -> None:
        """
        Add a new connection using user prompts.
        """
        try:
            connection_details = self.prompter.prompt_connection_fields()
            self.database.add_connection(**asdict(connection_details))
            logger.info("Connection added successfully.")
        except Exception as e:
            logger.error(f"Error adding connection: {e}")
        finally:
            self.database.close()

    def run_ssh_command(self, alias_or_id: str, command: str, timeout: Optional[float] = 30) -> None:
        """
        Run a command over SSH on a saved connection and print stdout/stderr.
        """
        try:
            if not command:
                logger.error("No remote command provided.")
                return

            if alias_or_id.isdigit():
                connection_details = self.database.get_connection_by_id(int(alias_or_id))
            else:
                connection_details = self.database.get_connection_by_alias(alias_or_id)

            protocol = getattr(connection_details, "protocol", None)
            if not protocol or protocol.lower() != "ssh":
                logger.error("ssh-run requires an SSH connection.")
                return

            from connmanager.connection_handler import SSHHandler

            raw_kwargs = {k: v for k, v in asdict(connection_details).items() if v is not None}

            # SSHHandler accepts: host_or_ip, port, username, password, ssh_key_path
            handler_kwargs = {
                k: v
                for k, v in raw_kwargs.items()
                if k in {"host_or_ip", "port", "username", "password", "ssh_key_path"}
            }

            handler = SSHHandler(**handler_kwargs)
            result = handler.run_command(command, timeout=timeout)

            if result.stdout:
                sys.stdout.write(result.stdout)
                if not result.stdout.endswith("\n"):
                    sys.stdout.write("\n")
            if result.stderr:
                sys.stderr.write(result.stderr)
                if not result.stderr.endswith("\n"):
                    sys.stderr.write("\n")

            if result.returncode != 0:
                logger.error(f"Remote command exited with status {result.returncode}.")
        except ConnectionHandlerException as e:
            logger.error(f"SSH command failed/timed out: {e}")
        except Exception as e:
            logger.error(f"An error occurred while running SSH command: {e}")
        finally:
            self.database.close()

    def edit_connection(self, alias_or_id: str) -> None:
        """
        Edit an existing connection by alias or id.
        """
        try:
            connection = self.database.get_connection(alias_or_id)
            if not connection:
                logger.info(f"No connection found with alias or ID '{alias_or_id}'.")
                return
            logger.info("Editing connection. Press Enter to keep the current value.")
            connection_details = self.prompter.prompt_connection_fields(existing=connection)
            try:
                # prompt_connection_fields always returns a ConnectionDetails dataclass
                from dataclasses import asdict
                update_kwargs = asdict(connection_details)
                self.database.update_connection(alias_or_id, **update_kwargs)
                logger.info("Connection updated successfully.")
            except Exception as e:
                logger.error(f"Error updating connection: {e}")
            finally:
                self.database.close()
        except Exception as e:
            logger.error(f"An error occurred while editing connection: {e}")

    def delete_connection(self, alias_or_id: str) -> None:
        """
        Delete a connection by alias or id.
        """
        try:
            self.database.delete_connection(alias_or_id)
            logger.info(f"Connection '{alias_or_id}' deleted successfully.")
        except Exception as e:
            logger.error(f"An error occurred while deleting connection: {e}")
        finally:
            self.database.close()

    def get_connections_summary(self, protocol_or_tag: Optional[str]) -> None:
        """
        Print a summary table of all connections, optionally filtered by protocol or tag.
        """
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
                logger.debug(f"Displayed {len(connections)} connections.")
            else:
                logger.info("No connections found.")
        except Exception as e:
            logger.error(f"An error occurred while getting connections {e}")
        finally:
            self.database.close()

    def search_connections(self, search_info: str) -> None:
        """
        Search for connections and print results as a table.
        """
        try:
            results = self.database.search_connections(search_info)
            if results:
                print_json_as_table(results, title="Search Results")
                logger.debug(f"Displayed {len(results)} search results.")
            else:
                logger.info("No connections found matching the search criteria.")
        except Exception as e:
            logger.error(f"An error occurred while searching for connections: {e}")
        finally:
            self.database.close()

    def connect_to_alias_or_id(self, alias_or_id: str) -> None:
        """
        Connect to a host by alias or id using the appropriate handler.
        """
        try:
            if alias_or_id.isdigit():
                connection_details = self.database.get_connection_by_id(int(alias_or_id))
            else:
                connection_details = self.database.get_connection_by_alias(alias_or_id)
            if not connection_details:
                logger.info(f"No connection found with alias or ID of: '{alias_or_id}'.")
                return

            if isinstance(connection_details, ConnectionDetails):
                protocol = connection_details.protocol
                raw_kwargs = {k: v for k, v in asdict(connection_details).items() if v is not None}
            else:
                protocol = connection_details.get("protocol")
                raw_kwargs = {k: v for k, v in connection_details.items() if v is not None}

            # Filter kwargs to only those accepted by the handler's __init__
            from connmanager.connection_handler import PROTOCOL_REGISTRY
            import inspect
            handler_cls = PROTOCOL_REGISTRY.get(protocol.lower())
            if handler_cls is None:
                logger.error(f"No handler registered for protocol: {protocol}")
                return
            sig = inspect.signature(handler_cls.__init__)
            valid_keys = set(sig.parameters.keys()) - {"self"}
            handler_kwargs = {k: v for k, v in raw_kwargs.items() if k in valid_keys}
            try:
                handler = handler_cls(**handler_kwargs)
                handler.connect()
                logger.info(f"Connected to {protocol.upper()} host '{alias_or_id}'.")
            except ConnectionHandlerException as e:
                logger.error(f"{protocol.upper()} connection failed/timed out: {e}")
            except Exception as e:
                logger.error(f"Error establishing {protocol.upper()} connection: {e}")
        except Exception as e:
            logger.error(f"An error occurred while connecting: {e}")
        finally:
            self.database.close()

    def import_connections(self, json_file: str) -> None:
        """
        Import connections from a JSON file.
        """
        try:
            with open(json_file, "r") as file:
                connections = json.load(file)
                for connection in connections:
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
                            logger.debug(f"Connection '{alias}' overwritten.")
                        else:
                            logger.info(f"Connection '{alias}' skipped.")
                    else:
                        self.database.add_connection(**connection)
                        logger.debug(f"Connection '{alias}' added.")
            logger.info(f"Connections imported successfully from {json_file}.")
        except Exception as e:
            logger.error(f"An error occurred while importing connections: {e}")
        finally:
            self.database.close()

    def export_connections(self, json_file: str) -> None:
        """
        Export all connections to a JSON file with decrypted passwords.
        """
        try:
            logger.warning("Exported JSON will contain passwords in plaintext. Handle with care!\n")
            connections = self.database.get_all_connections()
            decrypted_connections = []
            for connection in connections:
                connection.pop("id", None)
                # Decrypt password if present
                if "password" in connection and connection["password"]:
                    try:
                        # Use the same decrypt logic as in _row_to_connection_details
                        from connmanager.encryption_utils import decrypt
                        connection["password"] = decrypt(connection["password"])
                    except Exception:
                        logger.warning(f"Failed to decrypt password for alias '{connection.get('alias', '')}'. Exporting as-is.")
                decrypted_connections.append(connection)
            with open(json_file, "w") as file:
                json.dump(decrypted_connections, file, indent=4)
            logger.info(f"Connections exported successfully to {json_file}.")
        except Exception as e:
            logger.error(f"An error occurred while exporting connections: {e}")
        finally:
            self.database.close()
