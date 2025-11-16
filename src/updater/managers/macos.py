"""macOS system software update manager."""

import shutil
import asyncio
import re
from typing import AsyncIterator
from .base import BaseUpdateManager


class MacOSUpdateManager(BaseUpdateManager):
    """Manager for macOS system software updates."""

    @property
    def name(self) -> str:
        return "macos"

    @property
    def display_name(self) -> str:
        return "macOS System"

    @property
    def icon(self) -> str:
        return "🍎"

    async def is_available(self) -> bool:
        """Check if softwareupdate is available."""
        return shutil.which("softwareupdate") is not None

    async def check_updates(self) -> tuple[int, list[str]]:
        """Check for available macOS system updates."""
        self.report_progress("Checking for system updates...", 0.1)

        returncode, stdout, stderr = await self.run_command_simple(
            ["softwareupdate", "--list"],
            timeout=120
        )

        if returncode != 0 and "No new software available" not in stderr:
            self.logger.error(f"Failed to check macOS updates: {stderr}")
            return 0, []

        # Parse the output for available updates
        packages = []
        lines = stdout.split("\n") + stderr.split("\n")

        for line in lines:
            # Look for lines that indicate an update
            if "* Label:" in line or line.strip().startswith("* "):
                # Extract package name
                if "Label:" in line:
                    package = line.split("Label:")[-1].strip()
                else:
                    package = line.strip().lstrip("* ").strip()
                if package:
                    packages.append(package)

        # Also check for "Title:" lines as alternative format
        in_update_block = False
        for line in lines:
            if line.strip().startswith("*"):
                in_update_block = True
            elif "Title:" in line and in_update_block:
                title = line.split("Title:")[-1].strip()
                if title and title not in packages:
                    packages.append(title)
            elif line.strip() == "" and in_update_block:
                in_update_block = False

        return len(packages), packages

    async def perform_updates(self) -> AsyncIterator[str]:
        """Perform macOS system updates."""
        yield "Starting macOS system update..."
        yield "Note: This may require administrator privileges and a restart."

        self.report_progress("Installing system updates...", 0.3)

        # Run softwareupdate with verbose output
        async for line in self.run_command(
            ["softwareupdate", "--install", "--all", "--verbose"],
            timeout=3600  # System updates can take a long time
        ):
            yield line

            # Check for reboot requirement
            if "restart" in line.lower() or "reboot" in line.lower():
                self._requires_reboot = True

            if self._cancelled:
                return

        yield "macOS system update completed!"

        if hasattr(self, "_requires_reboot") and self._requires_reboot:
            yield "\n⚠️  A restart is required to complete some updates."

    async def update(self):
        """Override to track reboot requirement."""
        self._requires_reboot = False
        result = await super().update()
        result.requires_reboot = getattr(self, "_requires_reboot", False)
        return result

    async def get_system_version(self) -> dict:
        """Get detailed macOS version information."""
        info = {
            "product_name": "macOS",
            "product_version": "Unknown",
            "build_version": "Unknown"
        }

        # Get product version
        returncode, stdout, _ = await self.run_command_simple(
            ["sw_vers", "-productVersion"]
        )
        if returncode == 0:
            info["product_version"] = stdout.strip()

        # Get build version
        returncode, stdout, _ = await self.run_command_simple(
            ["sw_vers", "-buildVersion"]
        )
        if returncode == 0:
            info["build_version"] = stdout.strip()

        # Get product name
        returncode, stdout, _ = await self.run_command_simple(
            ["sw_vers", "-productName"]
        )
        if returncode == 0:
            info["product_name"] = stdout.strip()

        return info

    async def list_recommended_updates(self) -> list[dict]:
        """Get list of recommended updates with details."""
        updates = []

        returncode, stdout, stderr = await self.run_command_simple(
            ["softwareupdate", "--list", "--all"],
            timeout=120
        )

        output = stdout + "\n" + stderr

        # Parse output to extract update details
        current_update = {}
        for line in output.split("\n"):
            line = line.strip()

            if line.startswith("* "):
                if current_update:
                    updates.append(current_update)
                current_update = {"name": line[2:].strip()}
            elif "Title:" in line:
                current_update["title"] = line.split("Title:")[-1].strip()
            elif "Version:" in line:
                current_update["version"] = line.split("Version:")[-1].strip()
            elif "Size:" in line:
                current_update["size"] = line.split("Size:")[-1].strip()
            elif "Recommended:" in line:
                current_update["recommended"] = "YES" in line.upper()
            elif "Action:" in line:
                current_update["action"] = line.split("Action:")[-1].strip()

        if current_update:
            updates.append(current_update)

        return updates

    async def install_specific_update(self, update_name: str) -> AsyncIterator[str]:
        """Install a specific update by name."""
        yield f"Installing {update_name}..."

        async for line in self.run_command(
            ["softwareupdate", "--install", update_name, "--verbose"],
            timeout=3600
        ):
            yield line
