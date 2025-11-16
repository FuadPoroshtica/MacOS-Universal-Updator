"""Mac App Store update manager using mas CLI."""

import shutil
import asyncio
from typing import AsyncIterator
from .base import BaseUpdateManager


class AppStoreManager(BaseUpdateManager):
    """Manager for Mac App Store application updates."""

    @property
    def name(self) -> str:
        return "appstore"

    @property
    def display_name(self) -> str:
        return "App Store"

    @property
    def icon(self) -> str:
        return "🛍️"

    async def is_available(self) -> bool:
        """Check if mas (Mac App Store CLI) is installed."""
        return shutil.which("mas") is not None

    async def check_updates(self) -> tuple[int, list[str]]:
        """Check for App Store updates."""
        self.report_progress("Checking App Store updates...", 0.1)

        returncode, stdout, stderr = await self.run_command_simple(
            ["mas", "outdated"],
            timeout=60
        )

        if returncode != 0:
            self.logger.error(f"Failed to check App Store updates: {stderr}")
            return 0, []

        packages = []
        for line in stdout.strip().split("\n"):
            if line.strip():
                # Format: "app_id  app_name (old_version -> new_version)"
                parts = line.split(maxsplit=1)
                if len(parts) >= 2:
                    app_name = parts[1].split("(")[0].strip()
                    packages.append(app_name)

        return len(packages), packages

    async def perform_updates(self) -> AsyncIterator[str]:
        """Perform App Store updates."""
        yield "Starting App Store updates..."

        self.report_progress("Upgrading App Store applications...", 0.4)

        async for line in self.run_command(
            ["mas", "upgrade"],
            timeout=1800  # App Store updates can be large
        ):
            yield line

            if self._cancelled:
                return

        yield "App Store updates completed!"

    async def get_installed_apps(self) -> list[dict]:
        """Get list of installed App Store apps."""
        apps = []

        returncode, stdout, _ = await self.run_command_simple(
            ["mas", "list"],
            timeout=30
        )

        if returncode == 0:
            for line in stdout.strip().split("\n"):
                if line.strip():
                    parts = line.split(maxsplit=2)
                    if len(parts) >= 2:
                        app_id = parts[0]
                        rest = parts[1] if len(parts) == 2 else parts[1] + " " + parts[2]
                        # Extract name and version
                        if "(" in rest:
                            name = rest.split("(")[0].strip()
                            version = rest.split("(")[-1].rstrip(")")
                        else:
                            name = rest
                            version = "Unknown"
                        apps.append({
                            "id": app_id,
                            "name": name,
                            "version": version
                        })

        return apps

    async def get_outdated_apps(self) -> list[dict]:
        """Get detailed information about outdated apps."""
        apps = []

        returncode, stdout, _ = await self.run_command_simple(
            ["mas", "outdated"],
            timeout=60
        )

        if returncode == 0:
            for line in stdout.strip().split("\n"):
                if line.strip():
                    parts = line.split(maxsplit=1)
                    if len(parts) >= 2:
                        app_id = parts[0]
                        rest = parts[1]

                        # Parse "AppName (1.0 -> 2.0)" format
                        if "(" in rest and "->" in rest:
                            name = rest.split("(")[0].strip()
                            versions = rest.split("(")[-1].rstrip(")")
                            if "->" in versions:
                                old_ver, new_ver = versions.split("->")
                                apps.append({
                                    "id": app_id,
                                    "name": name,
                                    "current_version": old_ver.strip(),
                                    "new_version": new_ver.strip()
                                })
                        else:
                            apps.append({
                                "id": app_id,
                                "name": rest,
                                "current_version": "Unknown",
                                "new_version": "Available"
                            })

        return apps

    async def upgrade_specific_app(self, app_id: str) -> AsyncIterator[str]:
        """Upgrade a specific app by ID."""
        yield f"Upgrading app {app_id}..."

        async for line in self.run_command(
            ["mas", "upgrade", app_id],
            timeout=600
        ):
            yield line

    async def search_app(self, query: str) -> list[dict]:
        """Search for apps in the App Store."""
        apps = []

        returncode, stdout, _ = await self.run_command_simple(
            ["mas", "search", query],
            timeout=30
        )

        if returncode == 0:
            for line in stdout.strip().split("\n")[:10]:  # Limit to 10 results
                if line.strip():
                    parts = line.split(maxsplit=1)
                    if len(parts) >= 2:
                        apps.append({
                            "id": parts[0],
                            "name": parts[1].strip()
                        })

        return apps
