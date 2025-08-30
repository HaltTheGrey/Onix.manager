# Chamber Management Application - Deployment Guide

## Quick Start

### Option 1: Using the Launcher (Recommended)
1. **Run the launcher**: `python launcher.py`
   - The launcher will check dependencies and environment setup
   - It will create necessary directories and configuration files
   - If dependencies are missing, install them with: `pip install -r requirements.txt`

### Option 2: Direct Launch
1. **Install dependencies**: `pip install -r requirements.txt`
2. **Setup environment**: Copy `.env.example` to `.env` and configure
3. **Run application**: `python main.py`

## Configuration

### Environment Variables (.env file)
The application uses environment variables for configuration. Key settings:

```bash
# Application Settings
APP_NAME=Chamber Management System
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_PATH=data/chambers.db

# Grafana/Atlas SDK (optional)
GRAFANA_URL=https://your-grafana-instance.com
GRAFANA_API_KEY=your_api_key_here
ATLAS_SDK_ENDPOINT=https://atlas-api.example.com

# Authentication
REQUIRE_COMPANY_LOGIN=true
DEVELOPER_OVERRIDE=false

# UI Settings
UI_THEME=dark
WINDOW_WIDTH=1400
WINDOW_HEIGHT=900
AUTO_REFRESH_INTERVAL=5

# Multi-user Support
SOCKET_PORT=8765
```

### Authentication Modes

1. **Developer Mode** (`DEVELOPER_OVERRIDE=true`):
   - Bypasses all authentication
   - Creates admin user automatically
   - Use for development/testing

2. **Company Login** (`REQUIRE_COMPANY_LOGIN=true`):
   - Requires AWS CLI credentials
   - Uses company identity provider
   - Production recommended

3. **Simple Authentication** (fallback):
   - Built-in user accounts
   - Username/password based

## Features Overview

### 📊 Core Features
- **Real-time Chamber Monitoring**: Track TVAC, HASS, and THERMAL chambers
- **State Management**: Define and track chamber states (available, staging, setup, test phases, teardown)
- **Status Tracking**: Monitor issues and complications (maintenance, engineer needed, etc.)
- **Work Request System**: Create, assign, and track maintenance tickets
- **Multi-user Collaboration**: Real-time updates across multiple users

### 🔌 Data Sources
- **Grafana Integration**: Pull telemetry via Atlas SDK
- **Ethernet Connection**: Direct TCP/IP communication with chambers
- **Serial Communication**: RS232/USB serial interfaces
- **Manual Entry**: Manual data input and updates

### 📈 Visualizations
- **Overview Dashboard**: Bar charts of chamber counts and time spent in states
- **Live Telemetry**: Real-time temperature, vacuum, humidity, pressure data
- **Historical Data**: Trend analysis and data retention
- **Interactive Charts**: Zoom, pan, and drill-down capabilities

### 🔐 Security
- **Session Management**: Configurable session timeouts
- **Permission System**: Role-based access control (read, write, admin)
- **Audit Logging**: Track all user actions and changes
- **Data Encryption**: Secure storage of sensitive information

## Directory Structure

```
chamber_app/
├── core/           # Business logic and models
│   ├── application.py      # Main application controller
│   ├── chamber.py          # Chamber model and work requests
│   └── chamber_state.py    # State management and enums
├── ui/             # User interface components
│   ├── main_window.py      # Main application window
│   ├── chamber_card.py     # Individual chamber displays
│   ├── data_overview_panel.py  # Statistics and charts
│   └── work_requests_panel.py  # Work request management
├── data/           # Data persistence
│   └── database.py         # SQLite database operations
├── sdk/            # External integrations
│   └── telemetry_manager.py   # Grafana/Atlas/Ethernet/Serial
├── network/        # Multi-user support
│   └── multi_user.py       # WebSocket server and synchronization
├── auth/           # Authentication
│   └── auth_manager.py     # User management and permissions
├── utils/          # Utilities
│   ├── config.py           # Configuration management
│   └── logging_config.py   # Logging setup
└── tests/          # Test suite
    ├── conftest.py         # Test configuration
    ├── test_chamber_state.py
    └── test_chamber.py
```

## Database Schema

The application uses SQLite with the following main tables:
- `chambers`: Chamber configuration and metadata
- `telemetry`: Time-series telemetry data
- `state_transitions`: History of state/status changes
- `work_requests`: Work tickets and assignments
- `audit_log`: Security and change tracking

## Network Architecture

### Single User Mode
- Local SQLite database
- Direct telemetry connections
- No network dependencies

### Multi-User Mode
- WebSocket server on configurable port
- Real-time data synchronization
- Shared database access
- User session management

## Telemetry Integration

### Grafana/Atlas SDK
```python
# Configure in .env
GRAFANA_URL=https://grafana.company.com
GRAFANA_API_KEY=your_key_here
```

### Ethernet Chambers
- Direct TCP/IP connection
- Custom protocol support
- Configurable timeouts

### Serial Chambers
- RS232/USB serial ports
- Standard baud rates
- Protocol abstraction

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run all tests
pytest chamber_app/tests/

# Run with coverage
pytest --cov=chamber_app chamber_app/tests/
```

### Code Formatting
```bash
# Install formatting tools
pip install black flake8

# Format code
black chamber_app/

# Check style
flake8 chamber_app/
```

### Adding New Features

1. **New Chamber Type**: Add to `ChamberType` enum
2. **New State/Status**: Add to respective enums in `chamber_state.py`
3. **New Telemetry Source**: Implement `TelemetrySource` interface
4. **New UI Panel**: Extend UI components in `ui/` directory

## Troubleshooting

### Common Issues

1. **Dependencies Missing**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Permission Errors**:
   - Check file/directory permissions
   - Run as administrator if needed
   - Verify database path access

3. **Database Errors**:
   - Delete `data/chambers.db` to reset
   - Check disk space
   - Verify SQLite installation

4. **Network Issues**:
   - Check firewall settings
   - Verify port availability
   - Test with single-user mode first

5. **UI Issues**:
   - Update CustomTkinter: `pip install --upgrade customtkinter`
   - Check display scaling settings
   - Try different UI theme

### Logging
Logs are saved to `logs/chamber_app.log` with rotation. Adjust log level in `.env`:
```bash
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Performance
- Database auto-cleanup after 90 days (configurable)
- Telemetry sampling rates can be adjusted
- UI refresh interval is configurable
- Consider disabling debug mode in production

## Support and Maintenance

### Backup Strategy
- Database is automatically backed up during critical operations
- Manual backup: Copy `data/chambers.db`
- Configuration backup: Copy `.env` file

### Updates
- Code updates: Pull new version and restart
- Database migrations: Handled automatically
- Configuration changes: Update `.env` file

### Monitoring
- Check `logs/chamber_app.log` for errors
- Monitor disk space in `data/` directory
- Verify telemetry connections regularly

## Security Considerations

- Use company login in production environments
- Regularly rotate API keys and credentials
- Monitor audit logs for suspicious activity
- Keep dependencies updated for security patches
- Use encrypted connections for remote telemetry

## Advanced Configuration

### Custom Telemetry Protocols
Implement custom telemetry sources by extending the `TelemetrySource` class in `sdk/telemetry_manager.py`.

### Custom UI Themes
Modify theme settings in the UI components or add custom CustomTkinter themes.

### Database Optimization
For high-volume installations, consider:
- Indexing optimization
- Telemetry data partitioning
- External database backends (PostgreSQL, etc.)

### Load Balancing
For enterprise deployments:
- Multiple application instances
- Shared database backend
- Load balancer configuration
- Session affinity settings
