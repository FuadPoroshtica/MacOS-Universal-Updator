#!/bin/bash
echo "Updating macOS software..."
softwareupdate -ia --verbose

echo "Updating Homebrew..."
brew update && brew upgrade && brew cleanup

echo "Updating App Store apps..."
mas upgrade

echo "All updates done ✅"