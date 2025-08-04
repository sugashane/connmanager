
# ConnManager

A connection manager for SSH, RDP, VNC, VMRC, and HTTP.

## Features

- Add, edit, delete, and list connections
- Connect to hosts using SSH, RDP, VNC, VMRC, and HTTP
- Import and export connections as JSON

## Important Note


**Security Notice**: Passwords are now **encrypted at rest** in the database using Fernet symmetric encryption (`cryptography` package). Your credentials are protected in the local database file (`~/.cm.db`).

**Export Warning**: When you export connections to a JSON file, passwords are written in plaintext for compatibility. **Protect exported files** and do not share them publicly. You will see a warning during export.

If you do not provide a password when adding an entry, you will be prompted to enter it when connecting.

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

### Recommended: Install with pipx

`pipx` is the best way to install CLI tools in an isolated environment:

```sh
pipx install 'git+https://github.com/sugashane/connmanager.git'
```

If you don't have pipx, install it with:

```sh
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

#### Alternative: Local Install

Clone the repository and install locally:

```sh
git clone https://github.com/sugashane/connmanager.git
cd connmanager
pip install .
```

This project supports modern Python packaging with `pyproject.toml`.

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

You can use protocol names like `ssh`, `rdp`, `vnc`, `vmrc`, or `http` as filters.

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
