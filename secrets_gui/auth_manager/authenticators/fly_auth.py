#!/usr/bin/env python3
"""
Fly.io authenticator for system-wide authentication.
Uses Fly's native authentication system instead of environment variables.
"""

import os
import json
from pathlib import Path
from typing import Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_authenticator import BaseAuthenticator

class FlyAuthenticator(BaseAuthenticator):
    """Fly.io authenticator using fly CLI tool's native auth."""
    
    def __init__(self, credentials: dict):
        super().__init__("flyio", credentials)
        self.fly_config_dir = Path.home() / ".fly"
        self.required_keys = ["FLYIO_ORG_TOKEN", "FLYIO_ADMIN_TOKEN"]
        
    def authenticate(self) -> bool:
        """Authenticate with Fly.io using token through CLI."""
        # Get token from credentials
        token = (self.credentials.get("FLYIO_ORG_TOKEN") or 
                self.credentials.get("FLYIO_ADMIN_TOKEN"))
        
        if not token:
            self.logger.error("No Fly.io token found in credentials")
            self.update_status("no_credentials")
            return False
        
        self.logger.info("Setting up Fly.io authentication...")
        
        # IMPORTANT: Remove FLY_API_TOKEN from environment if it exists
        # as it interferes with Fly's native authentication
        self._remove_from_shell_profile("FLY_API_TOKEN")
        if "FLY_API_TOKEN" in os.environ:
            del os.environ["FLY_API_TOKEN"]
        
        # Use fly auth login with token directly
        # The --access-token flag should be used for authentication
        success, stdout, stderr = self.run_command(
            ["fly", "auth", "login", "--access-token", token],
            timeout=15
        )
        
        if not success:
            # If login fails, log the error
            self.logger.error(f"Fly.io login failed: {stderr}")
            self.update_status("failed")
            return False
        
        # Verify authentication worked by checking whoami
        success, stdout, stderr = self.run_command(
            ["fly", "auth", "whoami"],
            timeout=10
        )
        
        if success and "@" in stdout and not stdout.startswith("63f0750b"):
            # Successfully authenticated if we get an email address
            user = stdout.strip()
            self.update_status("authenticated")
            self.logger.info(f"✅ Fly.io authenticated as: {user}")
            return True
        else:
            self.logger.error(f"Fly.io authentication verification failed: {stdout}")
            self.update_status("failed")
            return False
    
    def verify_auth(self) -> bool:
        """Verify Fly.io authentication status."""
        # Make sure FLY_API_TOKEN is not set as it interferes
        env = os.environ.copy()
        if "FLY_API_TOKEN" in env:
            del env["FLY_API_TOKEN"]
        
        # Check authentication using whoami
        success, stdout, stderr = self.run_command(
            ["fly", "auth", "whoami"],
            env=env,
            timeout=10
        )
        
        # Debug logging
        self.logger.info(f"Fly.io verify_auth - success: {success}, stdout: '{stdout.strip()}', stderr: '{stderr.strip()}'")
        
        if success:
            # Check if we get an email address (authenticated)
            # vs a token ID (not authenticated)
            if "@" in stdout and not stdout.startswith("63f0750b"):
                self.update_status("authenticated")
                self.logger.info(f"Fly.io authenticated as: {stdout.strip()}")
                return True
            else:
                self.update_status("not_authenticated")
                self.logger.info(f"Fly.io not authenticated, got: {stdout.strip()}")
                return False
        else:
            self.update_status("not_authenticated")
            self.logger.error(f"Fly.io command failed: {stderr}")
            return False
    
    def logout(self) -> bool:
        """Logout from Fly.io."""
        # Remove FLY_API_TOKEN from shell profiles if it exists
        self._remove_from_shell_profile("FLY_API_TOKEN")
        
        # Clear from current environment
        if "FLY_API_TOKEN" in os.environ:
            del os.environ["FLY_API_TOKEN"]
        
        # Use fly's native logout
        success, _, _ = self.run_command(
            ["fly", "auth", "logout"],
            timeout=10
        )
        
        if success:
            self.update_status("logged_out")
            self.logger.info("Logged out from Fly.io")
            return True
        else:
            self.logger.warning("Fly.io logout may have failed")
            return False
    
    def _remove_from_shell_profile(self, key: str):
        """Remove environment variable from shell profiles."""
        for profile in [".bashrc", ".zshrc", ".profile"]:
            profile_path = Path.home() / profile
            if profile_path.exists():
                try:
                    content = profile_path.read_text()
                    lines = content.split('\n')
                    # Remove any lines that export this variable
                    lines = [l for l in lines if not l.startswith(f"export {key}=")]
                    profile_path.write_text('\n'.join(lines))
                    self.logger.debug(f"Removed {key} from {profile}")
                except Exception as e:
                    self.logger.warning(f"Could not update {profile}: {e}")
    
    def get_apps(self) -> list:
        """Get list of Fly.io apps."""
        # Make sure we're authenticated first
        if not self.verify_auth():
            self.logger.warning("Not authenticated, cannot list apps")
            return []
        
        # Don't use FLY_API_TOKEN environment variable
        env = os.environ.copy()
        if "FLY_API_TOKEN" in env:
            del env["FLY_API_TOKEN"]
        
        success, stdout, _ = self.run_command(
            ["fly", "apps", "list", "--json"],
            env=env,
            timeout=15
        )
        
        if success:
            try:
                return json.loads(stdout)
            except:
                return []
        return []
    
    def get_machines(self, app_name: str) -> list:
        """Get list of machines for a Fly.io app."""
        if not self.verify_auth():
            return []
        
        env = os.environ.copy()
        if "FLY_API_TOKEN" in env:
            del env["FLY_API_TOKEN"]
        
        success, stdout, _ = self.run_command(
            ["fly", "machines", "list", "--app", app_name, "--json"],
            env=env,
            timeout=15
        )
        
        if success:
            try:
                return json.loads(stdout)
            except:
                return []
        return []