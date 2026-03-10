#!/usr/bin/env python3
"""
Build script for lab_scripts packages.

This script automates the build process for Python packages in the lab_scripts directory.
It handles building wheel and source distributions, cleaning old artifacts, and validating
the package structure.

Usage:
    python build_package.py <package_folder>
    python build_package.py lab_scripts/dmm6500_buffer_download
    python build_package.py GEN4_BRUP_dmm6500_buffer_download

Options:
    --clean         Clean build artifacts before building
    --no-clean      Skip cleaning (default)
    --install       Install the package after building
    --verbose       Enable verbose output
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_status(message, status="info"):
    """Print colored status message."""
    color_map = {
        "info": Colors.OKBLUE,
        "success": Colors.OKGREEN,
        "warning": Colors.WARNING,
        "error": Colors.FAIL,
        "header": Colors.HEADER,
    }
    color = color_map.get(status, "")
    print(f"{color}{message}{Colors.ENDC}")


def find_package_root(package_path):
    """
    Find and validate the package root directory.
    
    Args:
        package_path: Path to the package (can be relative or absolute)
        
    Returns:
        Path object pointing to the validated package root
        
    Raises:
        FileNotFoundError: If package directory doesn't exist
        ValueError: If package structure is invalid
    """
    # Convert to Path object
    pkg_path = Path(package_path)
    
    # If relative path, check if it's relative to current directory or lab_scripts
    if not pkg_path.is_absolute():
        # Try as-is first
        if pkg_path.exists():
            pkg_path = pkg_path.resolve()
        # Try relative to lab_scripts directory
        elif Path(__file__).parent.joinpath(pkg_path.name).exists():
            pkg_path = Path(__file__).parent.joinpath(pkg_path.name).resolve()
        # Try treating the input as just the package name
        elif Path(__file__).parent.joinpath(package_path).exists():
            pkg_path = Path(__file__).parent.joinpath(package_path).resolve()
        else:
            raise FileNotFoundError(f"Package directory not found: {package_path}")
    
    if not pkg_path.exists():
        raise FileNotFoundError(f"Package directory does not exist: {pkg_path}")
    
    if not pkg_path.is_dir():
        raise ValueError(f"Path is not a directory: {pkg_path}")
    
    # Check for pyproject.toml
    pyproject_path = pkg_path / "pyproject.toml"
    if not pyproject_path.exists():
        raise ValueError(f"No pyproject.toml found in {pkg_path}")
    
    return pkg_path


def clean_build_artifacts(package_path, verbose=False):
    """
    Remove old build artifacts.
    
    Args:
        package_path: Path to the package root
        verbose: Enable verbose output
    """
    print_status(f"🧹 Cleaning build artifacts in {package_path.name}...", "info")
    
    artifacts_to_clean = [
        "dist",
        "build",
        "*.egg-info",
    ]
    
    cleaned = []
    for pattern in artifacts_to_clean:
        if "*" in pattern:
            # Handle glob patterns
            for item in package_path.glob(pattern):
                if item.exists():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    cleaned.append(item.name)
        else:
            # Handle direct paths
            item = package_path / pattern
            if item.exists():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                cleaned.append(pattern)
    
    if cleaned:
        if verbose:
            for item in cleaned:
                print(f"  Removed: {item}")
        print_status(f"  Cleaned {len(cleaned)} artifact(s)", "success")
    else:
        print_status("  No artifacts to clean", "info")


def build_package(package_path, verbose=False):
    """
    Build the package using Python build module.
    
    Args:
        package_path: Path to the package root
        verbose: Enable verbose output
        
    Returns:
        True if build succeeds, False otherwise
    """
    print_status(f"\n🔨 Building package: {package_path.name}", "header")
    
    # Check if 'build' module is available
    try:
        import build
    except ImportError:
        print_status("  ⚠️  'build' module not found. Installing...", "warning")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "build"],
            check=True,
            capture_output=not verbose
        )
    
    # Run the build
    build_cmd = [sys.executable, "-m", "build", str(package_path)]
    
    print_status(f"  Running: {' '.join(build_cmd)}", "info")
    
    try:
        result = subprocess.run(
            build_cmd,
            check=True,
            capture_output=not verbose,
            text=True,
            cwd=package_path
        )
        
        if verbose and result.stdout:
            print(result.stdout)
        
        print_status("  ✓ Build completed successfully", "success")
        return True
        
    except subprocess.CalledProcessError as e:
        print_status(f"  ✗ Build failed with exit code {e.returncode}", "error")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False


def list_build_artifacts(package_path):
    """
    List the built artifacts.
    
    Args:
        package_path: Path to the package root
    """
    dist_path = package_path / "dist"
    
    if not dist_path.exists() or not any(dist_path.iterdir()):
        print_status("  No artifacts found in dist/", "warning")
        return
    
    print_status("\n📦 Build artifacts:", "header")
    for item in sorted(dist_path.iterdir()):
        size_mb = item.stat().st_size / (1024 * 1024)
        print(f"  {item.name} ({size_mb:.2f} MB)")


def install_package(package_path, verbose=False):
    """
    Install the built package.
    
    Args:
        package_path: Path to the package root
        verbose: Enable verbose output
        
    Returns:
        True if installation succeeds, False otherwise
    """
    print_status("\n📥 Installing package...", "header")
    
    dist_path = package_path / "dist"
    
    # Find the wheel file
    wheel_files = list(dist_path.glob("*.whl"))
    if not wheel_files:
        print_status("  ✗ No wheel file found in dist/", "error")
        return False
    
    wheel_file = wheel_files[0]
    
    install_cmd = [sys.executable, "-m", "pip", "install", "--force-reinstall", str(wheel_file)]
    
    print_status(f"  Running: pip install {wheel_file.name}", "info")
    
    try:
        result = subprocess.run(
            install_cmd,
            check=True,
            capture_output=not verbose,
            text=True
        )
        
        if verbose and result.stdout:
            print(result.stdout)
        
        print_status("  ✓ Installation completed successfully", "success")
        return True
        
    except subprocess.CalledProcessError as e:
        print_status(f"  ✗ Installation failed with exit code {e.returncode}", "error")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build lab_scripts Python packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_package.py dmm6500_buffer_download
  python build_package.py lab_scripts/lockout_hysteresis_test --clean
  python build_package.py GEN4_BRUP_dmm6500_buffer_download --clean --install
  python build_package.py ../lab_scripts/dmm6500_buffer_download --verbose
"""
    )
    
    parser.add_argument(
        "package",
        help="Path to the package directory (relative or absolute)"
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts before building"
    )
    
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install the package after building"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Header
    print_status("=" * 60, "header")
    print_status("  Lab Scripts Package Builder", "header")
    print_status("=" * 60, "header")
    
    try:
        # Find and validate package root
        package_path = find_package_root(args.package)
        print_status(f"\n📁 Package: {package_path.name}", "info")
        print_status(f"   Path: {package_path}", "info")
        
        # Clean if requested
        if args.clean:
            clean_build_artifacts(package_path, verbose=args.verbose)
        
        # Build the package
        success = build_package(package_path, verbose=args.verbose)
        
        if not success:
            sys.exit(1)
        
        # List artifacts
        list_build_artifacts(package_path)
        
        # Install if requested
        if args.install:
            install_success = install_package(package_path, verbose=args.verbose)
            if not install_success:
                sys.exit(1)
        
        # Success footer
        print_status("\n" + "=" * 60, "header")
        print_status("  ✓ Build process completed successfully!", "success")
        print_status("=" * 60, "header")
        
    except (FileNotFoundError, ValueError) as e:
        print_status(f"\n✗ Error: {e}", "error")
        sys.exit(1)
    except KeyboardInterrupt:
        print_status("\n\n✗ Build cancelled by user", "warning")
        sys.exit(130)
    except Exception as e:
        print_status(f"\n✗ Unexpected error: {e}", "error")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
