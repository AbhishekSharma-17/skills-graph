#!/usr/bin/env python3
"""
Microsoft Agent Framework Skill - Freshness Checker

Validates that the skill's reference documentation is up-to-date
with the latest Microsoft Agent Framework SDK releases.

Usage:
    python check-freshness.py [--verbose] [--fix] [--output json|text]

Checks:
    1. PyPI package version vs skill's tracked version
    2. GitHub repository latest commit/release vs skill's last-updated date
    3. Reference file completeness (all expected files exist)
    4. Reference file staleness (files older than threshold)
    5. SKILL.md routing table integrity (all referenced files exist)
    6. Dead links in routing table
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ─── Configuration ────────────────────────────────────────────────────────────

SKILL_DIR = Path(__file__).parent.parent
REFERENCES_DIR = SKILL_DIR / "references"
METADATA_DIR = SKILL_DIR / "metadata"
SKILL_MD = SKILL_DIR / "SKILL.md"
VERSION_TRACKING = METADATA_DIR / "version-tracking.json"
SOURCES_JSON = METADATA_DIR / "sources.json"

PYPI_PACKAGE = "microsoft-agent-framework"
PYPI_URL = f"https://pypi.org/pypi/{PYPI_PACKAGE}/json"
GITHUB_REPO = "microsoft/agent-framework"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}"

# Maximum age (days) before a reference file is considered stale
STALENESS_THRESHOLD_DAYS = 90

# Expected reference files (core set that must exist)
EXPECTED_REFERENCE_FILES = [
    "01-getting-started.md",
    "02-running-agents.md",
    "03-structured-output.md",
    "04-tools-function.md",
    "05-tools-hosted.md",
    "06-rag.md",
    "07-sessions.md",
    "08-memory.md",
    "09-middleware.md",
    "10-providers.md",
    "11-workflows-core.md",
    "11a-workflow-executors.md",
    "11b-workflow-edges.md",
    "11c-workflow-events.md",
    "11d-workflow-builder-execution.md",
    "11e-workflow-agents.md",
    "11f-workflow-human-in-loop.md",
    "11g-workflow-state.md",
    "11h-workflow-checkpoints.md",
    "11i-workflow-declarative.md",
    "11j-workflow-observability.md",
    "11k-workflow-as-agent.md",
    "11l-workflow-visualization.md",
    "12a-orchestration-sequential.md",
    "12b-orchestration-concurrent.md",
    "12c-orchestration-handoff.md",
    "12d-orchestration-groupchat.md",
    "12e-orchestration-magentic.md",
    "13a-azure-functions.md",
    "13b-a2a-protocol.md",
    "13c-ag-ui-protocol.md",
    "13d-openai-compatible.md",
    "13e-deployment-guide.md",
    "14-declarative.md",
    "15-observability.md",
    "15a-tracing-observability.md",
    "16-multimodal.md",
    "17-custom-agents.md",
    "18-api-reference.md",
    "19-security.md",
    "20-purview.md",
    "21-m365-integration.md",
    "22-design-patterns-core.md",
    "23-design-patterns-advanced.md",
]


# ─── Utility Functions ────────────────────────────────────────────────────────

def fetch_json(url: str, timeout: int = 10) -> Optional[dict]:
    """Fetch JSON from URL with error handling."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "skill-freshness-checker/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        return None


def load_version_tracking() -> dict:
    """Load version tracking metadata."""
    if VERSION_TRACKING.exists():
        with open(VERSION_TRACKING) as f:
            return json.load(f)
    return {
        "skill_version": "1.0.0",
        "framework_version": "unknown",
        "last_checked": None,
        "last_updated": None,
    }


