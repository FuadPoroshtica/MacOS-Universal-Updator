"""Application settings management."""

import yaml
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
from datetime import datetime


@dataclass
class UpdatePreferences:
    """User preferences for updates."""
    auto_cleanup: bool = True
    notify_on_complete: bool = True
    notify_on_error: bool = True
    skip_on_battery: bool = True
    min_battery_percent: int = 20
    min_disk_space_gb: float = 5.0
    require_confirmation: bool = False
    backup_reminder: bool = True


@dataclass
class EnabledManagers:
    """Which update managers are enabled."""
    macos: bool = True
    homebrew: bool = True
    appstore: bool = True
    pip: bool = False
    npm: bool = False


@dataclass
class UIPreferences:
    """UI-related preferences."""
    theme: str = "dark"  # dark, light, auto
    show_system_info: bool = True
    compact_mode: bool = False
    animation_speed: float = 1.0
    log_lines_visible: int = 20


@dataclass
class Settings:
    """Main application settings."""
    version: str = "2.0.0"
    first_run: bool = True
    last_update: Optional[str] = None
    update_preferences: UpdatePreferences = field(default_factory=UpdatePreferences)
    enabled_managers: EnabledManagers = field(default_factory=EnabledManagers)
    ui_preferences: UIPreferences = field(default_factory=UIPreferences)
    custom_brew_taps: list[str] = field(default_factory=list)
    excluded_packages: list[str] = field(default_factory=list)


def get_config_directory() -> Path:
    """Get the configuration directory path."""
    config_dir = Path.home() / ".macos-updater"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_settings_file() -> Path:
    """Get the settings file path."""
    return get_config_directory() / "settings.yaml"


def load_settings() -> Settings:
    """Load settings from file or create default settings."""
    settings_file = get_settings_file()

    if not settings_file.exists():
        settings = Settings()
        save_settings(settings)
        return settings

    try:
        with open(settings_file, "r") as f:
            data = yaml.safe_load(f) or {}

        # Parse nested dataclasses
        update_prefs_data = data.get("update_preferences", {})
        enabled_managers_data = data.get("enabled_managers", {})
        ui_prefs_data = data.get("ui_preferences", {})

        settings = Settings(
            version=data.get("version", "2.0.0"),
            first_run=data.get("first_run", True),
            last_update=data.get("last_update"),
            update_preferences=UpdatePreferences(**update_prefs_data),
            enabled_managers=EnabledManagers(**enabled_managers_data),
            ui_preferences=UIPreferences(**ui_prefs_data),
            custom_brew_taps=data.get("custom_brew_taps", []),
            excluded_packages=data.get("excluded_packages", [])
        )
        return settings
    except Exception as e:
        # If loading fails, return default settings
        return Settings()


def save_settings(settings: Settings) -> bool:
    """Save settings to file."""
    settings_file = get_settings_file()

    try:
        # Convert to dict for YAML serialization
        data = {
            "version": settings.version,
            "first_run": settings.first_run,
            "last_update": settings.last_update,
            "update_preferences": asdict(settings.update_preferences),
            "enabled_managers": asdict(settings.enabled_managers),
            "ui_preferences": asdict(settings.ui_preferences),
            "custom_brew_taps": settings.custom_brew_taps,
            "excluded_packages": settings.excluded_packages,
        }

        with open(settings_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return True
    except Exception as e:
        return False


def reset_settings() -> Settings:
    """Reset settings to defaults."""
    settings = Settings()
    save_settings(settings)
    return settings


def update_last_run(settings: Settings) -> Settings:
    """Update the last run timestamp."""
    settings.last_update = datetime.now().isoformat()
    settings.first_run = False
    save_settings(settings)
    return settings
