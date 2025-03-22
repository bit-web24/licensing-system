"""This module contains the functions to encrypt and decrypt the license data"""

import base64
import json

from cryptography.fernet import Fernet

AES_KEY = Fernet.generate_key()
cipher = Fernet(AES_KEY)

def encrypt_license(data: dict):
    """Encrypts the license data and returns the encrypted key"""
    json_data = json.dumps(data).encode()
    encrypted_data = cipher.encrypt(json_data)
    return base64.urlsafe_b64encode(encrypted_data).decode()

def decrypt_license(encrypted_key: str):
    """Decrypts the license key and returns the license data"""
    try:
        decrypted_data = cipher.decrypt(base64.urlsafe_b64decode(encrypted_key))
        return json.loads(decrypted_data)
    except Exception as e:
        raise e
