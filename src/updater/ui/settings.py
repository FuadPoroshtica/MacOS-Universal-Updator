"""Settings screen for configuring application preferences."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Button, Switch, Input, Label, Select, TextArea
from textual.widget import Widget

from ..config.settings import load_settings, save_settings, reset_settings, Settings


class SettingsScreen(Widget):
    """Screen for configuring application settings."""

    DEFAULT_CSS = """
    SettingsScreen {
        height: 100%;
    }

    #settings-container {
        height: 100%;
        padding: 1;
    }

    .settings-section {
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
        padding: 0 0 1 0;
    }

    .form-label {
        width: 50%;
    }

    .form-input {
        width: 50%;
    }

    #action-buttons {
        height: auto;
        padding: 1;
    }

    TextArea {
        height: 10;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="settings-container"):
            yield Static("Application Settings", classes="title")
            yield Static("Configure your update preferences", classes="subtitle")

            # Update Preferences
            with Container(classes="settings-section"):
                yield Static("Update Preferences", classes="section-title")

                with Horizontal(classes="form-row"):
                    yield Label("Auto cleanup after updates:", classes="form-label")
                    yield Switch(
                        value=self.settings.update_preferences.auto_cleanup,
                        id="sw-auto-cleanup"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Notify on completion:", classes="form-label")
                    yield Switch(
                        value=self.settings.update_preferences.notify_on_complete,
                        id="sw-notify-complete"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Notify on errors:", classes="form-label")
                    yield Switch(
                        value=self.settings.update_preferences.notify_on_error,
                        id="sw-notify-error"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Skip updates on battery:", classes="form-label")
                    yield Switch(
                        value=self.settings.update_preferences.skip_on_battery,
                        id="sw-skip-battery"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Minimum battery percent:", classes="form-label")
                    yield Input(
                        str(self.settings.update_preferences.min_battery_percent),
                        type="integer",
                        id="inp-min-battery"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Minimum disk space (GB):", classes="form-label")
                    yield Input(
                        str(self.settings.update_preferences.min_disk_space_gb),
                        type="number",
                        id="inp-min-disk"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Show backup reminder:", classes="form-label")
                    yield Switch(
                        value=self.settings.update_preferences.backup_reminder,
                        id="sw-backup-reminder"
                    )

            # Enabled Managers
            with Container(classes="settings-section"):
                yield Static("Default Enabled Managers", classes="section-title")

                with Horizontal(classes="form-row"):
                    yield Label("macOS System Updates:", classes="form-label")
                    yield Switch(
                        value=self.settings.enabled_managers.macos,
                        id="sw-mgr-macos"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Homebrew:", classes="form-label")
                    yield Switch(
                        value=self.settings.enabled_managers.homebrew,
                        id="sw-mgr-homebrew"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("App Store:", classes="form-label")
                    yield Switch(
                        value=self.settings.enabled_managers.appstore,
                        id="sw-mgr-appstore"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Python pip:", classes="form-label")
                    yield Switch(
                        value=self.settings.enabled_managers.pip,
                        id="sw-mgr-pip"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Node.js npm:", classes="form-label")
                    yield Switch(
                        value=self.settings.enabled_managers.npm,
                        id="sw-mgr-npm"
                    )

            # UI Preferences
            with Container(classes="settings-section"):
                yield Static("UI Preferences", classes="section-title")

                with Horizontal(classes="form-row"):
                    yield Label("Theme:", classes="form-label")
                    yield Select(
                        [
                            ("Dark", "dark"),
                            ("Light", "light"),
                        ],
                        value=self.settings.ui_preferences.theme,
                        id="sel-theme"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Show system info on dashboard:", classes="form-label")
                    yield Switch(
                        value=self.settings.ui_preferences.show_system_info,
                        id="sw-show-sysinfo"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Compact mode:", classes="form-label")
                    yield Switch(
                        value=self.settings.ui_preferences.compact_mode,
                        id="sw-compact"
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Log lines visible:", classes="form-label")
                    yield Input(
                        str(self.settings.ui_preferences.log_lines_visible),
                        type="integer",
                        id="inp-log-lines"
                    )

            # Excluded Packages
            with Container(classes="settings-section"):
                yield Static("Excluded Packages", classes="section-title")
                yield Static("Enter package names to exclude from updates (one per line):")
                yield TextArea(
                    "\n".join(self.settings.excluded_packages),
                    id="ta-excluded"
                )

            # Custom Homebrew Taps
            with Container(classes="settings-section"):
                yield Static("Custom Homebrew Taps", classes="section-title")
                yield Static("Enter custom Homebrew taps (one per line):")
                yield TextArea(
                    "\n".join(self.settings.custom_brew_taps),
                    id="ta-taps"
                )

            # Action Buttons
            with Horizontal(id="action-buttons"):
                yield Button("Save Settings", variant="success", id="btn-save")
                yield Button("Reset to Defaults", variant="warning", id="btn-reset")
                yield Button("Export Settings", variant="primary", id="btn-export")
                yield Button("Import Settings", variant="primary", id="btn-import")

    def _save_settings(self) -> None:
        """Save all settings from the UI."""
        # Update preferences
        self.settings.update_preferences.auto_cleanup = self.query_one("#sw-auto-cleanup", Switch).value
        self.settings.update_preferences.notify_on_complete = self.query_one("#sw-notify-complete", Switch).value
        self.settings.update_preferences.notify_on_error = self.query_one("#sw-notify-error", Switch).value
        self.settings.update_preferences.skip_on_battery = self.query_one("#sw-skip-battery", Switch).value
        self.settings.update_preferences.backup_reminder = self.query_one("#sw-backup-reminder", Switch).value

        try:
            self.settings.update_preferences.min_battery_percent = int(
                self.query_one("#inp-min-battery", Input).value
            )
            self.settings.update_preferences.min_disk_space_gb = float(
                self.query_one("#inp-min-disk", Input).value
            )
            self.settings.ui_preferences.log_lines_visible = int(
                self.query_one("#inp-log-lines", Input).value
            )
        except ValueError:
            pass

        # Enabled managers
        self.settings.enabled_managers.macos = self.query_one("#sw-mgr-macos", Switch).value
        self.settings.enabled_managers.homebrew = self.query_one("#sw-mgr-homebrew", Switch).value
        self.settings.enabled_managers.appstore = self.query_one("#sw-mgr-appstore", Switch).value
        self.settings.enabled_managers.pip = self.query_one("#sw-mgr-pip", Switch).value
        self.settings.enabled_managers.npm = self.query_one("#sw-mgr-npm", Switch).value

        # UI preferences
        self.settings.ui_preferences.theme = self.query_one("#sel-theme", Select).value
        self.settings.ui_preferences.show_system_info = self.query_one("#sw-show-sysinfo", Switch).value
        self.settings.ui_preferences.compact_mode = self.query_one("#sw-compact", Switch).value

        # Excluded packages and taps
        excluded_text = self.query_one("#ta-excluded", TextArea).text
        self.settings.excluded_packages = [
            pkg.strip() for pkg in excluded_text.split("\n") if pkg.strip()
        ]

        taps_text = self.query_one("#ta-taps", TextArea).text
        self.settings.custom_brew_taps = [
            tap.strip() for tap in taps_text.split("\n") if tap.strip()
        ]

        # Save
        if save_settings(self.settings):
            self.notify("Settings saved successfully!", severity="information")

            # Apply theme change immediately
            if self.settings.ui_preferences.theme == "dark":
                self.app.dark = True
            else:
                self.app.dark = False
        else:
            self.notify("Failed to save settings", severity="error")

    def _reset_settings(self) -> None:
        """Reset settings to defaults."""
        self.settings = reset_settings()
        self.notify("Settings reset to defaults. Please reload the app.", severity="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save":
            self._save_settings()
        elif event.button.id == "btn-reset":
            self._reset_settings()
        elif event.button.id == "btn-export":
            self.notify("Settings exported to ~/.macos-updater/settings.yaml", severity="information")
        elif event.button.id == "btn-import":
            self.notify("Import feature coming soon", severity="information")
