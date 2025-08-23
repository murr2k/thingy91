# Secure Secrets Management Guide

This guide provides multiple secure methods for managing sensitive credentials like Onomondo API keys without storing them in files.

## Table of Contents
1. [GitHub Secrets Manager (Recommended for CI/CD)](#github-secrets-manager)
2. [Local Development Options](#local-development-options)
3. [Security Best Practices](#security-best-practices)
4. [Implementation Examples](#implementation-examples)

## GitHub Secrets Manager

### Setting Up Repository Secrets

1. **Navigate to Repository Settings**
   - Go to https://github.com/murr2k/thingy91
   - Click "Settings" → "Secrets and variables" → "Actions"

2. **Add Required Secrets**
   ```
   ONOMONDO_API_KEY        - Your Onomondo API key
   ONOMONDO_IMSI          - Device IMSI
   ONOMONDO_ICCID         - Device ICCID  
   ONOMONDO_KI            - Authentication key
   ONOMONDO_OPC           - Operator key
   SOFTSIM_PROFILE_ID     - Profile identifier
   ```

3. **Organization Secrets (Optional)**
   - For multiple repositories, use Organization secrets
   - Settings → Secrets → Organization secrets

### GitHub Actions Workflow

Create `.github/workflows/provision-softsim.yml`:

```yaml
name: Provision SoftSIM

on:
  workflow_dispatch:
    inputs:
      device_serial:
        description: 'Device Serial Number'
        required: true
        type: string

jobs:
  provision:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Create secure profile
      env:
        ONOMONDO_API_KEY: ${{ secrets.ONOMONDO_API_KEY }}
        ONOMONDO_IMSI: ${{ secrets.ONOMONDO_IMSI }}
        ONOMONDO_ICCID: ${{ secrets.ONOMONDO_ICCID }}
        ONOMONDO_KI: ${{ secrets.ONOMONDO_KI }}
        ONOMONDO_OPC: ${{ secrets.ONOMONDO_OPC }}
      run: |
        python scripts/create_secure_profile.py \
          --device-serial ${{ github.event.inputs.device_serial }}
    
    - name: Provision device
      run: |
        # Provisioning happens here with encrypted profile
        echo "Profile provisioned securely"
```

## Local Development Options

### Option 1: Environment Variables with Encryption

Create `scripts/secrets_manager.py`:

```python
#!/usr/bin/env python3
"""
Secure Secrets Manager for Local Development
"""

import os
import sys
import json
import base64
import hashlib
import getpass
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import keyring

class SecretsManager:
    """Secure secrets management using system keyring"""
    
    SERVICE_NAME = "thingy91-softsim"
    
    @staticmethod
    def store_secret(key: str, value: str):
        """Store secret in system keyring"""
        keyring.set_password(SecretsManager.SERVICE_NAME, key, value)
        print(f"✓ Stored {key} in system keyring")
    
    @staticmethod
    def get_secret(key: str) -> str:
        """Retrieve secret from system keyring"""
        value = keyring.get_password(SecretsManager.SERVICE_NAME, key)
        if not value:
            raise ValueError(f"Secret {key} not found")
        return value
    
    @staticmethod
    def delete_secret(key: str):
        """Remove secret from system keyring"""
        keyring.delete_password(SecretsManager.SERVICE_NAME, key)
        print(f"✓ Deleted {key} from system keyring")
    
    @staticmethod
    def list_secrets():
        """List all stored secret keys"""
        # Note: keyring doesn't provide list functionality
        # Track keys in a separate encrypted file
        known_keys = [
            "ONOMONDO_API_KEY",
            "ONOMONDO_IMSI",
            "ONOMONDO_ICCID",
            "ONOMONDO_KI",
            "ONOMONDO_OPC"
        ]
        print("Known secret keys:")
        for key in known_keys:
            try:
                SecretsManager.get_secret(key)
                print(f"  ✓ {key}")
            except:
                print(f"  ✗ {key} (not set)")

class EncryptedEnvFile:
    """Encrypted .env file manager"""
    
    def __init__(self, env_file=".env.encrypted"):
        self.env_file = Path(env_file)
        self.key_file = Path.home() / ".thingy91_key"
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            # Generate key from password
            password = getpass.getpass("Enter encryption password: ").encode()
            salt = os.urandom(16)
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            # Store key securely (with proper permissions)
            self.key_file.touch(mode=0o600)
            with open(self.key_file, 'wb') as f:
                f.write(salt + key)
            
            return key
    
    def encrypt_env(self, env_dict: dict):
        """Encrypt and save environment variables"""
        key = self._get_or_create_key()
        f = Fernet(key[-44:])  # Use last 44 bytes as Fernet key
        
        env_content = '\n'.join([f"{k}={v}" for k, v in env_dict.items()])
        encrypted = f.encrypt(env_content.encode())
        
        with open(self.env_file, 'wb') as file:
            file.write(encrypted)
        
        os.chmod(self.env_file, 0o600)
        print(f"✓ Encrypted secrets saved to {self.env_file}")
    
    def decrypt_env(self) -> dict:
        """Decrypt and load environment variables"""
        if not self.env_file.exists():
            raise FileNotFoundError(f"{self.env_file} not found")
        
        key = self._get_or_create_key()
        f = Fernet(key[-44:])
        
        with open(self.env_file, 'rb') as file:
            encrypted = file.read()
        
        decrypted = f.decrypt(encrypted).decode()
        
        env_dict = {}
        for line in decrypted.split('\n'):
            if '=' in line:
                k, v = line.split('=', 1)
                env_dict[k] = v
        
        return env_dict
    
    def load_to_environment(self):
        """Load decrypted variables to environment"""
        env_dict = self.decrypt_env()
        for k, v in env_dict.items():
            os.environ[k] = v
        print(f"✓ Loaded {len(env_dict)} secrets to environment")

def main():
    """CLI for secrets management"""
    if len(sys.argv) < 2:
        print("Usage: secrets_manager.py <command> [args]")
        print("Commands:")
        print("  store <key> <value>  - Store secret in keyring")
        print("  get <key>           - Get secret from keyring")
        print("  delete <key>        - Delete secret from keyring")
        print("  list                - List all secrets")
        print("  encrypt             - Create encrypted .env file")
        print("  decrypt             - Load encrypted .env file")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "store" and len(sys.argv) == 4:
        SecretsManager.store_secret(sys.argv[2], sys.argv[3])
    
    elif command == "get" and len(sys.argv) == 3:
        value = SecretsManager.get_secret(sys.argv[2])
        print(value)
    
    elif command == "delete" and len(sys.argv) == 3:
        SecretsManager.delete_secret(sys.argv[2])
    
    elif command == "list":
        SecretsManager.list_secrets()
    
    elif command == "encrypt":
        env_manager = EncryptedEnvFile()
        secrets = {}
        
        print("Enter secrets (empty value to skip):")
        for key in ["ONOMONDO_API_KEY", "ONOMONDO_IMSI", "ONOMONDO_ICCID", 
                    "ONOMONDO_KI", "ONOMONDO_OPC"]:
            value = getpass.getpass(f"{key}: ")
            if value:
                secrets[key] = value
        
        env_manager.encrypt_env(secrets)
    
    elif command == "decrypt":
        env_manager = EncryptedEnvFile()
        env_manager.load_to_environment()
    
    else:
        print("Invalid command or arguments")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Option 2: WSL Credential Manager Integration

Create `scripts/wsl_secrets.sh`:

```bash
#!/bin/bash
# WSL integration with Windows Credential Manager

# Store secret in Windows Credential Manager
store_secret() {
    local key=$1
    local value=$2
    
    # Use cmdkey on Windows side
    cmd.exe /c "cmdkey /generic:thingy91_${key} /user:${key} /pass:${value}" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✓ Stored ${key} in Windows Credential Manager"
    else
        echo "✗ Failed to store ${key}"
        return 1
    fi
}

# Retrieve secret from Windows Credential Manager
get_secret() {
    local key=$1
    
    # Use PowerShell to retrieve credential
    local value=$(powershell.exe -Command "
        \$cred = Get-StoredCredential -Target 'thingy91_${key}' -AsCredentialObject 2>\$null
        if (\$cred) {
            \$cred.GetNetworkCredential().Password
        }
    " 2>/dev/null | tr -d '\r\n')
    
    if [ -n "$value" ]; then
        echo "$value"
    else
        echo "Secret ${key} not found" >&2
        return 1
    fi
}

# Export secrets to environment
export_secrets() {
    export ONOMONDO_API_KEY=$(get_secret ONOMONDO_API_KEY)
    export ONOMONDO_IMSI=$(get_secret ONOMONDO_IMSI)
    export ONOMONDO_ICCID=$(get_secret ONOMONDO_ICCID)
    export ONOMONDO_KI=$(get_secret ONOMONDO_KI)
    export ONOMONDO_OPC=$(get_secret ONOMONDO_OPC)
    
    echo "✓ Secrets loaded to environment"
}

# Interactive setup
setup_secrets() {
    echo "Setting up Onomondo secrets..."
    
    read -s -p "Enter Onomondo API Key: " api_key
    echo
    store_secret ONOMONDO_API_KEY "$api_key"
    
    read -p "Enter IMSI: " imsi
    store_secret ONOMONDO_IMSI "$imsi"
    
    read -p "Enter ICCID: " iccid
    store_secret ONOMONDO_ICCID "$iccid"
    
    read -s -p "Enter KI: " ki
    echo
    store_secret ONOMONDO_KI "$ki"
    
    read -s -p "Enter OPC: " opc
    echo
    store_secret ONOMONDO_OPC "$opc"
    
    echo "✓ Setup complete"
}

# Main script
case "$1" in
    store)
        store_secret "$2" "$3"
        ;;
    get)
        get_secret "$2"
        ;;
    export)
        export_secrets
        ;;
    setup)
        setup_secrets
        ;;
    *)
        echo "Usage: $0 {store|get|export|setup} [key] [value]"
        exit 1
        ;;
