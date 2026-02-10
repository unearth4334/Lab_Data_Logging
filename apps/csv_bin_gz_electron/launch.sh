#!/usr/bin/env bash
# CSV to BIN.GZ Converter Launcher
# Uses the Electron App Framework

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

FRAMEWORK_DIR="$SCRIPT_DIR/../../electron-app-framework"
NODE_BIN=""
NPM_BIN=""

# Check for bundled portable Node.js in framework
if [[ -x "$FRAMEWORK_DIR/nodejs/node.exe" ]]; then
  NODE_BIN="$FRAMEWORK_DIR/nodejs/node.exe"
  NPM_BIN="$FRAMEWORK_DIR/nodejs/npm.cmd"
  export PATH="$FRAMEWORK_DIR/nodejs:$PATH"
  echo "Using bundled Node.js from framework"
elif [[ -x "$FRAMEWORK_DIR/nodejs/node" ]]; then
  NODE_BIN="$FRAMEWORK_DIR/nodejs/node"
  NPM_BIN="$FRAMEWORK_DIR/nodejs/npm"
  export PATH="$FRAMEWORK_DIR/nodejs:$PATH"
  echo "Using bundled Node.js from framework"
# Fallback to system Node.js
elif command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  NODE_BIN="node"
  NPM_BIN="npm"
  echo "Using system Node.js"
else
  echo "Error: Node.js not found." >&2
  echo "Please install Node.js or place portable Node.js in $FRAMEWORK_DIR/nodejs" >&2
  exit 127
fi

# Install framework dependencies if needed
if [[ ! -d "$FRAMEWORK_DIR/node_modules" || ! -f "$FRAMEWORK_DIR/node_modules/electron/cli.js" ]]; then
  echo "Installing framework dependencies..."
  cd "$FRAMEWORK_DIR"
  "$NPM_BIN" install
  cd "$SCRIPT_DIR"
fi

# Install app dependencies if needed
if [[ ! -d node_modules ]]; then
  echo "Installing app dependencies..."
  "$NPM_BIN" install
fi

# Launch the Electron app
echo "Launching CSV to BIN.GZ Converter..."
"$NODE_BIN" "$FRAMEWORK_DIR/node_modules/electron/cli.js" .
