#!/bin/bash
set -e

REPO="Belgudei772/developer"

echo "Downloading developer..."
curl -sL "https://github.com/$REPO/releases/latest/download/developer" -o developer
chmod +x developer
sudo mv developer /usr/local/bin/developer

echo "Done! Run with: developer"