esac
```

### Option 3: HashiCorp Vault Integration (Production)

Create `scripts/vault_integration.py`:

```python
#!/usr/bin/env python3
"""
HashiCorp Vault integration for production secrets
"""

import hvac
import os
from typing import Dict, Any

class VaultSecretsManager:
    """Production-grade secrets management with HashiCorp Vault"""
    
    def __init__(self, vault_url=None, vault_token=None):
        self.vault_url = vault_url or os.getenv('VAULT_ADDR', 'http://localhost:8200')
        self.vault_token = vault_token or os.getenv('VAULT_TOKEN')
        
        self.client = hvac.Client(
            url=self.vault_url,
            token=self.vault_token
        )
        
        if not self.client.is_authenticated():
            raise Exception("Vault authentication failed")
    
    def store_onomondo_secrets(self, secrets: Dict[str, str]):
        """Store Onomondo secrets in Vault"""
        self.client.secrets.kv.v2.create_or_update_secret(
            path='onomondo/softsim',
            secret=secrets
        )
        print("✓ Secrets stored in Vault")
    
    def get_onomondo_secrets(self) -> Dict[str, Any]:
        """Retrieve Onomondo secrets from Vault"""
        response = self.client.secrets.kv.v2.read_secret_version(
            path='onomondo/softsim'
        )
        return response['data']['data']
    
    def create_temporary_token(self, ttl='1h'):
        """Create temporary token for CI/CD"""
        response = self.client.auth.token.create(
            ttl=ttl,
            policies=['onomondo-read']
        )
        return response['auth']['client_token']
