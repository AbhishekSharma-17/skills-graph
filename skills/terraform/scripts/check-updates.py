#!/usr/bin/env python3
"""
Terraform Skill — Update Checker
================================
Checks for new upstream Terraform versions and validates skill integrity.

Usage:
    python scripts/check-updates.py              # Full report
    python scripts/check-updates.py --version    # Only check upstream version
    python scripts/check-updates.py --integrity  # Verify routing table references
    python scripts/check-updates.py --stale      # Show stale reference files
    python scripts/check-updates.py --stale 60   # Custom threshold (days)
    python scripts/check-updates.py --report     # Generate full report
    python scripts/check-updates.py --sitemap    # Check docs sitemap freshness
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

# Terraform is distributed via GitHub releases, not PyPI/npm.
UPSTREAM_VERSION_URL = "https://api.github.com/repos/hashicorp/terraform/releases/latest"
SITEMAP_URL = "https://developer.hashicorp.com/sitemap.xml"
STALE_THRESHOLD_DAYS = 90


def load_version():
    with open(VERSION_FILE) as f:
        return json.load(f)


def fetch_upstream_version():
    """Fetch the latest stable Terraform version from GitHub releases."""
    try:
        req = Request(
            UPSTREAM_VERSION_URL,
            headers={
                "User-Agent": "skill-checker/1.0",
                "Accept": "application/vnd.github+json",
            },
        )
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            tag = data.get("tag_name", "")
            # Strip leading 'v' if present (e.g., v1.11.4 -> 1.11.4)
            version = tag.lstrip("v")
            if not version:
                return {"error": "Empty tag name from GitHub API"}
            return {"latest": version, "published_at": data.get("published_at")}
    except (URLError, KeyError, json.JSONDecodeError) as e:
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
    published = upstream.get("published_at", "?")
    print(f"  Latest upstream:   {latest}")
    print(f"  Published:         {published}")

    if tracked == latest:
        print("\n  UP TO DATE")
        return True
    else:
        print(f"\n  UPDATE AVAILABLE: {tracked} -> {latest}")
        print("\n  Action needed:")
        print("    1. Review CHANGELOG: https://github.com/hashicorp/terraform/blob/main/CHANGELOG.md")
        print("    2. Check for breaking changes before bumping")
        print("    3. Update affected reference files")
        print("    4. Bump source_version_tracked in VERSION.json")
        return False


def check_sitemap():
    """Check that key documentation pages still exist."""
    print(f"\n{'=' * 60}")
    print("  DOCS SITEMAP CHECK")
    print(f"{'=' * 60}")
    ver = load_version()
    base = ver.get("urls", {}).get("docs", "https://developer.hashicorp.com")
    refs = ver.get("references", {})

    missing = []
    for file, info in refs.items():
        page = info.get("source_page", "")
        if not page:
            continue
        url = f"{base.rstrip('/docs')}{page}"
        try:
            req = Request(url, headers={"User-Agent": "skill-checker/1.0"})
            with urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    missing.append((file, url, resp.status))
        except URLError as e:
            missing.append((file, url, str(e)))

    if missing:
        print(f"\n  {len(missing)} reference(s) may have moved or been removed:\n")
        for f, u, status in missing:
            print(f"  {f:<40} {status}  {u}")
    else:
        print(f"\n  All {len(refs)} source pages accessible.")

    return len(missing) == 0


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
        print(f"  {'File':<40} {'Written For':<15} {'Last Updated'}")
        print(f"  {'-' * 40} {'-' * 15} {'-' * 12}")
        for ref, wf, up in stale:
            print(f"  {ref:<40} {wf:<15} {up}")
    else:
        print(f"\n  All references updated within {threshold_days} days")

    return len(stale) == 0


def generate_report():
    """Generate a full update report."""
    print(f"\n{'#' * 60}")
    print("  TERRAFORM SKILL — UPDATE REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'#' * 60}")

    v_ok = check_version()
    f_ok = check_integrity()
    s_ok = check_stale()

    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"{'=' * 60}")

    def status(ok):
        return "Up to date" if ok else ("Check needed" if ok is None else "Action needed")

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
