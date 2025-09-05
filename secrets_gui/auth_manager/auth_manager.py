#!/usr/bin/env python3
"""
System-wide Authentication Manager
Manages authentication for all development tools and services.
"""

import os
import sys
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import base64

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import authenticators
from authenticators.github_auth import GitHubAuthenticator
from authenticators.fly_auth import FlyAuthenticator
from authenticators.npm_auth import NPMAuthenticator
from authenticators.docker_auth import DockerAuthenticator
from authenticators.terraform_auth import TerraformAuthenticator
from authenticators.cloudflare_auth import CloudflareAuthenticator

# Cryptography imports for loading credentials
try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    from cryptography.fernet import Fernet
except ImportError:
    print("Warning: cryptography not installed. Using fallback.")
    Fernet = None

class AuthManager:
    """Main authentication manager that coordinates all service authenticators."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the auth manager."""
        self.config_path = config_path or str(Path.home() / ".authmanager" / "config.json")
        self.config_dir = Path(self.config_path).parent
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Load configuration
        self.config = self._load_config()
        
        # Load credentials from Secrets Manager
        self.credentials = self._load_credentials()
        
        # Initialize authenticators
        self.authenticators = {}
        self._init_authenticators()
        
        # Status tracking
        self.status = {}
        self.running = False
        self.monitor_thread = None
        
    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.config_dir / "auth_manager.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("AuthManager")
        
    def _load_config(self) -> dict:
        """Load configuration from file."""
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load config: {e}")
        
        # Default configuration
        default_config = {
            "services": {
                "github": {"enabled": True, "auto_refresh": True},
                "flyio": {"enabled": True, "auto_refresh": False},
                "npm": {"enabled": True, "auto_refresh": True},
                "docker": {"enabled": True, "auto_refresh": True},
                "terraform": {"enabled": True, "auto_refresh": True},
                "cloudflare": {"enabled": True, "auto_refresh": True},
            },
            "polling": {
                "interval": 300,  # 5 minutes
                "enabled": True
            },
            "secrets_path": str(Path.home() / "projects" / "thingy91" / "secrets_gui" / "data" / "secrets.json"),
            "master_key_path": str(Path.home() / "projects" / "thingy91" / "secrets_gui" / "data" / ".master_key")
        }
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: dict):
        """Save configuration to file."""
        config_file = Path(self.config_path)
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            config_file.chmod(0o600)  # Secure the file
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def _load_credentials(self) -> dict:
        """Load credentials from encrypted Secrets Manager."""
        secrets_path = Path(self.config["secrets_path"])
        master_key_path = Path(self.config["master_key_path"])
        
        if not secrets_path.exists() or not master_key_path.exists():
            self.logger.warning("Secrets files not found, using empty credentials")
            return {}
        
        try:
            # Load master key
            with open(master_key_path, 'r') as f:
                master_key = f.read().strip()
            
            # Derive encryption key
            if Fernet:
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'stable_salt_v1',
                    iterations=100000,
                    backend=default_backend()
                )
                key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
                fernet = Fernet(key)
            else:
                # Fallback if cryptography not available
                self.logger.warning("Using fallback decryption")
                return {}
            
            # Load and decrypt secrets
            with open(secrets_path, 'r') as f:
                encrypted_data = json.load(f)
            
            credentials = {}
            for service, encrypted_value in encrypted_data.items():
                try:
                    decrypted = fernet.decrypt(encrypted_value.encode())
                    credentials[service] = json.loads(decrypted)
                except Exception as e:
                    self.logger.error(f"Failed to decrypt {service}: {e}")
            
            self.logger.info(f"Loaded credentials for {len(credentials)} services")
            return credentials
            
        except Exception as e:
            self.logger.error(f"Failed to load credentials: {e}")
            return {}
    
    def _init_authenticators(self):
        """Initialize service authenticators."""
        # GitHub
        if self.config["services"].get("github", {}).get("enabled"):
            if "github" in self.credentials:
                self.authenticators["github"] = GitHubAuthenticator(self.credentials["github"])
                self.logger.info("Initialized GitHub authenticator")
        
        # Fly.io
        if self.config["services"].get("flyio", {}).get("enabled"):
            if "flyio" in self.credentials:
                self.authenticators["flyio"] = FlyAuthenticator(self.credentials["flyio"])
                self.logger.info("Initialized Fly.io authenticator")
        
        # NPM
        if self.config["services"].get("npm", {}).get("enabled"):
            if "npm" in self.credentials:
                self.authenticators["npm"] = NPMAuthenticator(self.credentials["npm"])
                self.logger.info("Initialized NPM authenticator")
        
        # Docker
        if self.config["services"].get("docker", {}).get("enabled"):
            if "docker" in self.credentials:
                self.authenticators["docker"] = DockerAuthenticator(self.credentials["docker"])
                self.logger.info("Initialized Docker authenticator")
        
        # Terraform
        if self.config["services"].get("terraform", {}).get("enabled"):
            if "terraform" in self.credentials:
                self.authenticators["terraform"] = TerraformAuthenticator(self.credentials["terraform"])
                self.logger.info("Initialized Terraform authenticator")
        
        # Cloudflare
        if self.config["services"].get("cloudflare", {}).get("enabled"):
            if "cloudflare" in self.credentials:
                self.authenticators["cloudflare"] = CloudflareAuthenticator(self.credentials["cloudflare"])
                self.logger.info("Initialized Cloudflare authenticator")
        
    def authenticate_all(self) -> Dict[str, bool]:
        """Authenticate all enabled services."""
        results = {}
        
        self.logger.info("=" * 60)
        self.logger.info("Starting system-wide authentication")
        self.logger.info("=" * 60)
        
        for name, auth in self.authenticators.items():
            self.logger.info(f"\nAuthenticating {name}...")
            try:
                success = auth.authenticate()
                results[name] = success
                
                if success:
                    self.logger.info(f"✅ {name} authenticated successfully")
                else:
                    self.logger.error(f"❌ {name} authentication failed")
                    
            except Exception as e:
                self.logger.error(f"❌ {name} authentication error: {e}")
                results[name] = False
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("Authentication Summary:")
        for name, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            self.logger.info(f"  {name}: {status}")
        self.logger.info("=" * 60)
        
        return results
    
    def verify_all(self) -> Dict[str, bool]:
        """Verify authentication status for all services."""
        results = {}
        
        for name, auth in self.authenticators.items():
            try:
                authenticated = auth.verify_auth()
                results[name] = authenticated
                self.status[name] = auth.get_status()
            except Exception as e:
                self.logger.error(f"Error verifying {name}: {e}")
                results[name] = False
                self.status[name] = {"authenticated": False, "error": str(e)}
        
        return results
    
    def refresh_if_needed(self):
        """Refresh authentication for services that need it."""
        refreshed = []
        
        for name, auth in self.authenticators.items():
            if self.config["services"].get(name, {}).get("auto_refresh"):
                try:
                    if auth.refresh_if_needed():
                        refreshed.append(name)
                        self.logger.info(f"Refreshed authentication for {name}")
                except Exception as e:
                    self.logger.error(f"Failed to refresh {name}: {e}")
        
        return refreshed
    
    def start_monitoring(self):
        """Start the background monitoring thread."""
        if self.running:
            self.logger.warning("Monitoring already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Started authentication monitoring")
    
    def stop_monitoring(self):
        """Stop the background monitoring thread."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Stopped authentication monitoring")
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        interval = self.config["polling"]["interval"]
        
        while self.running:
            try:
                # Verify all authentications
                self.verify_all()
                
                # Refresh if needed
                self.refresh_if_needed()
                
                # Log status
                authenticated = sum(1 for s in self.status.values() 
                                  if s.get("authenticated"))
                total = len(self.status)
                self.logger.debug(f"Auth status: {authenticated}/{total} authenticated")
                
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
            
            # Sleep for interval
            time.sleep(interval)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of all services."""
        # Trigger verification to populate status
        self.verify_all()
        
        return {
            "services": self.status,
            "summary": {
                "total": len(self.status),
                "authenticated": sum(1 for s in self.status.values() 
                                   if s.get("authenticated")),
                "failed": sum(1 for s in self.status.values() 
                             if not s.get("authenticated"))
            },
            "last_check": datetime.now().isoformat()
        }
    
    def logout_all(self):
        """Logout from all services."""
        for name, auth in self.authenticators.items():
            try:
                auth.logout()
                self.logger.info(f"Logged out from {name}")
            except Exception as e:
                self.logger.error(f"Failed to logout from {name}: {e}")


def main():
    """Main entry point for testing."""
    manager = AuthManager()
    
    # Authenticate all services
    results = manager.authenticate_all()
    
    # Verify status
    status = manager.verify_all()
    
    # Print status
    print("\nCurrent Authentication Status:")
    for service, authenticated in status.items():
        status_emoji = "✅" if authenticated else "❌"
        print(f"  {status_emoji} {service}: {'Authenticated' if authenticated else 'Not authenticated'}")
    
    # Start monitoring
    manager.start_monitoring()
    
    print("\n✅ Auth Manager initialized and monitoring started")
    print("Authentication is now available system-wide for all projects!")


if __name__ == "__main__":
    main()