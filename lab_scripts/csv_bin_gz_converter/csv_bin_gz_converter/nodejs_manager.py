"""
Portable Node.js Manager for CSV to BIN.GZ Converter

Resolution order for finding Node.js:
  1. electron-app-framework/nodejs/ (bundled portable node in the repo)
  2. ~/.csv_bin_gz_converter/nodejs/ (previously auto-downloaded cache)
  3. System PATH (node already installed)
  4. Auto-download portable Node.js v20 LTS to the cache directory
"""

import os
import sys
import platform
import subprocess
import urllib.request
import zipfile
import tarfile
import shutil
from pathlib import Path
from colorama import Fore, Style

NODE_VERSION = "v20.11.1"
CACHE_DIR = Path.home() / ".csv_bin_gz_converter" / "nodejs"

_DIST = {
    "windows": {
        "file": f"node-{NODE_VERSION}-win-x64.zip",
        "url":  f"https://nodejs.org/dist/{NODE_VERSION}/node-{NODE_VERSION}-win-x64.zip",
        "node": "node.exe",
        "npm":  "npm.cmd",
    },
    "darwin": {
        "file": f"node-{NODE_VERSION}-darwin-x64.tar.gz",
        "url":  f"https://nodejs.org/dist/{NODE_VERSION}/node-{NODE_VERSION}-darwin-x64.tar.gz",
        "node": "bin/node",
        "npm":  "bin/npm",
    },
    "linux": {
        "file": f"node-{NODE_VERSION}-linux-x64.tar.gz",
        "url":  f"https://nodejs.org/dist/{NODE_VERSION}/node-{NODE_VERSION}-linux-x64.tar.gz",
        "node": "bin/node",
        "npm":  "bin/npm",
    },
}


def _p(color, icon, msg):
    print(f"{color}{icon}{Style.RESET_ALL} {msg}")

def _info(msg):    _p(Fore.CYAN,   "ℹ", msg)
def _ok(msg):      _p(Fore.GREEN,  "✓", msg)
def _warn(msg):    _p(Fore.YELLOW, "⚠", msg)
def _err(msg):     _p(Fore.RED,    "✗", msg)


def _check_node_in_dir(directory: Path):
    """Return (node_exe, npm_exe) if a working node is found in directory, else (None, None)."""
    sys_name = platform.system().lower()
    dist = _DIST.get(sys_name)
    if dist is None:
        return None, None

    node_exe = directory / dist["node"]
    npm_exe  = directory / dist["npm"]
    if node_exe.exists():
        return node_exe, npm_exe
    return None, None


def _check_system_node():
    """Return (node_exe, npm_exe) if node is on the system PATH, else (None, None)."""
    node = shutil.which("node")
    npm  = shutil.which("npm") or shutil.which("npm.cmd")
    if node:
        return Path(node), Path(npm) if npm else None
    return None, None


def _find_framework_nodejs(app_root: Path):
    """Look for electron-app-framework/nodejs relative to the app root."""
    # app_root is apps/csv_bin_gz_electron  →  ../../electron-app-framework
    framework_nodejs = app_root.parent.parent / "electron-app-framework" / "nodejs"
    return _check_node_in_dir(framework_nodejs)


def _download_progress(block_num, block_size, total_size):
    if total_size <= 0:
        return
    downloaded = block_num * block_size
    pct = min(100, int(downloaded * 100 / total_size))
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    print(f"\r  [{bar}] {pct:3d}%", end="", flush=True)


