"""macOS notification utilities."""

import subprocess
from enum import Enum
from typing import Optional


class NotificationLevel(Enum):
    """Notification importance levels."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


def send_notification(
    title: str,
    message: str,
    level: NotificationLevel = NotificationLevel.INFO,
    sound: bool = True,
    subtitle: Optional[str] = None
) -> bool:
    """
    Send a macOS notification using osascript.

    Args:
        title: Notification title
        message: Main notification message
        level: Importance level (affects sound)
        sound: Whether to play a sound
        subtitle: Optional subtitle

    Returns:
        True if notification was sent successfully
    """
    # Build the AppleScript command
    script_parts = [f'display notification "{message}"']
    script_parts.append(f'with title "{title}"')

    if subtitle:
        script_parts.append(f'subtitle "{subtitle}"')

    # Choose sound based on level
    if sound:
        sound_map = {
            NotificationLevel.INFO: "default",
            NotificationLevel.SUCCESS: "Glass",
            NotificationLevel.WARNING: "Sosumi",
            NotificationLevel.ERROR: "Basso"
        }
        sound_name = sound_map.get(level, "default")
        script_parts.append(f'sound name "{sound_name}"')

    script = " ".join(script_parts)

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def notify_update_complete(
    total_updates: int,
    successful: int,
    failed: int
) -> bool:
    """Send notification about update completion."""
    if failed == 0:
        title = "Updates Complete"
        message = f"Successfully updated {successful} package(s)"
        level = NotificationLevel.SUCCESS
    else:
        title = "Updates Finished with Errors"
        message = f"{successful} succeeded, {failed} failed out of {total_updates} updates"
        level = NotificationLevel.WARNING

    return send_notification(title, message, level)


def notify_scheduled_update_starting() -> bool:
    """Send notification that scheduled update is starting."""
    return send_notification(
        "Scheduled Update Starting",
        "Your scheduled system update is now beginning",
        NotificationLevel.INFO,
        subtitle="macOS Universal Updater"
    )


def notify_reboot_required() -> bool:
    """Send notification that a reboot is required."""
    return send_notification(
        "Reboot Required",
        "Some updates require a system restart to complete",
        NotificationLevel.WARNING,
        subtitle="Please save your work"
    )


def notify_low_disk_space(free_gb: float) -> bool:
    """Send notification about low disk space."""
    return send_notification(
        "Low Disk Space",
        f"Only {free_gb:.1f} GB free. Updates may fail.",
        NotificationLevel.ERROR,
        subtitle="Please free up disk space"
    )


def notify_low_battery(percent: int) -> bool:
    """Send notification about low battery."""
    return send_notification(
        "Low Battery Warning",
        f"Battery at {percent}%. Please connect to power before updating.",
        NotificationLevel.WARNING
    )
