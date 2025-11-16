#!/usr/bin/env python3
"""
Scheduled update runner for macOS Universal Updater.

This script is executed by launchd for scheduled updates.
It runs in headless mode and logs all output.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add the src directory to the path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from updater.managers import (
    MacOSUpdateManager,
    HomebrewManager,
    AppStoreManager,
    PipManager,
    NpmManager
)
from updater.config.settings import load_settings, update_last_run
from updater.config.schedule import load_schedule, save_schedule
from updater.utils.logging import setup_logger, get_logger
from updater.utils.notifications import (
    notify_scheduled_update_starting,
    notify_update_complete,
    notify_reboot_required,
    notify_low_battery,
    notify_low_disk_space
)
from updater.utils.system import get_battery_status, get_disk_space, get_cpu_usage
from updater.ui.history import save_update_history


def should_skip_update() -> tuple[bool, str]:
    """Check if we should skip this scheduled update."""
    settings = load_settings()
    schedule = load_schedule()

    # Check battery
    if schedule.skip_if_on_battery:
        battery_percent, is_charging = get_battery_status()
        if battery_percent is not None:
            if not is_charging and battery_percent < settings.update_preferences.min_battery_percent:
                notify_low_battery(battery_percent)
                return True, f"Battery too low ({battery_percent}%)"

    # Check disk space
    _, disk_free = get_disk_space()
    disk_free_gb = disk_free / (1024 ** 3)
    if disk_free_gb < settings.update_preferences.min_disk_space_gb:
        notify_low_disk_space(disk_free_gb)
        return True, f"Low disk space ({disk_free_gb:.1f} GB)"

    # Check if system is busy
    if schedule.skip_if_busy:
        cpu = get_cpu_usage()
        if cpu > 80:
            return True, f"System busy (CPU at {cpu}%)"

    return False, ""


async def run_scheduled_updates():
    """Run the scheduled update process."""
    logger = setup_logger("scheduled_updater")
    logger.info("="*60)
    logger.info(f"Scheduled update started at {datetime.now().isoformat()}")
    logger.info("="*60)

    # Load configuration
    settings = load_settings()
    schedule = load_schedule()

    # Check if we should skip
    should_skip, reason = should_skip_update()
    if should_skip:
        logger.warning(f"Skipping scheduled update: {reason}")
        return

    # Send notification that we're starting
    if schedule.notify_before:
        notify_scheduled_update_starting()

    # Determine which managers to run
    managers = []
    if settings.enabled_managers.macos:
        managers.append(MacOSUpdateManager())
    if settings.enabled_managers.homebrew:
        managers.append(HomebrewManager())
    if settings.enabled_managers.appstore:
        managers.append(AppStoreManager())
    if settings.enabled_managers.pip:
        managers.append(PipManager())
    if settings.enabled_managers.npm:
        managers.append(NpmManager())

    if not managers:
        logger.warning("No update managers enabled")
        return

    # Run updates
    results = []
    requires_reboot = False
    start_time = datetime.now()

    for manager in managers:
        logger.info(f"\n--- {manager.display_name} ---")

        try:
            if not await manager.is_available():
                logger.warning(f"{manager.display_name} is not available")
                continue

            # Check for updates
            num_updates, packages = await manager.check_updates()
            logger.info(f"Found {num_updates} update(s) available")

            if num_updates == 0:
                continue

            # Log packages
            for pkg in packages[:10]:
                logger.info(f"  - {pkg}")
            if len(packages) > 10:
                logger.info(f"  ... and {len(packages) - 10} more")

            # Perform update
            result = await manager.update()
            results.append(result)

            # Log result
            if result.status.value == "completed":
                logger.info(f"Successfully updated {result.packages_updated} package(s)")
            else:
                logger.error(f"Update failed: {result.error_message}")

            if result.requires_reboot:
                requires_reboot = True
                logger.warning("Restart required for some updates")

            # Log output
            for line in result.output_log[-50:]:
                logger.debug(line)

        except Exception as e:
            logger.error(f"Error updating {manager.display_name}: {str(e)}")

    # Calculate duration
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Summary
    logger.info("\n" + "="*60)
    logger.info("Update Summary")
    logger.info("="*60)

    total = len(results)
    successful = sum(1 for r in results if r.status.value == "completed")
    failed = sum(1 for r in results if r.status.value == "failed")

    logger.info(f"Total managers run: {total}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Duration: {duration:.1f} seconds")

    # Update settings
    update_last_run(settings)

    # Update schedule last run
    schedule.last_scheduled_run = datetime.now().isoformat()
    save_schedule(schedule)

    # Save to history
    manager_names = [m.display_name for m in managers if await m.is_available()]
    status = "Success" if failed == 0 else f"{successful}/{total} Success"
    save_update_history(manager_names, status, duration)

    # Send notifications
    if settings.update_preferences.notify_on_complete:
        notify_update_complete(total, successful, failed)

    if requires_reboot:
        notify_reboot_required()

    logger.info(f"Scheduled update completed at {datetime.now().isoformat()}")


def main():
    """Main entry point for scheduled updates."""
    try:
        asyncio.run(run_scheduled_updates())
    except Exception as e:
        logger = get_logger("scheduled_updater")
        logger.error(f"Fatal error in scheduled update: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