def _download_node():
    """Download portable Node.js to CACHE_DIR.  Returns (node_exe, npm_exe) or (None, None)."""
    sys_name = platform.system().lower()
    dist = _DIST.get(sys_name)
    if dist is None:
        _err(f"Unsupported platform: {platform.system()}")
        return None, None

    _info(f"Downloading portable Node.js {NODE_VERSION} for {platform.system()}...")
    print(f"  Source: {dist['url']}")
    print(f"  Target: {CACHE_DIR}\n")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = CACHE_DIR.parent / dist["file"]

    try:
        urllib.request.urlretrieve(dist["url"], archive_path, reporthook=_download_progress)
        print()  # newline after progress bar
    except Exception as e:
        _err(f"Download failed: {e}")
        return None, None

    _info("Extracting...")
    try:
        if dist["file"].endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(CACHE_DIR.parent)
            # Move extracted dir → CACHE_DIR
            extracted = next(CACHE_DIR.parent.glob(f"node-{NODE_VERSION}-*"))
            if CACHE_DIR.exists():
                shutil.rmtree(CACHE_DIR)
            extracted.rename(CACHE_DIR)
        else:
            with tarfile.open(archive_path, "r:gz") as tf:
                tf.extractall(CACHE_DIR.parent)
            extracted = next(CACHE_DIR.parent.glob(f"node-{NODE_VERSION}-*"))
            if CACHE_DIR.exists():
                shutil.rmtree(CACHE_DIR)
            extracted.rename(CACHE_DIR)
    except Exception as e:
        _err(f"Extraction failed: {e}")
        return None, None
    finally:
        if archive_path.exists():
            archive_path.unlink()

    node_exe, npm_exe = _check_node_in_dir(CACHE_DIR)
    if node_exe:
        _ok(f"Portable Node.js installed to: {CACHE_DIR}")
        # Make binaries executable on Unix
        if platform.system() != "Windows":
            node_exe.chmod(node_exe.stat().st_mode | 0o111)
        return node_exe, npm_exe
    else:
        _err("Node.js extraction succeeded but binary not found")
        return None, None


def get_node(app_root: Path = None, auto_download: bool = True):
    """
    Find or download portable Node.js.

    Resolution order:
      1. electron-app-framework/nodejs/ (repo-bundled)
      2. ~/.csv_bin_gz_converter/nodejs/ (previously downloaded cache)
      3. System PATH
      4. Auto-download (if auto_download=True)

    Returns:
        (node_exe: Path, npm_exe: Path)  — paths to node and npm executables
        (None, None) if Node.js cannot be found or downloaded
    """
    # 1. Framework bundled portable node
    if app_root is not None:
        node, npm = _find_framework_nodejs(app_root)
        if node:
            _info(f"Using bundled Node.js from electron-app-framework")
            return node, npm

    # 2. Previously downloaded cache
    node, npm = _check_node_in_dir(CACHE_DIR)
    if node:
        _info(f"Using cached portable Node.js from: {CACHE_DIR}")
        return node, npm

    # 3. System PATH
    node, npm = _check_system_node()
    if node:
        _info(f"Using system Node.js: {node}")
        return node, npm

    # 4. Auto-download
    if not auto_download:
        return None, None

    _warn("Node.js not found. Downloading portable Node.js automatically...")
    return _download_node()


def ensure_npm_deps(node_exe: Path, npm_exe: Path, directory: Path):
    """
    Run `npm install` in directory if node_modules is missing or incomplete.

    Returns True on success, False on failure.
    """
    if not directory.exists():
        _err(f"Directory not found: {directory}")
        return False

    node_modules = directory / "node_modules"

    # Quick check using a known dep from package.json if present
    pkg_json = directory / "package.json"
    if node_modules.exists() and pkg_json.exists():
        try:
            import json
            deps = json.loads(pkg_json.read_text()).get("dependencies", {})
            first_dep = next(iter(deps), None)
            if first_dep and (node_modules / first_dep).exists():
                return True  # already installed
        except Exception:
            pass

    if node_modules.exists() and not pkg_json.exists():
        return True  # no package.json, nothing to install

    _info(f"Installing npm dependencies in: {directory.name}/")

    # Use npm.cmd on Windows, otherwise use node to run npm
    if npm_exe and npm_exe.exists():
        cmd = [str(npm_exe), "install", "--no-fund", "--no-audit"]
    else:
        # Fallback: invoke npm through node
        npm_js = node_exe.parent / "node_modules" / "npm" / "bin" / "npm-cli.js"
        if npm_js.exists():
            cmd = [str(node_exe), str(npm_js), "install", "--no-fund", "--no-audit"]
        else:
            _err("Cannot locate npm executable")
            return False

    env = os.environ.copy()
    # Prepend portable node dir to PATH so child processes find the right node
    env["PATH"] = str(node_exe.parent) + os.pathsep + env.get("PATH", "")

    result = subprocess.run(cmd, cwd=str(directory), env=env, check=False)
    if result.returncode == 0:
        _ok(f"Dependencies installed for {directory.name}")
        return True
    else:
        _err(f"npm install failed in {directory.name} (exit {result.returncode})")
        return False
