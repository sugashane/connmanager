from dataclasses import dataclass, field
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Dynamically get supported protocols from the registry
from connmanager.connection_handler import PROTOCOL_REGISTRY
PROTOCOLS = list(PROTOCOL_REGISTRY.keys())

@dataclass
class ConnectionDetails:
    """
    Dataclass representing all details required for a connection.
    """
    alias: str
    protocol: str
    host_or_ip: Optional[str] = None
    port: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_key_path: Optional[str] = None
    domain: Optional[str] = None
    resolution: Optional[str] = None
    tag: Optional[str] = None
    extras: Dict[str, str] = field(default_factory=dict)


class ConnectionPrompter:
    """
    Handles all user prompts for connection details.
    """
    def __init__(self, database) -> None:
        self.database = database

    def password_comparison(self) -> str:
        """
        Prompt for password twice and confirm match.
        """
        import getpass
        password1 = getpass.getpass("Enter the password: ")
        password2 = getpass.getpass("Re-enter the password: ")
        if password1 == password2:
            return password1
        else:
            logger.info("Passwords do not match. Please try again.")
            return self.password_comparison()

    def is_ipv6(self, ip: str) -> bool:
        """
        Check if the given IP is IPv6.
        """
        return ":" in ip

    def prompt_connection_fields(self, existing: Optional[dict] = None) -> ConnectionDetails:
        """
        Prompt the user for all connection fields, with validation and logging.
        """
        def get_default(key: str, fallback=None):
            if existing:
                if isinstance(existing, dict):
                    return existing.get(key, fallback)
                from dataclasses import asdict, is_dataclass
                if is_dataclass(existing):
                    return asdict(existing).get(key, fallback)
            return fallback

        while True:
            alias = input(f"Enter a unique alias for the connection{f' [{get_default('alias')}]' if existing else ''}: ") or get_default('alias')
            if not alias:
                logger.info("Alias cannot be empty. Please try again.")
            elif alias.isdigit():
                logger.info("Invalid alias. The alias cannot be only digits. Please try again.")
            elif not existing and self.database.alias_exists(alias):
                logger.info("This alias already exists. Please choose a different one.")
            else:
                break

        while True:
            protocol = input(f"Enter the protocol (e.g. {', '.join(PROTOCOLS)}{f' [{get_default('protocol')}]' if existing else ''}): ") or get_default('protocol')
            if protocol not in PROTOCOLS:
                logger.info(f"Invalid protocol. Please enter {', '.join(PROTOCOLS)}.")
            else:
                break

        if protocol.casefold() == "vmrc":
            host_or_ip = input(f"Enter vmrc URL (e.g. vmrc://<esxi-host>/?moid=<vmid>){f' [{get_default('host_or_ip')}]' if existing else ''}: ") or get_default('host_or_ip')
            port = None
            username = None
        else:
            while True:
                host_or_ip = input(f"Enter the hostname or IP address{f' [{get_default('host_or_ip')}]' if existing else ''}: ") or get_default('host_or_ip')
                if not host_or_ip:
                    logger.info("Invalid hostname or IP address. Please try again.")
                else:
                    break
            port = input(f"Enter the port (press Enter for default){f' [{get_default('port')}]' if existing else ''}: ") or get_default('port')
            username = input(f"Enter the username (press Enter if not applicable){f' [{get_default('username')}]' if existing else ''}: ") or get_default('username')

        password: Optional[str] = None
        ssh_key_path: Optional[str] = None
        domain: Optional[str] = None
        resolution: Optional[str] = None

        if protocol.casefold() == "ssh":
            auth_method = (
                input(f"Choose authentication method, password or key (default: password){f' [{get_default('ssh_key_path', 'password')}]' if existing else ''}: ")
                .strip()
                .lower()
            ) or ("key" if get_default('ssh_key_path') else "password")
            if auth_method == "key":
                ssh_key_path = input(f"Enter path to SSH private key (default is ~/.ssh/id_rsa){f' [{get_default('ssh_key_path')}]' if existing else ''}: ").strip() or get_default('ssh_key_path') or "~/.ssh/id_rsa"
            else:
                password = self.password_comparison() if not existing else (input("Enter the password (press Enter to keep current): ") or get_default('password'))
        elif protocol.casefold() == "rdp":
            if (
                host_or_ip is not None
                and self.is_ipv6(host_or_ip)
                and not host_or_ip.startswith("[")
                and not host_or_ip.endswith("]")
            ):
                host_or_ip = f"[{host_or_ip}]"
            password = self.password_comparison() if not existing else (input("Enter the password (press Enter to keep current): ") or get_default('password'))
            domain = input(f"Enter the domain (press Enter if not applicable){f' [{get_default('domain')}]' if existing else ''}: ") or get_default('domain')
            resolution = input(f"Enter the resolution (e.g., 1920x1080){f' [{get_default('resolution')}]' if existing else ''}: ") or get_default('resolution')

        while True:
            tag = input(f"Enter an optional tag (i.e lab, tools, personal){f' [{get_default('tag')}]' if existing else ''}: ") or get_default('tag')
            if tag in PROTOCOLS:
                logger.info("Invalid tag. Unable to use protocol as a tag.")
            else:
                break

        extras: Dict[str, str] = get_default('extras', {}) or {}
        logger.info("Enter extra options (key=value). Type 'done' when finished:")
        while True:
            extra = input().strip()
            if extra.lower() == "done":
                break
            try:
                key, value = extra.split("=")
                extras[key.strip()] = value.strip()
            except ValueError:
                logger.info("Invalid format for extra options. Please use 'key=value' format.")

        return ConnectionDetails(
            alias=alias,
            protocol=protocol,
            host_or_ip=host_or_ip,
            port=port,
            username=username,
            password=password,
            ssh_key_path=ssh_key_path,
            domain=domain,
            resolution=resolution,
            tag=tag,
            extras=extras,
        )
