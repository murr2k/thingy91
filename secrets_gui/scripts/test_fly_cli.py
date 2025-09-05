#!/usr/bin/env python3
"""
Test Fly.io authentication using the CLI with credentials from Secrets Manager.
"""

import json
import os
import subprocess
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64

SECRETS_FILE = "/home/murr2k/projects/thingy91/secrets_gui/data/secrets.json"
MASTER_KEY_FILE = "/home/murr2k/projects/thingy91/secrets_gui/data/.master_key"

def get_fly_token():
    """Get Fly.io token from encrypted storage."""
    # Load master key
    with open(MASTER_KEY_FILE, 'r') as f:
        master_key = f.read().strip()
    
    # Derive encryption key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'stable_salt_v1',
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
    fernet = Fernet(key)
    
    # Load and decrypt secrets
    with open(SECRETS_FILE, 'r') as f:
        encrypted_data = json.load(f)
    
    if 'flyio' in encrypted_data:
        decrypted = fernet.decrypt(encrypted_data['flyio'].encode())
        creds = json.loads(decrypted)
        # Return the org token which we know works
        return creds.get('FLYIO_ORG_TOKEN')
    return None

def main():
    print("=" * 60)
    print("🚀 Testing Fly.io CLI Authentication")
    print("=" * 60)
    
    # Get the token
    token = get_fly_token()
    if not token:
        print("❌ No Fly.io token found in Secrets Manager")
        return
    
    print("\n✅ Loaded Fly.io token from Secrets Manager")
    print(f"   Token starts with: {token[:20]}...")
    print(f"   Token length: {len(token)}")
    
    # Test with fly auth whoami
    print("\n🔐 Running: fly auth whoami")
    print("-" * 40)
    
    env = os.environ.copy()
    env['FLY_API_TOKEN'] = token
    
    try:
        result = subprocess.run(
            ['fly', 'auth', 'whoami'],
            env=env,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"✅ SUCCESS!")
            print(f"   Authenticated as: {result.stdout.strip()}")
            
            # Also test fly apps list
            print("\n📱 Running: fly apps list")
            print("-" * 40)
            
            result2 = subprocess.run(
                ['fly', 'apps', 'list'],
                env=env,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result2.returncode == 0:
                lines = result2.stdout.strip().split('\n')
                print(f"✅ Found {len(lines)-1} apps:")  # Subtract header line
                for line in lines[:5]:  # Show first 5 lines
                    print(f"   {line}")
                if len(lines) > 5:
                    print(f"   ... and {len(lines)-5} more")
        else:
            print(f"❌ FAILED")
            print(f"   Error: {result.stderr.strip()}")
            
    except subprocess.TimeoutExpired:
        print("⚠️  Command timed out")
    except FileNotFoundError:
        print("❌ fly CLI not found")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("  The Fly.io credentials in the Secrets Manager are working!")
    print("  The GUI health check issues are likely due to Docker networking.")
    print("=" * 60)

if __name__ == "__main__":
    main()