"""
Privacy-first encryption utilities for user authentication data.
Uses Fernet (AES-128) encryption for sensitive information.
"""
import json
import hashlib
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode
from django.conf import settings


class PrivacyEncryption:
    """Handles encryption/decryption for user authentication data"""
    
    # Static cipher instance using Django SECRET_KEY
    _cipher = None
    
    @staticmethod
    def _derive_key():
        """
        Derive a Fernet-compatible key from Django SECRET_KEY.
        Fernet requires a 32-byte key encoded in base64.
        """
        # Get SECRET_KEY and hash it to get a consistent 32-byte key
        secret = settings.SECRET_KEY.encode()
        # Use SHA256 to get 32 bytes
        key_material = hashlib.sha256(secret).digest()
        # Fernet requires base64 encoded 32-byte key
        return urlsafe_b64encode(key_material)
    
    @staticmethod
    def _get_cipher():
        """Get the Fernet cipher (lazy initialization)"""
        if PrivacyEncryption._cipher is None:
            key = PrivacyEncryption._derive_key()
            PrivacyEncryption._cipher = Fernet(key)
        return PrivacyEncryption._cipher
    
    @staticmethod
    def generate_key():
        """Generate a new Fernet key"""
        return Fernet.generate_key()
    
    @staticmethod
    def encrypt_library_id(library_id):
        """Encrypt library ID or student ID"""
        cipher = PrivacyEncryption._get_cipher()
        encrypted = cipher.encrypt(library_id.encode())
        return encrypted.decode()
    
    @staticmethod
    def decrypt_library_id(encrypted_id):
        """Decrypt library ID or student ID"""
        try:
            cipher = PrivacyEncryption._get_cipher()
            decrypted = cipher.decrypt(encrypted_id.encode())
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt library ID: {str(e)}")
    
    @staticmethod
    def encrypt_auth_data(name, phone, credentials):
        """
        Encrypt user authentication data (name, phone, credentials).
        Concatenates with commas and encrypts the entire string.
        """
        # Separate each field by comma
        auth_string = f"{name},{phone},{credentials}"
        
        cipher = PrivacyEncryption._get_cipher()
        encrypted = cipher.encrypt(auth_string.encode())
        return encrypted.decode()
    
    @staticmethod
    def decrypt_auth_data(encrypted_auth):
        """
        Decrypt user authentication data and return tuple of (name, phone, credentials)
        """
        try:
            cipher = PrivacyEncryption._get_cipher()
            decrypted = cipher.decrypt(encrypted_auth.encode())
            data = decrypted.decode()
            
            # Split by comma to get individual fields
            parts = data.split(',', 2)  # Split into max 3 parts
            if len(parts) == 3:
                return parts[0], parts[1], parts[2]
            else:
                raise ValueError("Invalid auth data format")
        except Exception as e:
            raise ValueError(f"Failed to decrypt auth data: {str(e)}")
    
    @staticmethod
    def hash_fingerprint(fingerprint_data):
        """
        Create a hash of browser fingerprint for anonymous user identification.
        Returns a consistent hash for the same fingerprint.
        """
        import hashlib
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    @staticmethod
    def generate_anonymous_user_id():
        """Generate a unique anonymous user ID"""
        import uuid
        return str(uuid.uuid4())


def encrypt_sensitive_field(value):
    """Helper function to encrypt any sensitive string"""
    return PrivacyEncryption._get_cipher().encrypt(value.encode()).decode()


def decrypt_sensitive_field(encrypted_value):
    """Helper function to decrypt any sensitive string"""
    try:
        return PrivacyEncryption._get_cipher().decrypt(encrypted_value.encode()).decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")
