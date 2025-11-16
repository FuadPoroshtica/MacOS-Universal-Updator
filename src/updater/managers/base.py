"""Base update manager class."""

import asyncio
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, AsyncIterator, Callable
from ..utils.logging import get_logger


class UpdateStatus(Enum):
    """Status of an update operation."""
    PENDING = "pending"
    CHECKING = "checking"
    UPDATING = "updating"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class UpdateResult:
    """Result of an update operation."""
    manager_name: str
    status: UpdateStatus
    packages_updated: int = 0
    packages_available: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    output_log: list[str] = field(default_factory=list)
    error_message: Optional[str] = None
    requires_reboot: bool = False

    @property
    def duration(self) -> Optional[float]:
        """Get the duration of the update in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class BaseUpdateManager(ABC):
    """Base class for all update managers."""

    def __init__(self):
        self.logger = get_logger()
        self._cancelled = False
        self._progress_callback: Optional[Callable[[str, float], None]] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the update manager."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable display name."""
        pass

    @property
    @abstractmethod
    def icon(self) -> str:
        """Icon/emoji for the manager."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this update manager is available on the system."""
        pass

    @abstractmethod
    async def check_updates(self) -> tuple[int, list[str]]:
        """
        Check for available updates.

        Returns:
            Tuple of (number of updates available, list of package names)
        """
        pass

    @abstractmethod
    async def perform_updates(self) -> AsyncIterator[str]:
        """
        Perform the updates, yielding log lines.

        Yields:
            Log lines as the update progresses
        """
        pass

    def set_progress_callback(self, callback: Callable[[str, float], None]) -> None:
        """Set a callback for progress updates."""
        self._progress_callback = callback

    def report_progress(self, message: str, percentage: float) -> None:
        """Report progress to the callback."""
        if self._progress_callback:
            self._progress_callback(message, percentage)

    def cancel(self) -> None:
        """Request cancellation of the current operation."""
        self._cancelled = True
        self.logger.info(f"{self.name}: Cancellation requested")

    def reset_cancel(self) -> None:
        """Reset the cancellation flag."""
        self._cancelled = False

    async def run_command(
        self,
        command: list[str],
        timeout: int = 300,
        env: Optional[dict] = None
    ) -> AsyncIterator[str]:
        """
        Run a command asynchronously and yield output lines.

        Args:
            command: Command and arguments to run
            timeout: Timeout in seconds
            env: Optional environment variables

        Yields:
            Output lines from the command
        """
        self.logger.debug(f"Running command: {' '.join(command)}")

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env
        )

        try:
            while True:
                if self._cancelled:
                    process.terminate()
                    yield "Operation cancelled by user"
                    break

                line = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=timeout
                )

                if not line:
                    break

                decoded_line = line.decode("utf-8", errors="replace").rstrip()
                if decoded_line:
                    yield decoded_line

            await process.wait()

        except asyncio.TimeoutError:
            process.terminate()
            yield f"Command timed out after {timeout} seconds"
            self.logger.error(f"Command timed out: {' '.join(command)}")
        except Exception as e:
            process.terminate()
            yield f"Error: {str(e)}"
            self.logger.error(f"Command error: {str(e)}")

    async def run_command_simple(
        self,
        command: list[str],
        timeout: int = 60
    ) -> tuple[int, str, str]:
        """
        Run a simple command and return the result.

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            return (
                process.returncode,
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace")
            )
        except asyncio.TimeoutError:
            return (-1, "", "Command timed out")
        except Exception as e:
            return (-1, "", str(e))

    async def update(self) -> UpdateResult:
        """
        Run the complete update process.

        Returns:
            UpdateResult with details of the operation
        """
        self.reset_cancel()
        result = UpdateResult(
            manager_name=self.name,
            status=UpdateStatus.PENDING,
            start_time=datetime.now()
        )

        self.logger.info(f"{self.name}: Starting update process")

        # Check if available
        if not await self.is_available():
            result.status = UpdateStatus.SKIPPED
            result.error_message = f"{self.display_name} is not available on this system"
            result.end_time = datetime.now()
            self.logger.warning(result.error_message)
            return result

        # Check for updates
        result.status = UpdateStatus.CHECKING
        self.report_progress("Checking for updates...", 0.1)

        try:
            num_updates, packages = await self.check_updates()
            result.packages_available = num_updates
            result.output_log.append(f"Found {num_updates} update(s) available")

            if num_updates == 0:
                result.status = UpdateStatus.COMPLETED
                result.end_time = datetime.now()
                self.logger.info(f"{self.name}: No updates available")
                return result

            # Perform updates
            result.status = UpdateStatus.UPDATING
            self.report_progress("Installing updates...", 0.3)

            async for line in self.perform_updates():
                result.output_log.append(line)
                if self._cancelled:
                    result.status = UpdateStatus.CANCELLED
                    break

            if result.status != UpdateStatus.CANCELLED:
                result.status = UpdateStatus.COMPLETED
                result.packages_updated = num_updates
                self.report_progress("Updates complete", 1.0)

            result.end_time = datetime.now()
            self.logger.info(
                f"{self.name}: Update completed. "
                f"{result.packages_updated}/{result.packages_available} packages updated"
            )

        except Exception as e:
            result.status = UpdateStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            self.logger.error(f"{self.name}: Update failed - {str(e)}")

        return result
