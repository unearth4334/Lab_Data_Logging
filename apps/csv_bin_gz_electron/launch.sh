#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

NODE_BIN=""

if [[ -x "$SCRIPT_DIR/nodejs/node.exe" ]]; then
  NODE_BIN="$SCRIPT_DIR/nodejs/node.exe"
  NPM_BIN="$SCRIPT_DIR/nodejs/npm.cmd"
  export PATH="$SCRIPT_DIR/nodejs:$PATH"
elif command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  NODE_BIN="node"
  NPM_BIN="npm"
else
  echo "Node.js not found. Please install Node.js or place portable Node.js in $SCRIPT_DIR/nodejs" >&2
  exit 127
fi

if [[ ! -d node_modules || ! -f node_modules/electron/cli.js || ! -d node_modules/js-yaml ]]; then
  echo "Installing npm dependencies..."
  "$NPM_BIN" install
fi

echo "Launching Electron app..."
"$NPM_BIN" start
