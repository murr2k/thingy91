#!/usr/bin/env python3
"""
Secure Secrets Manager for Local Development
Provides multiple secure storage options without storing secrets in files
"""

import os
import sys
import json
import base64
import hashlib
import getpass
from pathlib import Path
from typing import Dict, Optional, Any
import argparse

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    print("Warning: cryptography not installed. Some features unavailable.")
    print("Install with: pip install cryptography")

try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False
    print("Warning: keyring not installed. System keyring unavailable.")
    print("Install with: pip install keyring")


class SecretsManager:
    """Secure secrets management using system keyring"""
    
    SERVICE_NAME = "thingy91-softsim"
    KNOWN_KEYS = [
        "ONOMONDO_API_KEY",
        "ONOMONDO_IMSI",
        "ONOMONDO_ICCID",
        "ONOMONDO_KI",
        "ONOMONDO_OPC",
        "SOFTSIM_PROFILE_ID"
    ]
    
    @staticmethod
    def is_available() -> bool:
        """Check if keyring is available"""
        return HAS_KEYRING
    
    @staticmethod
    def store_secret(key: str, value: str) -> bool:
        """Store secret in system keyring"""
        if not HAS_KEYRING:
            print("Error: keyring not available")
            return False
        
        try:
            keyring.set_password(SecretsManager.SERVICE_NAME, key, value)
            print(f"✓ Stored {key} in system keyring")
            return True
        except Exception as e:
            print(f"✗ Failed to store {key}: {e}")
            return False
    
    @staticmethod
    def get_secret(key: str) -> Optional[str]:
        """Retrieve secret from system keyring"""
        if not HAS_KEYRING:
            return None
        
        try:
            value = keyring.get_password(SecretsManager.SERVICE_NAME, key)
            return value
        except Exception as e:
            print(f"Error retrieving {key}: {e}")
            return None
    
    @staticmethod
    def delete_secret(key: str) -> bool:
        """Remove secret from system keyring"""
        if not HAS_KEYRING:
            return False
        
        try:
            keyring.delete_password(SecretsManager.SERVICE_NAME, key)
            print(f"✓ Deleted {key} from system keyring")
            return True
        except Exception as e:
            print(f"✗ Failed to delete {key}: {e}")
            return False
    
    @staticmethod
    def list_secrets():
        """List all stored secret keys"""
        print("\n=== Secret Keys Status ===")
        for key in SecretsManager.KNOWN_KEYS:
            if SecretsManager.get_secret(key):
                print(f"  ✓ {key} (stored)")
            else:
                print(f"  ✗ {key} (not set)")
    
    @staticmethod
    def interactive_setup():
        """Interactive setup for all secrets"""
        if not HAS_KEYRING:
            print("Error: keyring not available")
            return False
        
        print("\n=== Onomondo Secrets Setup ===")
        print("Enter values for each secret (press Enter to skip):\n")
        
        stored_count = 0
        
        for key in SecretsManager.KNOWN_KEYS:
            current = SecretsManager.get_secret(key)
            if current:
                update = input(f"{key} already exists. Update? (y/N): ").lower()
                if update != 'y':
                    continue
            
            if "KEY" in key or "KI" in key or "OPC" in key:
                # Sensitive values - use password input
                value = getpass.getpass(f"Enter {key}: ")
            else:
                # Less sensitive values - normal input
                value = input(f"Enter {key}: ")
            
            if value:
                if SecretsManager.store_secret(key, value):
                    stored_count += 1
        
        print(f"\n✓ Setup complete. Stored {stored_count} secrets.")
        return True


