"""Auth package initialization."""

from .auth_manager import AuthenticationManager, User, create_default_auth_manager

__all__ = ['AuthenticationManager', 'User', 'create_default_auth_manager']
