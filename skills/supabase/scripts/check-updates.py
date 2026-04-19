#!/usr/bin/env python3
"""
Supabase Skill Update Checker
==============================
Checks for new upstream supabase-js versions and validates skill integrity.

Usage:
    python scripts/check-updates.py              # Full report
    python scripts/check-updates.py --version    # Only check upstream version
    python scripts/check-updates.py --integrity  # Verify routing table references
    python scripts/check-updates.py --stale      # Show stale reference files
    python scripts/check-updates.py --stale 60   # Custom threshold (days)
    python scripts/check-updates.py --report     # Generate full report
    python scripts/check-updates.py --sitemap    # Fetch docs sitemap for drift detection
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

UPSTREAM_VERSION_URL = "https://registry.npmjs.org/@supabase/supabase-js/latest"
DOCS_SITEMAP_URL = "https://supabase.com/sitemap.xml"

STALE_THRESHOLD_DAYS = 90


def load_version():
    """Load the VERSION.json file."""
    with open(VERSION_FILE) as f:
        return json.load(f)


def fetch_upstream_version():
    """Fetch the latest supabase-js version from npm."""
    try:
        req = Request(
            UPSTREAM_VERSION_URL,
            headers={"User-Agent": "skill-checker/1.0"},
        )
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if "version" in data:
                return {"latest": data["version"]}
            return {"error": "No 'version' field in npm response"}
    except (URLError, KeyError, json.JSONDecodeError) as e:
        return {"error": str(e)}


def fetch_sitemap():
    """Download the docs sitemap — useful to diff against tracked source pages."""
    try:
        req = Request(DOCS_SITEMAP_URL, headers={"User-Agent": "skill-checker/1.0"})
        with urlopen(req, timeout=15) as resp:
            xml = resp.read().decode()
            urls = []
            for line in xml.splitlines():
                line = line.strip()
                if line.startswith("<loc>") and line.endswith("</loc>"):
                    urls.append(line[5:-6])
            return urls
    except (URLError, Exception) as e:
        return {"error": str(e)}


def check_version():
    """Compare tracked version against upstream latest."""
    ver = load_version()
    tracked = ver.get("source_version_tracked", "unknown")

    print(f"\n{'=' * 60}")
    print("  VERSION CHECK")
    print(f"{'=' * 60}")
    print(f"  Skill version:     {ver.get('skill_version', '?')}")
    print(f"  Tracked source:    {tracked}")
    print(f"  Last checked:      {ver.get('last_checked', '?')}")

    upstream = fetch_upstream_version()
    if "error" in upstream:
        print(f"\n  Warning: {upstream['error']}")
        return None

    latest = upstream["latest"]
    print(f"  Latest upstream:   {latest}")

    if tracked and latest in tracked:
        print("\n  UP TO DATE")
        return True
    else:
        print(f"\n  UPDATE AVAILABLE: {tracked} -> {latest}")
        print("\n  Action needed:")
        print("    1. Check https://github.com/supabase/supabase-js/releases for breaking changes")
        print("    2. Update affected reference files")
        print("    3. Bump source_version_tracked in VERSION.json")
        return False


def check_integrity():
    """Verify all SKILL.md references exist on disk."""
    print(f"\n{'=' * 60}")
    print("  FILE INTEGRITY CHECK")
    print(f"{'=' * 60}")

    if not SKILL_MD.exists():
        print("\n  ERROR: SKILL.md not found")
        return False

    missing = []
    total = 0
    with open(SKILL_MD) as f:
        for line in f:
            if "references/" in line and ".md" in line:
                start = line.find("references/")
                if start >= 0:
                    rest = line[start:]
                    end = len(rest)
                    for char in ["`", "|", " ", ")", "\n"]:
                        pos = rest.find(char)
                        if 0 < pos < end:
                            end = pos
                    ref_path = rest[:end].strip()
                    if ref_path.endswith(".md"):
                        full_path = SKILL_DIR / ref_path
                        total += 1
                        if not full_path.exists():
                            missing.append(ref_path)

    if missing:
        print(f"\n  BROKEN reference(s): {len(missing)}")
        for m in missing:
            print(f"    MISSING: {m}")
    else:
        print(f"\n  All {total} references verified on disk")

    actual_files = list(REFERENCES_DIR.rglob("*.md")) if REFERENCES_DIR.exists() else []
    print(f"  Total .md files in references/: {len(actual_files)}")

    return len(missing) == 0


def check_stale(threshold_days=STALE_THRESHOLD_DAYS):
    """Find reference files that haven't been updated recently."""
    ver = load_version()
    refs = ver.get("references", {})
    cutoff = datetime.now() - timedelta(days=threshold_days)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    print(f"\n{'=' * 60}")
    print(f"  STALE REFERENCE CHECK (>{threshold_days} days)")
    print(f"{'=' * 60}")

    stale = []
    for ref, info in sorted(refs.items()):
        updated = info.get("last_updated", "unknown")
        if updated != "unknown" and updated < cutoff_str:
            stale.append((ref, info.get("written_for", "?"), updated))

    if stale:
        print(f"\n  {len(stale)} reference(s) may need review:\n")
        print(f"  {'File':<40} {'Written For':<25} {'Last Updated'}")
        print(f"  {'-' * 40} {'-' * 25} {'-' * 12}")
        for ref, wf, up in stale:
            print(f"  {ref:<40} {wf:<25} {up}")
    else:
        print(f"\n  All references updated within {threshold_days} days")

    return len(stale) == 0


