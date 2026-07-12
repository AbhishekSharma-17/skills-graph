#!/usr/bin/env python3
"""
Deno skill maintenance script.
Checks for new releases and documentation updates.

Usage:
    python check-updates.py --version     Check latest Deno version
    python check-updates.py --stale N     Show files not updated in N days
    python check-updates.py --integrity   Verify all referenced files exist
    python check-updates.py --report      Full maintenance report
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
VERSION_FILE = SKILL_DIR / "VERSION.json"
SKILL_FILE = SKILL_DIR / "SKILL.md"
REFERENCES_DIR = SKILL_DIR / "references"

PACKAGE_NAME = "deno"
DOCS_URL = "https://docs.deno.com"
GITHUB_API = "https://api.github.com/repos/denoland/deno/releases/latest"
PYPI_URL = None  # Not a Python package


def load_version_info() -> dict:
    with open(VERSION_FILE) as f:
        return json.load(f)


def check_latest_version() -> None:
    """Check the latest version of Deno."""
    try:
        import urllib.request
        req = urllib.request.Request(
            GITHUB_API,
            headers={"User-Agent": "skills-graph-checker"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            latest = data["tag_name"].lstrip("v")
            current = load_version_info()["source_version_tracked"]
            if latest != current:
                print(f"UPDATE AVAILABLE: {current} -> {latest}")
                print(f"  Release: https://github.com/denoland/deno/releases/tag/v{latest}")
            else:
                print(f"UP TO DATE: {current}")
    except Exception as e:
        print(f"ERROR checking version: {e}")


def check_stale_files(days: int) -> None:
    """Show reference files not updated within N days."""
    info = load_version_info()
    threshold = datetime.now() - timedelta(days=days)

    stale = []
    for filename, meta in info.get("references", {}).items():
        last_updated = datetime.strptime(meta["last_updated"], "%Y-%m-%d")
        if last_updated < threshold:
            age = (datetime.now() - last_updated).days
            stale.append((filename, age, meta.get("source_page", "")))

    if stale:
        print(f"STALE FILES (>{days} days old):")
        for filename, age, source in sorted(stale, key=lambda x: -x[1]):
            print(f"  {filename} — {age} days old")
            if source:
                print(f"    Source: {source}")
    else:
        print(f"All files updated within {days} days.")


def check_integrity() -> None:
    """Verify all referenced files exist on disk."""
    info = load_version_info()
    missing = []
    extra = []

    referenced = set(info.get("references", {}).keys())
    on_disk = {f.name for f in REFERENCES_DIR.iterdir() if f.is_file() and f.suffix == ".md"}

    for filename in referenced:
        filepath = REFERENCES_DIR / filename
        if not filepath.exists():
            missing.append(filename)

    for filename in on_disk - referenced:
        extra.append(filename)

    # Check SKILL.md routing table
    if SKILL_FILE.exists():
        content = SKILL_FILE.read_text()
        for filename in referenced:
            if filename not in content:
                print(f"  WARNING: {filename} not in SKILL.md routing table")

    if missing:
        print("MISSING FILES (referenced but not on disk):")
        for f in missing:
            print(f"  {f}")
    if extra:
        print("EXTRA FILES (on disk but not in VERSION.json):")
        for f in extra:
            print(f"  {f}")
    if not missing and not extra:
        print("INTEGRITY OK: All files accounted for.")


def full_report() -> None:
    """Generate a full maintenance report."""
    info = load_version_info()
    print("=" * 60)
    print(f"MAINTENANCE REPORT: {PACKAGE_NAME}")
    print("=" * 60)
    print(f"Skill version:  {info['skill_version']}")
    print(f"Source tracked: {info['source_version_tracked']}")
    print(f"Last checked:   {info['last_checked']}")
    print(f"Last updated:   {info['last_updated']}")
    print(f"Docs URL:       {DOCS_URL}")
    print()

    check_latest_version()
    print()
    check_stale_files(info.get("staleness_threshold_days", 90))
    print()
    check_integrity()
    print()

    ref_count = len(info.get("references", {}))
    total_lines = sum(
        sum(1 for _ in open(REFERENCES_DIR / f))
        for f in info.get("references", {})
        if (REFERENCES_DIR / f).exists()
    )
    print(f"Reference files: {ref_count}")
    print(f"Total lines:     {total_lines}")
    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    flag = sys.argv[1]

    if flag == "--version":
        check_latest_version()
    elif flag == "--stale":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        check_stale_files(days)
    elif flag == "--integrity":
        check_integrity()
    elif flag == "--report":
        full_report()
    else:
        print(f"Unknown flag: {flag}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
