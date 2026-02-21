#!/usr/bin/env python3
"""
Agno Skill Update Checker
=========================
Checks for new Agno versions and docs changes to determine if skill files need updating.

Usage:
    python scripts/check-updates.py              # Full check (PyPI + docs sitemap)
    python scripts/check-updates.py --version    # Only check PyPI version
    python scripts/check-updates.py --sitemap    # Only check docs sitemap for new pages
    python scripts/check-updates.py --stale      # Show reference files older than N days
    python scripts/check-updates.py --report     # Generate full update report
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

# --- Config ---
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
VERSION_FILE = SKILL_DIR / "VERSION.json"
REFERENCES_DIR = SKILL_DIR / "references"
PYPI_JSON_URL = "https://pypi.org/pypi/agno/json"
DOCS_BASE = "https://docs.agno.com"
STALE_THRESHOLD_DAYS = 30


def load_version():
    """Load the VERSION.json file."""
    with open(VERSION_FILE) as f:
        return json.load(f)


def fetch_pypi_version():
    """Fetch the latest Agno version from PyPI."""
    try:
        req = Request(PYPI_JSON_URL, headers={"User-Agent": "agno-skill-checker/1.0"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            version = data["info"]["version"]
            releases = sorted(data["releases"].keys())
            # Get recent releases (last 10)
            recent = releases[-10:] if len(releases) > 10 else releases
            return {
                "latest": version,
                "recent_releases": recent,
                "summary": data["info"].get("summary", ""),
            }
    except (URLError, KeyError, json.JSONDecodeError) as e:
        return {"error": str(e)}


def check_version():
    """Compare tracked version against PyPI latest."""
    ver = load_version()
    tracked = ver["agno_version_tracked"]
    print(f"\n{'='*60}")
    print(f"  AGNO VERSION CHECK")
    print(f"{'='*60}")
    print(f"  Skill version:     {ver['skill_version']}")
    print(f"  Tracked Agno:      {tracked}")
    print(f"  Docs snapshot:     {ver['docs_snapshot_date']}")
    print(f"  Last checked:      {ver['last_checked']}")

    pypi = fetch_pypi_version()
    if "error" in pypi:
        print(f"\n  ⚠ Could not reach PyPI: {pypi['error']}")
        print(f"  Manual check: {ver['urls']['pypi']}")
        return False

    latest = pypi["latest"]
    print(f"  Latest on PyPI:    {latest}")

    if tracked == latest:
        print(f"\n  ✅ UP TO DATE — skill tracks the latest version")
        return True
    else:
        print(f"\n  🔄 UPDATE AVAILABLE: {tracked} → {latest}")
        print(f"\n  Recent releases:")
        for r in pypi["recent_releases"]:
            marker = " ← tracked" if r == tracked else (" ← latest" if r == latest else "")
            print(f"    {r}{marker}")
        print(f"\n  Action needed:")
        print(f"    1. Check changelog: {ver['urls']['changelog']}")
        print(f"    2. Review docs for breaking changes")
        print(f"    3. Update affected reference files")
        print(f"    4. Bump agno_version_tracked in VERSION.json")
        return False


def check_sitemap():
    """Check docs sitemap for new/removed pages."""
    ver = load_version()
    known_paths = set(ver.get("docs_sitemap", []))
    print(f"\n{'='*60}")
    print(f"  DOCS SITEMAP CHECK")
    print(f"{'='*60}")
    print(f"  Known doc pages:   {len(known_paths)}")
    print(f"  Covered sections:  {len(ver.get('references', {}))}")

    # Try to fetch current sitemap from docs
    try:
        req = Request(
            f"{DOCS_BASE}/llms-full.txt",
            headers={"User-Agent": "agno-skill-checker/1.0"},
        )
        with urlopen(req, timeout=15) as resp:
            content = resp.read().decode()
            # Extract paths that look like doc URLs
            live_paths = set()
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("/") and not line.startswith("//"):
                    live_paths.add(line.split("#")[0])  # Remove anchors

            new_pages = live_paths - known_paths
            removed_pages = known_paths - live_paths

            if new_pages:
                print(f"\n  🆕 NEW PAGES FOUND ({len(new_pages)}):")
                for p in sorted(new_pages)[:20]:
                    print(f"    + {p}")
                if len(new_pages) > 20:
                    print(f"    ... and {len(new_pages) - 20} more")
            else:
                print(f"\n  ✅ No new pages detected")

            if removed_pages:
                print(f"\n  ❌ REMOVED PAGES ({len(removed_pages)}):")
                for p in sorted(removed_pages):
                    print(f"    - {p}")

            return len(new_pages) == 0
    except URLError as e:
        print(f"\n  ⚠ Could not fetch sitemap: {e}")
        print(f"  Manual check: {DOCS_BASE}")
        print(f"\n  Alternative: Use Tavily to crawl {DOCS_BASE}/introduction")
        print(f"  and compare sidebar navigation against VERSION.json docs_sitemap")
        return None


def check_stale(threshold_days=STALE_THRESHOLD_DAYS):
    """Find reference files that haven't been updated recently."""
    ver = load_version()
    refs = ver.get("references", {})
    cutoff = datetime.now() - timedelta(days=threshold_days)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"  STALE REFERENCE CHECK (>{threshold_days} days)")
    print(f"{'='*60}")

    stale = []
    for ref, info in sorted(refs.items()):
        updated = info.get("last_updated", "unknown")
        if updated < cutoff_str:
            stale.append((ref, info.get("written_for", "?"), updated))

    if stale:
        print(f"\n  ⚠ {len(stale)} reference(s) may need review:\n")
        print(f"  {'File':<35} {'Written For':<15} {'Last Updated'}")
        print(f"  {'─'*35} {'─'*15} {'─'*12}")
        for ref, wf, up in stale:
            print(f"  {ref:<35} {wf:<15} {up}")
    else:
        print(f"\n  ✅ All references updated within {threshold_days} days")

    return len(stale) == 0


