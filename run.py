#!/usr/bin/env python3
"""
Quick launcher for macOS Universal Updater.
Run this directly without installation for development/testing.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from updater.app import UpdaterApp


def main():
    """Launch the TUI application."""
    app = UpdaterApp()
    app.run()


if __name__ == "__main__":
    main()
