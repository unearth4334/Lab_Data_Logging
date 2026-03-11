"""
Launcher for CSV to BIN.GZ Converter Electron Application

Finds the Electron app and Node.js (portable or system), installs npm
dependencies if needed, then launches the app.  Node.js resolution order:
  1. electron-app-framework/nodejs/ (repo-bundled portable node)
  2. ~/.csv_bin_gz_converter/nodejs/ (auto-downloaded cache)
  3. System PATH
  4. Auto-download portable Node.js v20 LTS
"""

import subprocess
import os
from pathlib import Path
from colorama import init, Fore, Style
from .nodejs_manager import get_node, ensure_npm_deps

init()

def _ok(msg):   print(f"{Fore.GREEN}✓ {msg}{Style.RESET_ALL}")
def _err(msg):  print(f"{Fore.RED}✗ ERROR:{Style.RESET_ALL} {msg}")
def _warn(msg): print(f"{Fore.YELLOW}⚠{Style.RESET_ALL} {msg}")
def _info(msg): print(f"{Fore.BLUE}ℹ{Style.RESET_ALL} {msg}")

def _header(msg):
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{msg}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")


def _get_app_root() -> Path:
    """
    Find the csv_bin_gz_electron Electron app directory.

    Search order:
      1. Bundled inside the package: csv_bin_gz_converter/electron_app/   ← preferred
      2. shared/csv_bin_gz_electron/ at the repo root                     ← other-repo layout
      3. apps/csv_bin_gz_electron/ at the repo root                       ← Lab_Data_Logging layout
    """
    package_dir = Path(__file__).parent

    # 1. Bundled app (self-contained wheel)
    bundled = package_dir / "electron_app"
    if (bundled / "main.js").exists():
        return bundled

    # 2 & 3. Walk up the directory tree looking for shared/ or apps/ layouts
    for ancestor in package_dir.parents:
        for sub in ("shared/csv_bin_gz_electron", "apps/csv_bin_gz_electron"):
            candidate = ancestor / sub
            if (candidate / "main.js").exists():
                return candidate

    # Fallback for error message — bundled should always exist after install
    return bundled


def _get_framework_root(app_root: Path) -> Path:
    """Return the electron-app-framework directory (sibling of apps/)."""
    return app_root.parent.parent / "electron-app-framework"


def launch_app(debug: bool = False) -> int:
    """
    Launch the CSV to BIN.GZ Converter Electron application.

    Returns:
        int: exit code (0 = success)
    """
    _header("CSV to BIN.GZ Converter")

    # ── 1. Locate the Electron app ─────────────────────────────────────────
    app_root = _get_app_root()
    if not (app_root / "main.js").exists():
        _err(f"Electron app not found. Checked: {app_root}")
        print("\nClone or copy the Lab_Data_Logging repository so that")
        print("  apps/csv_bin_gz_electron/main.js  exists.")
        return 1
    _info(f"App: {app_root}")

    framework_root = _get_framework_root(app_root)

    # ── 2. Resolve Node.js (portable or system, auto-download if needed) ───
    print()
    node_exe, npm_exe = get_node(app_root=app_root, auto_download=True)
    if node_exe is None:
        _err("Could not obtain Node.js")
        return 1
    print()

    # ── 3. Install npm dependencies ─────────────────────────────────────────
    # Bundled app: electron is a direct dep of electron_app/package.json —
    # one npm install in app_root gets everything (electron + csv-parse + js-yaml).
    # Non-bundled (original repo): electron lives in electron-app-framework,
    # so we install there first, then the app dir.
    is_bundled = (app_root / "framework").exists()
    if is_bundled:
        if not ensure_npm_deps(node_exe, npm_exe, app_root):
            _err("Failed to install app dependencies")
            return 1
    else:
        if framework_root.exists() and (framework_root / "package.json").exists():
            if not ensure_npm_deps(node_exe, npm_exe, framework_root):
                _err("Failed to install framework dependencies")
                return 1
        if not ensure_npm_deps(node_exe, npm_exe, app_root):
            _err("Failed to install app dependencies")
            return 1
    print()

    # ── 4. Build launch command ─────────────────────────────────────────────
    # Prefer electron binary from app_root/node_modules (bundled), then from framework.
    electron_cli = app_root / "node_modules" / "electron" / "cli.js"
    if not electron_cli.exists():
        electron_cli = framework_root / "node_modules" / "electron" / "cli.js"

    if electron_cli.exists():
        cmd = [str(node_exe), str(electron_cli), "."]
    else:
        cmd = [str(npm_exe) if npm_exe else "npm", "start"]

    if debug:
        _info(f"Command: {' '.join(str(c) for c in cmd)}")

    print("Starting application...\n")

    # Prepend portable node dir to PATH for child processes
    env = os.environ.copy()
    env["PATH"] = str(node_exe.parent) + os.pathsep + env.get("PATH", "")
    
    # Set CSV_BIN_GZ_WORKDIR so the Electron app can find the Python venv
    # Look for .venv in potential locations moving up from the package directory
    venv_workdir = None
    for ancestor in [Path(__file__).parent] + list(Path(__file__).parent.parents):
        if (ancestor / ".venv").exists():
            venv_workdir = ancestor
            break
    if venv_workdir:
        env["CSV_BIN_GZ_WORKDIR"] = str(venv_workdir)
        _info(f"Setting Python search path: {venv_workdir}")

    result = subprocess.run(cmd, cwd=str(app_root), env=env, check=False)

    if result.returncode == 0:
        _ok("Application closed.")
    else:
        _warn(f"Application exited with code {result.returncode}")

    return result.returncode

