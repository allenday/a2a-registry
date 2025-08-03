#!/usr/bin/env python3
"""Release script for A2A Registry."""

import argparse
import re
import subprocess
import sys
from pathlib import Path


def update_version(version: str) -> None:
    """Update version in __init__.py file."""
    init_file = Path("src/a2a_registry/__init__.py")
    
    if not init_file.exists():
        print(f"Error: {init_file} not found")
        sys.exit(1)
    
    # Read current content
    content = init_file.read_text()
    
    # Update version
    pattern = r'__version__ = "[^"]*"'
    replacement = f'__version__ = "{version}"'
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, replacement, content)
        init_file.write_text(new_content)
        print(f"Updated version to {version} in {init_file}")
    else:
        print(f"Error: Could not find __version__ in {init_file}")
        sys.exit(1)


def validate_version(version: str) -> bool:
    """Validate version format."""
    pattern = r'^\d+\.\d+\.\d+$'
    if not re.match(pattern, version):
        print(f"Error: Version {version} is not in format X.Y.Z")
        return False
    return True


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result


def main():
    parser = argparse.ArgumentParser(description="A2A Registry release script")
    parser.add_argument("version", help="Version to release (e.g., 0.1.1)")
    parser.add_argument("--dry-run", action="store_true", help="Only update version, don't build")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    
    args = parser.parse_args()
    
    if not validate_version(args.version):
        sys.exit(1)
    
    print(f"Preparing release for version {args.version}")
    
    # Update version
    update_version(args.version)
    
    if args.dry_run:
        print("Dry run complete. Version updated but no build performed.")
        return
    
    # Run checks
    if not args.skip_tests:
        print("Running tests...")
        try:
            run_command(["make", "lint"])
            run_command(["make", "typecheck"])
            run_command(["make", "test"])
        except subprocess.CalledProcessError as e:
            print(f"Tests failed: {e}")
            sys.exit(1)
    
    # Build package
    print("Building package...")
    try:
        run_command(["make", "build"])
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)
    
    print(f"\nRelease {args.version} prepared successfully!")
    print("Next steps:")
    print("1. Review the changes")
    print("2. Commit and push the version update")
    print("3. Use GitHub Actions 'Release' workflow to publish")
    print("   - Go to Actions > Release > Run workflow")
    print("   - Enter version: {args.version}")
    print("   - Choose publish options")


if __name__ == "__main__":
    main() 