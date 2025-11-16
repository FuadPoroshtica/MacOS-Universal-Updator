#!/bin/bash
#
# macOS Universal Updater - Installation Script
#
# This script installs the macOS Universal Updater TUI application.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="macOS Universal Updater"
INSTALL_DIR="$HOME/.macos-updater"
BIN_DIR="$HOME/.local/bin"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════╗"
echo "║     macOS Universal Updater Installation       ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Error: This application is designed for macOS only.${NC}"
    exit 1
fi

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3.9 or later from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 9 ]]; then
    echo -e "${RED}Error: Python 3.9 or later is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check for pip
echo -e "${BLUE}Checking pip...${NC}"
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip3 is not installed.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pip3 found${NC}"

# Create installation directory
echo -e "${BLUE}Creating installation directory...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$BIN_DIR"
echo -e "${GREEN}✓ Directories created${NC}"

# Copy application files
echo -e "${BLUE}Copying application files...${NC}"
cp -r "$SCRIPT_DIR/src" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/scripts" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/pyproject.toml" "$INSTALL_DIR/"
echo -e "${GREEN}✓ Files copied${NC}"

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
python3 -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"
echo -e "${GREEN}✓ Virtual environment created${NC}"

# Install dependencies
echo -e "${BLUE}Installing dependencies (this may take a moment)...${NC}"
pip install --upgrade pip
pip install -r "$INSTALL_DIR/requirements.txt"
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Install the package
echo -e "${BLUE}Installing the application...${NC}"
cd "$INSTALL_DIR"
pip install -e .
echo -e "${GREEN}✓ Application installed${NC}"

# Create launcher script
echo -e "${BLUE}Creating launcher script...${NC}"
cat > "$BIN_DIR/macos-updater" << 'EOF'
#!/bin/bash
# macOS Universal Updater Launcher

INSTALL_DIR="$HOME/.macos-updater"

# Activate virtual environment
source "$INSTALL_DIR/venv/bin/activate"

# Run the application
python -m updater.cli "$@"
EOF

chmod +x "$BIN_DIR/macos-updater"

# Create alias script
cat > "$BIN_DIR/updater" << 'EOF'
#!/bin/bash
# Alias for macos-updater
exec "$HOME/.local/bin/macos-updater" "$@"
EOF

chmod +x "$BIN_DIR/updater"

echo -e "${GREEN}✓ Launcher scripts created${NC}"

# Add to PATH if needed
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${YELLOW}Adding $BIN_DIR to PATH...${NC}"

    # Determine shell
    SHELL_RC=""
    if [[ "$SHELL" == *"zsh"* ]]; then
        SHELL_RC="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]]; then
        SHELL_RC="$HOME/.bash_profile"
    fi

    if [[ -n "$SHELL_RC" ]]; then
        echo "" >> "$SHELL_RC"
        echo "# macOS Universal Updater" >> "$SHELL_RC"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_RC"
        echo -e "${GREEN}✓ PATH updated in $SHELL_RC${NC}"
        echo -e "${YELLOW}Please restart your terminal or run: source $SHELL_RC${NC}"
    fi
fi

# Copy scheduled runner to config directory
cp "$INSTALL_DIR/scripts/run_scheduled.py" "$INSTALL_DIR/run_scheduled.py"
chmod +x "$INSTALL_DIR/run_scheduled.py"

# Check for optional dependencies
echo -e "\n${BLUE}Checking optional dependencies...${NC}"

if command -v brew &> /dev/null; then
    echo -e "${GREEN}✓ Homebrew installed${NC}"
else
    echo -e "${YELLOW}⚠ Homebrew not found (install from https://brew.sh)${NC}"
fi

if command -v mas &> /dev/null; then
    echo -e "${GREEN}✓ Mac App Store CLI (mas) installed${NC}"
else
    echo -e "${YELLOW}⚠ mas not found (install with: brew install mas)${NC}"
fi

if command -v npm &> /dev/null; then
    echo -e "${GREEN}✓ npm installed${NC}"
else
    echo -e "${YELLOW}⚠ npm not found (optional for Node.js package updates)${NC}"
fi

# Installation complete
echo -e "\n${GREEN}"
echo "╔════════════════════════════════════════════════╗"
echo "║         Installation Complete! 🎉              ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "You can now run the updater with:"
echo -e "  ${BLUE}macos-updater${NC}      - Launch the TUI interface"
echo -e "  ${BLUE}updater${NC}            - Alias for macos-updater"
echo -e "  ${BLUE}updater check${NC}      - Check for updates"
echo -e "  ${BLUE}updater update${NC}     - Run updates from CLI"
echo -e "  ${BLUE}updater status${NC}     - Show system status"
echo -e "  ${BLUE}updater --help${NC}     - Show all commands"

echo -e "\n${YELLOW}Note: You may need to restart your terminal or run:${NC}"
echo -e "  source ~/.zshrc  (or ~/.bash_profile for bash)"

echo -e "\n${BLUE}Installation directory: $INSTALL_DIR${NC}"
echo -e "${BLUE}Configuration will be stored in: ~/.macos-updater/${NC}"

echo -e "\n${GREEN}Enjoy keeping your Mac up to date! 🍎${NC}"
