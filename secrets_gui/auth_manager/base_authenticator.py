#!/usr/bin/env python3
"""
Base authenticator class for all service authenticators.
"""

import subprocess
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import os

class BaseAuthenticator(ABC):
    """Base class for service authenticators."""
    
    def __init__(self, service_name: str, credentials: Dict[str, str]):
        """
        Initialize authenticator.
        
        Args:
            service_name: Name of the service
            credentials: Dictionary of credentials for the service
        """
        self.service_name = service_name
        self.credentials = credentials
        self.logger = logging.getLogger(f"auth.{service_name}")
        self.last_auth_time = None
        self.auth_status = "unknown"
        self.auth_expiry = None
        
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Perform authentication for the service.
        Returns True if successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def verify_auth(self) -> bool:
        """
        Verify if current authentication is valid.
        Returns True if authenticated, False otherwise.
        """
        pass
    
    @abstractmethod
    def logout(self) -> bool:
        """
        Logout from the service.
        Returns True if successful, False otherwise.
        """
        pass
    
    def refresh_if_needed(self) -> bool:
        """
        Refresh authentication if it's about to expire.
        Returns True if refresh was needed and successful.
        """
        if not self.needs_refresh():
            return False
        
        self.logger.info(f"Refreshing authentication for {self.service_name}")
        return self.authenticate()
    
    def needs_refresh(self) -> bool:
        """
        Check if authentication needs refresh.
        Override this for services with expiring tokens.
        """
        return False
    
    def run_command(self, cmd: list, env: Optional[Dict] = None, 
                   timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Run a shell command with optional environment variables.
        
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            process_env = os.environ.copy()
            if env:
                process_env.update(env)
            
            result = subprocess.run(
                cmd,
                env=process_env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {' '.join(cmd)}")
            return False, "", "Command timed out"
        except Exception as e:
            self.logger.error(f"Command failed: {e}")
            return False, "", str(e)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current authentication status."""
        return {
            "service": self.service_name,
            "authenticated": self.auth_status == "authenticated",
            "status": self.auth_status,
            "last_auth_time": self.last_auth_time.isoformat() if self.last_auth_time else None,
            "expiry": self.auth_expiry.isoformat() if self.auth_expiry else None,
            "needs_refresh": self.needs_refresh()
        }
    
    def update_status(self, status: str, expiry: Optional[datetime] = None):
        """Update authentication status."""
        self.auth_status = status
        self.last_auth_time = datetime.now()
        self.auth_expiry = expiry
        
        self.logger.info(
            f"{self.service_name} auth status: {status}"
            f"{f' (expires: {expiry})' if expiry else ''}"
        )