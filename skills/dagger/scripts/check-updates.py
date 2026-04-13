#!/usr/bin/env python3
"""Dagger skill maintenance script.

Checks for updates to the Dagger package and validates skill integrity.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
VERSION_FILE = SKILL_DIR / "VERSION.json"
SKILL_FILE = SKILL_DIR / "SKILL.md"
REFERENCES_DIR = SKILL_DIR / "references"
PACKAGE_NAME = "dagger-io"
DOCS_URL = "https://docs.dagger.io"


def load_version_info() -> dict:
    """Load VERSION.json data."""
    with open(VERSION_FILE) as f:
        return json.load(f)


def check_pypi_version() -> str | None:
    """Check latest version on PyPI."""
    try:
        result = subprocess.run(
            ["pip", "index", "versions", PACKAGE_NAME],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            # Parse "dagger-io (0.20.3)" format
            for line in result.stdout.splitlines():
                if PACKAGE_NAME in line and "(" in line:
                    return line.split("(")[1].split(")")[0].strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def check_version(args):
    """Compare tracked version with latest PyPI version."""
    info = load_version_info()
    tracked = info["source_version_tracked"]
    print(f"Tracked version: {tracked}")

    latest = check_pypi_version()
    if latest:
        print(f"Latest PyPI version: {latest}")
        if latest != tracked:
            print(f"⚠️  UPDATE AVAILABLE: {tracked} → {latest}")
            return 1
        else:
            print("✅ Up to date")
    else:
        print("⚠️  Could not fetch latest version from PyPI")
        return 1
    return 0


def check_staleness(args):
    """Check if skill content is stale."""
    info = load_version_info()
    threshold = args.days or info.get("staleness_threshold_days", 90)
    last_updated = datetime.fromisoformat(info["last_updated"])
    age_days = (datetime.now() - last_updated).days

    print(f"Last updated: {info['last_updated']} ({age_days} days ago)")
    print(f"Staleness threshold: {threshold} days")

    if age_days > threshold:
        print(f"⚠️  STALE: Content is {age_days} days old (threshold: {threshold})")
        return 1
    else:
        print(f"✅ Fresh: {threshold - age_days} days until stale")
    return 0


def check_integrity(args):
    """Validate skill file structure and references."""
    errors = []
    info = load_version_info()

    # Check SKILL.md exists and is under 100 lines
    if not SKILL_FILE.exists():
        errors.append("SKILL.md not found")
    else:
        lines = SKILL_FILE.read_text().splitlines()
        if len(lines) > 100:
            errors.append(f"SKILL.md is {len(lines)} lines (max 100)")

    # Check all referenced files exist
    for ref_name in info.get("references", {}):
        ref_path = REFERENCES_DIR / ref_name
        if not ref_path.exists():
            errors.append(f"Missing reference file: {ref_name}")
        else:
            line_count = len(ref_path.read_text().splitlines())
            if line_count > 500:
                errors.append(f"{ref_name} is {line_count} lines (max 500)")

    # Check VERSION.json required fields
    required_fields = [
        "skill_version",
        "source_version_tracked",
        "source_package",
        "docs_snapshot_date",
        "last_checked",
        "last_updated",
        "urls",
        "references",
        "staleness_threshold_days",
    ]
    for field in required_fields:
        if field not in info:
            errors.append(f"VERSION.json missing field: {field}")

    # Check CHANGELOG.md exists
    if not (SKILL_DIR / "CHANGELOG.md").exists():
        errors.append("CHANGELOG.md not found")

    # Check AUDIT-REPORT.md exists
    if not (SKILL_DIR / "AUDIT-REPORT.md").exists():
        errors.append("AUDIT-REPORT.md not found")

    if errors:
        print("❌ Integrity check failed:")
        for err in errors:
            print(f"   - {err}")
        return 1
    else:
        print("✅ All integrity checks passed")
        print(f"   - SKILL.md: valid router")
        print(f"   - References: {len(info['references'])} files present")
        print(f"   - VERSION.json: all fields present")
        print(f"   - CHANGELOG.md: present")
        print(f"   - AUDIT-REPORT.md: present")
    return 0


def generate_report(args):
    """Generate a full status report."""
    print("=" * 60)
    print("Dagger Skill — Status Report")
    print("=" * 60)
    print()

    info = load_version_info()
    print(f"Skill version: {info['skill_version']}")
    print(f"Source tracked: {PACKAGE_NAME}@{info['source_version_tracked']}")
    print(f"Last updated: {info['last_updated']}")
    print(f"Docs URL: {DOCS_URL}")
    print()

    print("--- Version Check ---")
    check_version(args)
    print()

    print("--- Staleness Check ---")
    check_staleness(args)
    print()

    print("--- Integrity Check ---")
    check_integrity(args)
    print()

    print("--- Reference Files ---")
    for ref_name, ref_info in info.get("references", {}).items():
        ref_path = REFERENCES_DIR / ref_name
        lines = len(ref_path.read_text().splitlines()) if ref_path.exists() else 0
        print(f"   {ref_name}: {lines} lines (written for {ref_info['written_for']})")


def main():
    parser = argparse.ArgumentParser(description="Dagger skill maintenance")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("--version", help="Check for package updates")
    subparsers.add_parser("--sitemap", help="Check docs sitemap for changes")

    stale_parser = subparsers.add_parser("--stale", help="Check staleness")
    stale_parser.add_argument("days", type=int, nargs="?", help="Custom threshold")

    subparsers.add_parser("--integrity", help="Validate skill structure")
    subparsers.add_parser("--report", help="Full status report")

    # Handle --flag style arguments
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--version":
            sys.exit(check_version(argparse.Namespace()))
        elif cmd == "--sitemap":
            print("Sitemap check not implemented for PyPI packages")
            sys.exit(0)
        elif cmd == "--stale":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else None
            sys.exit(check_staleness(argparse.Namespace(days=days)))
        elif cmd == "--integrity":
            sys.exit(check_integrity(argparse.Namespace()))
        elif cmd == "--report":
            generate_report(argparse.Namespace())
            sys.exit(0)

    parser.print_help()


if __name__ == "__main__":
    main()
