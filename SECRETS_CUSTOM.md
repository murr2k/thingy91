# Adding Custom Secrets for Other Services

The secrets manager can store credentials for any service, not just Onomondo. Here's how to add and use custom secrets.

## Method 1: Quick Add (Individual Secrets)

### Store a Secret
```bash
# Syntax: python3 scripts/secrets_manager.py store KEY VALUE
# Note: In WSL, this will inform you to use encrypted storage instead

# For encrypted file storage (WSL):
python3 scripts/secrets_manager.py encrypt
# Then add your custom keys when prompted
```

### Examples for Common Services

#### AWS Credentials
```bash
# Add to encrypted storage
python3 scripts/secrets_manager.py encrypt
# When prompted, add:
# AWS_ACCESS_KEY_ID: your-access-key
# AWS_SECRET_ACCESS_KEY: your-secret-key
# AWS_REGION: us-east-1
```

#### Azure Credentials
```bash
# AZURE_CLIENT_ID: your-client-id
# AZURE_CLIENT_SECRET: your-secret
# AZURE_TENANT_ID: your-tenant-id
# AZURE_SUBSCRIPTION_ID: your-subscription
```

#### Google Cloud
```bash
# GOOGLE_APPLICATION_CREDENTIALS: path-to-service-account
# GCP_PROJECT_ID: your-project-id
# GCP_API_KEY: your-api-key
```

#### Database Credentials
```bash
# DB_HOST: localhost
# DB_PORT: 5432
# DB_NAME: myapp
# DB_USER: dbuser
# DB_PASSWORD: secret-password
```

#### API Keys for Various Services
```bash
# OPENAI_API_KEY: sk-...
# STRIPE_API_KEY: sk_live_...
# TWILIO_ACCOUNT_SID: AC...
# TWILIO_AUTH_TOKEN: ...
# SENDGRID_API_KEY: SG...
# SLACK_BOT_TOKEN: xoxb-...
```

## Method 2: Modify the Script for Your Services

### Add Your Service's Keys to the Known List

Edit `scripts/secrets_manager.py` and add your keys:

```python
class SecretsManager:
    """Secure secrets management using system keyring"""
    
    SERVICE_NAME = "thingy91-softsim"
    KNOWN_KEYS = [
        # Onomondo
        "ONOMONDO_API_KEY",
        "ONOMONDO_IMSI",
        "ONOMONDO_ICCID",
        "ONOMONDO_KI",
        "ONOMONDO_OPC",
        "SOFTSIM_PROFILE_ID",
        
        # Add your services here:
        # AWS
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
        
        # Azure
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET",
        "AZURE_TENANT_ID",
        
        # Database
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        
        # Your custom keys
        "MY_SERVICE_API_KEY",
        "MY_SERVICE_SECRET",
    ]
```

Then run setup again:
```bash
python3 scripts/secrets_manager.py setup
```

## Method 3: Create Service-Specific Manager

Create a wrapper script for your service:

### Example: `scripts/aws_secrets.py`
```python
#!/usr/bin/env python3
"""AWS Secrets Manager"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from secrets_manager import EncryptedEnvFile

class AWSSecretsManager:
    AWS_KEYS = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY", 
        "AWS_REGION",
        "AWS_SESSION_TOKEN"
    ]
    
    def __init__(self):
        self.env_manager = EncryptedEnvFile(".aws.encrypted")
    
    def setup(self):
        """Interactive AWS setup"""
        print("=== AWS Credentials Setup ===")
        secrets = {}
        
        for key in self.AWS_KEYS:
            if "SECRET" in key or "TOKEN" in key:
                from getpass import getpass
                value = getpass(f"{key}: ")
            else:
                value = input(f"{key}: ")
            
            if value:
                secrets[key] = value
        
        if secrets:
            self.env_manager.encrypt_env(secrets)
            print("✓ AWS credentials encrypted")
    
    def load(self):
        """Load AWS credentials to environment"""
        return self.env_manager.load_to_environment()

if __name__ == "__main__":
    manager = AWSSecretsManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "load":
        manager.load()
    else:
        manager.setup()
```

## Method 4: Use Multiple Encrypted Files

You can organize secrets by service:

```bash
# Onomondo secrets
python3 scripts/secrets_manager.py encrypt --file .env.onomondo

# AWS secrets  
python3 scripts/secrets_manager.py encrypt --file .env.aws

# Database secrets
python3 scripts/secrets_manager.py encrypt --file .env.database

# Load specific service
python3 scripts/secrets_manager.py decrypt --file .env.aws
```

## Method 5: JSON Configuration

Create a JSON config for complex services:

### `configs/services.json`
```json
{
  "services": {
    "aws": {
      "credentials": {
        "access_key_id": "PROMPT",
        "secret_access_key": "SECURE_PROMPT",
        "region": "us-east-1"
      }
    },
    "database": {
      "primary": {
        "host": "localhost",
        "port": 5432,
        "database": "myapp",
        "user": "PROMPT",
        "password": "SECURE_PROMPT"
      }
    },
    "apis": {
      "openai": {
        "api_key": "SECURE_PROMPT",
        "organization": "PROMPT"
      },
      "stripe": {
        "publishable_key": "PROMPT",
        "secret_key": "SECURE_PROMPT"
      }
    }
  }
}
```

