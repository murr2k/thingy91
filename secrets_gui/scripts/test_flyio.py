#!/usr/bin/env python3
"""
Test Fly.io credentials and authentication.
"""

import json
import os
import sys
import requests
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

def get_flyio_credentials():
    """Get Fly.io credentials from encrypted storage."""
    # Load master key
    with open(MASTER_KEY_FILE, 'r') as f:
        master_key = f.read().strip()
    
    # Setup decryption
    key = derive_key(master_key)
    fernet = Fernet(key)
    
    # Load and decrypt secrets
    with open(SECRETS_FILE, 'r') as f:
        encrypted_data = json.load(f)
    
    if 'flyio' in encrypted_data:
        decrypted = fernet.decrypt(encrypted_data['flyio'].encode())
        return json.loads(decrypted)
    return None

def test_flyio_token(token, token_name):
    """Test a Fly.io token by making an API call."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    
    try:
        # Test the token with the user info endpoint
        response = requests.get(
            'https://api.fly.io/graphql',
            headers=headers,
            json={
                'query': '{ viewer { email name } }'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                return f"❌ {token_name}: API returned errors - {data['errors']}"
            elif 'data' in data and data['data']:
                viewer = data['data'].get('viewer', {})
                if viewer:
                    return f"✅ {token_name}: Valid! User: {viewer.get('email', 'N/A')}"
                else:
                    return f"⚠️  {token_name}: Token might be valid but no user info returned"
            else:
                return f"❌ {token_name}: Invalid response format"
        elif response.status_code == 401:
            return f"❌ {token_name}: Unauthorized - token is invalid or expired"
        else:
            return f"❌ {token_name}: HTTP {response.status_code} - {response.text[:100]}"
    except requests.exceptions.Timeout:
        return f"⚠️  {token_name}: Request timed out"
    except requests.exceptions.RequestException as e:
        return f"❌ {token_name}: Request failed - {e}"

def main():
    print("=" * 60)
    print("🔍 Testing Fly.io Credentials")
    print("=" * 60)
    
    # Get credentials
    creds = get_flyio_credentials()
    if not creds:
        print("❌ No Fly.io credentials found in storage")
        sys.exit(1)
    
    print(f"\n📦 Found Fly.io credentials:")
    for key in creds.keys():
        if 'token' in key.lower():
            masked = creds[key][:8] + "..." if len(creds[key]) > 8 else "***"
            print(f"  - {key}: {masked}")
        else:
            print(f"  - {key}: {creds[key] if creds[key] else '(empty)'}")
    
    print("\n🔐 Testing authentication with each token:\n")
    
    # Test each token
    tokens_to_test = [
        ('FLYIO_AUTH_TOKEN', 'Auth Token'),
        ('FLYIO_ORG_TOKEN', 'Organization Token'),
        ('FLYIO_DEPLOY_TOKEN', 'Deploy Token'),
        ('FLYIO_ADMIN_TOKEN', 'Admin Token')
    ]
    
    valid_tokens = []
    for key, name in tokens_to_test:
        if key in creds and creds[key]:
            result = test_flyio_token(creds[key], name)
            print(result)
            if "✅" in result:
                valid_tokens.append((key, creds[key]))
    
    # If we have a valid token, test more operations
    if valid_tokens:
        print("\n📊 Testing API operations with valid token:\n")
        key, token = valid_tokens[0]
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        # Test listing organizations
        response = requests.get(
            'https://api.fly.io/graphql',
            headers=headers,
            json={
                'query': '{ organizations { nodes { id name slug } } }'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('organizations'):
                orgs = data['data']['organizations'].get('nodes', [])
                print(f"✅ Organizations accessible: {len(orgs)} found")
                for org in orgs[:3]:  # Show first 3
                    print(f"   - {org.get('name')} ({org.get('slug')})")
            else:
                print("⚠️  No organizations found or error in response")
    
    print("\n" + "=" * 60)
    
    if valid_tokens:
        print("✅ Fly.io authentication successful!")
        print(f"\n💡 To use with Fly CLI:")
        print(f"   export FLY_API_TOKEN='{valid_tokens[0][1]}'")
        print(f"   fly status")
    else:
        print("❌ No valid Fly.io tokens found")
        print("\n💡 You may need to:")
        print("   1. Generate new tokens at https://fly.io/user/personal_access_tokens")
        print("   2. Update the credentials in the Secrets Manager GUI")
    
    print("=" * 60)

if __name__ == "__main__":
    main()