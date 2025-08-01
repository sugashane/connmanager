import shutil
import subprocess


class ConnectionHandler:
    def __init__(self, host_or_ip, port, username, password, protocol):
        self.host_or_ip = host_or_ip
        self.port = port
        self.username = username
        self.password = password
        self.protocol = protocol

    def connect(self):
        raise NotImplementedError("Subclasses should implement this method")


class SSHHandler(ConnectionHandler):
    protocol = "ssh"

    def __init__(self, host_or_ip, port, username, password=None, ssh_key_path=None):
        super().__init__(host_or_ip, port, username, password, protocol="ssh")
        self.ssh_key_path = ssh_key_path

    def connect(self):
        # Check if sshpass is available
        sshpass_installed = shutil.which("sshpass") is not None

        ssh_command = []

        # If sshpass is installed and a password is provided, use sshpass
        if sshpass_installed and self.password is not None:
            ssh_command.extend(["sshpass", "-p", self.password])

        # Add the ssh command
        ssh_command.extend(["ssh", "-o", "StrictHostKeyChecking=no"])

        # Add the path to the private key if provided
        if self.ssh_key_path:
            ssh_command.extend(["-i", self.ssh_key_path])

        # Add the username and host information
        if self.port:
            ssh_command.append(f"-p {self.port}")

        if self.username:
            ssh_command.append(f"{self.username}@{self.host_or_ip}")
        else:
            ssh_command.append(self.host_or_ip)
        # Open an SSH session. The -t flag forces pseudo-terminal allocation
        # print(ssh_command)
        try:
            subprocess.run(ssh_command, check=True)
        except subprocess.CalledProcessError as e:
            raise ConnectionHandlerException(f"SSH session failed to start: {e}")


class RDPHandler(ConnectionHandler):
    protocol = "rdp"

    def __init__(
        self, host_or_ip, username, password=None, domain=None, resolution=None
    ):
        super().__init__(host_or_ip, username, password, protocol="rdp")
        self.domain = domain
        self.resolution = resolution

    def connect(self):
        # RDP-specific connect code
        print(f"RDP: Connecting to {self.host_or_ip} with {self.username}")
        rdp_command = ["xfreerdp", "/v:" + f'"{self.host_or_ip}"']
        print(rdp_command)
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
            raise ConnectionHandlerException(f"RDP session failed to start: {e}")


class VMRCHandler(ConnectionHandler):
    protocol = "vmrc"

    def __init__(self, host_or_ip):
        super().__init__(host_or_ip, username=None, password=None, protocol="vmrc")

    def connect(self):
        vmrc_command = [f'open "{self.host_or_ip}"']
        print(vmrc_command)
        try:
            subprocess.run(vmrc_command, check=True, shell=True)
        except subprocess.CalledProcessError as e:
            raise ConnectionHandlerException(f"vmrc session failed to start: {e}")


class VNCHandler(ConnectionHandler):
    protocol = "vnc"

    def connect(self):
        # VNC-specific connect code
        pass


class ConnectionHandlerException(Exception):
    pass
