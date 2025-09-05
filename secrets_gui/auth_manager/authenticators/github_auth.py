#!/usr/bin/env python3
"""
GitHub CLI authenticator for system-wide authentication.
"""

import os
import json
from pathlib import Path
from typing import Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_authenticator import BaseAuthenticator

class GitHubAuthenticator(BaseAuthenticator):
    """GitHub CLI authenticator using gh tool."""
    
    def __init__(self, credentials: dict):
        super().__init__("github", credentials)
        self.gh_config_dir = Path.home() / ".config" / "gh"
        self.required_keys = ["GITHUB_TOKEN", "GITHUB_ADMIN_TOKEN"]
        
    def authenticate(self) -> bool:
        """Authenticate with GitHub CLI using token."""
        # Use admin token if available, otherwise regular token
        token = (self.credentials.get("GITHUB_ADMIN_TOKEN") or 
                self.credentials.get("GITHUB_TOKEN"))
        
        if not token:
            self.logger.error("No GitHub token found in credentials")
            self.update_status("no_credentials")
            return False
        
        self.logger.info("Authenticating with GitHub CLI...")
        
        # First, try to logout to clear any existing auth
        self.run_command(["gh", "auth", "logout", "--hostname", "github.com"], timeout=5)
        
        # Login with token using stdin
        success, stdout, stderr = self.run_command(
            ["gh", "auth", "login", "--hostname", "github.com", "--with-token"],
            env={"GH_TOKEN": token},
            timeout=30
        )
        
        # Alternative: write token to stdin
        if not success:
            import subprocess
            try:
                process = subprocess.Popen(
                    ["gh", "auth", "login", "--hostname", "github.com", "--with-token"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(input=token, timeout=30)
                success = process.returncode == 0
            except Exception as e:
                self.logger.error(f"Failed to authenticate: {e}")
                success = False
        
        if success:
            self.update_status("authenticated")
            self.logger.info("✅ GitHub CLI authenticated successfully")
            
            # Set git credential helper to use gh
            self.run_command(["gh", "auth", "setup-git"])
            
            # Also set environment variable for other tools
            self._update_shell_profile("GITHUB_TOKEN", token)
            
            return True
        else:
            self.logger.error(f"GitHub authentication failed: {stderr}")
            self.update_status("failed")
            return False
    
    def verify_auth(self) -> bool:
        """Verify GitHub CLI authentication status."""
        success, stdout, stderr = self.run_command(
            ["gh", "auth", "status", "--hostname", "github.com"],
            timeout=10
        )
        
        if success and "Logged in to github.com" in stdout:
            # Extract username if possible
            if "Logged in to github.com as" in stdout:
                username = stdout.split("Logged in to github.com as")[1].split()[0]
                self.logger.info(f"GitHub authenticated as: {username}")
            
            self.update_status("authenticated")
            return True
        else:
            self.update_status("not_authenticated")
            return False
    
    def logout(self) -> bool:
        """Logout from GitHub CLI."""
        success, _, _ = self.run_command(
            ["gh", "auth", "logout", "--hostname", "github.com"],
            timeout=10
        )
        
        if success:
            self.update_status("logged_out")
            self.logger.info("Logged out from GitHub")
        
        return success
    
    def _update_shell_profile(self, key: str, value: str):
        """Update shell profile with environment variable."""
        # Update both .bashrc and .zshrc if they exist
        for profile in [".bashrc", ".zshrc"]:
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
    
    def get_authenticated_user(self) -> Optional[str]:
        """Get the currently authenticated GitHub username."""
        success, stdout, _ = self.run_command(
            ["gh", "api", "user", "--jq", ".login"],
            timeout=10
        )
        
        if success:
            return stdout.strip()
        return None