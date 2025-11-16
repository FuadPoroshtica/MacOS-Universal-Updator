"""Python pip package manager update manager."""

import shutil
import asyncio
from typing import AsyncIterator
from .base import BaseUpdateManager


class PipManager(BaseUpdateManager):
    """Manager for Python pip package updates."""

    @property
    def name(self) -> str:
        return "pip"

    @property
    def display_name(self) -> str:
        return "Python Packages"

    @property
    def icon(self) -> str:
        return "🐍"

    async def is_available(self) -> bool:
        """Check if pip is installed."""
        return shutil.which("pip3") is not None or shutil.which("pip") is not None

    def _get_pip_command(self) -> str:
        """Get the pip command to use."""
        if shutil.which("pip3"):
            return "pip3"
        return "pip"

    async def check_updates(self) -> tuple[int, list[str]]:
        """Check for outdated pip packages."""
        self.report_progress("Checking for outdated Python packages...", 0.1)

        pip_cmd = self._get_pip_command()

        # Use JSON format which works reliably
        returncode, stdout, stderr = await self.run_command_simple(
            [pip_cmd, "list", "--outdated", "--format=json"],
            timeout=120
        )

        packages = []
        if returncode == 0 and stdout.strip():
            try:
                import json
                data = json.loads(stdout)
                for pkg in data:
                    packages.append(pkg.get("name", "Unknown"))
            except Exception:
                pass

        # Fallback to tabular format if JSON fails
        if not packages and returncode != 0:
            self.logger.warning(f"pip check returned non-zero: {stderr}")
            returncode, stdout, stderr = await self.run_command_simple(
                [pip_cmd, "list", "--outdated"],
                timeout=120
            )

            for line in stdout.strip().split("\n"):
                if line.strip() and not line.startswith("Package") and not line.startswith("-"):
                    parts = line.split()
                    if parts and len(parts) >= 1:
                        packages.append(parts[0])

        return len(packages), packages

    async def perform_updates(self) -> AsyncIterator[str]:
        """Perform pip package updates."""
        yield "Starting Python package updates..."

        pip_cmd = self._get_pip_command()

        # First, get list of outdated packages
        self.report_progress("Getting outdated packages...", 0.2)
        returncode, stdout, _ = await self.run_command_simple(
            [pip_cmd, "list", "--outdated", "--format=json"],
            timeout=120
        )

        packages = []
        if stdout.strip():
            try:
                import json
                data = json.loads(stdout)
                for pkg in data:
                    packages.append(pkg.get("name", "Unknown"))
            except Exception:
                pass

        if not packages:
            yield "No packages to update."
            return

        yield f"Found {len(packages)} package(s) to update."

        # Update pip itself first
        yield "\nUpgrading pip..."
        self.report_progress("Upgrading pip...", 0.3)
        async for line in self.run_command(
            [pip_cmd, "install", "--upgrade", "pip"],
            timeout=120
        ):
            yield line

        if self._cancelled:
            return

        # Update packages
        total = len(packages)
        for i, package in enumerate(packages):
            progress = 0.3 + (0.7 * (i / total))
            self.report_progress(f"Upgrading {package}...", progress)
            yield f"\nUpgrading {package} ({i+1}/{total})..."

            async for line in self.run_command(
                [pip_cmd, "install", "--upgrade", package],
                timeout=300
            ):
                yield line

            if self._cancelled:
                return

        yield "\nPython package updates completed!"

    async def get_pip_version(self) -> str:
        """Get pip version."""
        pip_cmd = self._get_pip_command()
        returncode, stdout, _ = await self.run_command_simple([pip_cmd, "--version"])

        if returncode == 0:
            return stdout.strip()
        return "Unknown"

    async def get_installed_packages(self) -> list[dict]:
        """Get list of installed pip packages."""
        pip_cmd = self._get_pip_command()
        packages = []

        returncode, stdout, _ = await self.run_command_simple(
            [pip_cmd, "list", "--format=freeze"],
            timeout=60
        )

        if returncode == 0:
            for line in stdout.strip().split("\n"):
                if "==" in line:
                    parts = line.split("==")
                    packages.append({
                        "name": parts[0].strip(),
                        "version": parts[1].strip() if len(parts) > 1 else "Unknown"
                    })

        return packages

    async def get_outdated_packages(self) -> list[dict]:
        """Get detailed information about outdated packages."""
        pip_cmd = self._get_pip_command()
        packages = []

        returncode, stdout, _ = await self.run_command_simple(
            [pip_cmd, "list", "--outdated", "--format=json"],
            timeout=120
        )

        if returncode == 0:
            try:
                import json
                data = json.loads(stdout)
                for pkg in data:
                    packages.append({
                        "name": pkg.get("name", "Unknown"),
                        "current_version": pkg.get("version", "Unknown"),
                        "new_version": pkg.get("latest_version", "Unknown"),
                        "type": pkg.get("latest_filetype", "Unknown")
                    })
            except Exception:
                pass

        return packages
