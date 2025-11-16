"""System information and checks."""

import subprocess
import platform
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import psutil


@dataclass
class SystemInfo:
    """System information container."""
    os_version: str
    os_build: str
    hostname: str
    cpu_count: int
    memory_total: int
    disk_total: int
    disk_free: int
    battery_percent: Optional[int]
    is_charging: Optional[bool]
    uptime: float


def get_system_info() -> SystemInfo:
    """Gather comprehensive system information."""
    # Get macOS version
    os_version = platform.mac_ver()[0] or "Unknown"

    # Get build number
    try:
        result = subprocess.run(
            ["sw_vers", "-buildVersion"],
            capture_output=True,
            text=True,
            timeout=5
        )
        os_build = result.stdout.strip() if result.returncode == 0 else "Unknown"
    except Exception:
        os_build = "Unknown"

    # Get hostname
    hostname = platform.node()

    # CPU and memory
    cpu_count = psutil.cpu_count()
    memory = psutil.virtual_memory()

    # Disk space
    disk = psutil.disk_usage("/")

    # Battery info
    battery = psutil.sensors_battery()
    battery_percent = int(battery.percent) if battery else None
    is_charging = battery.power_plugged if battery else None

    # Uptime
    uptime = psutil.boot_time()

    return SystemInfo(
        os_version=os_version,
        os_build=os_build,
        hostname=hostname,
        cpu_count=cpu_count,
        memory_total=memory.total,
        disk_total=disk.total,
        disk_free=disk.free,
        battery_percent=battery_percent,
        is_charging=is_charging,
        uptime=uptime
    )


def get_disk_space() -> tuple[int, int]:
    """Get disk space (total, free) in bytes."""
    disk = psutil.disk_usage("/")
    return disk.total, disk.free


def get_battery_status() -> tuple[Optional[int], Optional[bool]]:
    """Get battery percentage and charging status."""
    battery = psutil.sensors_battery()
    if battery:
        return int(battery.percent), battery.power_plugged
    return None, None


def check_prerequisites() -> dict[str, bool]:
    """Check if required tools are installed."""
    tools = {
        "homebrew": "brew",
        "mas": "mas",
        "python3": "python3",
        "pip": "pip3",
        "npm": "npm",
        "softwareupdate": "softwareupdate",
    }

    results = {}
    for name, command in tools.items():
        results[name] = shutil.which(command) is not None

    return results


def check_sudo_available() -> bool:
    """Check if sudo is available without password (for softwareupdate)."""
    try:
        result = subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def get_cpu_usage() -> float:
    """Get current CPU usage percentage."""
    return psutil.cpu_percent(interval=0.1)


def get_memory_usage() -> tuple[int, int, float]:
    """Get memory usage (used, total, percentage)."""
    mem = psutil.virtual_memory()
    return mem.used, mem.total, mem.percent


def format_bytes(bytes_val: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"
