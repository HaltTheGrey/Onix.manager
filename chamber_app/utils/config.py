"""
Configuration management utilities.
Handles loading and parsing of environment variables and configuration files.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


def load_config(env_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from environment variables and .env file.
    
    Args:
        env_file: Optional path to .env file. Defaults to .env in project root.
        
    Returns:
        Dictionary containing configuration values.
    """
    # Determine project root
    project_root = Path(__file__).parent.parent.parent
    
    # Load .env file
    if env_file is None:
        env_file_path = project_root / ".env"
    else:
        env_file_path = Path(env_file)
    
    if env_file_path.exists():
        load_dotenv(env_file_path)
        logger.info(f"Loaded configuration from {env_file_path}")
    else:
        logger.warning(f"No .env file found at {env_file_path}, using environment variables only")
    
    # Build configuration dictionary
    config = {
        # Application Settings
        'APP_NAME': os.getenv('APP_NAME', 'Chamber Management System'),
        'APP_VERSION': os.getenv('APP_VERSION', '1.0.0'),
        'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true',
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        
        # Database Configuration
        'DATABASE_PATH': os.getenv('DATABASE_PATH', 'data/chambers.db'),
        'BACKUP_INTERVAL': int(os.getenv('BACKUP_INTERVAL', '3600')),
        
        # Grafana/Atlas SDK Configuration
        'GRAFANA_URL': os.getenv('GRAFANA_URL', ''),
        'GRAFANA_API_KEY': os.getenv('GRAFANA_API_KEY', ''),
        'ATLAS_SDK_ENDPOINT': os.getenv('ATLAS_SDK_ENDPOINT', ''),
        'REQUIRE_COMPANY_LOGIN': os.getenv('REQUIRE_COMPANY_LOGIN', 'true').lower() == 'true',
        'DEVELOPER_OVERRIDE': os.getenv('DEVELOPER_OVERRIDE', 'false').lower() == 'true',
        
        # AWS Configuration
        'AWS_PROFILE': os.getenv('AWS_PROFILE', 'default'),
        'AWS_REGION': os.getenv('AWS_REGION', 'us-east-1'),
        
        # Network Configuration
        'ETHERNET_TIMEOUT': int(os.getenv('ETHERNET_TIMEOUT', '30')),
        'SERIAL_TIMEOUT': int(os.getenv('SERIAL_TIMEOUT', '5')),
        'SOCKET_PORT': int(os.getenv('SOCKET_PORT', '8765')),
        'MULTICAST_GROUP': os.getenv('MULTICAST_GROUP', '224.1.1.1'),
        
        # UI Configuration
        'UI_THEME': os.getenv('UI_THEME', 'dark'),
        'WINDOW_WIDTH': int(os.getenv('WINDOW_WIDTH', '1400')),
        'WINDOW_HEIGHT': int(os.getenv('WINDOW_HEIGHT', '900')),
        'AUTO_REFRESH_INTERVAL': int(os.getenv('AUTO_REFRESH_INTERVAL', '5')),
        
        # Chamber Defaults
        'DEFAULT_CHAMBER_TYPES': os.getenv('DEFAULT_CHAMBER_TYPES', 'TVAC,HASS,THERMAL').split(','),
        'MAX_CHAMBERS_PER_TYPE': int(os.getenv('MAX_CHAMBERS_PER_TYPE', '10')),
        'TELEMETRY_RETENTION_DAYS': int(os.getenv('TELEMETRY_RETENTION_DAYS', '90')),
        
        # Security
        'SESSION_TIMEOUT': int(os.getenv('SESSION_TIMEOUT', '3600')),
        'ENCRYPTION_KEY': os.getenv('ENCRYPTION_KEY', ''),
        'ENABLE_AUDIT_LOG': os.getenv('ENABLE_AUDIT_LOG', 'true').lower() == 'true',
        
        # Paths
        'PROJECT_ROOT': str(project_root),
        'DATA_DIR': str(project_root / 'data'),
        'LOGS_DIR': str(project_root / 'logs'),
    }
    
    # Create necessary directories
    for dir_key in ['DATA_DIR', 'LOGS_DIR']:
        Path(config[dir_key]).mkdir(parents=True, exist_ok=True)
    
    return config


def get_database_path(config: Dict[str, Any]) -> Path:
    """Get the full path to the database file."""
    if Path(config['DATABASE_PATH']).is_absolute():
        return Path(config['DATABASE_PATH'])
    else:
        return Path(config['PROJECT_ROOT']) / config['DATABASE_PATH']


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration values for common issues.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if configuration is valid, False otherwise
    """
    required_keys = ['APP_NAME', 'DATABASE_PATH']
    
    for key in required_keys:
        if not config.get(key):
            logger.error(f"Required configuration key '{key}' is missing or empty")
            return False
    
    # Validate numeric values
    numeric_keys = ['WINDOW_WIDTH', 'WINDOW_HEIGHT', 'SOCKET_PORT']
    for key in numeric_keys:
        if config.get(key, 0) <= 0:
            logger.error(f"Configuration key '{key}' must be a positive number")
            return False
    
    logger.info("Configuration validation passed")
    return True
