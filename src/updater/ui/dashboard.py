"""Dashboard screen showing system overview."""

import asyncio
from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid, ScrollableContainer
from textual.widgets import Static, ProgressBar, Button, Label, DataTable
from textual.reactive import reactive
from textual.widget import Widget
from textual.timer import Timer

from ..utils.system import (
    get_system_info,
    check_prerequisites,
    format_bytes,
    get_cpu_usage,
    get_memory_usage
)
from ..config.settings import load_settings
from ..config.schedule import load_schedule, is_service_installed
from ..managers import (
    HomebrewManager,
    MacOSUpdateManager,
    AppStoreManager,
    PipManager,
    NpmManager
)


class MetricCard(Widget):
    """A card displaying a single metric."""

    DEFAULT_CSS = """
    MetricCard {
        height: auto;
        border: solid $primary-darken-2;
        padding: 1;
        margin: 0 1 1 0;
    }

    MetricCard .metric-title {
        color: $text-muted;
        text-style: italic;
    }

    MetricCard .metric-value {
        text-style: bold;
        color: $accent;
        padding-top: 1;
    }

    MetricCard .metric-icon {
        text-align: right;
    }
    """

    def __init__(self, title: str, value: str, icon: str = "") -> None:
        super().__init__()
        self.metric_title = title
        self.metric_value = value
        self.metric_icon = icon

    def compose(self) -> ComposeResult:
        with Vertical():
            if self.metric_icon:
                yield Static(self.metric_icon, classes="metric-icon")
            yield Static(self.metric_title, classes="metric-title")
            yield Static(self.metric_value, classes="metric-value")

    def update_value(self, value: str) -> None:
        """Update the metric value."""
        self.metric_value = value
        value_widget = self.query_one(".metric-value", Static)
        value_widget.update(value)


class ToolStatus(Widget):
    """Widget showing availability of a tool."""

    DEFAULT_CSS = """
    ToolStatus {
        height: auto;
        padding: 0 1;
    }

    ToolStatus .tool-available {
        color: $success;
    }

    ToolStatus .tool-unavailable {
        color: $error;
    }
    """

    def __init__(self, name: str, available: bool) -> None:
        super().__init__()
        self.tool_name = name
        self.available = available

    def compose(self) -> ComposeResult:
        status = "✓" if self.available else "✗"
        css_class = "tool-available" if self.available else "tool-unavailable"
        yield Static(f"{status} {self.tool_name}", classes=css_class)


