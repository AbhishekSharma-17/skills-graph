#!/usr/bin/env python3
"""
Agno Skill Version Checker

Compares the Agno version this skill was written for against the latest
release on PyPI and GitHub. Shows what changed so you know which reference
files may need updating.

Usage:
    python scripts/version_check.py              # Full check (PyPI + GitHub releases)
    python scripts/version_check.py --quick      # PyPI version check only
    python scripts/version_check.py --releases 5 # Show last N GitHub releases
    python scripts/version_check.py --update     # Update VERSION.json to latest after review
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
VERSION_FILE = SKILL_DIR / "VERSION.json"

PYPI_URL = "https://pypi.org/pypi/agno/json"
GITHUB_RELEASES_URL = "https://api.github.com/repos/agno-agi/agno/releases"
GITHUB_LATEST_URL = "https://api.github.com/repos/agno-agi/agno/releases/latest"


def load_version_manifest() -> dict:
    """Load the local VERSION.json manifest."""
    if not VERSION_FILE.exists():
        print(f"ERROR: {VERSION_FILE} not found.")
        print("Run this script from the agno-skill directory.")
        sys.exit(1)
    with open(VERSION_FILE) as f:
        return json.load(f)


def fetch_json(url: str, exit_on_fail: bool = True) -> dict | None:
    """Fetch JSON from a URL. Returns None on failure if exit_on_fail=False."""
    req = urllib.request.Request(url, headers={"User-Agent": "agno-skill-checker/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if exit_on_fail:
            print(f"HTTP Error {e.code} fetching {url}")
            sys.exit(1)
        return None
    except urllib.error.URLError as e:
        if exit_on_fail:
            print(f"Network error: {e.reason}")
            print("Check your internet connection.")
            sys.exit(1)
        return None


def parse_version(v: str) -> tuple:
    """Parse version string like '2.5.2' into comparable tuple."""
    v = v.lstrip("v")
    parts = v.split(".")
    return tuple(int(p) for p in parts)


def get_pypi_latest() -> dict:
    """Get latest version info from PyPI."""
    data = fetch_json(PYPI_URL)
    info = data.get("info", {})
    return {
        "version": info.get("version", "unknown"),
        "summary": info.get("summary", ""),
        "requires_python": info.get("requires_python", ""),
    }


def get_github_releases(count: int = 10) -> list | None:
    """Get recent GitHub releases. Returns None if GitHub is unreachable."""
    url = f"{GITHUB_RELEASES_URL}?per_page={count}"
    data = fetch_json(url, exit_on_fail=False)
    if data is None:
        return None
    result = []
    for r in data:
        result.append({
            "tag": r.get("tag_name", ""),
            "name": r.get("name", ""),
            "published": r.get("published_at", "")[:10],
            "body": r.get("body", ""),
            "url": r.get("html_url", ""),
        })
    return result


def get_releases_since(current_version: str, releases: list) -> list:
    """Filter releases newer than current_version."""
    current = parse_version(current_version)
    newer = []
    for r in releases:
        tag = r["tag"]
        try:
            rv = parse_version(tag)
        except (ValueError, IndexError):
            continue
        if rv > current:
            newer.append(r)
    return newer


def print_header(text: str):
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}")


def print_status(manifest: dict, pypi: dict):
    """Print version comparison status."""
    current = manifest["agno_version"]
    latest = pypi["version"]

    print_header("Agno Skill Version Check")
    print(f"  Skill written for:  v{current}")
    print(f"  Latest on PyPI:     v{latest}")
    print(f"  Last checked:       {manifest['last_checked']}")
    print(f"  Skill version:      {manifest['skill_version']}")

    current_t = parse_version(current)
    latest_t = parse_version(latest)

    if current_t == latest_t:
        print(f"\n  ✅ UP TO DATE — skill matches latest Agno release")
    elif current_t > latest_t:
        print(f"\n  ⚠️  Skill version is AHEAD of PyPI (dev build?)")
    else:
        # Determine severity
        if current_t[0] != latest_t[0]:
            severity = "MAJOR"
        elif current_t[1] != latest_t[1]:
            severity = "MINOR"
        else:
            severity = "PATCH"
        print(f"\n  ⚠️  UPDATE AVAILABLE — {severity} version change")
        print(f"     {current} → {latest}")


def print_reference_status(manifest: dict):
    """Print per-reference file status."""
    print_header("Reference File Status")
    refs = manifest.get("references", {})
    for filename, info in refs.items():
        written_for = info.get("written_for", "unknown")
        last_updated = info.get("last_updated", "unknown")
        topics = ", ".join(info.get("topics", []))
        print(f"\n  📄 {filename}")
        print(f"     Written for: v{written_for}  |  Updated: {last_updated}")
        print(f"     Topics: {topics}")


def print_releases(releases: list, label: str = "Recent Releases"):
    """Print release notes."""
    print_header(label)
    if not releases:
        print("  No releases found.")
        return

    for r in releases:
        print(f"\n  🏷  {r['tag']}  ({r['published']})")
        if r["name"] and r["name"] != r["tag"]:
            print(f"     {r['name']}")
        body = r.get("body", "").strip()
        if body:
            # Show first 15 lines of release notes
            lines = body.split("\n")[:15]
            for line in lines:
                print(f"     {line}")
            if len(body.split("\n")) > 15:
                print(f"     ... ({len(body.split(chr(10)))} total lines)")
                print(f"     Full notes: {r['url']}")
        print()


def print_update_suggestions(newer_releases: list, manifest: dict):
    """Suggest which reference files may need updates."""
    if not newer_releases:
        return

    print_header("Update Suggestions")

    # Collect all release body text
    all_notes = " ".join(r.get("body", "") for r in newer_releases).lower()

    # Keyword mapping to reference files
    keyword_map = {
        "agents.md": ["agent", "tool", "memory", "knowledge", "storage", "session", "structured output", "rag"],
        "teams.md": ["team", "coordinate", "route", "broadcast", "delegate", "member", "leader"],
        "workflows.md": ["workflow", "step", "parallel", "loop", "condition", "router", "pipeline", "stepin", "stepout"],
        "workflow-patterns.md": ["workflow", "step", "parallel", "loop", "condition", "router", "pipeline"],
    }

    flagged = {}
    for filename, keywords in keyword_map.items():
        matches = [kw for kw in keywords if kw in all_notes]
        if matches:
            flagged[filename] = matches

    if flagged:
        print("  Based on release notes, these files may need updates:\n")
        for filename, keywords in flagged.items():
            ref_info = manifest.get("references", {}).get(filename, {})
            written_for = ref_info.get("written_for", "?")
            print(f"  📄 {filename} (written for v{written_for})")
            print(f"     Matched keywords: {', '.join(keywords)}")
    else:
        print("  No obvious matches found in release notes.")
        print("  Review the releases above manually to be sure.")

    print(f"\n  💡 To update, review the Agno docs and release notes,")
    print(f"     edit the reference files, then run:")
    print(f"     python scripts/version_check.py --update")


def update_manifest(manifest: dict, latest_version: str):
    """Update VERSION.json to mark current version."""
    today = date.today().isoformat()
    manifest["agno_version"] = latest_version
    manifest["last_checked"] = today

    # Update all reference entries
    for filename in manifest.get("references", {}):
        manifest["references"][filename]["written_for"] = latest_version
        manifest["references"][filename]["last_updated"] = today

    # Bump skill patch version
    sv = manifest.get("skill_version", "1.0.0").split(".")
    sv[-1] = str(int(sv[-1]) + 1)
    manifest["skill_version"] = ".".join(sv)

    with open(VERSION_FILE, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    print_header("VERSION.json Updated")
    print(f"  agno_version:  v{latest_version}")
    print(f"  last_checked:  {today}")
    print(f"  skill_version: {manifest['skill_version']}")
    print(f"\n  All reference files marked as updated.")


def main():
    parser = argparse.ArgumentParser(description="Check Agno version and suggest skill updates")
    parser.add_argument("--quick", action="store_true", help="PyPI check only (no GitHub releases)")
    parser.add_argument("--releases", type=int, default=10, help="Number of GitHub releases to fetch")
    parser.add_argument("--update", action="store_true", help="Update VERSION.json to latest version")
    args = parser.parse_args()

    manifest = load_version_manifest()

    # Always check PyPI
    print("Checking PyPI for latest Agno version...")
    pypi = get_pypi_latest()
    print_status(manifest, pypi)

    if args.quick:
        print_reference_status(manifest)
        return

    # Fetch GitHub releases
    print("\nFetching GitHub releases...")
    releases = get_github_releases(args.releases)

    if releases is None:
        print("  ⚠️  Could not reach GitHub API — skipping release notes.")
        print("     You can view releases at: https://github.com/agno-agi/agno/releases")
        print_reference_status(manifest)
        if args.update:
            current_t = parse_version(manifest["agno_version"])
            latest_t = parse_version(pypi["version"])
            if current_t < latest_t:
                update_manifest(manifest, pypi["version"])
            else:
                print("\n  Already up to date — nothing to update.")
        return

    # Show releases newer than current
    newer = get_releases_since(manifest["agno_version"], releases)
    if newer:
        print_releases(newer, f"Releases Since v{manifest['agno_version']}")
    else:
        print_releases(releases[:3], "Latest Releases")

    # Show reference status
    print_reference_status(manifest)

    # Show update suggestions
    if newer:
        print_update_suggestions(newer, manifest)

    # Update if requested
    if args.update:
        current_t = parse_version(manifest["agno_version"])
        latest_t = parse_version(pypi["version"])
        if current_t < latest_t:
            update_manifest(manifest, pypi["version"])
        else:
            print("\n  Already up to date — nothing to update.")


if __name__ == "__main__":
    main()
