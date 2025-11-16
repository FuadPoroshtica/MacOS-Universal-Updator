"""Node.js npm package manager update manager."""

import shutil
import json
from typing import AsyncIterator
from .base import BaseUpdateManager


class NpmManager(BaseUpdateManager):
    """Manager for global npm package updates."""

    @property
    def name(self) -> str:
        return "npm"

    @property
    def display_name(self) -> str:
        return "Node.js Packages"

    @property
    def icon(self) -> str:
        return "📦"

    async def is_available(self) -> bool:
        """Check if npm is installed."""
        return shutil.which("npm") is not None

    async def check_updates(self) -> tuple[int, list[str]]:
        """Check for outdated global npm packages."""
        self.report_progress("Checking for outdated npm packages...", 0.1)

        returncode, stdout, stderr = await self.run_command_simple(
            ["npm", "outdated", "-g", "--json"],
            timeout=120
        )

        # npm outdated returns non-zero when packages are outdated
        if returncode != 0 and not stdout.strip():
            # If no output and error, there's a real problem
            if stderr.strip():
                self.logger.warning(f"npm check warning: {stderr}")
            return 0, []

        packages = []
        if stdout.strip():
            try:
                data = json.loads(stdout)
                packages = list(data.keys())
            except json.JSONDecodeError:
                # Fallback to non-JSON output
                for line in stdout.strip().split("\n"):
                    if line.strip() and not line.startswith("Package"):
                        parts = line.split()
                        if parts:
                            packages.append(parts[0])

        return len(packages), packages

    async def perform_updates(self) -> AsyncIterator[str]:
        """Perform npm package updates."""
        yield "Starting npm global package updates..."

        # First, get list of outdated packages
        self.report_progress("Getting outdated packages...", 0.2)
        returncode, stdout, _ = await self.run_command_simple(
            ["npm", "outdated", "-g", "--json"],
            timeout=120
        )

        packages = []
        if stdout.strip():
            try:
                data = json.loads(stdout)
                packages = list(data.keys())
            except json.JSONDecodeError:
                pass

        if not packages:
            yield "No packages to update."
            return

        yield f"Found {len(packages)} package(s) to update."

        # Update npm itself first if outdated
        if "npm" in packages:
            yield "\nUpgrading npm..."
            self.report_progress("Upgrading npm...", 0.3)
            async for line in self.run_command(
                ["npm", "install", "-g", "npm@latest"],
                timeout=300
            ):
                yield line

            if self._cancelled:
                return

            packages.remove("npm")

        # Update remaining packages
        total = len(packages)
        for i, package in enumerate(packages):
            progress = 0.3 + (0.7 * (i / total))
            self.report_progress(f"Upgrading {package}...", progress)
            yield f"\nUpgrading {package} ({i+1}/{total})..."

            async for line in self.run_command(
                ["npm", "install", "-g", f"{package}@latest"],
                timeout=300
            ):
                yield line

            if self._cancelled:
                return

        yield "\nnpm global package updates completed!"

    async def get_npm_version(self) -> tuple[str, str]:
        """Get npm and Node.js versions."""
        npm_version = "Unknown"
        node_version = "Unknown"

        returncode, stdout, _ = await self.run_command_simple(["npm", "--version"])
        if returncode == 0:
            npm_version = stdout.strip()

        returncode, stdout, _ = await self.run_command_simple(["node", "--version"])
        if returncode == 0:
            node_version = stdout.strip()

        return npm_version, node_version

    async def get_global_packages(self) -> list[dict]:
        """Get list of globally installed npm packages."""
        packages = []

        returncode, stdout, _ = await self.run_command_simple(
            ["npm", "list", "-g", "--depth=0", "--json"],
            timeout=60
        )

        if returncode == 0:
            try:
                data = json.loads(stdout)
                deps = data.get("dependencies", {})
                for name, info in deps.items():
                    packages.append({
                        "name": name,
                        "version": info.get("version", "Unknown")
                    })
            except json.JSONDecodeError:
                pass

        return packages

    async def get_outdated_packages(self) -> list[dict]:
        """Get detailed information about outdated packages."""
        packages = []

        returncode, stdout, _ = await self.run_command_simple(
            ["npm", "outdated", "-g", "--json"],
            timeout=120
        )

        if stdout.strip():
            try:
                data = json.loads(stdout)
                for name, info in data.items():
                    packages.append({
                        "name": name,
                        "current_version": info.get("current", "Unknown"),
                        "wanted_version": info.get("wanted", "Unknown"),
                        "latest_version": info.get("latest", "Unknown"),
                        "location": info.get("location", "global")
                    })
            except json.JSONDecodeError:
                pass

        return packages

    async def clear_cache(self) -> AsyncIterator[str]:
        """Clear npm cache."""
        yield "Clearing npm cache..."

        async for line in self.run_command(
            ["npm", "cache", "clean", "--force"],
            timeout=120
        ):
            yield line

        yield "npm cache cleared!"
