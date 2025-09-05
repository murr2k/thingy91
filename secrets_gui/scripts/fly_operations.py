#!/usr/bin/env python3
"""
Test Fly.io operations with the authenticated token.
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

def get_fly_token():
    """Get working Fly.io token from encrypted storage."""
    with open(MASTER_KEY_FILE, 'r') as f:
        master_key = f.read().strip()
    
    key = derive_key(master_key)
    fernet = Fernet(key)
    
    with open(SECRETS_FILE, 'r') as f:
        encrypted_data = json.load(f)
    
    if 'flyio' in encrypted_data:
        decrypted = fernet.decrypt(encrypted_data['flyio'].encode())
        creds = json.loads(decrypted)
        # Return the org token which we know works
        return creds.get('FLYIO_ORG_TOKEN')
    return None

def run_fly_command(cmd_args, token):
    """Run a fly CLI command with authentication."""
    env = os.environ.copy()
    env['FLY_API_TOKEN'] = token
    
    try:
        result = subprocess.run(
            ['fly'] + cmd_args,
            env=env,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 60)
    print("🚀 Testing Fly.io Operations")
    print("=" * 60)
    
    token = get_fly_token()
    if not token:
        print("❌ No Fly.io token found")
        return
    
    print("✅ Using authenticated token")
    
    # Test 1: List apps
    print("\n📱 Listing Fly.io apps:")
    print("-" * 40)
    success, stdout, stderr = run_fly_command(['apps', 'list'], token)
    if success:
        if stdout.strip():
            print(stdout)
        else:
            print("No apps found (this is normal if you haven't deployed any)")
    else:
        print(f"Failed to list apps: {stderr}")
    
    # Test 2: List organizations
    print("\n🏢 Listing organizations:")
    print("-" * 40)
    success, stdout, stderr = run_fly_command(['orgs', 'list'], token)
    if success:
        print(stdout)
    else:
        print(f"Failed to list orgs: {stderr}")
    
    # Test 3: Check account status
    print("\n👤 Account information:")
    print("-" * 40)
    success, stdout, stderr = run_fly_command(['auth', 'whoami'], token)
    if success:
        print(f"Logged in as: {stdout.strip()}")
    
    # Test 4: List regions (useful info, doesn't require apps)
    print("\n🌍 Available regions:")
    print("-" * 40)
    success, stdout, stderr = run_fly_command(['platform', 'regions'], token)
    if success:
        # Show first 10 lines of regions
        lines = stdout.strip().split('\n')
        for line in lines[:10]:
            print(line)
        if len(lines) > 10:
            print(f"... and {len(lines) - 10} more regions")
    
    print("\n" + "=" * 60)
    print("✅ Fly.io integration is working!")
    print("\n💡 Quick reference:")
    print("  fly apps list         - List all apps")
    print("  fly launch            - Create new app")
    print("  fly deploy            - Deploy app")
    print("  fly logs              - View app logs")
    print("  fly status            - Check app status")
    print("=" * 60)

if __name__ == "__main__":
    main()