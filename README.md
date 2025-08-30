# Chamber Management Application

A comprehensive Python application for managing and tracking HASS, TVAC, and THERMAL chambers with real-time telemetry, multi-user support, and interactive visualizations.

## Features

- **Real-time Telemetry**: Integration with Grafana (Atlas SDK), Ethernet, and Serial communications
- **Multi-user Collaboration**: Local socket-based sharing and synchronized data
- **Dynamic UI**: Responsive interface with dockable menus and expandable graphs
- **Persistent Storage**: SQLite-based data persistence for telemetry and work requests
- **State Tracking**: Comprehensive chamber state and status management
- **Work Requests**: Integrated ticketing system for chamber maintenance and operations

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   - Copy `.env.example` to `.env`
   - Configure your Grafana/Atlas SDK credentials
   - Set up chamber connection parameters

3. **Run Application**:
   ```bash
   python main.py
   ```

## Architecture

```
chamber_app/
├── core/           # Chamber logic and state tracking
├── ui/             # Display components and user interaction  
├── data/           # Persistent storage and telemetry history
├── sdk/            # Grafana and Atlas SDK integration
├── network/        # Ethernet/Serial communication
├── utils/          # Shared helpers and formatting
├── auth/           # User connection and access control
└── tests/          # Unit and integration tests
```

## Chamber States

- **Available/Empty**: Chamber ready for use
- **Staging**: Preparing chamber for test
- **Setup**: Installing test equipment
- **Test Start**: Beginning test sequence
- **Test Nominal**: Automated test execution
- **Test End**: Test completion
- **Test Teardown**: Removing test equipment

## Status Labels

- **Engineer Needed**: Requires engineering intervention
- **Issues/Halted**: Problems requiring attention
- **Maintenance**: Scheduled or unscheduled maintenance
- **Bake Out**: Chamber conditioning process
- **Chamber Down**: Offline for repairs
- **Setup Issues**: Problems during setup
- **Test Issues**: Problems during testing
- **Currently Being Worked On**: Active work in progress
- **SSL Support Needed**: Security configuration required

## Configuration

The application uses environment variables for configuration. See `.env.example` for all available options.

## Development

Run tests:
```bash
pytest tests/
```

Format code:
```bash
black chamber_app/
```

Lint code:
```bash
flake8 chamber_app/
```

## License

Internal use only - Proprietary application for chamber management operations.