class DashboardScreen(Widget):
    """Main dashboard screen."""

    DEFAULT_CSS = """
    DashboardScreen {
        height: 100%;
    }

    #dashboard-grid {
        grid-size: 3;
        grid-gutter: 1;
        padding: 1;
        height: auto;
    }

    #system-info {
        column-span: 2;
        border: solid $primary;
        padding: 1;
        height: auto;
    }

    #quick-actions {
        border: solid $accent;
        padding: 1;
        height: auto;
    }

    #tools-status {
        border: solid $secondary;
        padding: 1;
        height: auto;
    }

    #schedule-status {
        border: solid $warning;
        padding: 1;
        height: auto;
    }

    #health-status {
        border: solid $success;
        padding: 1;
        height: auto;
    }

    #software-status {
        column-span: 3;
        border: solid $primary;
        padding: 1;
        height: auto;
    }

    .section-header {
        text-style: bold;
        color: $text;
        padding-bottom: 1;
    }

    #resource-bars {
        height: auto;
        padding: 1;
    }

    #software-table {
        height: 12;
    }
    """

    cpu_usage = reactive(0.0)
    memory_usage = reactive(0.0)

    def __init__(self) -> None:
        super().__init__()
        self._update_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("System Dashboard", classes="title")
            yield Static("Monitor your system health and update status", classes="subtitle")

            with Grid(id="dashboard-grid"):
                # System Information
                with Container(id="system-info"):
                    yield Static("System Information", classes="section-header")
                    with Horizontal():
                        yield MetricCard("macOS Version", "Loading...", "🍎")
                        yield MetricCard("Hostname", "Loading...", "💻")
                        yield MetricCard("Uptime", "Loading...", "⏱️")

                # Quick Actions
                with Container(id="quick-actions"):
                    yield Static("Quick Actions", classes="section-header")
                    yield Button("Check All Updates", variant="primary", id="btn-check-updates")
                    yield Button("Run All Updates", variant="success", id="btn-run-updates")
                    yield Button("System Info", variant="default", id="btn-system-info")

                # Tools Status
                with Container(id="tools-status"):
                    yield Static("Available Tools", classes="section-header")
                    yield Static("Checking...", id="tools-list")

                # Schedule Status
                with Container(id="schedule-status"):
                    yield Static("Schedule Status", classes="section-header")
                    yield Static("Loading...", id="schedule-info")

                # Health Status
                with Container(id="health-status"):
                    yield Static("System Health", classes="section-header")
                    with Vertical(id="resource-bars"):
                        yield Static("CPU Usage:")
                        yield ProgressBar(total=100, id="cpu-bar")
                        yield Static("Memory Usage:")
                        yield ProgressBar(total=100, id="memory-bar")
                        yield Static("Disk Space:")
                        yield ProgressBar(total=100, id="disk-bar")

                # Software Status - shows all available software with update counts
                with Container(id="software-status"):
                    yield Static("Software Update Status", classes="section-header")
                    yield Static("Click 'Scan for Updates' to check all software", id="software-hint")
                    yield DataTable(id="software-table")
                    yield Button("Scan for Updates", variant="primary", id="btn-scan-updates")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self._setup_software_table()
        self.refresh_data()
        # Start periodic updates
        self._update_timer = self.set_interval(5, self._update_resources)

    def on_unmount(self) -> None:
        """Called when widget is unmounted."""
        if self._update_timer:
            self._update_timer.stop()

    def refresh_data(self) -> None:
        """Refresh all dashboard data."""
        self.call_later(self._load_system_info)
        self.call_later(self._load_tools_status)
        self.call_later(self._load_schedule_status)
        self._update_resources()
        self._load_software_status()

    def _setup_software_table(self) -> None:
        """Setup the software status table."""
        table = self.query_one("#software-table", DataTable)
        table.add_columns("Software", "Status", "Updates", "Version/Info")

    def _load_software_status(self) -> None:
        """Load initial software status (availability only)."""
        table = self.query_one("#software-table", DataTable)
        table.clear()

        managers = [
            MacOSUpdateManager(),
            HomebrewManager(),
            AppStoreManager(),
            PipManager(),
            NpmManager(),
        ]

        async def check_availability():
            for mgr in managers:
                available = await mgr.is_available()
                status = "Available" if available else "Not Installed"
                self.app.call_from_thread(
                    table.add_row,
                    f"{mgr.icon} {mgr.display_name}",
                    status,
                    "Not scanned",
                    "Click 'Scan for Updates'"
                )

        self.run_worker(check_availability, thread=True)

    def _load_system_info(self) -> None:
        """Load system information."""
        try:
            info = get_system_info()

            # Update metric cards
            cards = list(self.query(MetricCard))
            if len(cards) >= 3:
                cards[0].update_value(info.os_version)
                cards[1].update_value(info.hostname)

                # Calculate uptime
                import time
                uptime_seconds = time.time() - info.uptime
                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                cards[2].update_value(f"{days}d {hours}h")

            # Update disk bar
            disk_bar = self.query_one("#disk-bar", ProgressBar)
            disk_percent = ((info.disk_total - info.disk_free) / info.disk_total) * 100
            disk_bar.update(progress=disk_percent)

        except Exception as e:
            pass

    def _load_tools_status(self) -> None:
        """Load tools availability status."""
        try:
            tools = check_prerequisites()
            tools_list = self.query_one("#tools-list", Static)

            status_lines = []
            for tool, available in tools.items():
                icon = "✓" if available else "✗"
                color = "green" if available else "red"
                status_lines.append(f"[{color}]{icon}[/] {tool.title()}")

            tools_list.update("\n".join(status_lines))
        except Exception:
            pass

    def _load_schedule_status(self) -> None:
        """Load schedule status."""
        try:
            schedule = load_schedule()
            schedule_info = self.query_one("#schedule-info", Static)

            if not schedule.enabled:
                schedule_info.update("[yellow]Scheduling disabled[/]")
            elif is_service_installed():
                schedule_info.update(
                    f"[green]Active[/]\n"
                    f"Frequency: {schedule.frequency}\n"
                    f"Time: {schedule.time_preset}"
                )
            else:
                schedule_info.update("[red]Service not installed[/]")
        except Exception:
            pass

    def _update_resources(self) -> None:
        """Update resource usage bars."""
        try:
            # CPU
            cpu_bar = self.query_one("#cpu-bar", ProgressBar)
            cpu = get_cpu_usage()
            cpu_bar.update(progress=cpu)

            # Memory
            memory_bar = self.query_one("#memory-bar", ProgressBar)
            _, _, mem_percent = get_memory_usage()
            memory_bar.update(progress=mem_percent)
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-check-updates":
            # Switch to updates tab and check
            self.app.action_switch_tab("updates")
        elif event.button.id == "btn-run-updates":
            # Switch to updates tab
            self.app.action_switch_tab("updates")
        elif event.button.id == "btn-system-info":
            self.app.push_screen(SystemInfoScreen())
        elif event.button.id == "btn-scan-updates":
            self._scan_for_updates()

    def _scan_for_updates(self) -> None:
        """Scan all managers for available updates."""
        hint = self.query_one("#software-hint", Static)
        hint.update("Scanning for updates... This may take a moment.")

        table = self.query_one("#software-table", DataTable)
        table.clear()

        managers = [
            MacOSUpdateManager(),
            HomebrewManager(),
            AppStoreManager(),
            PipManager(),
            NpmManager(),
        ]

        async def scan():
            total_updates = 0
            for mgr in managers:
                # Check availability
                available = await mgr.is_available()

                if not available:
                    self.app.call_from_thread(
                        table.add_row,
                        f"{mgr.icon} {mgr.display_name}",
                        "Not Installed",
                        "-",
                        "Install to enable"
                    )
                    continue

                # Check for updates
                try:
                    num_updates, packages = await mgr.check_updates()
                    total_updates += num_updates

                    if num_updates > 0:
                        status = "Updates Available"
                        updates_str = str(num_updates)
                        # Show first few package names
                        if packages:
                            info = ", ".join(packages[:3])
                            if len(packages) > 3:
                                info += f" +{len(packages)-3} more"
                        else:
                            info = "Updates ready"
                    else:
                        status = "Up to Date"
                        updates_str = "0"
                        info = "All packages current"

                    self.app.call_from_thread(
                        table.add_row,
                        f"{mgr.icon} {mgr.display_name}",
                        status,
                        updates_str,
                        info
                    )
                except Exception as e:
                    self.app.call_from_thread(
                        table.add_row,
                        f"{mgr.icon} {mgr.display_name}",
                        "Error",
                        "-",
                        str(e)[:40]
                    )

            # Update hint with summary
            self.app.call_from_thread(
                hint.update,
                f"Scan complete. Total: {total_updates} update(s) available."
            )

        self.run_worker(scan, thread=True)


class SystemInfoScreen(Widget):
    """Detailed system information screen."""

    def compose(self) -> ComposeResult:
        from textual.containers import Center

        with Center():
            with Vertical(classes="info-box"):
                yield Static("# Detailed System Information", classes="title")
                yield Static("Loading...", id="detailed-info")
                yield Button("Close", variant="primary", id="close-info")

    def on_mount(self) -> None:
        """Load detailed information."""
        self._load_info()

    def _load_info(self) -> None:
        """Load detailed system information."""
        try:
            info = get_system_info()
            info_widget = self.query_one("#detailed-info", Static)

            details = f"""
**Operating System**
- Version: {info.os_version}
- Build: {info.os_build}
- Hostname: {info.hostname}

**Hardware**
- CPU Cores: {info.cpu_count}
- Total Memory: {format_bytes(info.memory_total)}
- Total Disk: {format_bytes(info.disk_total)}
- Free Disk: {format_bytes(info.disk_free)}

**Power**
- Battery: {info.battery_percent}% {'(Charging)' if info.is_charging else '(On Battery)' if info.battery_percent else 'N/A'}
"""
            info_widget.update(details)
        except Exception as e:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "close-info":
            self.app.pop_screen()
