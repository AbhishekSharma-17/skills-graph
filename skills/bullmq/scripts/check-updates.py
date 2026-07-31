#!/usr/bin/env python3
"""
BullMQ Skill Update Checker
================================
Checks for upstream BullMQ (npm) updates and validates skill integrity.

Usage:
    python scripts/check-updates.py              # Full report
    python scripts/check-updates.py --version    # Check npm version
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

NPM_PACKAGE = "bullmq"
NPM_REGISTRY_URL = f"https://registry.npmjs.org/{NPM_PACKAGE}/latest"
STALE_THRESHOLD_DAYS = 90


def load_version():
    with open(VERSION_FILE) as f:
        return json.load(f)


def check_version():
    """Compare tracked version against npm latest."""
    ver = load_version()
    print(f"\n{'='*60}")
    print(f"  VERSION CHECK")
    print(f"{'='*60}")
    print(f"  Skill version:     {ver['skill_version']}")
    print(f"  Tracked source:    {ver['source_version_tracked']}")
    print(f"  Snapshot date:     {ver['docs_snapshot_date']}")

    try:
        req = Request(NPM_REGISTRY_URL, headers={"User-Agent": "skill-checker/1.0"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            latest = data.get("version", "unknown")
            print(f"  npm latest:        {latest}")
            print(f"\n  Check https://github.com/taskforcesh/bullmq/releases for changes")
            return True
    except (URLError, KeyError) as e:
        print(f"\n  Could not reach npm registry: {e}")
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
        for ref, wf, up in stale:
            print(f"  {ref:<45} written_for={wf}  updated={up}")
    else:
        print(f"\n  All references updated within {threshold_days} days")
    return len(stale) == 0


def check_integrity():
    """Verify all SKILL.md references exist on disk."""
    print(f"\n{'='*60}")
    print(f"  FILE INTEGRITY CHECK")
    print(f"{'='*60}")

    missing = []
    total = 0
    with open(SKILL_MD) as f:
        for line in f:
            if "references/" in line and ".md" in line:
                start = line.find("references/")
                if start >= 0:
                    end = line.find(".md", start) + 3
                    ref_path = line[start:end]
                    full_path = SKILL_DIR / ref_path
                    total += 1
                    if not full_path.exists():
                        missing.append(ref_path)

    if missing:
        print(f"\n  {len(missing)} BROKEN reference(s):")
        for m in missing:
            print(f"    MISSING: {m}")
    else:
        print(f"\n  All {total} references verified on disk")

    actual = list(REFERENCES_DIR.rglob("*.md"))
    print(f"  Total .md files in references/: {len(actual)}")

    oversized = []
    for f in actual:
        lines = len(f.read_text().splitlines())
        if lines > 500:
            oversized.append((f.name, lines))

    if oversized:
        print(f"\n  {len(oversized)} file(s) exceed 500-line limit:")
        for name, lines in oversized:
            print(f"    {name}: {lines} lines")
    else:
        print(f"  All files within 500-line limit")

    return len(missing) == 0 and len(oversized) == 0


def generate_report():
    print(f"\n{'#'*60}")
    print(f"  BULLMQ SKILL — UPDATE REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'#'*60}")

    v_ok = check_version()
    st_ok = check_stale()
    f_ok = check_integrity()

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Version:    {'Checked' if v_ok else 'Could not check'}")
    print(f"  Freshness:  {'All recent' if st_ok else 'Stale files found'}")
    print(f"  Integrity:  {'All valid' if f_ok else 'Issues found'}")


def main():
    if not VERSION_FILE.exists():
        print("ERROR: VERSION.json not found.")
        sys.exit(1)

    args = sys.argv[1:]
    if not args or "--report" in args:
        generate_report()
    elif "--version" in args:
        check_version()
    elif "--stale" in args:
        days = STALE_THRESHOLD_DAYS
        for i, a in enumerate(args):
            if a == "--stale" and i + 1 < len(args):
                try:
                    days = int(args[i + 1])
                except ValueError:
                    pass
        check_stale(days)
    elif "--integrity" in args:
        check_integrity()
    else:
        print(f"Usage: python {sys.argv[0]} [--version|--stale [days]|--integrity|--report]")


if __name__ == "__main__":
    main()
