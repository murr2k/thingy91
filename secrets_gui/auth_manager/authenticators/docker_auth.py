#!/usr/bin/env python3
"""
Docker authenticator for system-wide authentication.
"""

import os
import json
from pathlib import Path
from typing import Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_authenticator import BaseAuthenticator

class DockerAuthenticator(BaseAuthenticator):
    """Docker Hub authenticator."""
    
    def __init__(self, credentials: dict):
        super().__init__("docker", credentials)
        self.docker_config_dir = Path.home() / ".docker"
        self.docker_config_file = self.docker_config_dir / "config.json"
        self.required_keys = ["DOCKER_USERNAME", "DOCKER_PASSWORD", "DOCKER_PAT"]
        
    def authenticate(self) -> bool:
        """Authenticate with Docker Hub using credentials."""
        username = self.credentials.get("DOCKER_USERNAME")
        # Use PAT if available, otherwise password
        password = (self.credentials.get("DOCKER_PAT") or 
                   self.credentials.get("DOCKER_PASSWORD"))
        
        if not username or not password:
            self.logger.error("No Docker credentials found")
            self.update_status("no_credentials")
            return False
        
        self.logger.info("Authenticating with Docker Hub...")
        
        # Login using docker CLI
        import subprocess
        try:
            # Use stdin to pass password securely
            process = subprocess.Popen(
                ["docker", "login", "-u", username, "--password-stdin"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=password, timeout=30)
            success = process.returncode == 0
            
            if success:
                self.update_status("authenticated")
                self.logger.info(f"✅ Docker authenticated as: {username}")
                
                # Also set environment variables for Docker tools
                self._update_shell_profile("DOCKER_USERNAME", username)
                if self.credentials.get("DOCKER_PAT"):
                    self._update_shell_profile("DOCKER_PAT", password)
                
                # Ensure config has correct permissions
                if self.docker_config_file.exists():
                    self.docker_config_file.chmod(0o600)
                
                return True
            else:
                self.logger.error(f"Docker authentication failed: {stderr}")
                self.update_status("failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to authenticate: {e}")
            self.update_status("failed")
            return False
    
    def verify_auth(self) -> bool:
        """Verify Docker authentication status."""
        # Check if docker config exists and has auth
        if not self.docker_config_file.exists():
            self.update_status("not_authenticated")
            return False
        
        try:
            with open(self.docker_config_file, 'r') as f:
                config = json.load(f)
            
            # Check for auths section
            if "auths" in config:
                # Check for docker hub or index.docker.io
                docker_hub_auth = (
                    config["auths"].get("https://index.docker.io/v1/") or
                    config["auths"].get("docker.io") or
                    config["auths"].get("index.docker.io")
                )
                
                if docker_hub_auth and docker_hub_auth.get("auth"):
                    self.update_status("authenticated")
                    return True
            
            self.update_status("not_authenticated")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking Docker auth: {e}")
            self.update_status("not_authenticated")
            return False
    
    def logout(self) -> bool:
        """Logout from Docker Hub."""
        success, _, _ = self.run_command(
            ["docker", "logout"],
            timeout=10
        )
        
        # Remove from shell profiles
        self._remove_from_shell_profile("DOCKER_USERNAME")
        self._remove_from_shell_profile("DOCKER_PAT")
        
        if success:
            self.update_status("logged_out")
            self.logger.info("Logged out from Docker Hub")
        
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
    
    def get_logged_in_registries(self) -> list:
        """Get list of registries currently logged into."""
        if not self.docker_config_file.exists():
            return []
        
        try:
            with open(self.docker_config_file, 'r') as f:
                config = json.load(f)
            
            if "auths" in config:
                return list(config["auths"].keys())
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error reading Docker config: {e}")
            return []