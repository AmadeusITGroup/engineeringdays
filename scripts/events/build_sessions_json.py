#!/usr/bin/env python3
"""Build a pretalx-compatible sessions JSON file from manual talk entries."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def prompt_non_empty(label):
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("  This field is required.")


def prompt_optional(label, default=""):
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def parse_speakers(raw):
    return [s.strip() for s in raw.split(",") if s.strip()]


def validate_iso_datetime(value):
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False


def prompt_iso_datetime(label):
    while True:
        value = input(f"{label} (ISO 8601, e.g. 2026-11-10T09:00:00+01:00): ").strip()
        if validate_iso_datetime(value):
            return value
        print("  Invalid ISO date/time. Please try again.")


def collect_talk(index):
    print(f"\nTalk #{index}")
    print("-" * 40)

    title = prompt_non_empty("Title")
    session_type = prompt_optional("Session type", "Talk")
    track = prompt_optional("Track", "General")
    description = prompt_optional("Description", "")

    while True:
        speakers_raw = prompt_non_empty("Speaker names (comma-separated)")
        speakers = parse_speakers(speakers_raw)
        if speakers:
            break
        print("  Enter at least one speaker.")

    room = prompt_optional("Room", "TBD")
    start = prompt_iso_datetime("Start")
    end = prompt_iso_datetime("End")

    return {
        "ID": f"MANUAL{index:03d}",
        "Proposal title": title,
        "Session type": {"en": session_type},
        "Track": {"en": track},
        "Description": description,
        "Speaker names": speakers,
        "Room": {"en": room},
        "Start": start,
        "End": end,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Create a pretalx-like sessions JSON file by manually entering talks."
    )
    parser.add_argument(
        "--out",
        default="sessions-manual.json",
        help="Output JSON path (default: sessions-manual.json)",
    )
    args = parser.parse_args()

    print("Manual Sessions Builder")
    print("Enter your talks. Leave title empty when finished.\n")

    sessions = []
    index = 1

    while True:
        first = input("Add a talk? [Y/n]: ").strip().lower()
        if first in {"n", "no"}:
            break
        if first not in {"", "y", "yes"}:
            print("Please answer y or n.")
            continue

        sessions.append(collect_talk(index))
        index += 1

    if not sessions:
        print("No talks entered. Nothing written.")
        sys.exit(1)

    out_path = Path(args.out)
    out_path.write_text(json.dumps(sessions, indent=2, ensure_ascii=False) + "\n")

    print(f"\nDone. Wrote {len(sessions)} talks to {out_path}")
    print("You can now run:")
    print(f"  python3 scripts/events/update_event.py {out_path} --slug <event-slug>")


if __name__ == "__main__":
    main()
