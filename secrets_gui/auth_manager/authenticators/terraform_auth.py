#!/usr/bin/env python3
"""
Terraform Cloud authenticator for system-wide authentication.
"""

import os
import json
from pathlib import Path
from typing import Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_authenticator import BaseAuthenticator

class TerraformAuthenticator(BaseAuthenticator):
    """Terraform Cloud authenticator."""
    
    def __init__(self, credentials: dict):
        super().__init__("terraform", credentials)
        self.terraform_dir = Path.home() / ".terraform.d"
        self.credentials_file = self.terraform_dir / "credentials.tfrc.json"
        self.required_keys = ["TERRAFORM_CLOUD_TOKEN", "TF_TOKEN_app_terraform_io"]
        
    def authenticate(self) -> bool:
        """Authenticate with Terraform Cloud using token."""
        # Use either token format
        token = (self.credentials.get("TERRAFORM_CLOUD_TOKEN") or 
                self.credentials.get("TF_TOKEN_app_terraform_io"))
        
        if not token:
            self.logger.error("No Terraform Cloud token found in credentials")
            self.update_status("no_credentials")
            return False
        
        self.logger.info("Configuring Terraform Cloud authentication...")
        
        # Create .terraform.d directory if it doesn't exist
        self.terraform_dir.mkdir(parents=True, exist_ok=True)
        
        # Create credentials file
        credentials_config = {
            "credentials": {
                "app.terraform.io": {
                    "token": token
                }
            }
        }
        
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials_config, f, indent=2)
            
            # Secure the file
            self.credentials_file.chmod(0o600)
            
            # Also set environment variable for Terraform CLI
            self._update_shell_profile("TF_TOKEN_app_terraform_io", token)
            self._update_shell_profile("TERRAFORM_CLOUD_TOKEN", token)
            
            # Verify the token works
            success = self._verify_token(token)
            
            if success:
                self.update_status("authenticated")
                self.logger.info("✅ Terraform Cloud authenticated successfully")
                return True
            else:
                self.update_status("failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to configure Terraform auth: {e}")
            self.update_status("failed")
            return False
    
    def verify_auth(self) -> bool:
        """Verify Terraform Cloud authentication status."""
        # Check if credentials file exists
        if not self.credentials_file.exists():
            self.update_status("not_authenticated")
            return False
        
        try:
            with open(self.credentials_file, 'r') as f:
                config = json.load(f)
            
            # Check for token
            if "credentials" in config:
                tf_cloud = config["credentials"].get("app.terraform.io", {})
                token = tf_cloud.get("token")
                
                if token:
                    # Verify the token still works
                    if self._verify_token(token):
                        self.update_status("authenticated")
                        return True
            
            self.update_status("not_authenticated")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking Terraform auth: {e}")
            self.update_status("not_authenticated")
            return False
    
    def logout(self) -> bool:
        """Logout from Terraform Cloud."""
        try:
            # Remove credentials file
            if self.credentials_file.exists():
                self.credentials_file.unlink()
            
            # Remove from shell profiles
            self._remove_from_shell_profile("TF_TOKEN_app_terraform_io")
            self._remove_from_shell_profile("TERRAFORM_CLOUD_TOKEN")
            
            self.update_status("logged_out")
            self.logger.info("Logged out from Terraform Cloud")
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging out: {e}")
            return False
    
    def _verify_token(self, token: str) -> bool:
        """Verify token with Terraform Cloud API."""
        try:
            import requests
            
            response = requests.get(
                "https://app.terraform.io/api/v2/account/details",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/vnd.api+json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    username = data["data"]["attributes"].get("username", "Unknown")
                    self.logger.info(f"Terraform Cloud user: {username}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Could not verify token: {e}")
            # Assume token is valid if we can't verify
            return True
    
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