def check_file_integrity():
    """Verify all SKILL.md references exist on disk."""
    skill_md = SKILL_DIR / "SKILL.md"
    print(f"\n{'='*60}")
    print(f"  FILE INTEGRITY CHECK")
    print(f"{'='*60}")

    missing = []
    total = 0
    with open(skill_md) as f:
        for line in f:
            if "references/" in line and ".md" in line:
                # Extract reference path
                start = line.find("references/")
                if start >= 0:
                    end = line.find(".md", start) + 3
                    ref_path = line[start:end]
                    full_path = SKILL_DIR / ref_path
                    total += 1
                    if not full_path.exists():
                        missing.append(ref_path)

    if missing:
        print(f"\n  ❌ {len(missing)} BROKEN reference(s):")
        for m in missing:
            print(f"    MISSING: {m}")
    else:
        print(f"\n  ✅ All {total} references verified on disk")

    # Count actual files
    actual_files = list(REFERENCES_DIR.rglob("*.md"))
    print(f"  Total .md files in references/: {len(actual_files)}")

    return len(missing) == 0


def generate_report():
    """Generate a full update report."""
    print(f"\n{'#'*60}")
    print(f"  AGNO SKILL UPDATE REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'#'*60}")

    v_ok = check_version()
    s_ok = check_sitemap()
    st_ok = check_stale()
    f_ok = check_file_integrity()

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Version:    {'✅ Up to date' if v_ok else '🔄 Update available'}")
    print(f"  Sitemap:    {'✅ No changes' if s_ok else ('⚠ Check needed' if s_ok is None else '🆕 New pages found')}")
    print(f"  Freshness:  {'✅ All recent' if st_ok else '⚠ Stale files found'}")
    print(f"  Integrity:  {'✅ All valid' if f_ok else '❌ Broken refs'}")

    if all([v_ok, s_ok, st_ok, f_ok]):
        print(f"\n  🎉 Everything looks good! No updates needed.")
    else:
        print(f"\n  📋 Action items:")
        if not v_ok:
            print(f"    → Check Agno changelog and update affected references")
        if s_ok is False:
            print(f"    → Review new docs pages and create reference files")
        if not st_ok:
            print(f"    → Re-check stale references against current docs")
        if not f_ok:
            print(f"    → Fix or recreate missing reference files")


def main():
    if not VERSION_FILE.exists():
        print("ERROR: VERSION.json not found. Run from the skill root directory.")
        sys.exit(1)

    args = sys.argv[1:]

    if not args or "--report" in args:
        generate_report()
    elif "--version" in args:
        check_version()
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
    elif "--integrity" in args:
        check_file_integrity()
    else:
        print(f"Usage: python {sys.argv[0]} [--version|--sitemap|--stale [days]|--integrity|--report]")


if __name__ == "__main__":
    main()
