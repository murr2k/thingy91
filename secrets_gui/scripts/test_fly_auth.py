#!/usr/bin/env python3
"""
Test Fly.io authentication using the actual tokens.
"""

import json
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import subprocess

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

def get_flyio_tokens():
    """Get Fly.io tokens from encrypted storage."""
    with open(MASTER_KEY_FILE, 'r') as f:
        master_key = f.read().strip()
    
    key = derive_key(master_key)
    fernet = Fernet(key)
    
    with open(SECRETS_FILE, 'r') as f:
        encrypted_data = json.load(f)
    
    if 'flyio' in encrypted_data:
        decrypted = fernet.decrypt(encrypted_data['flyio'].encode())
        return json.loads(decrypted)
    return None

def test_with_cli(token, token_name):
    """Test token using the Fly CLI."""
    print(f"\nTesting {token_name}:")
    print(f"  Token starts with: {token[:30]}...")
    print(f"  Token length: {len(token)}")
    
    # Set environment variable and test
    env = os.environ.copy()
    env['FLY_API_TOKEN'] = token
    
    try:
        # Try to get current user info
        result = subprocess.run(
            ['fly', 'auth', 'whoami'],
            env=env,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"  ✅ SUCCESS: {result.stdout.strip()}")
            return True
        else:
            print(f"  ❌ FAILED: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  Command timed out")
        return False
    except FileNotFoundError:
        print(f"  ❌ fly CLI not found - install with: curl -L https://fly.io/install.sh | sh")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 Testing Fly.io Authentication")
    print("=" * 60)
    
    creds = get_flyio_tokens()
    if not creds:
        print("❌ No Fly.io credentials found")
        return
    
    # Test the org_token and admin_token (they appear to be the same)
    tokens_to_test = []
    
    if creds.get('FLYIO_ORG_TOKEN'):
        tokens_to_test.append((creds['FLYIO_ORG_TOKEN'], 'Organization Token'))
    
    if creds.get('FLYIO_ADMIN_TOKEN'):
        # Only test if different from org_token
        if creds['FLYIO_ADMIN_TOKEN'] != creds.get('FLYIO_ORG_TOKEN'):
            tokens_to_test.append((creds['FLYIO_ADMIN_TOKEN'], 'Admin Token'))
        else:
            print("\nNote: Admin token is identical to Org token, skipping duplicate test")
    
    working_token = None
    for token, name in tokens_to_test:
        if test_with_cli(token, name):
            working_token = token
            break
    
    if working_token:
        print("\n" + "=" * 60)
        print("✅ Authentication successful!")
        print("\nTo use this token in your shell:")
        print(f"export FLY_API_TOKEN='{working_token}'")
        print("fly apps list")
    else:
        print("\n" + "=" * 60)
        print("❌ No working tokens found")
        print("\nTroubleshooting steps:")
        print("1. Check if fly CLI is installed: fly version")
        print("2. The tokens might be expired - generate new ones at:")
        print("   https://fly.io/user/personal_access_tokens")

if __name__ == "__main__":
    main()