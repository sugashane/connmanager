"""
Config utilities for ConnManager. Loads and saves config from ~/.config/cm/config.ini
"""
import os
import configparser

CONFIG_DIR = os.path.join(os.path.expanduser(os.environ.get("XDG_CONFIG_HOME", "~/.config")), "cm")
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.ini")

DEFAULTS = {
    "db_path": os.path.join(CONFIG_DIR, "cm.db"),
    "key_path": os.path.join(CONFIG_DIR, "cm.key")
}

def load_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_PATH):
        config["connmanager"] = DEFAULTS
        with open(CONFIG_PATH, "w") as f:
            config.write(f)
    else:
        config.read(CONFIG_PATH)
        if "connmanager" not in config:
            config["connmanager"] = DEFAULTS
    return config["connmanager"]

