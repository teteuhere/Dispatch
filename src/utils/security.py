import os
import json
from cryptography.fernet import Fernet

class IntelSecurity:
    def __init__(self, key_path):
        self.key_path = key_path
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)

    def _load_or_generate_key(self):
        if not os.path.exists(self.key_path):
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(self.key_path), exist_ok=True)
            with open(self.key_path, "wb") as f:
                f.write(key)
            return key

        with open(self.key_path, "rb") as f:
            return f.read()

    def encrypt_payload(self, data_dict):
        """Converts a Dictionary -> Encrypted String"""
        json_str = json.dumps(data_dict)
        encrypted_bytes = self.cipher.encrypt(json_str.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')

    def decrypt_payload(self, encrypted_token):
        """Converts Encrypted String -> Dictionary"""
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_token.encode('utf-8'))
            return json.loads(decrypted_bytes.decode('utf-8'))
        except Exception as e:
            print(f"[SECURITY ALERT] Decryption failed: {e}")
            return {}
