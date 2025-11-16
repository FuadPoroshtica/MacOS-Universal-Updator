"""Homebrew package manager update manager."""

import shutil
import asyncio
from typing import AsyncIterator
from .base import BaseUpdateManager


class HomebrewManager(BaseUpdateManager):
    """Manager for Homebrew package updates."""

    @property
    def name(self) -> str:
        return "homebrew"

    @property
    def display_name(self) -> str:
        return "Homebrew"

    @property
    def icon(self) -> str:
        return "🍺"

    async def is_available(self) -> bool:
        """Check if Homebrew is installed."""
        return shutil.which("brew") is not None

    async def check_updates(self) -> tuple[int, list[str]]:
        """Check for outdated Homebrew packages."""
        # First update the formula index
        self.report_progress("Updating Homebrew formulae...", 0.1)
        await self.run_command_simple(["brew", "update"])

        # Check for outdated packages
        self.report_progress("Checking for outdated packages...", 0.2)
        returncode, stdout, stderr = await self.run_command_simple(
            ["brew", "outdated", "--verbose"]
        )

        if returncode != 0:
            self.logger.error(f"Failed to check Homebrew updates: {stderr}")
            return 0, []

        packages = []
        for line in stdout.strip().split("\n"):
            if line.strip():
                # Extract package name (first word)
                package_name = line.split()[0] if line.split() else ""
                if package_name:
                    packages.append(package_name)

        return len(packages), packages

    async def perform_updates(self) -> AsyncIterator[str]:
        """Perform Homebrew updates."""
        yield "Starting Homebrew upgrade..."

        # Upgrade all packages
        self.report_progress("Upgrading packages...", 0.4)
        async for line in self.run_command(["brew", "upgrade"], timeout=600):
            yield line
            if self._cancelled:
                return

        # Upgrade casks
        yield "\nUpgrading casks..."
        self.report_progress("Upgrading casks...", 0.7)
        async for line in self.run_command(["brew", "upgrade", "--cask"], timeout=600):
            yield line
            if self._cancelled:
                return

        # Cleanup old versions
        yield "\nCleaning up old versions..."
        self.report_progress("Cleaning up...", 0.9)
        async for line in self.run_command(["brew", "cleanup", "--prune=7"], timeout=120):
            yield line

        yield "Homebrew upgrade completed!"

    async def get_info(self) -> dict:
        """Get Homebrew information."""
        info = {
            "version": "Unknown",
            "formulae_count": 0,
            "cask_count": 0,
            "prefix": "/usr/local"
        }

        # Get version
        returncode, stdout, _ = await self.run_command_simple(["brew", "--version"])
        if returncode == 0:
            info["version"] = stdout.split("\n")[0].strip()

        # Get installed formulae count
        returncode, stdout, _ = await self.run_command_simple(["brew", "list", "--formula", "-1"])
        if returncode == 0:
            info["formulae_count"] = len([l for l in stdout.strip().split("\n") if l])

        # Get installed casks count
        returncode, stdout, _ = await self.run_command_simple(["brew", "list", "--cask", "-1"])
        if returncode == 0:
            info["cask_count"] = len([l for l in stdout.strip().split("\n") if l])

        # Get prefix
        returncode, stdout, _ = await self.run_command_simple(["brew", "--prefix"])
        if returncode == 0:
            info["prefix"] = stdout.strip()

        return info

    async def doctor(self) -> list[str]:
        """Run brew doctor and return issues."""
        issues = []
        returncode, stdout, stderr = await self.run_command_simple(
            ["brew", "doctor"],
            timeout=120
        )

        if returncode != 0:
            for line in stdout.split("\n"):
                if line.strip() and not line.startswith("Please note"):
                    issues.append(line.strip())

        return issues
