#!/usr/bin/env python3
"""Build step for the Amadeus Events site, run in CI before publishing.

This does two things:

1. Regenerates the OpenFeedback data for every event that ships a
   ``generate_openfeedback.py`` (each event's generator reads/writes files
   relative to its own folder, so it is run with that folder as the cwd).
2. Validates that every JSON file in the repository parses, so a malformed
   data file fails the build instead of being published.

Usage (from anywhere):
    python scripts/ci/build.py
"""

import json
import subprocess
import sys
from pathlib import Path

# This script lives in scripts/ci/, so the repository root is two levels up.
REPO_ROOT = Path(__file__).resolve().parents[2]

# Folders that are templates/tooling, not published event data.
EXCLUDED_DIRS = {".git", ".github", "_template", "scripts", ".kiro"}


def regenerate_openfeedback():
    """Run every event's generate_openfeedback.py from its own folder."""
    generators = [
        p
        for p in REPO_ROOT.rglob("generate_openfeedback.py")
        if not set(p.relative_to(REPO_ROOT).parts) & EXCLUDED_DIRS
    ]
    for generator in sorted(generators):
        event_dir = generator.parent
        print(f"Generating OpenFeedback data in {event_dir.relative_to(REPO_ROOT)}")
        subprocess.run(
            [sys.executable, generator.name],
            cwd=event_dir,
            check=True,
        )


def validate_json():
    """Ensure every JSON file in the repo parses."""
    errors = []
    for path in REPO_ROOT.rglob("*.json"):
        if set(path.relative_to(REPO_ROOT).parts) & EXCLUDED_DIRS:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            errors.append(f"{path.relative_to(REPO_ROOT)}: {exc}")

    if errors:
        print("Invalid JSON files found:")
        print("\n".join(errors))
        sys.exit(1)
    print("All JSON files valid.")


def main():
    regenerate_openfeedback()
    validate_json()
    print("Build complete.")


if __name__ == "__main__":
    main()
