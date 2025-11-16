"""Command-line interface for macOS Universal Updater."""

import click
import asyncio
from pathlib import Path


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit")
@click.pass_context
def main(ctx, version):
    """macOS Universal Updater - Keep your system up to date."""
    if version:
        from . import __version__
        click.echo(f"macOS Universal Updater v{__version__}")
        return

    if ctx.invoked_subcommand is None:
        # Launch the TUI by default
        from .app import UpdaterApp
        app = UpdaterApp()
        app.run()


@main.command()
def tui():
    """Launch the interactive TUI interface."""
    from .app import UpdaterApp
    app = UpdaterApp()
    app.run()


@main.command()
@click.option("--macos/--no-macos", default=True, help="Update macOS system")
@click.option("--homebrew/--no-homebrew", default=True, help="Update Homebrew packages")
@click.option("--appstore/--no-appstore", default=True, help="Update App Store apps")
@click.option("--pip/--no-pip", default=False, help="Update Python packages")
@click.option("--npm/--no-npm", default=False, help="Update Node.js packages")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def update(macos, homebrew, appstore, pip, npm, verbose):
    """Run updates from the command line (non-interactive)."""
    from .managers import (
        MacOSUpdateManager,
        HomebrewManager,
        AppStoreManager,
        PipManager,
        NpmManager
    )
    from .utils.logging import setup_logger
    import logging

    if verbose:
        setup_logger(level=logging.DEBUG)
    else:
        setup_logger()

    managers = []
    if macos:
        managers.append(MacOSUpdateManager())
    if homebrew:
        managers.append(HomebrewManager())
    if appstore:
        managers.append(AppStoreManager())
    if pip:
        managers.append(PipManager())
    if npm:
        managers.append(NpmManager())

    if not managers:
        click.echo("No update managers selected.")
        return

    async def run_updates():
        results = []
        for manager in managers:
            click.echo(f"\n{'='*50}")
            click.echo(f"{manager.icon} {manager.display_name}")
            click.echo('='*50)

            if not await manager.is_available():
                click.echo(f"  ⚠️  {manager.display_name} is not available")
                continue

            click.echo("  Checking for updates...")
            num_updates, packages = await manager.check_updates()

            if num_updates == 0:
                click.echo("  ✓ Already up to date")
                continue

            click.echo(f"  Found {num_updates} update(s)")

            if verbose:
                for pkg in packages[:10]:
                    click.echo(f"    - {pkg}")
                if len(packages) > 10:
                    click.echo(f"    ... and {len(packages) - 10} more")

            click.echo("  Installing updates...")
            result = await manager.update()
            results.append(result)

            if result.status.value == "completed":
                click.echo(f"  ✓ Updated {result.packages_updated} package(s)")
            else:
                click.echo(f"  ✗ Failed: {result.error_message}")

            if result.requires_reboot:
                click.echo("  ⚠️  Restart required!")

        # Summary
        click.echo(f"\n{'='*50}")
        click.echo("Summary")
        click.echo('='*50)
        total = len(results)
        successful = sum(1 for r in results if r.status.value == "completed")
        click.echo(f"  {successful}/{total} managers updated successfully")

    asyncio.run(run_updates())


@main.command()
def check():
    """Check for available updates without installing."""
    from .managers import (
        MacOSUpdateManager,
        HomebrewManager,
        AppStoreManager,
        PipManager,
        NpmManager
    )
    from .config.settings import load_settings

    settings = load_settings()

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

    async def check_all():
        total_updates = 0
        for manager in managers:
            click.echo(f"{manager.icon} {manager.display_name}: ", nl=False)

            if not await manager.is_available():
                click.echo("Not installed")
                continue

            num_updates, _ = await manager.check_updates()
            total_updates += num_updates

            if num_updates > 0:
                click.echo(f"{num_updates} update(s) available")
            else:
                click.echo("Up to date")

        click.echo(f"\nTotal: {total_updates} update(s) available")

    asyncio.run(check_all())


@main.command()
def schedule():
    """View or modify update schedule."""
    from .config.schedule import load_schedule, is_service_installed, get_service_status

    schedule = load_schedule()
    status = get_service_status()

    click.echo("Schedule Configuration")
    click.echo('='*50)
    click.echo(f"Enabled: {schedule.enabled}")
    click.echo(f"Frequency: {schedule.frequency}")
    click.echo(f"Time: {schedule.time_preset}")
    if schedule.time_preset == "custom":
        click.echo(f"Custom time: {schedule.custom_hour:02d}:{schedule.custom_minute:02d}")
    click.echo(f"Day of week: {schedule.day_of_week}")
    click.echo(f"\nService Status:")
    click.echo(f"  Installed: {status['installed']}")
    click.echo(f"  Loaded: {status['loaded']}")
    click.echo(f"  Status: {status['status']}")


@main.command()
def status():
    """Show system status and available tools."""
    from .utils.system import get_system_info, check_prerequisites, format_bytes
    from .config.settings import load_settings

    info = get_system_info()
    tools = check_prerequisites()
    settings = load_settings()

    click.echo("System Status")
    click.echo('='*50)
    click.echo(f"macOS Version: {info.os_version} ({info.os_build})")
    click.echo(f"Hostname: {info.hostname}")
    click.echo(f"CPU Cores: {info.cpu_count}")
    click.echo(f"Memory: {format_bytes(info.memory_total)}")
    click.echo(f"Disk: {format_bytes(info.disk_free)} free of {format_bytes(info.disk_total)}")
    if info.battery_percent is not None:
        charging = "Charging" if info.is_charging else "On Battery"
        click.echo(f"Battery: {info.battery_percent}% ({charging})")

    click.echo("\nAvailable Tools:")
    for tool, available in tools.items():
        status = "✓" if available else "✗"
        click.echo(f"  {status} {tool}")

    click.echo(f"\nLast Update: {settings.last_update or 'Never'}")


@main.command()
def config():
    """Open configuration directory."""
    import subprocess
    from .config.settings import get_config_directory

    config_dir = get_config_directory()
    click.echo(f"Configuration directory: {config_dir}")
    try:
        subprocess.run(["open", str(config_dir)], check=True)
    except Exception:
        pass


@main.command()
def reset():
    """Reset all settings to defaults."""
    from .config.settings import reset_settings

    if click.confirm("Are you sure you want to reset all settings?"):
        reset_settings()
        click.echo("Settings reset to defaults.")
    else:
        click.echo("Cancelled.")


if __name__ == "__main__":
    main()
