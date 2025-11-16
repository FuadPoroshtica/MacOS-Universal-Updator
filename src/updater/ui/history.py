"""History screen showing update logs and past operations."""

from datetime import datetime
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Button, DataTable, Log
from textual.widget import Widget
import yaml

from ..utils.logging import get_log_directory, get_recent_logs, clear_old_logs
from ..config.settings import load_settings


class HistoryScreen(Widget):
    """Screen for viewing update history and logs."""

    DEFAULT_CSS = """
    HistoryScreen {
        height: 100%;
    }

    #history-container {
        height: 100%;
        padding: 1;
    }

    #stats-section {
        height: auto;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }

    #logs-section {
        height: 1fr;
        border: solid $secondary;
        padding: 1;
    }

    .section-title {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }

    #action-buttons {
        height: auto;
        padding: 1;
    }

    .stat-item {
        padding: 0 2;
    }

    .stat-value {
        text-style: bold;
        color: $accent;
    }

    #log-viewer {
        height: 100%;
        border: solid $primary-darken-3;
        background: $surface-darken-1;
    }

    DataTable {
        height: 15;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()
        self.history_data = []

    def compose(self) -> ComposeResult:
        with Vertical(id="history-container"):
            yield Static("Update History", classes="title")
            yield Static("View past updates and system logs", classes="subtitle")

            # Statistics Section
            with Container(id="stats-section"):
                yield Static("Statistics", classes="section-title")
                with Horizontal():
                    yield Static("Last Update: ", classes="stat-item")
                    yield Static("Never", id="last-update", classes="stat-value")
                    yield Static("  Total Sessions: ", classes="stat-item")
                    yield Static("0", id="total-sessions", classes="stat-value")
                    yield Static("  Log Files: ", classes="stat-item")
                    yield Static("0", id="log-count", classes="stat-value")

            # Recent Updates Table
            with Container(classes="settings-section"):
                yield Static("Recent Update Sessions", classes="section-title")
                yield DataTable(id="history-table")

            # Log Viewer
            with Container(id="logs-section"):
                yield Static("Log Viewer", classes="section-title")
                yield Log(id="log-viewer", highlight=True, markup=True)

            # Action Buttons
            with Horizontal(id="action-buttons"):
                yield Button("Refresh", variant="primary", id="btn-refresh")
                yield Button("Clear Old Logs", variant="warning", id="btn-clear-old")
                yield Button("Export Logs", variant="default", id="btn-export")
                yield Button("View Full Log", variant="default", id="btn-view-full")

    def on_mount(self) -> None:
        """Load data when mounted."""
        self._setup_table()
        self._load_data()

    def _setup_table(self) -> None:
        """Setup the history table columns."""
        table = self.query_one("#history-table", DataTable)
        table.add_columns("Date", "Time", "Managers", "Status", "Duration")

    def _load_data(self) -> None:
        """Load all history data."""
        self._load_stats()
        self._load_history_table()
        self._load_recent_logs()

    def _load_stats(self) -> None:
        """Load statistics."""
        # Last update
        last_update_widget = self.query_one("#last-update", Static)
        if self.settings.last_update:
            try:
                dt = datetime.fromisoformat(self.settings.last_update)
                last_update_widget.update(dt.strftime("%Y-%m-%d %H:%M"))
            except Exception:
                last_update_widget.update("Unknown")
        else:
            last_update_widget.update("Never")

        # Count log files
        log_dir = get_log_directory()
        log_files = list(log_dir.glob("updater_*.log"))
        log_count_widget = self.query_one("#log-count", Static)
        log_count_widget.update(str(len(log_files)))

        # Count sessions (estimate from log files)
        total_sessions_widget = self.query_one("#total-sessions", Static)
        total_sessions_widget.update(str(len(log_files)))

    def _load_history_table(self) -> None:
        """Load history into the table."""
        table = self.query_one("#history-table", DataTable)
        table.clear()

        # Load from history file if exists
        history_file = get_log_directory() / "update_history.yaml"

        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    history = yaml.safe_load(f) or []

                for entry in history[-20:]:  # Last 20 entries
                    table.add_row(
                        entry.get("date", "Unknown"),
                        entry.get("time", "Unknown"),
                        entry.get("managers", "Unknown"),
                        entry.get("status", "Unknown"),
                        entry.get("duration", "Unknown")
                    )
            except Exception:
                pass

        # If no history, add placeholder
        if table.row_count == 0:
            table.add_row("No history", "available", "yet", "-", "-")

    def _load_recent_logs(self) -> None:
        """Load recent log entries."""
        log_viewer = self.query_one("#log-viewer", Log)
        log_viewer.clear()

        logs = get_recent_logs(100)

        if not logs:
            log_viewer.write_line("[dim]No recent logs available[/]")
            return

        for line in logs:
            # Color code based on log level
            if "ERROR" in line:
                log_viewer.write_line(f"[red]{line.rstrip()}[/]")
            elif "WARNING" in line:
                log_viewer.write_line(f"[yellow]{line.rstrip()}[/]")
            elif "INFO" in line:
                log_viewer.write_line(f"[green]{line.rstrip()}[/]")
            else:
                log_viewer.write_line(line.rstrip())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-refresh":
            self._load_data()
            self.notify("History refreshed", severity="information")
        elif event.button.id == "btn-clear-old":
            self._clear_old_logs()
        elif event.button.id == "btn-export":
            self._export_logs()
        elif event.button.id == "btn-view-full":
            self._view_full_log()

    def _clear_old_logs(self) -> None:
        """Clear old log files."""
        removed = clear_old_logs(30)
        self.notify(f"Removed {removed} old log file(s)", severity="information")
        self._load_data()

    def _export_logs(self) -> None:
        """Export logs to a file."""
        log_dir = get_log_directory()
        export_file = Path.home() / "Desktop" / f"updater_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        try:
            logs = get_recent_logs(1000)
            with open(export_file, "w") as f:
                f.writelines(logs)
            self.notify(f"Logs exported to {export_file}", severity="information")
        except Exception as e:
            self.notify(f"Failed to export logs: {str(e)}", severity="error")

    def _view_full_log(self) -> None:
        """Open the log directory in Finder."""
        import subprocess
        log_dir = get_log_directory()
        try:
            subprocess.run(["open", str(log_dir)], check=True)
            self.notify(f"Opened {log_dir}", severity="information")
        except Exception:
            self.notify(f"Log directory: {log_dir}", severity="information")


def save_update_history(
    managers: list[str],
    status: str,
    duration: float
) -> None:
    """Save an update session to history."""
    history_file = get_log_directory() / "update_history.yaml"

    # Load existing history
    history = []
    if history_file.exists():
        try:
            with open(history_file, "r") as f:
                history = yaml.safe_load(f) or []
        except Exception:
            pass

    # Add new entry
    now = datetime.now()
    entry = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "managers": ", ".join(managers),
        "status": status,
        "duration": f"{duration:.1f}s"
    }
    history.append(entry)

    # Keep only last 100 entries
    history = history[-100:]

    # Save
    try:
        with open(history_file, "w") as f:
            yaml.dump(history, f, default_flow_style=False)
    except Exception:
        pass
