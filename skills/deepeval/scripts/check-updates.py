#!/usr/bin/env python3
"""
DeepEval Skill Update Checker
================================
Checks for upstream DeepEval (PyPI) updates and validates skill integrity.

Usage:
    python scripts/check-updates.py              # Full report
    python scripts/check-updates.py --version    # Check PyPI version
    python scripts/check-updates.py --stale      # Show stale files
    python scripts/check-updates.py --stale 60   # Custom threshold (days)
    python scripts/check-updates.py --integrity  # Verify routing table
    python scripts/check-updates.py --report     # Full report
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

# --- Config ---
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
VERSION_FILE = SKILL_DIR / "VERSION.json"
REFERENCES_DIR = SKILL_DIR / "references"
SKILL_MD = SKILL_DIR / "SKILL.md"

PYPI_PACKAGE = "deepeval"
PYPI_URL = f"https://pypi.org/pypi/{PYPI_PACKAGE}/json"
STALE_THRESHOLD_DAYS = 90


def load_version():
    with open(VERSION_FILE) as f:
        return json.load(f)


def check_version():
    """Compare tracked version against PyPI latest."""
    ver = load_version()
    print(f"\n{'='*60}")
    print(f"  VERSION CHECK")
    print(f"{'='*60}")
    print(f"  Skill version:     {ver['skill_version']}")
    print(f"  Tracked source:    {ver['source_version_tracked']}")
    print(f"  Snapshot date:     {ver['docs_snapshot_date']}")

    try:
        req = Request(PYPI_URL, headers={"User-Agent": "skill-checker/1.0"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            latest = data.get("info", {}).get("version", "unknown")
            print(f"  PyPI latest:       {latest}")
            print(f"\n  Check https://deepeval.com/changelog/changelog-2026 for changes")
            return True
    except (URLError, KeyError) as e:
        print(f"\n  Could not reach PyPI: {e}")
        return None


def check_stale(threshold_days=STALE_THRESHOLD_DAYS):
    """Find reference files not updated recently."""
    ver = load_version()
    refs = ver.get("references", {})
    cutoff = (datetime.now() - timedelta(days=threshold_days)).strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"  STALE REFERENCE CHECK (>{threshold_days} days)")
    print(f"{'='*60}")

    stale = []
    for ref, info in sorted(refs.items()):
        updated = info.get("last_updated", "unknown")
        if updated < cutoff:
            stale.append((ref, info.get("written_for", "?"), updated))

    if stale:
        print(f"\n  {len(stale)} reference(s) may need review:\n")
        for ref, ver_written, updated in stale:
            print(f"    - {ref}")
            print(f"      Written for: {ver_written} | Last updated: {updated}")
    else:
        print(f"\n  All references updated within {threshold_days} days.")

    return stale


def check_integrity():
    """Verify all referenced files exist and SKILL.md routing is consistent."""
    print(f"\n{'='*60}")
    print(f"  INTEGRITY CHECK")
    print(f"{'='*60}")

    issues = []

    # Check SKILL.md exists
    if not SKILL_MD.exists():
        issues.append("SKILL.md not found")
        print(f"\n  FAIL: SKILL.md missing")
        return issues

    # Check SKILL.md line count
    lines = SKILL_MD.read_text().splitlines()
    if len(lines) > 100:
        issues.append(f"SKILL.md exceeds 100 lines ({len(lines)} lines)")

    # Check all reference files exist
    ver = load_version()
    refs = ver.get("references", {})
    for ref_file in sorted(refs.keys()):
        ref_path = REFERENCES_DIR / ref_file
        if not ref_path.exists():
            issues.append(f"Missing reference: {ref_file}")
        else:
            content = ref_path.read_text()
            line_count = len(content.splitlines())
            if line_count > 500:
                issues.append(f"{ref_file} exceeds 500 lines ({line_count})")

    # Check for files on disk not in VERSION.json
    if REFERENCES_DIR.exists():
        disk_files = {f.name for f in REFERENCES_DIR.glob("*.md")}
        tracked_files = set(refs.keys())
        untracked = disk_files - tracked_files
        if untracked:
            for f in sorted(untracked):
                issues.append(f"Untracked reference on disk: {f}")

    if issues:
        print(f"\n  {len(issues)} issue(s) found:\n")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print(f"\n  All checks passed. {len(refs)} references verified.")

    return issues


def full_report():
    """Run all checks and print summary."""
    print(f"\n{'#'*60}")
    print(f"  DEEPEVAL SKILL — UPDATE & INTEGRITY REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'#'*60}")

    check_version()
    stale = check_stale()
    issues = check_integrity()

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Stale references:  {len(stale)}")
    print(f"  Integrity issues:  {len(issues)}")

    if not stale and not issues:
        print(f"\n  STATUS: ALL CLEAR")
    else:
        print(f"\n  STATUS: NEEDS ATTENTION")

    print()
    return 0 if (not stale and not issues) else 1


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--report" in args:
        sys.exit(full_report())
    elif "--version" in args:
        check_version()
    elif "--stale" in args:
        threshold = STALE_THRESHOLD_DAYS
        idx = args.index("--stale")
        if idx + 1 < len(args) and args[idx + 1].isdigit():
            threshold = int(args[idx + 1])
        check_stale(threshold)
    elif "--integrity" in args:
        issues = check_integrity()
        sys.exit(1 if issues else 0)
    else:
        print(f"Unknown argument: {args}")
        print(__doc__)
        sys.exit(1)
