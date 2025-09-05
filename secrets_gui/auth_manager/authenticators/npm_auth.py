#!/usr/bin/env python3
"""
NPM Registry authenticator for system-wide authentication.
"""

import os
from pathlib import Path
from typing import Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_authenticator import BaseAuthenticator

class NPMAuthenticator(BaseAuthenticator):
    """NPM Registry authenticator."""
    
    def __init__(self, credentials: dict):
        super().__init__("npm", credentials)
        self.npmrc_path = Path.home() / ".npmrc"
        self.required_keys = ["NPM_REGISTRY_TOKEN", "NPM_AUTH_TOKEN"]
        
    def authenticate(self) -> bool:
        """Authenticate with NPM registry using token."""
        # Use registry token or auth token
        token = (self.credentials.get("NPM_REGISTRY_TOKEN") or 
                self.credentials.get("NPM_AUTH_TOKEN"))
        
        if not token:
            self.logger.error("No NPM token found in credentials")
            self.update_status("no_credentials")
            return False
        
        self.logger.info("Configuring NPM authentication...")
        
        # Set the auth token for npm registry
        success, stdout, stderr = self.run_command(
            ["npm", "config", "set", 
             "//registry.npmjs.org/:_authToken", token],
            timeout=10
        )
        
        if not success:
            self.logger.error(f"Failed to set NPM token: {stderr}")
            self.update_status("failed")
            return False
        
        # Verify the configuration
        success, stdout, stderr = self.run_command(
            ["npm", "whoami"],
            timeout=10
        )
        
        if success:
            username = stdout.strip()
            self.update_status("authenticated")
            self.logger.info(f"✅ NPM authenticated as: {username}")
            
            # Also set environment variable for other tools
            self._update_shell_profile("NPM_TOKEN", token)
            
            # Ensure .npmrc has correct permissions
            if self.npmrc_path.exists():
                self.npmrc_path.chmod(0o600)
            
            return True
        else:
            # Some registries don't support whoami, check config instead
            success, stdout, stderr = self.run_command(
                ["npm", "config", "get", "//registry.npmjs.org/:_authToken"],
                timeout=10
            )
            
            if success and token in stdout:
                self.update_status("authenticated")
                self.logger.info("✅ NPM token configured successfully")
                self._update_shell_profile("NPM_TOKEN", token)
                return True
            else:
                self.logger.error(f"NPM authentication failed: {stderr}")
                self.update_status("failed")
                return False
    
    def verify_auth(self) -> bool:
        """Verify NPM authentication status."""
        # Try npm whoami first
        success, stdout, stderr = self.run_command(
            ["npm", "whoami"],
            timeout=10
        )
        
        if success:
            self.update_status("authenticated")
            return True
        
        # Check if token is configured
        success, stdout, stderr = self.run_command(
            ["npm", "config", "get", "//registry.npmjs.org/:_authToken"],
            timeout=10
        )
        
        if success and stdout.strip() and stdout.strip() != "undefined":
            self.update_status("authenticated")
            return True
        else:
            self.update_status("not_authenticated")
            return False
    
    def logout(self) -> bool:
        """Logout from NPM registry."""
        # Remove auth token
        success, _, _ = self.run_command(
            ["npm", "config", "delete", "//registry.npmjs.org/:_authToken"],
            timeout=10
        )
        
        # Remove from shell profiles
        self._remove_from_shell_profile("NPM_TOKEN")
        
        if success:
            self.update_status("logged_out")
            self.logger.info("Logged out from NPM")
        
        return success
    
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
    
    def configure_registry(self, registry_url: str = "https://registry.npmjs.org/"):
        """Configure NPM to use a specific registry."""
        success, _, _ = self.run_command(
            ["npm", "config", "set", "registry", registry_url],
            timeout=10
        )
        
        if success:
            self.logger.info(f"Configured NPM registry: {registry_url}")
        
        return success