def check_sitemap():
    """Fetch the upstream sitemap and report a quick tally."""
    print(f"\n{'=' * 60}")
    print("  DOCS SITEMAP CHECK")
    print(f"{'=' * 60}")

    urls = fetch_sitemap()
    if isinstance(urls, dict) and "error" in urls:
        print(f"\n  Warning: {urls['error']}")
        return None

    print(f"  Total URLs in sitemap: {len(urls)}")
    ver = load_version()
    tracked_pages = {info.get("source_page") for info in ver.get("references", {}).values()}
    tracked_urls = {f"https://supabase.com{p}" for p in tracked_pages if p}
    present = tracked_urls & set(urls)
    print(f"  Tracked pages present in sitemap: {len(present)}/{len(tracked_urls)}")
    missing_from_sitemap = tracked_urls - set(urls)
    if missing_from_sitemap:
        print("  Pages not found in current sitemap (may have moved):")
        for u in sorted(missing_from_sitemap):
            print(f"    {u}")
    return len(missing_from_sitemap) == 0


def generate_report():
    """Generate a full update report."""
    print(f"\n{'#' * 60}")
    print("  SUPABASE SKILL UPDATE REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'#' * 60}")

    v_ok = check_version()
    f_ok = check_integrity()
    s_ok = check_stale()

    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"{'=' * 60}")
    status = lambda ok: "Up to date" if ok else ("Check needed" if ok is None else "Action needed")
    print(f"  Version:    {status(v_ok)}")
    print(f"  Integrity:  {'All valid' if f_ok else 'Broken refs'}")
    print(f"  Freshness:  {'All recent' if s_ok else 'Stale files found'}")


def main():
    if not VERSION_FILE.exists():
        print("ERROR: VERSION.json not found. Run from the skill root directory.")
        sys.exit(1)

    args = sys.argv[1:]

    if not args or "--report" in args:
        generate_report()
    elif "--version" in args:
        check_version()
    elif "--integrity" in args:
        check_integrity()
    elif "--sitemap" in args:
        check_sitemap()
    elif "--stale" in args:
        days = STALE_THRESHOLD_DAYS
        for i, a in enumerate(args):
            if a == "--stale" and i + 1 < len(args):
                try:
                    days = int(args[i + 1])
                except ValueError:
                    pass
        check_stale(days)
    else:
        print(f"Usage: python {sys.argv[0]} [--version|--integrity|--sitemap|--stale [days]|--report]")


if __name__ == "__main__":
    main()