```

## Security Best Practices

### 1. Never Commit Secrets
```bash
# Add to .gitignore
.env
.env.*
*.key
*.pem
secrets/
credentials.json
```

### 2. Use Git Hooks for Prevention
Create `.githooks/pre-commit`:

```bash
#!/bin/bash
# Prevent committing secrets

# Check for potential secrets
FILES=$(git diff --cached --name-only)

for FILE in $FILES; do
    # Check for API keys, passwords, etc.
    if grep -qE "(api_key|API_KEY|password|PASSWORD|secret|SECRET|key|KEY).*=.*['\"].*['\"]" "$FILE"; then
        echo "⚠️  Potential secret found in $FILE"
        echo "Please review and remove sensitive data"
        exit 1
    fi
done

exit 0
```

### 3. Runtime Secret Injection
Create `scripts/secure_provision.py`:

```python
#!/usr/bin/env python3
"""
Secure provisioning with runtime secret injection
"""

import os
import sys
from provision_softsim import SoftSIMProvisioner, SoftSIMProfile

def get_secret(key: str) -> str:
    """Get secret from environment or prompt"""
    value = os.getenv(key)
    if not value:
        from getpass import getpass
        value = getpass(f"Enter {key}: ")
    return value

def main():
    # Get secrets at runtime
    profile = SoftSIMProfile(
        imsi=get_secret('ONOMONDO_IMSI'),
        iccid=get_secret('ONOMONDO_ICCID'),
        ki=get_secret('ONOMONDO_KI'),
        opc=get_secret('ONOMONDO_OPC'),
        profile_id=get_secret('SOFTSIM_PROFILE_ID'),
        apn='onomondo'
    )
    
    # Provision without ever writing secrets to disk
    provisioner = SoftSIMProvisioner(sys.argv[1])
    provisioner.connect()
    provisioner.provision_profile(profile)
    provisioner.activate()
    provisioner.disconnect()

