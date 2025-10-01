import shutil
import subprocess
import logging
from typing import Any, Optional, Type, Dict

logger = logging.getLogger(__name__)

# Protocol registry for extensibility
PROTOCOL_REGISTRY: Dict[str, Type['ConnectionHandler']] = {}

def register_protocol(name: str):
    def decorator(cls):
        PROTOCOL_REGISTRY[name.lower()] = cls
        return cls
    return decorator

def connection_handler_factory(protocol: str, **kwargs: Any) -> 'ConnectionHandler':
    """
    Factory function to instantiate the appropriate connection handler based on protocol.
    """
    handler_cls = PROTOCOL_REGISTRY.get(protocol.lower())
    if not handler_cls:
        raise ValueError(f"Unsupported protocol: {protocol}")
    return handler_cls(**kwargs)

class ConnectionHandler:
    """
    Base connection handler for all protocols.
    """
    def __init__(
        self,
        host_or_ip: str,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        protocol: Optional[str] = None,
    ) -> None:
        self.host_or_ip = host_or_ip
        self.port = port
        self.username = username
        self.password = password
        self.protocol = protocol

    def connect(self) -> None:
        raise NotImplementedError("Subclasses should implement this method")

@register_protocol("ssh")
class SSHHandler(ConnectionHandler):
    protocol = "ssh"

    def __init__(
        self,
        host_or_ip: str,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        ssh_key_path: Optional[str] = None,
    ) -> None:
        super().__init__(host_or_ip, port=port, username=username, password=password, protocol="ssh")
        self.ssh_key_path = ssh_key_path

    def connect(self) -> None:
        sshpass_installed = shutil.which("sshpass") is not None
        ssh_command: list[str] = []
        if sshpass_installed and self.password is not None:
            ssh_command.extend(["sshpass", "-p", self.password])
        ssh_command.extend(["ssh", "-o", "StrictHostKeyChecking=no"])
        if self.ssh_key_path:
            ssh_command.extend(["-i", self.ssh_key_path])
        if self.port:
            ssh_command.append(f"-p {self.port}")
        if self.username:
            ssh_command.append(f"{self.username}@{self.host_or_ip}")
        else:
            ssh_command.append(self.host_or_ip)
        logger.debug(f"Running SSH command: {' '.join(ssh_command)}")
        try:
            subprocess.run(ssh_command, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"SSH session to {self.host_or_ip} failed to start")


@register_protocol("rdp")
class RDPHandler(ConnectionHandler):
    protocol = "rdp"

    def __init__(
        self,
        host_or_ip: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        domain: Optional[str] = None,
        resolution: Optional[str] = None,
    ) -> None:
        super().__init__(host_or_ip, username=username, password=password, protocol="rdp")
        self.domain = domain
        self.resolution = resolution

    def connect(self) -> None:
        logger.info(f"RDP: Connecting to {self.host_or_ip} with {self.username}")
        rdp_command: list[str] = ["xfreerdp", "/v:" + f'"{self.host_or_ip}"']
        if self.username:
            rdp_command.append("/u:" + self.username)
        if self.password:
            rdp_command.append("/p:" + self.password)
        if self.domain:
            rdp_command.append("/d:" + self.domain)
        else:
            rdp_command.append("/d:WORKGROUP")
        if self.resolution:
            rdp_command.append("/size:" + self.resolution)
        rdp_command.append("/cert:ignore")
        command_str = " ".join(rdp_command)
        try:
            subprocess.run(
                command_str,
                check=True,
                shell=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"RDP session failed to start: {e}")
            raise ConnectionHandlerException(f"RDP session failed to start: {e}")

@register_protocol("vmrc")
class VMRCHandler(ConnectionHandler):
    protocol = "vmrc"

    def __init__(self, host_or_ip: str) -> None:
        super().__init__(host_or_ip, protocol="vmrc")

    def connect(self) -> None:
        vmrc_command: list[str] = [f'open "{self.host_or_ip}"']
        logger.debug(f"VMRC command: {vmrc_command}")
        try:
            subprocess.run(vmrc_command, check=True, shell=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"vmrc session failed to start: {e}")
            raise ConnectionHandlerException(f"vmrc session failed to start: {e}")


@register_protocol("vnc")
class VNCHandler(ConnectionHandler):
    protocol = "vnc"

    def __init__(self, host_or_ip: str, port: Optional[int] = None, **kwargs) -> None:
        # Default port to 5901 if not provided
        if port is None:
            port = 5901
        super().__init__(host_or_ip, port=port, protocol="vnc")

    def connect(self) -> None:
        # Example: open vnc://host:port (macOS)
        vnc_url = f"vnc://{self.host_or_ip}:{self.port}"
        vnc_command = [f'open "{vnc_url}"']
        logger.info(f"Opening VNC connection to {vnc_url}")
        logger.debug(f"VNC command: {vnc_command}")
        try:
            subprocess.run(vnc_command, check=True, shell=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"VNC session failed to start: {e}")
            raise ConnectionHandlerException(f"VNC session failed to start: {e}")

@register_protocol("http")
class HTTPHandler(ConnectionHandler):
    protocol = "http"

    def __init__(self, host_or_ip: str, **kwargs) -> None:
        super().__init__(host_or_ip, protocol="http")

    def connect(self) -> None:
        http_command: list[str]
        if self.host_or_ip.startswith("http://") or self.host_or_ip.startswith("https://"):
            http_command = [f'open "{self.host_or_ip}"']
        else:
            self.host_or_ip = "http://" + self.host_or_ip
            http_command = [f'open "{self.host_or_ip}"']
        logger.info(f"Opening HTTP URL: {self.host_or_ip}")
        logger.debug(f"HTTP command: {http_command}")
        try:
            subprocess.run(http_command, check=True, shell=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"http session failed to start: {e}")
            raise ConnectionHandlerException(f"http session failed to start: {e}")

class ConnectionHandlerException(Exception):
    """
    Exception raised for errors in connection handlers.
    """
    pass