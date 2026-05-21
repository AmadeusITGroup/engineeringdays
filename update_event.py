#!/usr/bin/env python3
"""
Update an existing event with a finalized program from a pretalx sessions JSON export.

Usage:
    python update_event.py <sessions.json> --slug "event-slug-2026"

This replaces CFP placeholder content with real session data:
1. Parses the pretalx sessions JSON to extract tracks, types, speakers, etc.
2. Updates config.json with real metadata (replaces example tracks/types)
3. Copies sessions into sessions.json
4. Generates program.html
5. Regenerates index.html (removes CFP links, adds "View Program")
6. Updates the root events.json registry with session count
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

from create_event import (
    parse_sessions,
    generate_event_json,
    generate_index_html,
    generate_program_html,
    generate_script_js,
    add_to_landing_page,
)


def main():
    parser = argparse.ArgumentParser(
        description="Update an existing event with finalized sessions from a pretalx JSON export."
    )
    parser.add_argument("sessions_file", help="Path to the pretalx sessions JSON export")
    parser.add_argument("--slug", required=True, help="Event folder name (e.g., 'engineering-days-2026')")
    args = parser.parse_args()

    repo_root = Path(__file__).parent
    event_dir = repo_root / args.slug

    # Validate inputs
    sessions_path = Path(args.sessions_file)
    if not sessions_path.exists():
        print(f"Error: Sessions file not found: {sessions_path}")
        sys.exit(1)

    if not event_dir.exists():
        print(f"Error: Event folder not found: {event_dir}")
        print(f"   Available events: {', '.join(d.name for d in repo_root.iterdir() if d.is_dir() and (d / 'config.json').exists())}")
        sys.exit(1)

    config_path = event_dir / "config.json"
    if not config_path.exists():
        print(f"Error: No config.json found in {event_dir}")
        sys.exit(1)

    # Load existing config to preserve user-edited fields
    existing_config = json.loads(config_path.read_text())

    # Load and parse sessions
    with open(sessions_path) as f:
        sessions_data = json.load(f)

    if not sessions_data:
        print("Error: Sessions file is empty.")
        sys.exit(1)

    print(f"🔄 Updating event: {existing_config['eventName']}")
    print(f"   Slug: {args.slug}")
    print(f"   Sessions file: {sessions_path.name} ({len(sessions_data)} sessions)")

    # Parse metadata from sessions
    meta = parse_sessions(sessions_data)

    # Preserve dates/locations from existing config if sessions don't provide them
    if not meta["locations"] and existing_config.get("locations"):
        meta["locations"] = existing_config["locations"]
    if not meta["start_date"] and existing_config.get("dates", {}).get("display"):
        meta["date_display_override"] = existing_config["dates"]["display"]

    print(f"   Tracks: {', '.join(meta['tracks'])}")
    print(f"   Session types: {', '.join(meta['session_types'].keys())}")
    print(f"   Speakers: {meta['speakers_count']}")
    print(f"   Locations: {len(meta['locations'])} sites")

    # Build a fake args namespace with preserved values from existing config
    class UpdateArgs:
        name = existing_config["eventName"]
        slug = args.slug
        tagline = existing_config.get("tagline", "")
        description = existing_config.get("description", "")
        organizer = existing_config.get("organizer", "DevRel")
        contact = existing_config.get("contact", "devrel@amadeus.com")

    update_args = UpdateArgs()

    # Generate updated config (now with real session data, not CFP placeholders)
    event_config = generate_event_json(meta, update_args)

    # Preserve any custom colors from existing config
    if existing_config.get("colors"):
        event_config["colors"] = existing_config["colors"]

    # Write updated files
    config_path.write_text(json.dumps(event_config, indent=2, ensure_ascii=False))
    print(f"  ✓ {args.slug}/config.json (updated with real data)")

    (event_dir / "index.html").write_text(generate_index_html(event_config, has_sessions=True))
    print(f"  ✓ {args.slug}/index.html (CFP removed, program linked)")

    (event_dir / "program.html").write_text(generate_program_html(event_config))
    print(f"  ✓ {args.slug}/program.html (generated)")

    (event_dir / "script.js").write_text(generate_script_js())
    print(f"  ✓ {args.slug}/script.js")

    shutil.copy2(sessions_path, event_dir / "sessions.json")
    print(f"  ✓ {args.slug}/sessions.json ({len(sessions_data)} sessions)")

    # Update landing page registry
    add_to_landing_page(event_config, meta, repo_root)

    print(f"\n🎉 Done! Event updated with finalized program.")
    print(f"   Preview: open {event_dir}/index.html in a browser")
    print(f"   Program: open {event_dir}/program.html in a browser")


if __name__ == "__main__":
    main()
