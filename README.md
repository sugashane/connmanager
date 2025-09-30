
# ConnManager

A connection manager for SSH, RDP, VNC, VMRC, and HTTP.

## Features

- Add, edit, delete, and list connections
- Connect to hosts using SSH, RDP, VNC, VMRC, and HTTP
- Import and export connections as JSON

## Important Note


**Security Notice**: Passwords are now **encrypted at rest** in the database using Fernet symmetric encryption (`cryptography` package). Your credentials are protected in the local database file (`~/.config/cm/cm.db`).

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

### Launch Interactive TUI (Default)

```sh
cm
```

The TUI launches automatically when no command is specified. You can also explicitly launch it with:

```sh
cm tui
```

-or-

```sh
cm t
```

The TUI (Text User Interface) provides an interactive, curses-based interface where you can:
- Browse all connections in a scrollable list
- Search connections in real-time
- Connect to selected connections with Enter
- Add, edit, and delete connections
- Navigate with arrow keys or vim-style keys (j/k)

**TUI Controls:**
- `↑/↓` or `j/k` - Navigate up/down
- `Enter` - Connect to selected connection
- `/` - Enter search mode
- `Esc` - Exit search mode
- `a` - Add new connection
- `e` - Edit selected connection
- `d` - Delete selected connection
- `r` - Refresh connections list
- `h` or `?` - Show help
- `q` or `Ctrl+C` - Quit TUI

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

By default, the database is stored at: `~/.config/cm/cm.db`
The encryption key is stored at: `~/.config/cm/cm.key`

You can change the database and key locations by editing the `config.ini` file at `~/.config/cm/config.ini`.

Example `config.ini`:

```ini
[connmanager]
db_path = /Users/youruser/.config/cm/cm.db
key_path = /Users/youruser/.config/cm/cm.key
```

## Shell Autocompletion

### Zsh Completion

For zsh autocompletion with command and connection alias suggestions:

1. **Copy the completion script:**
   ```sh
   mkdir -p ~/.zsh/completions
   cp completions/_cm ~/.zsh/completions/
   ```

2. **Add to your `~/.zshrc`:**
   ```sh
   # Add completion directory to fpath
   fpath=(~/.zsh/completions $fpath)
   
   # Enable completions
   autoload -Uz compinit
   zstyle ':completion:*' menu select
   zmodload zsh/complist
   compinit
   _comp_options+=(globdots)
   
   # Source the cm completion
   source ~/.zsh/completions/_cm
   ```

3. **Reload your shell:**
   ```sh
   source ~/.zshrc
   ```

### Bash Completion

For bash users, you can create a basic completion script:

1. **Create completion script:**
   ```sh
   sudo tee /etc/bash_completion.d/cm > /dev/null << 'EOF'
   _cm_completion() {
       local cur prev commands
       COMPREPLY=()
       cur="${COMP_WORDS[COMP_CWORD]}"
       prev="${COMP_WORDS[COMP_CWORD-1]}"
       
       commands="add connect list search delete edit tui import export a c l s d e t i x"
       
       if [[ ${COMP_CWORD} == 1 ]]; then
           COMPREPLY=($(compgen -W "${commands}" -- ${cur}))
           return 0
       fi
       
       # Complete connection aliases for connect/edit/delete commands
       if [[ "$prev" =~ ^(connect|edit|delete|c|e|d)$ ]]; then
           local aliases=$(cm list 2>/dev/null | awk 'NR>1 {print $4}' | grep -v '^Alias$' | grep -v '^$')
           COMPREPLY=($(compgen -W "${aliases}" -- ${cur}))
       fi
   }
   
   complete -F _cm_completion cm
   EOF
   ```

2. **Reload bash completion:**
   ```sh
   source /etc/bash_completion.d/cm
   ```

**Features:**
- Tab completion for all commands and shortcuts
- Auto-suggests connection aliases for `connect`, `edit`, and `delete` commands
- Works with both full commands (`connect`) and shortcuts (`c`)

## License

This project is licensed under the MIT License.
