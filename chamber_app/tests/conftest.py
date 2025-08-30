"""
Test configuration and utilities.
"""

import os
import tempfile
import pytest
from pathlib import Path

# Test configuration
TEST_CONFIG = {
    'APP_NAME': 'Chamber Management Test',
    'APP_VERSION': '1.0.0-test',
    'DEBUG': True,
    'LOG_LEVEL': 'DEBUG',
    'DATABASE_PATH': ':memory:',  # Use in-memory database for tests
    'BACKUP_INTERVAL': 3600,
    'GRAFANA_URL': 'http://test-grafana.com',
    'GRAFANA_API_KEY': 'test-key',
    'ATLAS_SDK_ENDPOINT': 'http://test-atlas.com',
    'REQUIRE_COMPANY_LOGIN': False,
    'DEVELOPER_OVERRIDE': True,
    'AWS_PROFILE': 'test',
    'AWS_REGION': 'us-east-1',
    'ETHERNET_TIMEOUT': 5,
    'SERIAL_TIMEOUT': 2,
    'SOCKET_PORT': 8766,
    'MULTICAST_GROUP': '224.1.1.2',
    'UI_THEME': 'dark',
    'WINDOW_WIDTH': 800,
    'WINDOW_HEIGHT': 600,
    'AUTO_REFRESH_INTERVAL': 1,
    'DEFAULT_CHAMBER_TYPES': ['TVAC', 'HASS', 'THERMAL'],
    'MAX_CHAMBERS_PER_TYPE': 5,
    'TELEMETRY_RETENTION_DAYS': 1,
    'SESSION_TIMEOUT': 300,
    'ENCRYPTION_KEY': 'test-key',
    'ENABLE_AUDIT_LOG': True,
    'PROJECT_ROOT': str(Path(__file__).parent.parent.parent),
    'DATA_DIR': str(Path(tempfile.gettempdir()) / 'chamber_app_test'),
    'LOGS_DIR': str(Path(tempfile.gettempdir()) / 'chamber_app_test' / 'logs'),
}


@pytest.fixture
def test_config():
    """Provide test configuration."""
    return TEST_CONFIG.copy()


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def setup_test_environment():
    """Setup test environment."""
    # Create test directories
    Path(TEST_CONFIG['DATA_DIR']).mkdir(parents=True, exist_ok=True)
    Path(TEST_CONFIG['LOGS_DIR']).mkdir(parents=True, exist_ok=True)


def cleanup_test_environment():
    """Clean up test environment."""
    import shutil
    try:
        shutil.rmtree(TEST_CONFIG['DATA_DIR'])
    except:
        pass
