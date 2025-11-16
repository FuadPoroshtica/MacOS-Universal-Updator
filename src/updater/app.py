"""Main TUI application using Textual framework."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, TabbedContent, TabPane
from textual.containers import Container

from .ui.dashboard import DashboardScreen
from .ui.updates import UpdatesScreen
from .ui.schedule import ScheduleScreen
from .ui.settings import SettingsScreen
from .ui.history import HistoryScreen
from .config.settings import load_settings, save_settings


class UpdaterApp(App):
    """Main macOS Universal Updater TUI application."""

    TITLE = "macOS Universal Updater"
    SUB_TITLE = "Keep your system up to date"

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
        padding: 1;
    }

    TabbedContent {
        height: 100%;
    }

    TabPane {
        padding: 1;
    }

    .title {
        text-style: bold;
        color: $accent;
        text-align: center;
        padding: 1;
    }

    .subtitle {
        color: $text-muted;
        text-align: center;
        padding-bottom: 1;
    }

    .info-box {
        border: solid $primary;
        padding: 1;
        margin: 1;
        height: auto;
    }

    .warning-box {
        border: solid $warning;
        padding: 1;
        margin: 1;
        background: $warning 10%;
    }

    .error-box {
        border: solid $error;
        padding: 1;
        margin: 1;
        background: $error 10%;
    }

    .success-box {
        border: solid $success;
        padding: 1;
        margin: 1;
        background: $success 10%;
    }

    .status-indicator {
        padding: 0 1;
    }

    .status-good {
        color: $success;
    }

    .status-warning {
        color: $warning;
    }

    .status-error {
        color: $error;
    }

    .progress-container {
        height: auto;
        padding: 1;
    }

    Button {
        margin: 1;
    }

    Button.primary {
        background: $primary;
    }

    Button.success {
        background: $success;
    }

    Button.warning {
        background: $warning;
    }

    Button.error {
        background: $error;
    }

    .log-output {
        height: 100%;
        border: solid $primary-darken-2;
        background: $surface-darken-1;
        padding: 1;
    }

    DataTable {
        height: 100%;
    }

    .section-title {
        text-style: bold;
        color: $text;
        padding: 1 0;
    }

    .metric {
        padding: 0 2;
    }

    .metric-value {
        text-style: bold;
        color: $accent;
    }

    .package-list {
        height: 1fr;
        border: solid $primary-darken-2;
    }

    Switch {
        margin: 1 0;
    }

    Input {
        margin: 1 0;
    }

    Select {
        margin: 1 0;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("d", "switch_tab('dashboard')", "Dashboard"),
        Binding("u", "switch_tab('updates')", "Updates"),
        Binding("s", "switch_tab('schedule')", "Schedule"),
        Binding("c", "switch_tab('settings')", "Settings"),
        Binding("h", "switch_tab('history')", "History"),
        Binding("r", "refresh", "Refresh"),
        Binding("?", "help", "Help"),
    ]

    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.dark = self.settings.ui_preferences.theme == "dark"

    def compose(self) -> ComposeResult:
        """Create the main application layout."""
        yield Header(show_clock=True)

        with Container(id="main-container"):
            with TabbedContent(initial="dashboard"):
                with TabPane("Dashboard", id="dashboard"):
                    yield DashboardScreen()
                with TabPane("Updates", id="updates"):
                    yield UpdatesScreen()
                with TabPane("Schedule", id="schedule"):
                    yield ScheduleScreen()
                with TabPane("Settings", id="settings"):
                    yield SettingsScreen()
                with TabPane("History", id="history"):
                    yield HistoryScreen()

        yield Footer()

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab."""
        tabbed_content = self.query_one(TabbedContent)
        tabbed_content.active = tab_id

    def action_refresh(self) -> None:
        """Refresh the current view."""
        # Get the active tab and refresh it
        tabbed_content = self.query_one(TabbedContent)
        active_tab = tabbed_content.active

        if active_tab == "dashboard":
            dashboard = self.query_one(DashboardScreen)
            dashboard.refresh_data()
        elif active_tab == "updates":
            updates = self.query_one(UpdatesScreen)
            updates.check_all_updates()

    def action_help(self) -> None:
        """Show help information."""
        self.push_screen(HelpScreen())

    def on_mount(self) -> None:
        """Called when app is mounted."""
        # Mark first run as complete
        if self.settings.first_run:
            self.settings.first_run = False
            save_settings(self.settings)

        # Set theme
        if self.settings.ui_preferences.theme == "light":
            self.dark = False
        else:
            self.dark = True


class HelpScreen(App):
    """Help screen modal."""

    def compose(self) -> ComposeResult:
        from textual.widgets import Static, Button
        from textual.containers import Vertical, Center

        with Center():
            with Vertical(classes="info-box"):
                yield Static("# macOS Universal Updater Help", classes="title")
                yield Static("""
## Keyboard Shortcuts

- **d** - Dashboard view
- **u** - Updates view
- **s** - Schedule view
- **c** - Settings view
- **h** - History view
- **r** - Refresh current view
- **q** - Quit application
- **?** - Show this help

## Features

- Update macOS system software
- Update Homebrew packages and casks
- Update Mac App Store applications
- Update Python pip packages
- Update Node.js npm packages
- Schedule automatic updates
- Track update history
- System health monitoring

## Tips

- Use the Updates tab to select which managers to run
- Configure excluded packages in Settings
- Set up scheduled updates in the Schedule tab
- Monitor system health in the Dashboard
""")
                yield Button("Close", variant="primary", id="close-help")

    def on_button_pressed(self, event) -> None:
        if event.button.id == "close-help":
            self.app.pop_screen()


def run_app():
    """Run the TUI application."""
    app = UpdaterApp()
    app.run()


if __name__ == "__main__":
    run_app()
