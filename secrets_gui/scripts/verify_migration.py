#!/usr/bin/env python3
"""
Verify that all credentials were successfully migrated.
"""

import json
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64

SECRETS_FILE = "/home/murr2k/projects/thingy91/secrets_gui/data/secrets.json"
MASTER_KEY_FILE = "/home/murr2k/projects/thingy91/secrets_gui/data/.master_key"

def derive_key(master_key: str) -> bytes:
    """Derive encryption key from master key."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'stable_salt_v1',
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
    return key

def main():
    print("=" * 60)
    print("🔍 Verifying Migration")
    print("=" * 60)
    
    # Load master key
    with open(MASTER_KEY_FILE, 'r') as f:
        master_key = f.read().strip()
    
    # Setup decryption
    key = derive_key(master_key)
    fernet = Fernet(key)
    
    # Load and decrypt secrets
    with open(SECRETS_FILE, 'r') as f:
        encrypted_data = json.load(f)
    
    print(f"\n📦 Found {len(encrypted_data)} services:\n")
    
    for service, encrypted_value in encrypted_data.items():
        try:
            decrypted = fernet.decrypt(encrypted_value.encode())
            credentials = json.loads(decrypted)
            
            print(f"✓ {service}:")
            for key, value in credentials.items():
                # Mask the value for security
                if len(str(value)) > 10:
                    masked = str(value)[:4] + "..." + str(value)[-4:]
                else:
                    masked = "***"
                print(f"    - {key}: {masked}")
        except Exception as e:
            print(f"✗ {service}: Failed to decrypt - {e}")
    
    print("\n" + "=" * 60)
    print("✅ Verification Complete!")
    print(f"\nAll credentials are accessible at:")
    print("   http://localhost:5000")
    print("   Username: admin")
    print("   Password: changeme")
    print("=" * 60)

if __name__ == "__main__":
    main()