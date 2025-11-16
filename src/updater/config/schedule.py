"""Schedule configuration and management."""

import subprocess
import yaml
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
from typing import Optional
from datetime import datetime, time


class ScheduleTime(Enum):
    """Predefined schedule times."""
    EARLY_MORNING = "early_morning"  # 6:00 AM
    MORNING = "morning"  # 9:00 AM
    AFTERNOON = "afternoon"  # 2:00 PM
    EVENING = "evening"  # 6:00 PM
    NIGHT = "night"  # 10:00 PM
    CUSTOM = "custom"


class ScheduleFrequency(Enum):
    """Update frequency options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


@dataclass
class ScheduleConfig:
    """Schedule configuration."""
    enabled: bool = False
    frequency: str = "weekly"
    time_preset: str = "morning"
    custom_hour: int = 9
    custom_minute: int = 0
    day_of_week: int = 1  # Monday = 1, Sunday = 7
    day_of_month: int = 1
    notify_before: bool = True
    auto_reboot: bool = False
    skip_if_on_battery: bool = True
    skip_if_busy: bool = True  # Skip if CPU usage is high
    last_scheduled_run: Optional[str] = None
    next_scheduled_run: Optional[str] = None


def get_schedule_file() -> Path:
    """Get the schedule configuration file path."""
    config_dir = Path.home() / ".macos-updater"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "schedule.yaml"


def load_schedule() -> ScheduleConfig:
    """Load schedule configuration."""
    schedule_file = get_schedule_file()

    if not schedule_file.exists():
        config = ScheduleConfig()
        save_schedule(config)
        return config

    try:
        with open(schedule_file, "r") as f:
            data = yaml.safe_load(f) or {}
        return ScheduleConfig(**data)
    except Exception:
        return ScheduleConfig()


def save_schedule(config: ScheduleConfig) -> bool:
    """Save schedule configuration."""
    schedule_file = get_schedule_file()

    try:
        with open(schedule_file, "w") as f:
            yaml.dump(asdict(config), f, default_flow_style=False, sort_keys=False)
        return True
    except Exception:
        return False


def get_time_for_preset(preset: ScheduleTime) -> tuple[int, int]:
    """Get hour and minute for a time preset."""
    time_map = {
        ScheduleTime.EARLY_MORNING: (6, 0),
        ScheduleTime.MORNING: (9, 0),
        ScheduleTime.AFTERNOON: (14, 0),
        ScheduleTime.EVENING: (18, 0),
        ScheduleTime.NIGHT: (22, 0),
    }
    return time_map.get(preset, (9, 0))


def get_launchd_plist_path() -> Path:
    """Get the path for the launchd plist file."""
    return Path.home() / "Library" / "LaunchAgents" / "com.macos-updater.scheduled.plist"


def generate_launchd_plist(config: ScheduleConfig) -> str:
    """Generate a launchd plist file content for scheduled updates."""
    # Determine the hour and minute
    if config.time_preset == ScheduleTime.CUSTOM.value:
        hour = config.custom_hour
        minute = config.custom_minute
    else:
        try:
            preset = ScheduleTime(config.time_preset)
            hour, minute = get_time_for_preset(preset)
        except ValueError:
            hour, minute = 9, 0

    # Get the Python executable and script path
    python_path = subprocess.run(
        ["which", "python3"],
        capture_output=True,
        text=True
    ).stdout.strip() or "/usr/bin/python3"

    updater_script = Path.home() / ".macos-updater" / "run_scheduled.py"

    # Build calendar interval based on frequency
    calendar_interval = f"""        <dict>
            <key>Hour</key>
            <integer>{hour}</integer>
            <key>Minute</key>
            <integer>{minute}</integer>"""

    if config.frequency == ScheduleFrequency.WEEKLY.value:
        calendar_interval += f"""
            <key>Weekday</key>
            <integer>{config.day_of_week}</integer>"""
    elif config.frequency == ScheduleFrequency.MONTHLY.value:
        calendar_interval += f"""
            <key>Day</key>
            <integer>{config.day_of_month}</integer>"""
    elif config.frequency == ScheduleFrequency.BIWEEKLY.value:
        # For biweekly, we'll use weekly and check in the script
        calendar_interval += f"""
            <key>Weekday</key>
            <integer>{config.day_of_week}</integer>"""

    calendar_interval += """
        </dict>"""

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.macos-updater.scheduled</string>

    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{updater_script}</string>
    </array>

    <key>StartCalendarInterval</key>
    {calendar_interval}

    <key>StandardOutPath</key>
    <string>{Path.home()}/.macos-updater/logs/scheduled_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>{Path.home()}/.macos-updater/logs/scheduled_stderr.log</string>

    <key>RunAtLoad</key>
    <false/>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
"""
    return plist_content


def install_launchd_service(config: ScheduleConfig) -> tuple[bool, str]:
    """Install the launchd service for scheduled updates."""
    plist_path = get_launchd_plist_path()

    # Ensure LaunchAgents directory exists
    plist_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate and write the plist
    plist_content = generate_launchd_plist(config)

    try:
        with open(plist_path, "w") as f:
            f.write(plist_content)

        # Unload if already loaded
        subprocess.run(
            ["launchctl", "unload", str(plist_path)],
            capture_output=True,
            timeout=10
        )

        # Load the new service
        result = subprocess.run(
            ["launchctl", "load", str(plist_path)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return True, "Service installed successfully"
        else:
            return False, f"Failed to load service: {result.stderr}"

    except Exception as e:
        return False, f"Error installing service: {str(e)}"


def uninstall_launchd_service() -> tuple[bool, str]:
    """Uninstall the launchd service."""
    plist_path = get_launchd_plist_path()

    if not plist_path.exists():
        return True, "Service not installed"

    try:
        # Unload the service
        result = subprocess.run(
            ["launchctl", "unload", str(plist_path)],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Remove the plist file
        plist_path.unlink()

        return True, "Service uninstalled successfully"

    except Exception as e:
        return False, f"Error uninstalling service: {str(e)}"


def is_service_installed() -> bool:
    """Check if the launchd service is installed."""
    plist_path = get_launchd_plist_path()
    return plist_path.exists()


def get_service_status() -> dict:
    """Get the status of the launchd service."""
    if not is_service_installed():
        return {"installed": False, "loaded": False, "status": "Not installed"}

    try:
        result = subprocess.run(
            ["launchctl", "list", "com.macos-updater.scheduled"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return {
                "installed": True,
                "loaded": True,
                "status": "Running",
                "details": result.stdout.strip()
            }
        else:
            return {
                "installed": True,
                "loaded": False,
                "status": "Installed but not loaded"
            }

    except Exception as e:
        return {
            "installed": True,
            "loaded": False,
            "status": f"Error checking status: {str(e)}"
        }