class EncryptedEnvFile:
    """Encrypted .env file manager for team sharing"""
    
    def __init__(self, env_file: str = ".env.encrypted"):
        self.env_file = Path(env_file)
        self.key_file = Path.home() / ".config" / "thingy91" / "encryption.key"
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
    
    def is_available(self) -> bool:
        """Check if encryption is available"""
        return HAS_CRYPTO
    
    def _derive_key(self, password: bytes, salt: bytes) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password))
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                data = f.read()
                if len(data) >= 60:  # 16 bytes salt + 44 bytes key
                    return data[16:]
        
        # Generate new key
        password = getpass.getpass("Create encryption password: ").encode()
        confirm = getpass.getpass("Confirm password: ").encode()
        
        if password != confirm:
            raise ValueError("Passwords do not match")
        
        salt = os.urandom(16)
        key = self._derive_key(password, salt)
        
        # Store with proper permissions
        self.key_file.touch(mode=0o600)
        with open(self.key_file, 'wb') as f:
            f.write(salt + key)
        
        print(f"✓ Encryption key saved to {self.key_file}")
        return key
    
    def encrypt_env(self, env_dict: Dict[str, str]) -> bool:
        """Encrypt and save environment variables"""
        if not HAS_CRYPTO:
            print("Error: cryptography library not available")
            return False
        
        try:
            key = self._get_or_create_key()
            f = Fernet(key)
            
            env_content = json.dumps(env_dict, indent=2)
            encrypted = f.encrypt(env_content.encode())
            
            with open(self.env_file, 'wb') as file:
                file.write(encrypted)
            
            os.chmod(self.env_file, 0o600)
            print(f"✓ Encrypted {len(env_dict)} secrets to {self.env_file}")
            return True
            
        except Exception as e:
            print(f"✗ Encryption failed: {e}")
            return False
    
    def decrypt_env(self) -> Optional[Dict[str, str]]:
        """Decrypt and load environment variables"""
        if not HAS_CRYPTO:
            return None
        
        if not self.env_file.exists():
            print(f"Error: {self.env_file} not found")
            return None
        
        try:
            password = getpass.getpass("Enter decryption password: ").encode()
            
            # Read salt from key file or encrypted file
            if self.key_file.exists():
                with open(self.key_file, 'rb') as f:
                    salt = f.read(16)
            else:
                # Try to extract salt from file header (if implemented)
                salt = os.urandom(16)  # Fallback
            
            key = self._derive_key(password, salt)
            f = Fernet(key)
            
            with open(self.env_file, 'rb') as file:
                encrypted = file.read()
            
            decrypted = f.decrypt(encrypted).decode()
            return json.loads(decrypted)
            
        except Exception as e:
            print(f"✗ Decryption failed: {e}")
            return None
    
    def load_to_environment(self) -> bool:
        """Load decrypted variables to environment"""
        env_dict = self.decrypt_env()
        if not env_dict:
            return False
        
        for k, v in env_dict.items():
            os.environ[k] = v
        
        print(f"✓ Loaded {len(env_dict)} secrets to environment")
        return True


class EnvironmentSecrets:
    """Simple environment variable management"""
    
    @staticmethod
    def get_or_prompt(key: str, sensitive: bool = False) -> str:
        """Get from environment or prompt user"""
        value = os.environ.get(key)
        if value:
            return value
        
        if sensitive:
            value = getpass.getpass(f"Enter {key}: ")
        else:
            value = input(f"Enter {key}: ")
        
        if value:
            os.environ[key] = value
        
        return value
    
    @staticmethod
    def export_script() -> str:
        """Generate export script for bash"""
        script = "#!/bin/bash\n"
        script += "# Source this file to load secrets: source load_secrets.sh\n\n"
        
        for key in SecretsManager.KNOWN_KEYS:
            value = SecretsManager.get_secret(key) if HAS_KEYRING else ""
            if value:
                # Escape single quotes in value
                value = value.replace("'", "'\"'\"'")
                script += f"export {key}='{value}'\n"
        
        return script
    
    @staticmethod
    def verify_environment() -> bool:
        """Verify all required secrets are in environment"""
        missing = []
        for key in SecretsManager.KNOWN_KEYS:
            if not os.environ.get(key):
                missing.append(key)
        
        if missing:
            print("Missing environment variables:")
            for key in missing:
                print(f"  - {key}")
            return False
        
        print("✓ All required secrets found in environment")
        return True


