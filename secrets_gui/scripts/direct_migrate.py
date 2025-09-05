#!/usr/bin/env python3
"""
Direct migration script that imports credentials into the encrypted secrets file.
Works directly with the secrets.json file instead of going through the API.
"""

import json
import os
import sys
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64

# Paths
OLD_CREDENTIALS_FILE = "/home/murr2k/projects/mcp-secrets-server/secrets/credentials.json"
SECRETS_FILE = "/home/murr2k/projects/thingy91/secrets_gui/data/secrets.json"
MASTER_KEY_FILE = "/home/murr2k/projects/thingy91/secrets_gui/data/.master_key"

# Service mappings
SERVICE_KEY_MAPPINGS = {
    "github": {
        "token": "GITHUB_TOKEN",
        "user": "GITHUB_USER", 
        "admin_token": "GITHUB_ADMIN_TOKEN"
    },
    "flyio": {
        "token": "FLYIO_AUTH_TOKEN",
        "org": "FLYIO_ORG",
        "org_token": "FLYIO_ORG_TOKEN",
        "deploy_token": "FLYIO_DEPLOY_TOKEN",
        "admin_token": "FLYIO_ADMIN_TOKEN"
    },
    "npm": {
        "token": "NPM_AUTH_TOKEN",
        "auth_token": "NPM_REGISTRY_TOKEN"
    },
    "grafana": {
        "token": "GRAFANA_API_KEY"
    },
    "googleplay": {
        "service_account": "GOOGLE_PLAY_SERVICE_ACCOUNT"
    },
    "docker": {
        "pat": "DOCKER_HUB_ACCESS_TOKEN"
    },
    "macrofab": {
        "api_key": "MACROFAB_API_KEY"
    },
    "cloudflare": {
        "email": "CLOUDFLARE_EMAIL",
        "global_api_key": "CLOUDFLARE_API_KEY"
    },
    "nexar": {
        "client_id": "NEXAR_CLIENT_ID",
        "client_secret": "NEXAR_CLIENT_SECRET",
        "access_token": "NEXAR_ACCESS_TOKEN"
    },
    "terraform": {
        "api_token": "TERRAFORM_API_TOKEN"
    },
    "edgeimpulse": {
        "project_api_key": "EDGE_IMPULSE_API_KEY",
        "hmac_key": "EDGE_IMPULSE_HMAC_KEY"
    },
    "cal": {
        "api_key": "CAL_API_KEY"
    },
    "Wolfram": {
        "app_id": "WOLFRAM_APP_ID"
    },
    "infisical": {
        "service_token": "INFISICAL_SERVICE_TOKEN"
    },
    "digikey": {
        "client_id": "DIGIKEY_CLIENT_ID",
        "client_secret": "DIGIKEY_CLIENT_SECRET",
        "access_token": "DIGIKEY_ACCESS_TOKEN",
        "refresh_token": "DIGIKEY_REFRESH_TOKEN"
    },
    "digikey_production": {
        "client_id": "DIGIKEY_PROD_CLIENT_ID",
        "client_secret": "DIGIKEY_PROD_CLIENT_SECRET",
        "access_token": "DIGIKEY_PROD_ACCESS_TOKEN",
        "refresh_token": "DIGIKEY_PROD_REFRESH_TOKEN"
    },
    "blynk": {
        "auth_token": "BLYNK_AUTH_TOKEN",
        "organization_id": "BLYNK_ORGANIZATION_ID",
        "template_name": "BLYNK_TEMPLATE_NAME"
    }
}

def load_old_credentials():
    """Load the old unencrypted credentials."""
    with open(OLD_CREDENTIALS_FILE, 'r') as f:
        return json.load(f)

