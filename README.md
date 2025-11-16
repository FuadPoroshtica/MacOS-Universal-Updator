# macOS Universal Updater

A beautiful, feature-rich Terminal User Interface (TUI) application for managing all your macOS software updates in one place.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![License](https://img.shields.io/badge/license-MIT-orange)

## Features

### Update Management
- **macOS System Updates** - Native system software updates
- **Homebrew** - Package manager for formulae and casks
- **Mac App Store** - App Store applications via `mas` CLI
- **Python Packages** - Global pip package updates
- **Node.js Packages** - Global npm package updates

### User Interface
- Beautiful, modern TUI built with [Textual](https://textual.textualize.io/)
- Real-time progress tracking with visual progress bars
- Live update logs with syntax highlighting
- System health dashboard with resource monitoring
- Dark and light theme support
- Keyboard shortcuts for quick navigation

### Scheduling
- Automatic scheduled updates via macOS launchd
- Flexible scheduling: daily, weekly, bi-weekly, or monthly
- Preset time options: early morning, morning, afternoon, evening, night
- Custom time configuration
- Skip updates when on battery or when system is busy
- Pre-update notifications

### Safety Features
- Battery level checking (skip if too low)
- Disk space verification
- Skip current update functionality
- Cancel all operations
- Comprehensive error handling
- Update history and logging

### Configuration
- YAML-based settings
- Excluded packages list
- Custom Homebrew taps
- Configurable notifications
- Backup reminders
- Export/import settings

## Screenshots

```
╔════════════════════════════════════════════════════════════╗
║  macOS Universal Updater                           12:34   ║
╠════════════════════════════════════════════════════════════╣
║  Dashboard │ Updates │ Schedule │ Settings │ History       ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  System Dashboard                                          ║
║  Monitor your system health and update status              ║
║                                                            ║
║  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐      ║
║  │ 🍎 macOS    │  │ 💻 Hostname  │  │ ⏱️ Uptime   │      ║
║  │ 14.2.1      │  │ MacBook-Pro  │  │ 5d 12h      │      ║
║  └─────────────┘  └──────────────┘  └─────────────┘      ║
║                                                            ║
║  ┌─ Available Tools ─┐  ┌─ System Health ──────────┐     ║
║  │ ✓ Homebrew        │  │ CPU:    [████░░░░] 45%  │     ║
║  │ ✓ mas             │  │ Memory: [██████░░] 72%  │     ║
║  │ ✓ pip3            │  │ Disk:   [███████░] 85%  │     ║
║  │ ✓ npm             │  └──────────────────────────┘     ║
║  └────────────────────┘                                    ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/FuadPoroshtica/MacOS-Universal-Updator.git
cd MacOS-Universal-Updator

# Run the installer
./install.sh
```

### Manual Installation

```bash
# Create installation directory
mkdir -p ~/.macos-updater
cp -r src scripts requirements.txt pyproject.toml ~/.macos-updater/

# Create virtual environment
cd ~/.macos-updater
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Create launcher script (add to ~/.local/bin or /usr/local/bin)
# See install.sh for details
```

### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/FuadPoroshtica/MacOS-Universal-Updator.git
cd MacOS-Universal-Updator
./setup_dev.sh

# Activate environment
source venv/bin/activate

# Run the application
python run.py
```

## Usage

### Launch TUI Interface

```bash
# Start the interactive TUI
macos-updater

# Or use these convenient aliases:
updater       # Standard alias
upmm          # Short alias (Update My Mac)
updatemymac   # Full name alias
```

### Command-Line Interface

```bash
# Check for available updates
updater check

# Run updates (non-interactive)
updater update --homebrew --appstore

# Run all updates with verbose output
updater update --macos --homebrew --appstore --pip --npm --verbose

# View system status
updater status

# View schedule configuration
updater schedule

# Open configuration directory
updater config

# Reset settings to defaults
updater reset

# Show version
updater --version

# Show help
updater --help
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `d` | Switch to Dashboard |
| `u` | Switch to Updates |
| `s` | Switch to Schedule |
| `c` | Switch to Settings |
| `h` | Switch to History |
| `r` | Refresh current view |
| `q` | Quit application |
| `?` | Show help |

## Configuration

Configuration files are stored in `~/.macos-updater/`:

- `settings.yaml` - Main application settings
- `schedule.yaml` - Scheduling configuration
- `logs/` - Update logs directory
- `update_history.yaml` - History of update sessions

### Settings Structure

```yaml
version: "2.0.0"
first_run: false
last_update: "2024-01-15T10:30:00"

update_preferences:
  auto_cleanup: true
  notify_on_complete: true
  notify_on_error: true
  skip_on_battery: true
  min_battery_percent: 20
  min_disk_space_gb: 5.0
  backup_reminder: true

enabled_managers:
  macos: true
  homebrew: true
  appstore: true
  pip: false
  npm: false

ui_preferences:
  theme: "dark"
  show_system_info: true
  compact_mode: false
  log_lines_visible: 20

excluded_packages: []
custom_brew_taps: []
```

## Scheduling Automatic Updates

### Setting Up Scheduled Updates

1. Launch the TUI: `macos-updater`
2. Navigate to the **Schedule** tab
3. Enable scheduling with the toggle
4. Choose frequency (daily, weekly, bi-weekly, monthly)
5. Select preferred time (morning, evening, etc.)
6. Configure options (notify before, skip on battery, etc.)
7. Click **Save Configuration**
8. Click **Install Service**

The application uses macOS launchd to run scheduled updates automatically.

### Schedule Options

- **Frequency**: Daily, Weekly, Bi-weekly, Monthly
- **Time Presets**:
  - Early Morning: 6:00 AM
  - Morning: 9:00 AM
  - Afternoon: 2:00 PM
  - Evening: 6:00 PM
  - Night: 10:00 PM
  - Custom: Any hour/minute

### Managing the Service

```bash
# Check if service is loaded
launchctl list | grep macos-updater

# View service status
launchctl list com.macos-updater.scheduled

# Manually load service
launchctl load ~/Library/LaunchAgents/com.macos-updater.scheduled.plist

# Manually unload service
launchctl unload ~/Library/LaunchAgents/com.macos-updater.scheduled.plist
```

## Dependencies

### Required
- Python 3.9 or later
- pip (Python package manager)

### Python Packages (auto-installed)
- textual >= 0.47.0
- rich >= 13.7.0
- pyyaml >= 6.0.1
- psutil >= 5.9.0
- packaging >= 23.0
- click >= 8.1.0
- apscheduler >= 3.10.0

### Optional (for full functionality)
- [Homebrew](https://brew.sh) - Package manager for macOS
- [mas](https://github.com/mas-cli/mas) - Mac App Store CLI (`brew install mas`)
- npm/Node.js - For Node.js package updates

## Architecture

```
MacOS-Universal-Updator/
├── src/
│   └── updater/
│       ├── __init__.py          # Package initialization
│       ├── app.py               # Main TUI application
│       ├── cli.py               # Command-line interface
│       ├── managers/            # Update managers
│       │   ├── base.py          # Base manager class
│       │   ├── homebrew.py      # Homebrew updates
│       │   ├── macos.py         # macOS system updates
│       │   ├── appstore.py      # App Store updates
│       │   ├── pip.py           # Python package updates
│       │   └── npm.py           # Node.js package updates
│       ├── ui/                  # TUI screens
│       │   ├── dashboard.py     # System dashboard
│       │   ├── updates.py       # Update management
│       │   ├── schedule.py      # Scheduling config
│       │   ├── settings.py      # Settings management
│       │   └── history.py       # Update history
│       ├── config/              # Configuration
│       │   ├── settings.py      # Settings management
│       │   └── schedule.py      # Schedule configuration
│       └── utils/               # Utilities
│           ├── system.py        # System information
│           ├── notifications.py # macOS notifications
│           └── logging.py       # Logging utilities
├── scripts/
│   └── run_scheduled.py         # Scheduled update runner
├── install.sh                   # Installation script
├── uninstall.sh                 # Uninstallation script
├── setup_dev.sh                 # Development setup
├── run.py                       # Quick launcher
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project configuration
└── README.md                    # This file
```

## Troubleshooting

### Common Issues

**Application won't start**
```bash
# Check Python version
python3 --version  # Should be 3.9+

# Reinstall dependencies
source ~/.macos-updater/venv/bin/activate
pip install -r requirements.txt
```

**Homebrew updates fail**
```bash
# Check if Homebrew is installed
brew --version

# Fix Homebrew issues
brew doctor
```

**App Store updates fail**
```bash
# Check if mas is installed
mas version

# Install mas
brew install mas

# Sign in to App Store (required for mas)
mas signin email@example.com
```

**Scheduled updates not running**
```bash
# Check service status
launchctl list | grep macos-updater

# Check logs
tail -f ~/.macos-updater/logs/scheduled_stdout.log
tail -f ~/.macos-updater/logs/scheduled_stderr.log
```

**Permission issues**
```bash
# System updates may require sudo
sudo softwareupdate -ia

# Grant terminal full disk access in System Preferences
```

## Uninstallation

```bash
# Run uninstaller
./uninstall.sh

# Or manually:
# 1. Remove launchd service
launchctl unload ~/Library/LaunchAgents/com.macos-updater.scheduled.plist
rm ~/Library/LaunchAgents/com.macos-updater.scheduled.plist

# 2. Remove application
rm -rf ~/.macos-updater

# 3. Remove launcher scripts
rm ~/.local/bin/macos-updater
rm ~/.local/bin/updater
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development

```bash
# Setup development environment
./setup_dev.sh
source venv/bin/activate

# Run tests
pytest

# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Textual](https://textual.textualize.io/) - Modern TUI framework
- Uses [Rich](https://github.com/Textualize/rich) - Beautiful terminal formatting
- Inspired by the need for a unified macOS update experience

## Roadmap

- [ ] Add support for Ruby Gems
- [ ] Add support for Rust Cargo
- [ ] Implement update rollback functionality
- [ ] Add network usage monitoring during updates
- [ ] Create native macOS menu bar app
- [ ] Add update size estimation
- [ ] Implement selective package updates
- [ ] Add support for multiple Homebrew environments
- [ ] Create web dashboard for remote monitoring

## Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Search existing [Issues](https://github.com/FuadPoroshtica/MacOS-Universal-Updator/issues)
3. Open a new issue with detailed information

---

**Made with ❤️ for macOS users who want to keep their systems up to date effortlessly.**
