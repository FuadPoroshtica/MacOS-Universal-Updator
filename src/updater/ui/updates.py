"""Updates screen for running and monitoring updates."""

import asyncio
from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, ProgressBar, Button, Checkbox, Log, DataTable
from textual.widget import Widget
from textual.worker import Worker, get_current_worker

from ..managers import (
    HomebrewManager,
    MacOSUpdateManager,
    AppStoreManager,
    PipManager,
    NpmManager,
    UpdateStatus,
    UpdateResult
)
from ..config.settings import load_settings, save_settings, update_last_run
from ..utils.notifications import notify_update_complete, notify_reboot_required
from ..utils.system import get_battery_status, get_disk_space, format_bytes
from ..utils.logging import get_logger


class UpdateManagerWidget(Widget):
    """Widget for a single update manager."""

    DEFAULT_CSS = """
    UpdateManagerWidget {
        height: auto;
        border: solid $primary-darken-2;
        padding: 1;
        margin-bottom: 1;
    }

    .manager-header {
        height: auto;
    }

    .manager-name {
        text-style: bold;
    }

    .manager-status {
        color: $text-muted;
    }

    .status-pending {
        color: $text-muted;
    }

    .status-checking {
        color: $warning;
    }

    .status-updating {
        color: $primary;
    }

    .status-completed {
        color: $success;
    }

    .status-failed {
        color: $error;
    }

    .status-skipped {
        color: $text-muted;
    }
    """

    def __init__(self, manager, enabled: bool = True) -> None:
        super().__init__()
        self.manager = manager
        self.enabled = enabled
        self.status = UpdateStatus.PENDING
        self.updates_available = 0
        self.packages = []
        self.result: UpdateResult | None = None

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(classes="manager-header"):
                yield Checkbox(
                    f"{self.manager.icon} {self.manager.display_name}",
                    value=self.enabled,
                    id=f"cb-{self.manager.name}"
                )
            yield Static("Status: Pending", id=f"status-{self.manager.name}", classes="manager-status")
            yield ProgressBar(total=100, id=f"progress-{self.manager.name}", show_eta=False)
            yield Static("", id=f"info-{self.manager.name}")

    def update_status(self, status: UpdateStatus, message: str = "") -> None:
        """Update the status display."""
        self.status = status
        status_widget = self.query_one(f"#status-{self.manager.name}", Static)

        status_text = {
            UpdateStatus.PENDING: "Pending",
            UpdateStatus.CHECKING: "Checking for updates...",
            UpdateStatus.UPDATING: "Installing updates...",
            UpdateStatus.COMPLETED: "Completed",
            UpdateStatus.FAILED: "Failed",
            UpdateStatus.SKIPPED: "Skipped",
            UpdateStatus.CANCELLED: "Cancelled"
        }.get(status, "Unknown")

        if message:
            status_text = f"{status_text} - {message}"

        status_widget.update(f"Status: {status_text}")
        status_widget.remove_class("status-pending", "status-checking", "status-updating",
                                   "status-completed", "status-failed", "status-skipped")
        status_widget.add_class(f"status-{status.value}")

    def update_progress(self, percentage: float) -> None:
        """Update the progress bar."""
        progress_bar = self.query_one(f"#progress-{self.manager.name}", ProgressBar)
        progress_bar.update(progress=percentage * 100)

    def update_info(self, info: str) -> None:
        """Update the info text."""
        info_widget = self.query_one(f"#info-{self.manager.name}", Static)
        info_widget.update(info)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox toggle."""
        self.enabled = event.value


class UpdatesScreen(Widget):
    """Screen for managing and running updates."""

    DEFAULT_CSS = """
    UpdatesScreen {
        height: 100%;
    }

    #updates-container {
        height: 100%;
    }

    #managers-panel {
        width: 1fr;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    #log-panel {
        width: 2fr;
        height: 100%;
        border: solid $secondary;
        padding: 1;
    }

    #action-buttons {
        height: auto;
        padding: 1;
    }

    #managers-list {
        height: 1fr;
        overflow-y: auto;
    }

    .log-title {
        text-style: bold;
        padding-bottom: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.logger = get_logger()
        self.settings = load_settings()
        self.managers = []
        self.manager_widgets = {}
        self._update_running = False
        self.worker: Worker | None = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Update Manager", classes="title")
            yield Static("Select and run updates for your system", classes="subtitle")

            with Horizontal(id="action-buttons"):
                yield Button("Check All", variant="primary", id="btn-check")
                yield Button("Update Selected", variant="success", id="btn-update")
                yield Button("Skip Current", variant="warning", id="btn-skip")
                yield Button("Cancel", variant="error", id="btn-cancel")
                yield Button("Select All", variant="default", id="btn-select-all")
                yield Button("Deselect All", variant="default", id="btn-deselect-all")

            with Horizontal(id="updates-container"):
                with Vertical(id="managers-panel"):
                    yield Static("Package Managers", classes="log-title")
                    with ScrollableContainer(id="managers-list"):
                        # Create manager widgets
                        pass  # Will be populated in on_mount

                with Vertical(id="log-panel"):
                    yield Static("Update Log", classes="log-title")
                    yield Log(id="update-log", highlight=True, markup=True)

    def on_mount(self) -> None:
        """Initialize managers on mount."""
        self._initialize_managers()

    def _initialize_managers(self) -> None:
        """Initialize all update managers."""
        # Create managers
        self.managers = [
            MacOSUpdateManager(),
            HomebrewManager(),
            AppStoreManager(),
            PipManager(),
            NpmManager(),
        ]

        # Create widgets
        managers_list = self.query_one("#managers-list", ScrollableContainer)

        for manager in self.managers:
            enabled = getattr(self.settings.enabled_managers, manager.name, False)
            widget = UpdateManagerWidget(manager, enabled)
            self.manager_widgets[manager.name] = widget
            managers_list.mount(widget)

    def _log(self, message: str, style: str = "") -> None:
        """Add a message to the log."""
        log_widget = self.query_one("#update-log", Log)
        timestamp = datetime.now().strftime("%H:%M:%S")

        if style:
            log_widget.write_line(f"[{style}][{timestamp}] {message}[/]")
        else:
            log_widget.write_line(f"[{timestamp}] {message}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-check":
            self.check_all_updates()
        elif event.button.id == "btn-update":
            self.run_updates()
        elif event.button.id == "btn-skip":
            self.skip_current()
        elif event.button.id == "btn-cancel":
            self.cancel_updates()
        elif event.button.id == "btn-select-all":
            self.select_all()
        elif event.button.id == "btn-deselect-all":
            self.deselect_all()

    def select_all(self) -> None:
        """Select all managers."""
        for widget in self.manager_widgets.values():
            checkbox = widget.query_one(Checkbox)
            checkbox.value = True
            widget.enabled = True

    def deselect_all(self) -> None:
        """Deselect all managers."""
        for widget in self.manager_widgets.values():
            checkbox = widget.query_one(Checkbox)
            checkbox.value = False
            widget.enabled = False

    def check_all_updates(self) -> None:
        """Check for updates from all enabled managers."""
        if self._update_running:
            self._log("Update operation already in progress", "yellow")
            return

        self._log("Starting update check...", "bold")
        self.worker = self.run_worker(self._check_updates_worker, thread=True)

    async def _check_updates_worker(self) -> None:
        """Worker to check updates."""
        self._update_running = True

        for manager in self.managers:
            widget = self.manager_widgets[manager.name]

            if not widget.enabled:
                widget.update_status(UpdateStatus.SKIPPED, "Not selected")
                continue

            self.call_from_thread(widget.update_status, UpdateStatus.CHECKING)
            self.call_from_thread(self._log, f"Checking {manager.display_name}...")

            try:
                # Check if available
                available = await manager.is_available()
                if not available:
                    self.call_from_thread(widget.update_status, UpdateStatus.SKIPPED, "Not installed")
                    self.call_from_thread(widget.update_info, "Tool not available on system")
                    continue

                # Check for updates
                num_updates, packages = await manager.check_updates()
                widget.updates_available = num_updates
                widget.packages = packages

                self.call_from_thread(widget.update_progress, 1.0)
                self.call_from_thread(widget.update_status, UpdateStatus.PENDING)

                if num_updates > 0:
                    info = f"{num_updates} update(s) available"
                    self.call_from_thread(widget.update_info, info)
                    self.call_from_thread(self._log, f"{manager.display_name}: {info}", "green")
                else:
                    self.call_from_thread(widget.update_info, "Up to date")
                    self.call_from_thread(self._log, f"{manager.display_name}: Up to date")

            except Exception as e:
                self.call_from_thread(widget.update_status, UpdateStatus.FAILED, str(e))
                self.call_from_thread(self._log, f"{manager.display_name}: Error - {str(e)}", "red")

        self._update_running = False
        self.call_from_thread(self._log, "Update check completed", "bold")

    def run_updates(self) -> None:
        """Run updates for selected managers."""
        if self._update_running:
            self._log("Update operation already in progress", "yellow")
            return

        # Pre-flight checks
        if not self._pre_flight_checks():
            return

        self._log("Starting updates...", "bold green")
        self.worker = self.run_worker(self._run_updates_worker, thread=True)

    def _pre_flight_checks(self) -> bool:
        """Perform pre-flight checks before updating."""
        # Check battery
        if self.settings.update_preferences.skip_on_battery:
            battery_percent, is_charging = get_battery_status()
            if battery_percent is not None:
                if not is_charging and battery_percent < self.settings.update_preferences.min_battery_percent:
                    self._log(
                        f"Battery too low ({battery_percent}%). Please connect to power.",
                        "red"
                    )
                    return False

        # Check disk space
        _, disk_free = get_disk_space()
        disk_free_gb = disk_free / (1024 ** 3)
        if disk_free_gb < self.settings.update_preferences.min_disk_space_gb:
            self._log(
                f"Low disk space ({disk_free_gb:.1f} GB free). Need at least "
                f"{self.settings.update_preferences.min_disk_space_gb} GB.",
                "red"
            )
            return False

        return True

    async def _run_updates_worker(self) -> None:
        """Worker to run updates."""
        self._update_running = True
        results = []
        requires_reboot = False

        for manager in self.managers:
            widget = self.manager_widgets[manager.name]

            if not widget.enabled or widget.updates_available == 0:
                continue

            self.call_from_thread(self._log, f"\n{'='*50}")
            self.call_from_thread(self._log, f"Updating {manager.display_name}...", "bold")

            # Set progress callback
            def progress_callback(message, percentage):
                self.call_from_thread(widget.update_progress, percentage)
                self.call_from_thread(widget.update_info, message)

            manager.set_progress_callback(progress_callback)

            try:
                result = await manager.update()
                results.append(result)
                widget.result = result

                if result.requires_reboot:
                    requires_reboot = True

                # Log output
                for line in result.output_log[-20:]:  # Last 20 lines
                    self.call_from_thread(self._log, line)

                if result.status == UpdateStatus.COMPLETED:
                    self.call_from_thread(widget.update_status, UpdateStatus.COMPLETED)
                    self.call_from_thread(
                        self._log,
                        f"{manager.display_name}: Updated {result.packages_updated} package(s)",
                        "green"
                    )
                elif result.status == UpdateStatus.FAILED:
                    self.call_from_thread(widget.update_status, UpdateStatus.FAILED, result.error_message or "")
                    self.call_from_thread(
                        self._log,
                        f"{manager.display_name}: Failed - {result.error_message}",
                        "red"
                    )
                elif result.status == UpdateStatus.CANCELLED:
                    self.call_from_thread(widget.update_status, UpdateStatus.CANCELLED)
                    self.call_from_thread(self._log, f"{manager.display_name}: Cancelled", "yellow")

            except Exception as e:
                self.call_from_thread(widget.update_status, UpdateStatus.FAILED, str(e))
                self.call_from_thread(self._log, f"{manager.display_name}: Error - {str(e)}", "red")

        self._update_running = False

        # Summary
        total = len(results)
        successful = sum(1 for r in results if r.status == UpdateStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == UpdateStatus.FAILED)

        self.call_from_thread(self._log, f"\n{'='*50}")
        self.call_from_thread(self._log, f"Update Summary: {successful}/{total} successful", "bold")

        # Notifications
        if self.settings.update_preferences.notify_on_complete:
            notify_update_complete(total, successful, failed)

        if requires_reboot:
            self.call_from_thread(self._log, "⚠️  A system restart is required!", "bold yellow")
            notify_reboot_required()

        # Update last run time
        self.settings = update_last_run(self.settings)

    def skip_current(self) -> None:
        """Skip the current update."""
        for manager in self.managers:
            if not manager._cancelled:
                manager.cancel()
                self._log(f"Skipping {manager.display_name}...", "yellow")
                break

    def cancel_updates(self) -> None:
        """Cancel all updates."""
        self._log("Cancelling all updates...", "red")
        for manager in self.managers:
            manager.cancel()

        if self.worker:
            self.worker.cancel()

        self._update_running = False