def get_or_create_master_key():
    """Get existing master key or create a new one."""
    if os.path.exists(MASTER_KEY_FILE):
        with open(MASTER_KEY_FILE, 'r') as f:
            return f.read().strip()
    else:
        # Generate a new master key
        import secrets
        import string
        chars = string.ascii_letters + string.digits + string.punctuation
        master_key = ''.join(secrets.choice(chars) for _ in range(32))
        
        # Save it
        os.makedirs(os.path.dirname(MASTER_KEY_FILE), exist_ok=True)
        with open(MASTER_KEY_FILE, 'w') as f:
            f.write(master_key)
        os.chmod(MASTER_KEY_FILE, 0o600)
        
        print(f"✓ Created new master key at {MASTER_KEY_FILE}")
        return master_key

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

def load_existing_secrets(fernet):
    """Load existing secrets if file exists."""
    if os.path.exists(SECRETS_FILE):
        try:
            with open(SECRETS_FILE, 'r') as f:
                encrypted_data = json.load(f)
            
            secrets = {}
            for service, encrypted_value in encrypted_data.items():
                try:
                    decrypted = fernet.decrypt(encrypted_value.encode())
                    secrets[service] = json.loads(decrypted)
                except:
                    # Skip if we can't decrypt
                    pass
            return secrets
        except:
            return {}
    return {}

def save_secrets(secrets, fernet):
    """Save encrypted secrets to file."""
    encrypted_data = {}
    for service, values in secrets.items():
        encrypted = fernet.encrypt(json.dumps(values).encode()).decode()
        encrypted_data[service] = encrypted
    
    os.makedirs(os.path.dirname(SECRETS_FILE), exist_ok=True)
    with open(SECRETS_FILE, 'w') as f:
        json.dump(encrypted_data, f, indent=2)
    os.chmod(SECRETS_FILE, 0o600)

def main():
    print("=" * 60)
    print("🔄 Direct Credential Migration")
    print("=" * 60)
    
    # Load old credentials
    print("\n📂 Loading old credentials...")
    old_creds = load_old_credentials()
    print(f"✓ Found {len(old_creds)} services")
    
    # Get master key and setup encryption
    print("\n🔐 Setting up encryption...")
    master_key = get_or_create_master_key()
    key = derive_key(master_key)
    fernet = Fernet(key)
    
    # Load existing secrets
    print("\n📥 Loading existing secrets...")
    secrets = load_existing_secrets(fernet)
    print(f"✓ Found {len(secrets)} existing services")
    
    # Migrate each service
    migrated = 0
    for old_service, old_data in old_creds.items():
        if isinstance(old_data, dict):
            print(f"\n📦 Processing {old_service}...")
            
            # Get the key mappings
            key_map = SERVICE_KEY_MAPPINGS.get(old_service, {})
            
            # Build the new credentials
            new_creds = {}
            for old_key, value in old_data.items():
                if value and value != "":
                    new_key = key_map.get(old_key, old_key.upper())
                    new_creds[new_key] = str(value)
                    print(f"  ✓ {old_key} -> {new_key}")
            
            if new_creds:
                # Determine the service name for storage
                if old_service == "docker":
                    service_name = "docker_hub"
                elif old_service == "googleplay":
                    service_name = "google_play"
                elif old_service == "terraform":
                    service_name = "terraform_cloud"
                elif old_service == "edgeimpulse":
                    service_name = "edge_impulse"
                elif old_service == "cal":
                    service_name = "cal_com"
                elif old_service == "Wolfram":
                    service_name = "wolfram_alpha"
                else:
                    service_name = old_service
                
                # Update or add to secrets
                if service_name in secrets:
                    secrets[service_name].update(new_creds)
                else:
                    secrets[service_name] = new_creds
                migrated += 1
    
    # Save all secrets
    print("\n💾 Saving encrypted secrets...")
    save_secrets(secrets, fernet)
    
    print("\n" + "=" * 60)
    print(f"✅ Migration Complete!")
    print(f"   - Services migrated: {migrated}")
    print(f"   - Secrets file: {SECRETS_FILE}")
    print(f"   - Master key: {MASTER_KEY_FILE}")
    print("\n💡 The secrets are now available in the GUI at:")
    print("   http://localhost:5000")
    print("=" * 60)

if __name__ == "__main__":
    main()