def save_version_tracking(data: dict):
    """Save version tracking metadata."""
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(VERSION_TRACKING, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ─── Check Functions ──────────────────────────────────────────────────────────

class FreshnessReport:
    """Collects and reports freshness check results."""

    def __init__(self):
        self.checks: List[Dict] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def add_check(self, name: str, status: str, detail: str, severity: str = "info"):
        self.checks.append({
            "name": name,
            "status": status,
            "detail": detail,
            "severity": severity,
        })
        if severity == "warning":
            self.warnings.append(f"{name}: {detail}")
        elif severity == "error":
            self.errors.append(f"{name}: {detail}")

    @property
    def is_fresh(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict:
        return {
            "timestamp": datetime.now().isoformat(),
            "is_fresh": self.is_fresh,
            "total_checks": len(self.checks),
            "warnings": len(self.warnings),
            "errors": len(self.errors),
            "checks": self.checks,
        }

    def print_text(self, verbose: bool = False):
        print("=" * 70)
        print("  Microsoft Agent Framework Skill — Freshness Report")
        print("=" * 70)
        print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Status:    {'FRESH' if self.is_fresh else 'STALE'}")
        print(f"  Checks:    {len(self.checks)} total, {len(self.warnings)} warnings, {len(self.errors)} errors")
        print("=" * 70)

        for check in self.checks:
            icon = {"pass": "✅", "fail": "❌", "warn": "⚠️", "skip": "⏭️"}.get(check["status"], "❓")
            if verbose or check["severity"] in ("warning", "error"):
                print(f"  {icon} [{check['severity'].upper():7s}] {check['name']}")
                print(f"     {check['detail']}")

        if self.errors:
            print("\n  ERRORS:")
            for err in self.errors:
                print(f"    ❌ {err}")

        if self.warnings:
            print("\n  WARNINGS:")
            for warn in self.warnings:
                print(f"    ⚠️  {warn}")

        print("=" * 70)


def check_pypi_version(report: FreshnessReport, tracking: dict, verbose: bool):
    """Check if PyPI has a newer version than what we track."""
    data = fetch_json(PYPI_URL)

    if data is None:
        report.add_check(
            "PyPI Version",
            "skip",
            f"Could not reach PyPI for {PYPI_PACKAGE} (may not be published yet)",
            "info",
        )
        return

    latest = data.get("info", {}).get("version", "unknown")
    tracked = tracking.get("framework_version", "unknown")

    if latest == tracked:
        report.add_check("PyPI Version", "pass", f"Up to date: {latest}", "info")
    else:
        report.add_check(
            "PyPI Version",
            "warn",
            f"PyPI has {latest}, skill tracks {tracked}",
            "warning",
        )


def check_github_release(report: FreshnessReport, tracking: dict, verbose: bool):
    """Check GitHub for latest release."""
    data = fetch_json(f"{GITHUB_API}/releases/latest")

    if data is None:
        # Try tags instead
        tags = fetch_json(f"{GITHUB_API}/tags")
        if tags and len(tags) > 0:
            latest_tag = tags[0].get("name", "unknown")
            report.add_check(
                "GitHub Release",
                "warn",
                f"Latest tag: {latest_tag} (no formal release found)",
                "info",
            )
        else:
            report.add_check(
                "GitHub Release",
                "skip",
                "Could not fetch GitHub releases/tags",
                "info",
            )
        return

    release_name = data.get("tag_name", "unknown")
    published = data.get("published_at", "")
    tracked = tracking.get("framework_version", "unknown")

    if release_name == tracked or tracked in release_name:
        report.add_check(
            "GitHub Release",
            "pass",
            f"Up to date: {release_name} (published {published[:10]})",
            "info",
        )
    else:
        report.add_check(
            "GitHub Release",
            "warn",
            f"GitHub has {release_name}, skill tracks {tracked}",
            "warning",
        )


def check_reference_completeness(report: FreshnessReport, verbose: bool):
    """Check that all expected reference files exist."""
    missing = []
    present = []

    for filename in EXPECTED_REFERENCE_FILES:
        filepath = REFERENCES_DIR / filename
        if filepath.exists():
            present.append(filename)
        else:
            missing.append(filename)

    if missing:
        report.add_check(
            "Reference Completeness",
            "fail",
            f"Missing {len(missing)} files: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}",
            "error",
        )
    else:
        report.add_check(
            "Reference Completeness",
            "pass",
            f"All {len(EXPECTED_REFERENCE_FILES)} expected reference files present",
            "info",
        )


def check_reference_staleness(report: FreshnessReport, verbose: bool):
    """Check if any reference files are older than the staleness threshold."""
    stale_files = []
    threshold = datetime.now() - timedelta(days=STALENESS_THRESHOLD_DAYS)

    if not REFERENCES_DIR.exists():
        report.add_check("Reference Staleness", "fail", "References directory not found", "error")
        return

    for filepath in sorted(REFERENCES_DIR.glob("*.md")):
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        if mtime < threshold:
            age_days = (datetime.now() - mtime).days
            stale_files.append((filepath.name, age_days))

    if stale_files:
        report.add_check(
            "Reference Staleness",
            "warn",
            f"{len(stale_files)} files older than {STALENESS_THRESHOLD_DAYS} days: "
            + ", ".join(f"{f}({d}d)" for f, d in stale_files[:5]),
            "warning",
        )
    else:
        report.add_check(
            "Reference Staleness",
            "pass",
            f"All reference files updated within last {STALENESS_THRESHOLD_DAYS} days",
            "info",
        )


def check_routing_table(report: FreshnessReport, verbose: bool):
    """Check SKILL.md routing table references valid files."""
    if not SKILL_MD.exists():
        report.add_check("Routing Table", "fail", "SKILL.md not found", "error")
        return

    with open(SKILL_MD) as f:
        content = f.read()

    # Extract file references from routing table
    # Pattern: references/filename.md or `filename.md`
    file_refs = set(re.findall(r"references/([^\s|`,\)]+\.md)", content))

    missing_refs = []
    valid_refs = []

    for ref in sorted(file_refs):
        filepath = REFERENCES_DIR / ref
        if filepath.exists():
            valid_refs.append(ref)
        else:
            missing_refs.append(ref)

    if missing_refs:
        report.add_check(
            "Routing Table",
            "fail",
            f"{len(missing_refs)} dead references: {', '.join(missing_refs[:5])}",
            "error",
        )
    else:
        report.add_check(
            "Routing Table",
            "pass",
            f"All {len(valid_refs)} routing table references valid",
            "info",
        )


def check_file_sizes(report: FreshnessReport, verbose: bool):
    """Check that reference files have minimum content."""
    small_files = []
    MIN_LINES = 50

    if not REFERENCES_DIR.exists():
        return

    for filepath in sorted(REFERENCES_DIR.glob("*.md")):
        with open(filepath) as f:
            line_count = sum(1 for _ in f)
        if line_count < MIN_LINES:
            small_files.append((filepath.name, line_count))

    if small_files:
        report.add_check(
            "File Sizes",
            "warn",
            f"{len(small_files)} files under {MIN_LINES} lines: "
            + ", ".join(f"{f}({l}L)" for f, l in small_files[:5]),
            "warning",
        )
    else:
        report.add_check(
            "File Sizes",
            "pass",
            f"All reference files meet minimum {MIN_LINES}-line threshold",
            "info",
        )


def check_total_coverage(report: FreshnessReport, verbose: bool):
    """Report total skill coverage statistics."""
    if not REFERENCES_DIR.exists():
        return

    total_files = 0
    total_lines = 0
    total_bytes = 0

    for filepath in REFERENCES_DIR.glob("*.md"):
        total_files += 1
        stat = filepath.stat()
        total_bytes += stat.st_size
        with open(filepath) as f:
            total_lines += sum(1 for _ in f)

    report.add_check(
        "Total Coverage",
        "pass",
        f"{total_files} files, {total_lines:,} lines, {total_bytes / 1024:.0f} KB",
        "info",
    )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Check freshness of Microsoft Agent Framework skill documentation"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all checks")
    parser.add_argument("--fix", action="store_true", help="Update version tracking after check")
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    # Load tracking data
    tracking = load_version_tracking()

    # Run all checks
    report = FreshnessReport()

    check_pypi_version(report, tracking, args.verbose)
    check_github_release(report, tracking, args.verbose)
    check_reference_completeness(report, args.verbose)
    check_reference_staleness(report, args.verbose)
    check_routing_table(report, args.verbose)
    check_file_sizes(report, args.verbose)
    check_total_coverage(report, args.verbose)

    # Output results
    if args.output == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        report.print_text(verbose=args.verbose)

    # Optionally update tracking
    if args.fix:
        tracking["last_checked"] = datetime.now().isoformat()
        save_version_tracking(tracking)
        print(f"\n  Updated version tracking at {VERSION_TRACKING}")

    # Exit code: 0 if fresh, 1 if stale
    sys.exit(0 if report.is_fresh else 1)


if __name__ == "__main__":
    main()
