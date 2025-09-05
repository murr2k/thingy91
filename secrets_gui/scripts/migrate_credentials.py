#!/usr/bin/env python3
"""
One-time migration script to import credentials from old unencrypted JSON file
to the new encrypted Secrets Manager GUI.
"""

import json
import os
import sys
import requests
from pathlib import Path
from typing import Dict, Any

# Configuration
OLD_CREDENTIALS_FILE = "/home/murr2k/projects/mcp-secrets-server/secrets/credentials.json"
SECRETS_API_URL = "http://localhost:5000"  # Secrets Manager GUI API

# Service name mappings (old name -> new service name)
SERVICE_MAPPINGS = {
    "github": "github",
    "flyio": "flyio", 
    "npm": "npm",
    "grafana": "grafana",
    "googleplay": "google_play",
    "docker": "docker_hub",
    "macrofab": "macrofab",
    "cloudflare": "cloudflare",
    "nexar": "nexar",
    "terraform": "terraform_cloud",
    "edgeimpulse": "edge_impulse",
    "cal": "cal_com",
    "Wolfram": "wolfram_alpha",
    "infisical": "infisical",
    "digikey": "digikey",
    "digikey_production": "digikey_production",  # Separate service for production
    "blynk": "blynk"
}

# Key mappings for each service (old key name -> new key name)
KEY_MAPPINGS = {
    "github": {
        "token": "personal_access_token",
        "user": "username",
        "admin_token": "admin_token"
    },
    "flyio": {
        "token": "auth_token",
        "org": "organization",
        "org_token": "org_token",
        "deploy_token": "deploy_token",
        "admin_token": "admin_token"
    },
    "npm": {
        "token": "auth_token",
        "auth_token": "registry_token"
    },
    "grafana": {
        "token": "api_key"
    },
    "googleplay": {
        "service_account": "service_account_json"
    },
    "docker": {
        "pat": "access_token"
    },
    "macrofab": {
        "api_key": "api_key"
    },
    "cloudflare": {
        "email": "email",
        "global_api_key": "api_key"
    },
    "nexar": {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "access_token": "access_token"
    },
    "terraform": {
        "api_token": "api_token"
    },
    "edgeimpulse": {
        "project_api_key": "api_key",
        "hmac_key": "hmac_key"
    },
    "cal": {
        "api_key": "api_key"
    },
    "Wolfram": {
        "app_id": "app_id"
    },
    "infisical": {
        "service_token": "service_token"
    },
    "digikey": {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "access_token": "access_token",
        "refresh_token": "refresh_token"
    },
    "digikey_production": {
        "client_id": "prod_client_id",
        "client_secret": "prod_client_secret",
        "access_token": "prod_access_token",
        "refresh_token": "prod_refresh_token"
    },
    "blynk": {
        "auth_token": "auth_token",
        "organization_id": "organization_id",
        "template_name": "template_name"
    }
}