def create_github_secrets_script():
    """Create script for setting GitHub secrets"""
    script = """#!/bin/bash
# Script to set GitHub secrets for the repository
# Usage: ./set_github_secrets.sh

REPO="murr2k/thingy91"

echo "Setting GitHub secrets for $REPO"
echo "You'll be prompted for each secret value"
echo

read -s -p "Enter ONOMONDO_API_KEY: " api_key
echo
gh secret set ONOMONDO_API_KEY --repo $REPO --body "$api_key"

read -p "Enter ONOMONDO_IMSI: " imsi
gh secret set ONOMONDO_IMSI --repo $REPO --body "$imsi"

read -p "Enter ONOMONDO_ICCID: " iccid
gh secret set ONOMONDO_ICCID --repo $REPO --body "$iccid"

read -s -p "Enter ONOMONDO_KI: " ki
echo
gh secret set ONOMONDO_KI --repo $REPO --body "$ki"

read -s -p "Enter ONOMONDO_OPC: " opc
echo
gh secret set ONOMONDO_OPC --repo $REPO --body "$opc"

read -p "Enter SOFTSIM_PROFILE_ID: " profile_id
gh secret set SOFTSIM_PROFILE_ID --repo $REPO --body "$profile_id"

echo
echo "✓ GitHub secrets configured"
echo "View at: https://github.com/$REPO/settings/secrets/actions"
"""
    
    with open("set_github_secrets.sh", "w") as f:
        f.write(script)
    
    os.chmod("set_github_secrets.sh", 0o755)
    print("✓ Created set_github_secrets.sh")


def main():
    """CLI for secrets management"""
    parser = argparse.ArgumentParser(
        description="Secure Secrets Manager for Onomondo SoftSIM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s setup              # Interactive setup
  %(prog)s store KEY VALUE    # Store a single secret
  %(prog)s get KEY            # Retrieve a secret
  %(prog)s list               # List all secrets
  %(prog)s encrypt            # Create encrypted file
  %(prog)s decrypt            # Load from encrypted file
  %(prog)s export             # Export as shell script
  %(prog)s github             # Create GitHub secrets script
        """
    )
    
    parser.add_argument('command', choices=[
        'setup', 'store', 'get', 'delete', 'list',
        'encrypt', 'decrypt', 'export', 'verify', 'github'
    ], help='Command to execute')
    
    parser.add_argument('key', nargs='?', help='Secret key')
    parser.add_argument('value', nargs='?', help='Secret value')
    
    parser.add_argument('--file', default='.env.encrypted',
                       help='Encrypted file path (default: .env.encrypted)')
    
    args = parser.parse_args()
    
    # Execute command
    if args.command == 'setup':
        if HAS_KEYRING:
            SecretsManager.interactive_setup()
        else:
            print("Keyring not available. Using encrypted file instead.")
            args.command = 'encrypt'
    
    if args.command == 'store':
        if not args.key or not args.value:
            print("Usage: secrets_manager.py store KEY VALUE")
            sys.exit(1)
        SecretsManager.store_secret(args.key, args.value)
    
    elif args.command == 'get':
        if not args.key:
            print("Usage: secrets_manager.py get KEY")
            sys.exit(1)
        value = SecretsManager.get_secret(args.key)
        if value:
            print(value)
        else:
            print(f"Secret {args.key} not found", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == 'delete':
        if not args.key:
            print("Usage: secrets_manager.py delete KEY")
            sys.exit(1)
        SecretsManager.delete_secret(args.key)
    
    elif args.command == 'list':
        SecretsManager.list_secrets()
    
    elif args.command == 'encrypt':
        env_manager = EncryptedEnvFile(args.file)
        if not env_manager.is_available():
            print("Error: cryptography library not installed")
            sys.exit(1)
        
        print("Enter secrets to encrypt (empty to skip):")
        secrets = {}
        
        for key in SecretsManager.KNOWN_KEYS:
            if "KEY" in key or "KI" in key or "OPC" in key:
                value = getpass.getpass(f"{key}: ")
            else:
                value = input(f"{key}: ")
            
            if value:
                secrets[key] = value
        
        if secrets:
            env_manager.encrypt_env(secrets)
        else:
            print("No secrets provided")
    
    elif args.command == 'decrypt':
        env_manager = EncryptedEnvFile(args.file)
        env_manager.load_to_environment()
    
    elif args.command == 'export':
        script = EnvironmentSecrets.export_script()
        
        output_file = "load_secrets.sh"
        with open(output_file, "w") as f:
            f.write(script)
        
        os.chmod(output_file, 0o600)
        print(f"✓ Export script saved to {output_file}")
        print(f"Usage: source {output_file}")
    
    elif args.command == 'verify':
        EnvironmentSecrets.verify_environment()
    
    elif args.command == 'github':
        create_github_secrets_script()


if __name__ == "__main__":
    main()