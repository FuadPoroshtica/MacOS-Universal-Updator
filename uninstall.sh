#!/bin/bash
#
# macOS Universal Updater - Uninstallation Script
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="$HOME/.macos-updater"
BIN_DIR="$HOME/.local/bin"

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════╗"
echo "║    macOS Universal Updater Uninstallation     ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${NC}"

# Confirm uninstallation
echo -e "${YELLOW}This will remove:${NC}"
echo "  - Application files in $INSTALL_DIR"
echo "  - Launcher scripts in $BIN_DIR"
echo "  - Scheduled update service (if installed)"
echo ""
echo -e "${YELLOW}Your configuration and logs will be preserved.${NC}"
echo ""

read -p "Are you sure you want to uninstall? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Remove scheduled service if installed
echo -e "${BLUE}Removing scheduled service...${NC}"
PLIST_FILE="$HOME/Library/LaunchAgents/com.macos-updater.scheduled.plist"
if [[ -f "$PLIST_FILE" ]]; then
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    rm -f "$PLIST_FILE"
    echo -e "${GREEN}✓ Scheduled service removed${NC}"
else
    echo -e "${GREEN}✓ No scheduled service found${NC}"
fi

# Remove launcher scripts
echo -e "${BLUE}Removing launcher scripts...${NC}"
rm -f "$BIN_DIR/macos-updater"
rm -f "$BIN_DIR/updater"
echo -e "${GREEN}✓ Launcher scripts removed${NC}"

# Remove application files (keep config and logs)
echo -e "${BLUE}Removing application files...${NC}"
rm -rf "$INSTALL_DIR/src"
rm -rf "$INSTALL_DIR/scripts"
rm -rf "$INSTALL_DIR/venv"
rm -f "$INSTALL_DIR/requirements.txt"
rm -f "$INSTALL_DIR/pyproject.toml"
rm -f "$INSTALL_DIR/run_scheduled.py"
echo -e "${GREEN}✓ Application files removed${NC}"

# Ask about config/logs
echo ""
read -p "Do you also want to remove configuration and logs? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$INSTALL_DIR"
    echo -e "${GREEN}✓ Configuration and logs removed${NC}"
else
    echo -e "${YELLOW}Configuration and logs preserved in $INSTALL_DIR${NC}"
fi

echo -e "\n${GREEN}"
echo "╔════════════════════════════════════════════════╗"
echo "║        Uninstallation Complete! 👋            ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${NC}"

echo "macOS Universal Updater has been removed."
echo "Thank you for using the application!"
