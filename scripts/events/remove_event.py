#!/usr/bin/env python3
"""Remove an event from the Amadeus Events hub.

Reads events.json, presents an alphabetical list, and removes
the selected event's folder + registry entry.
"""

import json
import shutil
import sys
from pathlib import Path


def main():
    # This script lives in scripts/events/, so the repository root is two levels up.
    repo_root = Path(__file__).resolve().parents[2]
    events_path = repo_root / "events.json"

    if not events_path.exists():
        print("Error: events.json not found.")
        sys.exit(1)

    events = json.loads(events_path.read_text())
    if not events:
        print("No events registered in events.json.")
        sys.exit(0)

    # Sort alphabetically by name
    events_sorted = sorted(events, key=lambda e: e["name"].lower())

    print("\n📋 Registered events:\n")
    for i, event in enumerate(events_sorted, 1):
        folder_exists = (repo_root / event["slug"]).is_dir()
        status = "✓" if folder_exists else "⚠️  (folder missing)"
        print(f"  {i}. {event['name']} [{event['slug']}] {status}")

    print(f"\n  0. Cancel\n")

    try:
        choice = input("Select event to remove (number): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        sys.exit(0)

    if choice == "0" or choice == "":
        print("Cancelled.")
        sys.exit(0)

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(events_sorted):
            raise ValueError()
    except ValueError:
        print("Invalid selection.")
        sys.exit(1)

    selected = events_sorted[idx]
    slug = selected["slug"]
    name = selected["name"]

    # Confirm
    try:
        confirm = input(f'\n⚠️  Remove "{name}" ({slug}/)? This deletes the folder. [y/N]: ').strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        sys.exit(0)

    if confirm != "y":
        print("Cancelled.")
        sys.exit(0)

    # Remove folder
    event_dir = repo_root / slug
    if event_dir.is_dir():
        shutil.rmtree(event_dir)
        print(f"  ✓ Removed folder: {slug}/")
    else:
        print(f"  ⚠️  Folder not found: {slug}/ (skipping)")

    # Remove from events.json
    events = [e for e in events if e["slug"] != slug]
    events_path.write_text(json.dumps(events, indent=2, ensure_ascii=False) + "\n")
    print(f"  ✓ Removed from events.json")

    print(f'\n🗑️  Done! "{name}" has been removed.')


if __name__ == "__main__":
    main()