def load_old_credentials() -> Dict[str, Any]:
    """Load credentials from the old unencrypted JSON file."""
    try:
        with open(OLD_CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find credentials file at {OLD_CREDENTIALS_FILE}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file: {e}")
        sys.exit(1)


def check_api_health() -> bool:
    """Check if the Secrets Manager API is running."""
    try:
        response = requests.get(f"{SECRETS_API_URL}/api/status", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def get_existing_services() -> list:
    """Get list of existing services from the API."""
    try:
        response = requests.get(f"{SECRETS_API_URL}/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Extract service IDs from the status response
            return [{'id': sid} for sid in data.keys()]
    except requests.exceptions.RequestException:
        pass
    return []


def save_credential(service_name: str, key_name: str, value: str) -> bool:
    """Save a single credential to the Secrets Manager."""
    if not value or value == "":
        print(f"  ⚠️  Skipping empty {key_name}")
        return False
        
    try:
        # The API expects the full config for the service
        # We'll send just this one key-value pair
        payload = {
            key_name: value
        }
        
        response = requests.post(
            f"{SECRETS_API_URL}/api/service/{service_name}/configure",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"  ✓ Saved {key_name}")
            return True
        else:
            print(f"  ✗ Failed to save {key_name}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error saving {key_name}: {e}")
        return False


def save_service_credentials(service_name: str, credentials: Dict[str, str]) -> bool:
    """Save all credentials for a service at once."""
    if not credentials:
        return False
        
    try:
        response = requests.post(
            f"{SECRETS_API_URL}/api/service/{service_name}/configure",
            json=credentials,
            timeout=10
        )
        
        if response.status_code == 200:
            for key in credentials.keys():
                print(f"  ✓ Saved {key}")
            return True
        else:
            print(f"  ✗ Failed to save credentials: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error saving credentials: {e}")
        return False


def migrate_service(old_name: str, old_data: Dict[str, Any], existing_services: list) -> int:
    """Migrate credentials for a single service."""
    # Get the new service name
    new_name = SERVICE_MAPPINGS.get(old_name)
    if not new_name:
        print(f"\n⚠️  Unknown service '{old_name}' - skipping")
        return 0
    
    print(f"\n📦 Migrating {old_name} -> {new_name}")
    
    # Get key mappings for this service
    key_map = KEY_MAPPINGS.get(old_name, {})
    
    # Build credentials dict with proper key names
    credentials = {}
    for old_key, value in old_data.items():
        if value and value != "":  # Skip empty values
            new_key = key_map.get(old_key, old_key)  # Use same key name if no mapping
            credentials[new_key] = str(value)
    
    if not credentials:
        print(f"  ⚠️  No credentials to migrate")
        return 0
    
    # Save all credentials at once
    if save_service_credentials(new_name, credentials):
        return len(credentials)
    else:
        return 0


def main():
    """Main migration function."""
    print("=" * 60)
    print("🔄 Starting credential migration")
    print("=" * 60)
    
    # Check if API is running
    print("\n🔍 Checking Secrets Manager API...")
    if not check_api_health():
        print("❌ Secrets Manager API is not running!")
        print("Please start the application first:")
        print("  cd /home/murr2k/projects/thingy91/secrets_gui")
        print("  python app.py")
        sys.exit(1)
    print("✓ API is running")
    
    # Load old credentials
    print("\n📂 Loading old credentials...")
    old_creds = load_old_credentials()
    print(f"✓ Found {len(old_creds)} services")
    
    # Get existing services
    print("\n🔍 Checking existing services...")
    existing_services = get_existing_services()
    print(f"✓ Found {len(existing_services)} configured services")
    
    # Migrate each service
    total_migrated = 0
    successful_services = 0
    
    for service_name, service_data in old_creds.items():
        if isinstance(service_data, dict):
            count = migrate_service(service_name, service_data, existing_services)
            if count > 0:
                successful_services += 1
                total_migrated += count
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Migration Complete!")
    print(f"   - Services processed: {successful_services}")
    print(f"   - Credentials migrated: {total_migrated}")
    
    # Check for services that need to be added
    missing_services = []
    for old_name in old_creds.keys():
        new_name = SERVICE_MAPPINGS.get(old_name)
        if new_name and new_name not in [s['id'] for s in existing_services]:
            if new_name in ['edge_impulse', 'cal_com', 'wolfram_alpha']:
                missing_services.append(new_name)
    
    if missing_services:
        print(f"\n⚠️  The following services need to be added to the GUI first:")
        for service in missing_services:
            print(f"   - {service}")
        print("\nRun this migration again after adding these services.")
    
    print("\n💡 Next steps:")
    print("   1. Verify credentials in the web UI: http://localhost:5000")
    print("   2. Test service connections")
    print("   3. Plan credential rotation for production use")
    print("=" * 60)


if __name__ == "__main__":
    main()