if __name__ == "__main__":
    main()
```

### 4. Docker Secrets for Container Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  provisioner:
    build: .
    secrets:
      - onomondo_api_key
      - onomondo_credentials
    environment:
      - ONOMONDO_API_KEY_FILE=/run/secrets/onomondo_api_key

secrets:
  onomondo_api_key:
    external: true
  onomondo_credentials:
    external: true
```

### 5. Azure Key Vault Integration (Alternative)

```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://your-vault.vault.azure.net/",
    credential=credential
)

# Retrieve secret
api_key = client.get_secret("onomondo-api-key").value
```

## Implementation Examples

### Example 1: CI/CD Pipeline with GitHub Secrets

```yaml
# .github/workflows/secure-deploy.yml
name: Secure Deployment

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Provision devices
      env:
        SECRETS_JSON: ${{ toJson(secrets) }}
      run: |
        # Secrets are injected as environment variables
        python scripts/batch_provision.py \
          --devices devices.csv \
          --use-env-secrets
```

### Example 2: Local Development Workflow

```bash
# One-time setup
./scripts/wsl_secrets.sh setup

# Before development
source ./scripts/wsl_secrets.sh export

# Use in Python
import os
api_key = os.environ['ONOMONDO_API_KEY']

# Use in provisioning
./scripts/secure_provision.py /dev/ttyACM0
```

### Example 3: Production Deployment

```python
# Production provisioning service
from vault_integration import VaultSecretsManager

vault = VaultSecretsManager()
secrets = vault.get_onomondo_secrets()

# Use secrets without exposing them
provision_device(secrets['imsi'], secrets['iccid'])
```

## Recommended Setup for Your Project

1. **For CI/CD**: Use GitHub Secrets Manager
2. **For Local Development**: Use WSL Credential Manager or system keyring
3. **For Production**: Consider HashiCorp Vault or cloud provider's secret manager
4. **For Team Collaboration**: Use encrypted .env files with shared keys in password manager

## Quick Start

1. **Set up GitHub Secrets**:
   ```bash
   gh secret set ONOMONDO_API_KEY
   gh secret set ONOMONDO_IMSI
   gh secret set ONOMONDO_ICCID
   gh secret set ONOMONDO_KI
   gh secret set ONOMONDO_OPC
   ```

2. **Set up local secrets**:
   ```bash
   python scripts/secrets_manager.py encrypt
   # Or
   ./scripts/wsl_secrets.sh setup
   ```

3. **Use in provisioning**:
   ```bash
   # Secrets loaded from secure storage
   python scripts/secure_provision.py /dev/ttyACM0
   ```

## Security Checklist

- [ ] No secrets in source code
- [ ] No secrets in git history
- [ ] Secrets encrypted at rest
- [ ] Secrets transmitted over secure channels
- [ ] Access logging enabled
- [ ] Regular secret rotation
- [ ] Minimal privilege principle
- [ ] Separate secrets per environment
- [ ] Audit trail for secret access
- [ ] Emergency revocation procedure

## Support

For additional security guidance:
- GitHub Secrets: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- HashiCorp Vault: https://www.vaultproject.io/docs
- Azure Key Vault: https://azure.microsoft.com/en-us/services/key-vault/
- AWS Secrets Manager: https://aws.amazon.com/secrets-manager/