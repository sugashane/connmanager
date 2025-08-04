"""
Utilities for encrypting and decrypting sensitive fields using Fernet symmetric encryption.
"""
import os
from cryptography.fernet import Fernet, InvalidToken
from connmanager.config_utils import load_config

FERNET_KEY_PATH = load_config().get("key_path", os.path.expanduser("~/.config/cm/cm.key"))

def generate_key() -> bytes:
    key = Fernet.generate_key()
    with open(FERNET_KEY_PATH, "wb") as f:
        f.write(key)
    return key

def load_key() -> bytes:
    if not os.path.exists(FERNET_KEY_PATH):
        return generate_key()
    with open(FERNET_KEY_PATH, "rb") as f:
        return f.read()

def get_fernet() -> Fernet:
    return Fernet(load_key())

def encrypt(plaintext: str) -> str:
    f = get_fernet()
    return f.encrypt(plaintext.encode()).decode()

def decrypt(ciphertext: str) -> str:
    f = get_fernet()
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        raise ValueError("Invalid encryption token or wrong key.")
