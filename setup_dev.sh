#!/bin/bash
#
# Development environment setup for macOS Universal Updater
#

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}Setting up development environment...${NC}"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Install dev dependencies
pip install pytest pytest-asyncio black ruff mypy

echo -e "${GREEN}Development environment ready!${NC}"
echo ""
echo "Activate with: source venv/bin/activate"
echo "Run app with: python run.py"
echo "Run tests with: pytest"
echo "Format code with: black src/"
echo "Lint code with: ruff check src/"