Then create a loader:
```python
import json

def load_service_config(service_name):
    with open('configs/services.json') as f:
        config = json.load(f)
    
    service_config = config['services'].get(service_name, {})
    
    # Process prompts
    for key, value in service_config.items():
        if value == "PROMPT":
            service_config[key] = input(f"{key}: ")
        elif value == "SECURE_PROMPT":
            from getpass import getpass
            service_config[key] = getpass(f"{key}: ")
    
    return service_config
```

## Using Custom Secrets

### Load to Environment
```bash
# Load all secrets
python3 scripts/secrets_manager.py decrypt

# Access in Python
import os
api_key = os.environ.get('MY_SERVICE_API_KEY')

# Access in bash
echo $MY_SERVICE_API_KEY
```

### In Your Application
```python
import os
from typing import Optional

class ConfigManager:
    """Centralized configuration management"""
    
    @staticmethod
    def get_secret(key: str, default: Optional[str] = None) -> str:
        """Get secret from environment with fallback"""
        value = os.environ.get(key, default)
        if not value:
            raise ValueError(f"Required secret {key} not found")
        return value
    
    @staticmethod
    def get_aws_config():
        return {
            'aws_access_key_id': ConfigManager.get_secret('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': ConfigManager.get_secret('AWS_SECRET_ACCESS_KEY'),
            'region_name': ConfigManager.get_secret('AWS_REGION', 'us-east-1')
        }
    
    @staticmethod
    def get_database_url():
        user = ConfigManager.get_secret('DB_USER')
        password = ConfigManager.get_secret('DB_PASSWORD')
        host = ConfigManager.get_secret('DB_HOST', 'localhost')
        port = ConfigManager.get_secret('DB_PORT', '5432')
        name = ConfigManager.get_secret('DB_NAME')
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
```

## GitHub Actions for Multiple Services

### `.github/workflows/multi-service.yml`
```yaml
name: Multi-Service Deployment

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS
      env:
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        AWS_REGION: ${{ secrets.AWS_REGION }}
      run: |
        aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
        aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
        aws configure set region $AWS_REGION
    
    - name: Setup Database
      env:
        DB_CONNECTION: ${{ secrets.DB_CONNECTION_STRING }}
      run: |
        echo "Database configured"
    
    - name: Configure APIs
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        STRIPE_API_KEY: ${{ secrets.STRIPE_API_KEY }}
      run: |
        echo "APIs configured"
```

## Best Practices for Multiple Services

### 1. Namespace Your Secrets
```bash
# Use prefixes to organize
ONOMONDO_API_KEY=...
AWS_ACCESS_KEY=...
GCP_PROJECT_ID=...
AZURE_CLIENT_ID=...
DB_PROD_PASSWORD=...
DB_DEV_PASSWORD=...
```

### 2. Separate by Environment
```bash
# Production secrets
.env.production.encrypted

# Development secrets  
.env.development.encrypted

# Testing secrets
.env.test.encrypted
```

### 3. Document Required Secrets
Create a `.env.example` (safe to commit):
```bash
# Onomondo Configuration
ONOMONDO_API_KEY=your-api-key-here
ONOMONDO_IMSI=your-imsi

# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
DB_USER=dbuser
DB_PASSWORD=secret

# External APIs
OPENAI_API_KEY=sk-...
STRIPE_API_KEY=sk_live_...
```

### 4. Validation Script
Create `scripts/validate_secrets.py`:
```python
#!/usr/bin/env python3
"""Validate all required secrets are present"""

import os
import sys

REQUIRED_SECRETS = {
    'Onomondo': [
        'ONOMONDO_API_KEY',
        'ONOMONDO_IMSI',
    ],
    'AWS': [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
    ],
    'Database': [
        'DB_HOST',
        'DB_USER',
        'DB_PASSWORD',
    ]
}

def validate():
    missing = {}
    
    for service, keys in REQUIRED_SECRETS.items():
        for key in keys:
            if not os.environ.get(key):
                if service not in missing:
                    missing[service] = []
                missing[service].append(key)
    
    if missing:
        print("❌ Missing secrets:")
        for service, keys in missing.items():
            print(f"\n{service}:")
            for key in keys:
                print(f"  - {key}")
        return False
    
    print("✅ All required secrets found")
    return True

if __name__ == "__main__":
    sys.exit(0 if validate() else 1)
```

## Quick Reference

```bash
# Add any custom secret (interactive)
python3 scripts/secrets_manager.py encrypt
# Enter any key-value pairs you want

# Load all secrets
python3 scripts/secrets_manager.py decrypt

# Verify secrets
python3 scripts/validate_secrets.py

# Export for team member
# Share: .env.encrypted + password (via secure channel)

# For CI/CD
# Add to GitHub Secrets: Settings → Secrets → Actions
```

## Security Notes

- Never hardcode service credentials
- Use different credentials per environment
- Rotate secrets regularly
- Audit secret access
- Use least-privilege principle
- Consider secret expiration
- Implement secret versioning for critical services