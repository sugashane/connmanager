# ConnManager

A connection manager for SSH, RDP, VNC, and VMRC.

## Features

- Add, edit, delete, and list connections
- Connect to hosts using SSH, RDP, VNC, and VMRC
- Import and export connections as JSON

## Important Note

**Security Warning**: Passwords are stored in the database and exported JSON files as plain text. To ensure the security of your credentials, avoid making these files publicly visible. Additionally, providing a password when adding an entry is optional. If you choose not to provide a password, you will be prompted to enter it when connecting.

## Prerequisites

This application has only been tested on macOS.

### SSH

If you want to log in with the saved password, you will need to install `sshpass`.

- For macOS, you can install it with Brew:

  ```sh
  brew install sshpass
  ```

### RDP

You will need to install the following:

- [xQuartz](https://www.xquartz.org/)

- xfreerdp (via Brew) with the command:

  ```sh
  brew install freerdp
  ```

## Installation

### Clone the Repository

```sh
git clone https://github.com/sugashane/connmanager.git
cd connmanager
```

### Install the Package

```sh
pip install .
```

-or-

```sh
pip3 install .
```

## Usage

### Add a Connection

```sh
cm add
```

-or-

```sh
cm a
```

### Connect to a Host

```sh
cm connect <alias_or_id>
```

-or-

```sh
cm c <alias_or_id>
```

### List Connections

```sh
cm list <optional: protocol name or tag name>
```

-or-

```sh
cm l <optional: protocol name or tag name>
```

### Search Connections

```sh
cm search <text>
```

-or-

```sh
cm s <text>
```

### Delete a Connection

```sh
cm delete <alias_or_id>
```

-or-

```sh
cm d <alias_or_id>
```

### Edit a Connection

```sh
cm edit <alias_or_id>
```

-or-

```sh
cm e <alias_or_id>
```

### Import Connections from JSON

```sh
cm import <json_file>
```

-or-

```sh
cm i <json_file>
```

### Export Connections to JSON

```sh
cm export <json_file>
```

-or-

```sh
cm x <json_file>
```

## Database Location

By default, the database is stored at: `~/.cm.db`

You can change the database location by updating the DB_PATH variable in the main.py script.

## License

This project is licensed under the MIT License.
