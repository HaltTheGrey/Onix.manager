"""
Authentication and user management.
Handles user login, permissions, and session management.
"""

import os
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..utils import get_logger


@dataclass
class User:
    """Represents a user in the system."""
    username: str
    display_name: str
    email: str
    permissions: List[str]
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True


class AuthenticationManager:
    """
    Manages user authentication and permissions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Current session
        self.current_user: Optional[User] = None
        self.session_expires_at: Optional[datetime] = None
        
        # Built-in users for development
        self.users = {
            "admin": User(
                username="admin",
                display_name="Administrator",
                email="admin@company.com",
                permissions=["read", "write", "admin"],
                created_at=datetime.now()
            ),
            "technician": User(
                username="technician",
                display_name="Technician",
                email="tech@company.com", 
                permissions=["read", "write"],
                created_at=datetime.now()
            ),
            "viewer": User(
                username="viewer",
                display_name="Viewer",
                email="viewer@company.com",
                permissions=["read"],
                created_at=datetime.now()
            )
        }
        
        self.logger.info("Authentication manager initialized")
    
    def authenticate_user(self, username: str, password: Optional[str] = None) -> bool:
        """
        Authenticate a user.
        
        Args:
            username: Username to authenticate
            password: Password (optional for development mode)
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Check if developer override is enabled
            if self.config.get('DEVELOPER_OVERRIDE', False):
                return self._authenticate_developer_mode(username)
            
            # Check if company login is required
            if self.config.get('REQUIRE_COMPANY_LOGIN', True):
                return self._authenticate_company_login(username)
            
            # Fallback to simple authentication
            return self._authenticate_simple(username, password)
            
        except Exception as e:
            self.logger.error(f"Authentication error for user {username}: {e}")
            return False
    
    def _authenticate_developer_mode(self, username: str) -> bool:
        """Authenticate in developer mode (bypass all checks)."""
        if username in self.users:
            user = self.users[username]
        else:
            # Create a temporary admin user
            user = User(
                username=username,
                display_name=username.title(),
                email=f"{username}@dev.local",
                permissions=["read", "write", "admin"],
                created_at=datetime.now()
            )
            self.users[username] = user
        
        self._start_session(user)
        self.logger.info(f"Developer mode authentication successful for {username}")
        return True
    
    def _authenticate_company_login(self, username: str) -> bool:
        """Authenticate using company login (AWS CLI/ada)."""
        try:
            # Check if AWS credentials are available
            aws_profile = self.config.get('AWS_PROFILE', 'default')
            
            # In a real implementation, this would:
            # 1. Check AWS CLI credentials
            # 2. Validate with company identity provider
            # 3. Use ada for authentication
            
            # For now, simulate company authentication
            if self._check_aws_credentials():
                if username in self.users:
                    user = self.users[username]
                else:
                    # Create user from company directory
                    user = User(
                        username=username,
                        display_name=username.title(),
                        email=f"{username}@company.com",
                        permissions=["read", "write"],                        created_at=datetime.now()
                    )
                    self.users[username] = user
                
                self._start_session(user)
                self.logger.info(f"Company authentication successful for {username}")
                return True
            else:
                self.logger.warning(f"AWS credentials not available for {username}")
                return False
                
        except Exception as e:
            self.logger.error(f"Company authentication error: {e}")
            return False
    
    def _authenticate_simple(self, username: str, password: Optional[str]) -> bool:
        """Simple username/password authentication."""
        if not username or not password:
            return False
        
        # Check built-in users
        if username in self.users:
            # In a real implementation, you'd check password hash
            # For now, accept any password for built-in users
            user = self.users[username]
            self._start_session(user)
            self.logger.info(f"Simple authentication successful for {username}")
            return True
        
        return False
    
    def _check_aws_credentials(self) -> bool:
        """Check if AWS credentials are available."""
        try:
            # Check environment variables
            if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
                return True
            
            # Check AWS config files
            aws_config_path = os.path.expanduser('~/.aws/credentials')
            if os.path.exists(aws_config_path):
                return True
            
            return False
            
        except Exception:
            return False
    
    def _start_session(self, user: User):
        """Start a user session."""
        self.current_user = user
        self.current_user.last_login = datetime.now()
          # Set session expiration
        timeout_seconds = self.config.get('SESSION_TIMEOUT', 3600)
        self.session_expires_at = datetime.now() + timedelta(seconds=timeout_seconds)
        
        self.logger.info(f"Session started for user {user.username}")
    
    def logout(self):
        """Logout the current user."""
        if self.current_user:
            self.logger.info(f"User {self.current_user.username} logged out")
            self.current_user = None
            self.session_expires_at = None
    
    def is_authenticated(self) -> bool:
        """Check if a user is currently authenticated."""
        if not self.current_user or not self.session_expires_at:
            return False
        
        # Check session expiration
        if datetime.now() > self.session_expires_at:
            self.logger.info("Session expired")
            self.logout()
            return False
        
        return True
    
    def has_permission(self, permission: str) -> bool:
        """Check if current user has a specific permission."""
        if not self.is_authenticated() or not self.current_user:
            return False
        
        return permission in self.current_user.permissions
    
    def get_current_user(self) -> Optional[User]:
        """Get the current authenticated user."""
        if self.is_authenticated():
            return self.current_user
        return None
    
    def extend_session(self):
        """Extend the current session."""
        if self.is_authenticated():
            timeout_seconds = self.config.get('SESSION_TIMEOUT', 3600)
            self.session_expires_at = datetime.now() + timedelta(seconds=timeout_seconds)
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information."""
        if not self.is_authenticated() or not self.current_user:
            return {}
        
        user = self.current_user
        return {
            'username': user.username,
            'display_name': user.display_name,
            'email': user.email,
            'permissions': user.permissions,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'session_expires_at': self.session_expires_at.isoformat() if self.session_expires_at else None
        }


def create_default_auth_manager(config: Dict[str, Any]) -> AuthenticationManager:
    """Create and configure the default authentication manager."""
    auth_manager = AuthenticationManager(config)
    
    # Auto-login in development mode
    if config.get('DEVELOPER_OVERRIDE', False):
        auth_manager.authenticate_user("admin")
    
    return auth_manager
