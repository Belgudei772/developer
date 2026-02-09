#!/bin/bash
set -e

REPO="Belgudei772/developer"
INSTALL_DIR="$HOME/.local/bin"

# Create install directory
mkdir -p "$INSTALL_DIR"

echo "Downloading developer..."
curl -sL "https://github.com/$REPO/releases/latest/download/developer" -o "$INSTALL_DIR/developer"
chmod +x "$INSTALL_DIR/developer"

# Check if ~/.local/bin is in PATH
if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo ""
    echo "Add this to your ~/.zshrc (or ~/.bashrc):"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "Then run: source ~/.zshrc"
fi

echo "Done! Run with: developer"
