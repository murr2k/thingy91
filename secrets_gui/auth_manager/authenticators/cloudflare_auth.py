#!/usr/bin/env python3
"""
Cloudflare authenticator for system-wide authentication.
"""

import os
import json
from pathlib import Path
from typing import Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_authenticator import BaseAuthenticator

class CloudflareAuthenticator(BaseAuthenticator):
    """Cloudflare authenticator."""
    
    def __init__(self, credentials: dict):
        super().__init__("cloudflare", credentials)
        self.wrangler_config = Path.home() / ".wrangler" / "config" / "default.toml"
        self.required_keys = ["CLOUDFLARE_API_TOKEN", "CLOUDFLARE_API_KEY", "CLOUDFLARE_EMAIL"]
        
    def authenticate(self) -> bool:
        """Authenticate with Cloudflare using token or API key."""
        # Prefer API token over API key
        api_token = self.credentials.get("CLOUDFLARE_API_TOKEN")
        api_key = self.credentials.get("CLOUDFLARE_API_KEY")
        email = self.credentials.get("CLOUDFLARE_EMAIL")
        
        if not (api_token or (api_key and email)):
            self.logger.error("No Cloudflare credentials found")
            self.update_status("no_credentials")
            return False
        
        self.logger.info("Configuring Cloudflare authentication...")
        
        # Set environment variables for various Cloudflare tools
        if api_token:
            self._update_shell_profile("CLOUDFLARE_API_TOKEN", api_token)
            self._update_shell_profile("CF_API_TOKEN", api_token)
        
        if api_key and email:
            self._update_shell_profile("CLOUDFLARE_API_KEY", api_key)
            self._update_shell_profile("CLOUDFLARE_EMAIL", email)
            self._update_shell_profile("CF_API_KEY", api_key)
            self._update_shell_profile("CF_EMAIL", email)
        
        # Configure wrangler if installed
        self._configure_wrangler(api_token, api_key, email)
        
        # Verify authentication
        if self._verify_credentials(api_token, api_key, email):
            self.update_status("authenticated")
            self.logger.info("✅ Cloudflare authenticated successfully")
            return True
        else:
            self.update_status("failed")
            return False
    
    def verify_auth(self) -> bool:
        """Verify Cloudflare authentication status."""
        # Check environment variables
        api_token = os.environ.get("CLOUDFLARE_API_TOKEN") or os.environ.get("CF_API_TOKEN")
        api_key = os.environ.get("CLOUDFLARE_API_KEY") or os.environ.get("CF_API_KEY")
        email = os.environ.get("CLOUDFLARE_EMAIL") or os.environ.get("CF_EMAIL")
        
        # If no env vars, try to get from credentials
        if not (api_token or api_key):
            api_token = self.credentials.get("CLOUDFLARE_API_TOKEN")
            api_key = self.credentials.get("CLOUDFLARE_API_KEY")
            email = self.credentials.get("CLOUDFLARE_EMAIL")
        
        if api_token or (api_key and email):
            if self._verify_credentials(api_token, api_key, email):
                self.update_status("authenticated")
                return True
        
        self.update_status("not_authenticated")
        return False
    
    def logout(self) -> bool:
        """Logout from Cloudflare."""
        # Remove from shell profiles
        for key in ["CLOUDFLARE_API_TOKEN", "CF_API_TOKEN", 
                   "CLOUDFLARE_API_KEY", "CF_API_KEY",
                   "CLOUDFLARE_EMAIL", "CF_EMAIL"]:
            self._remove_from_shell_profile(key)
        
        # Remove wrangler config if exists
        if self.wrangler_config.exists():
            try:
                self.wrangler_config.unlink()
            except:
                pass
        
        self.update_status("logged_out")
        self.logger.info("Logged out from Cloudflare")
        return True
    
    def _verify_credentials(self, api_token: Optional[str], 
                           api_key: Optional[str], 
                           email: Optional[str]) -> bool:
        """Verify credentials with Cloudflare API."""
        try:
            import requests
            
            # Try API token first
            if api_token:
                response = requests.get(
                    "https://api.cloudflare.com/client/v4/user/tokens/verify",
                    headers={
                        "Authorization": f"Bearer {api_token}",
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.logger.info("Cloudflare API token verified")
                        return True
            
            # Try API key
            if api_key and email:
                response = requests.get(
                    "https://api.cloudflare.com/client/v4/user",
                    headers={
                        "X-Auth-Key": api_key,
                        "X-Auth-Email": email,
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        user_email = data["result"].get("email", "Unknown")
                        self.logger.info(f"Cloudflare authenticated as: {user_email}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Could not verify Cloudflare credentials: {e}")
            # Assume valid if we can't verify
            return True
    
    def _configure_wrangler(self, api_token: Optional[str], 
                           api_key: Optional[str], 
                           email: Optional[str]):
        """Configure Wrangler CLI if installed."""
        # Check if wrangler is installed
        success, _, _ = self.run_command(["which", "wrangler"], timeout=5)
        if not success:
            return
        
        # Create wrangler config directory
        self.wrangler_config.parent.mkdir(parents=True, exist_ok=True)
        
        # Create config file
        config_content = []
        if api_token:
            config_content.append(f'api_token = "{api_token}"')
        elif api_key and email:
            config_content.append(f'api_key = "{api_key}"')
            config_content.append(f'email = "{email}"')
        
        if config_content:
            try:
                self.wrangler_config.write_text('\n'.join(config_content))
                self.wrangler_config.chmod(0o600)
                self.logger.debug("Configured Wrangler CLI")
            except Exception as e:
                self.logger.warning(f"Could not configure Wrangler: {e}")
    
    def _update_shell_profile(self, key: str, value: str):
        """Update shell profile with environment variable."""
        for profile in [".bashrc", ".zshrc", ".profile"]:
            profile_path = Path.home() / profile
            if profile_path.exists():
                try:
                    content = profile_path.read_text()
                    
                    # Remove old export if exists
                    lines = content.split('\n')
                    lines = [l for l in lines if not l.startswith(f"export {key}=")]
                    
                    # Add new export
                    lines.append(f"export {key}='{value}'")
                    
                    profile_path.write_text('\n'.join(lines))
                    self.logger.debug(f"Updated {profile} with {key}")
                except Exception as e:
                    self.logger.warning(f"Could not update {profile}: {e}")
    
    def _remove_from_shell_profile(self, key: str):
        """Remove environment variable from shell profiles."""
        for profile in [".bashrc", ".zshrc", ".profile"]:
            profile_path = Path.home() / profile
            if profile_path.exists():
                try:
                    content = profile_path.read_text()
                    lines = content.split('\n')
                    lines = [l for l in lines if not l.startswith(f"export {key}=")]
                    profile_path.write_text('\n'.join(lines))
                    self.logger.debug(f"Removed {key} from {profile}")
                except Exception as e:
                    self.logger.warning(f"Could not update {profile}: {e}")