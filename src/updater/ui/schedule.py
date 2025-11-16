"""Schedule screen for configuring automatic updates."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Static, Button, Switch, Select, Input, Label
from textual.widget import Widget

from ..config.schedule import (
    load_schedule,
    save_schedule,
    ScheduleConfig,
    ScheduleTime,
    ScheduleFrequency,
    install_launchd_service,
    uninstall_launchd_service,
    is_service_installed,
    get_service_status
)


class ScheduleScreen(Widget):
    """Screen for configuring scheduled updates."""

    DEFAULT_CSS = """
    ScheduleScreen {
        height: 100%;
    }

    #schedule-container {
        height: 100%;
        padding: 1;
    }

    .schedule-section {
        border: solid $primary-darken-2;
        padding: 1;
        margin-bottom: 1;
        height: auto;
    }

    .section-title {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }

    .form-row {
        height: auto;
        padding: 1 0;
    }

    .form-label {
        width: 30%;
    }

    .form-input {
        width: 70%;
    }

    #service-status {
        border: solid $warning;
        padding: 1;
        margin-bottom: 1;
    }

    .status-installed {
        color: $success;
    }

    .status-not-installed {
        color: $error;
    }

    #action-buttons {
        height: auto;
        padding: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.schedule_config = load_schedule()

    def compose(self) -> ComposeResult:
        with Vertical(id="schedule-container"):
            yield Static("Automatic Update Scheduling", classes="title")
            yield Static("Configure when updates should run automatically", classes="subtitle")

            # Service Status
            with Container(id="service-status"):
                yield Static("Service Status", classes="section-title")
                yield Static("Checking...", id="status-text")

            # Enable/Disable
            with Container(classes="schedule-section"):
                yield Static("Enable Scheduling", classes="section-title")
                with Horizontal(classes="form-row"):
                    yield Label("Enable automatic updates:", classes="form-label")
                    yield Switch(value=self.schedule_config.enabled, id="sw-enabled")

            # Frequency Settings
            with Container(classes="schedule-section"):
                yield Static("Frequency", classes="section-title")
                with Horizontal(classes="form-row"):
                    yield Label("Update frequency:", classes="form-label")
                    yield Select(
                        [
                            ("Daily", ScheduleFrequency.DAILY.value),
                            ("Weekly", ScheduleFrequency.WEEKLY.value),
                            ("Bi-weekly", ScheduleFrequency.BIWEEKLY.value),
                            ("Monthly", ScheduleFrequency.MONTHLY.value),
                        ],
                        value=self.schedule_config.frequency,
                        id="sel-frequency"
                    )

            # Time Settings
            with Container(classes="schedule-section"):
                yield Static("Time of Day", classes="section-title")
                with Horizontal(classes="form-row"):
                    yield Label("Preferred time:", classes="form-label")
                    yield Select(
                        [
                            ("Early Morning (6:00 AM)", ScheduleTime.EARLY_MORNING.value),
                            ("Morning (9:00 AM)", ScheduleTime.MORNING.value),
                            ("Afternoon (2:00 PM)", ScheduleTime.AFTERNOON.value),
                            ("Evening (6:00 PM)", ScheduleTime.EVENING.value),
                            ("Night (10:00 PM)", ScheduleTime.NIGHT.value),
                            ("Custom Time", ScheduleTime.CUSTOM.value),
                        ],
                        value=self.schedule_config.time_preset,
                        id="sel-time"
                    )

                with Horizontal(classes="form-row", id="custom-time-row"):
                    yield Label("Custom hour (0-23):", classes="form-label")
                    yield Input(
                        str(self.schedule_config.custom_hour),
                        type="integer",
                        id="inp-hour"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Custom minute (0-59):", classes="form-label")
                    yield Input(
                        str(self.schedule_config.custom_minute),
                        type="integer",
                        id="inp-minute"
                    )

            # Day Settings
            with Container(classes="schedule-section"):
                yield Static("Day Settings", classes="section-title")
                with Horizontal(classes="form-row"):
                    yield Label("Day of week (1=Mon, 7=Sun):", classes="form-label")
                    yield Select(
                        [
                            ("Monday", 1),
                            ("Tuesday", 2),
                            ("Wednesday", 3),
                            ("Thursday", 4),
                            ("Friday", 5),
                            ("Saturday", 6),
                            ("Sunday", 7),
                        ],
                        value=self.schedule_config.day_of_week,
                        id="sel-weekday"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Day of month (1-28):", classes="form-label")
                    yield Input(
                        str(self.schedule_config.day_of_month),
                        type="integer",
                        id="inp-monthday"
                    )

            # Options
            with Container(classes="schedule-section"):
                yield Static("Options", classes="section-title")
                with Horizontal(classes="form-row"):
                    yield Label("Notify before starting:", classes="form-label")
                    yield Switch(value=self.schedule_config.notify_before, id="sw-notify")

                with Horizontal(classes="form-row"):
                    yield Label("Skip if on battery:", classes="form-label")
                    yield Switch(value=self.schedule_config.skip_if_on_battery, id="sw-battery")

                with Horizontal(classes="form-row"):
                    yield Label("Skip if system busy:", classes="form-label")
                    yield Switch(value=self.schedule_config.skip_if_busy, id="sw-busy")

            # Action Buttons
            with Horizontal(id="action-buttons"):
                yield Button("Save Configuration", variant="success", id="btn-save")
                yield Button("Install Service", variant="primary", id="btn-install")
                yield Button("Uninstall Service", variant="error", id="btn-uninstall")
                yield Button("Test Run", variant="warning", id="btn-test")

    def on_mount(self) -> None:
        """Update service status on mount."""
        self._update_service_status()

    def _update_service_status(self) -> None:
        """Update the service status display."""
        status_text = self.query_one("#status-text", Static)
        status = get_service_status()

        if status["installed"]:
            if status["loaded"]:
                status_text.update(f"[green]✓ Service installed and running[/]\n{status.get('status', '')}")
            else:
                status_text.update("[yellow]⚠ Service installed but not loaded[/]")
        else:
            status_text.update("[red]✗ Service not installed[/]")

    def _save_config(self) -> None:
        """Save the current configuration."""
        # Get values from widgets
        self.schedule_config.enabled = self.query_one("#sw-enabled", Switch).value
        self.schedule_config.frequency = self.query_one("#sel-frequency", Select).value
        self.schedule_config.time_preset = self.query_one("#sel-time", Select).value

        try:
            self.schedule_config.custom_hour = int(self.query_one("#inp-hour", Input).value)
            self.schedule_config.custom_minute = int(self.query_one("#inp-minute", Input).value)
            self.schedule_config.day_of_week = self.query_one("#sel-weekday", Select).value
            self.schedule_config.day_of_month = int(self.query_one("#inp-monthday", Input).value)
        except ValueError:
            pass

        self.schedule_config.notify_before = self.query_one("#sw-notify", Switch).value
        self.schedule_config.skip_if_on_battery = self.query_one("#sw-battery", Switch).value
        self.schedule_config.skip_if_busy = self.query_one("#sw-busy", Switch).value

        # Save to file
        if save_schedule(self.schedule_config):
            self.notify("Configuration saved successfully!", severity="information")
        else:
            self.notify("Failed to save configuration", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save":
            self._save_config()
        elif event.button.id == "btn-install":
            self._install_service()
        elif event.button.id == "btn-uninstall":
            self._uninstall_service()
        elif event.button.id == "btn-test":
            self._test_run()

    def _install_service(self) -> None:
        """Install the launchd service."""
        self._save_config()  # Save first

        if not self.schedule_config.enabled:
            self.notify("Please enable scheduling first", severity="warning")
            return

        success, message = install_launchd_service(self.schedule_config)

        if success:
            self.notify(f"Service installed: {message}", severity="information")
        else:
            self.notify(f"Failed to install service: {message}", severity="error")

        self._update_service_status()

    def _uninstall_service(self) -> None:
        """Uninstall the launchd service."""
        success, message = uninstall_launchd_service()

        if success:
            self.notify(f"Service uninstalled: {message}", severity="information")
        else:
            self.notify(f"Failed to uninstall service: {message}", severity="error")

        self._update_service_status()

    def _test_run(self) -> None:
        """Test the scheduled update configuration."""
        self.notify("Test run would execute scheduled updates now", severity="information")
        # In a real implementation, this would trigger a test run
