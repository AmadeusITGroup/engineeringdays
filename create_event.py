#!/usr/bin/env python3
"""
Generate a complete event website from a pretalx sessions JSON export.

Usage:
    python create_event.py <sessions.json> --name "Event Name" --slug "event-slug-2026"

The script will:
1. Parse the sessions JSON to extract dates, tracks, session types, locations
2. Generate the event folder with index.html, program.html, styles.css, script.js, config.json
3. Add an event card to the root index.html

Minimal manual input required — just the event name and optionally:
  --tagline, --description, --organizer, --contact
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


README_EVENTS_START = "<!-- EVENTS_LIST_START -->"
README_EVENTS_END = "<!-- EVENTS_LIST_END -->"


def parse_sessions(sessions_data):
    """Extract metadata from pretalx sessions export."""
    tracks = set()
    session_types = {}
    locations = set()
    rooms = set()
    dates = []
    speakers_count = 0
    speakers_set = set()

    for session in sessions_data:
        # Tracks
        track = session.get("Track", {})
        if isinstance(track, dict):
            track_name = track.get("en", "")
        else:
            track_name = str(track) if track else ""
        if track_name:
            tracks.add(track_name)

        # Session types
        stype = session.get("Session type", {})
        if isinstance(stype, dict):
            stype_name = stype.get("en", "")
        else:
            stype_name = str(stype) if stype else ""
        if stype_name:
            session_types[stype_name] = session_types.get(stype_name, 0) + 1

        # Locations/sites
        site_field = None
        for key in session.keys():
            if "site" in key.lower() or "present" in key.lower():
                site_field = session[key]
                break
        if site_field:
            locations.add(site_field)

        # Rooms
        room = session.get("Room", {})
        if isinstance(room, dict):
            room_name = room.get("en", "")
        else:
            room_name = str(room) if room else ""
        if room_name:
            rooms.add(room_name)

        # Dates
        start = session.get("Start")
        if start:
            try:
                dt = datetime.fromisoformat(start)
                dates.append(dt)
            except (ValueError, TypeError):
                pass

        # Speakers
        for speaker in session.get("Speaker names", []):
            if speaker:
                speakers_set.add(speaker)

    speakers_count = len(speakers_set)

    # Determine date range
    if dates:
        dates.sort()
        start_date = dates[0]
        end_date = dates[-1]
    else:
        start_date = end_date = None

    return {
        "tracks": sorted(tracks),
        "session_types": session_types,
        "locations": sorted(locations),
        "rooms": sorted(rooms),
        "start_date": start_date,
        "end_date": end_date,
        "session_count": len(sessions_data),
        "speakers_count": speakers_count,
    }


def format_date_display(start_date, end_date):
    """Format dates for display (e.g., '29-30 April 2026')."""
    if not start_date:
        return "TBD"
    if not end_date or start_date.date() == end_date.date():
        return start_date.strftime("%-d %B %Y")
    if start_date.month == end_date.month and start_date.year == end_date.year:
        return f"{start_date.day}-{end_date.day} {start_date.strftime('%B %Y')}"
    return f"{start_date.strftime('%-d %B')} - {end_date.strftime('%-d %B %Y')}"


def parse_display_dates(date_display):
    """Best-effort parse for human date ranges like '10-11 November 2026'."""
    if not date_display:
        return None, None

    text = date_display.strip()
    if not text:
        return None, None

    patterns = [
        # 10-11 November 2026
        (r"^(\d{1,2})\s*[-–]\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$", "same_month"),
        # 10 November - 11 December 2026
        (r"^(\d{1,2})\s+([A-Za-z]+)\s*[-–]\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$", "two_months"),
        # 10 November 2026
        (r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$", "single"),
    ]

    for pattern, kind in patterns:
        match = re.match(pattern, text)
        if not match:
            continue
        try:
            if kind == "same_month":
                start_day, end_day, month_name, year = match.groups()
                start = datetime.strptime(f"{int(start_day)} {month_name} {year}", "%d %B %Y")
                end = datetime.strptime(f"{int(end_day)} {month_name} {year}", "%d %B %Y")
                return start, end

            if kind == "two_months":
                start_day, start_month, end_day, end_month, year = match.groups()
                start = datetime.strptime(f"{int(start_day)} {start_month} {year}", "%d %B %Y")
                end = datetime.strptime(f"{int(end_day)} {end_month} {year}", "%d %B %Y")
                return start, end

            if kind == "single":
                day, month_name, year = match.groups()
                start = datetime.strptime(f"{int(day)} {month_name} {year}", "%d %B %Y")
                return start, start
        except ValueError:
            continue

    return None, None


def split_upcoming_and_past(events):
    """Split events list by end date (falls back to parsed display date)."""
    today = datetime.now().date()
    upcoming = []
    past = []

    for event in events:
        end_date = None

        raw_end = event.get("dates", {}).get("end", "")
        if raw_end:
            try:
                end_date = datetime.strptime(raw_end, "%Y-%m-%d").date()
            except ValueError:
                end_date = None

        if not end_date:
            _, parsed_end = parse_display_dates(event.get("dates", {}).get("display", ""))
            if parsed_end:
                end_date = parsed_end.date()

        if end_date and end_date < today:
            past.append(event)
        else:
            upcoming.append(event)

    return upcoming, past


def update_readme_events_section(repo_root, events):
    """Keep README event lists synchronized with events.json."""
    readme_path = repo_root / "README.md"
    if not readme_path.exists():
        return

    upcoming, past = split_upcoming_and_past(events)
    upcoming_lines = [
        f"- [{e['name']}]({e['slug']}/index.html) - {e['dates']['display']}"
        for e in upcoming
    ]
    past_lines = [
        f"- [{e['name']}]({e['slug']}/index.html) - {e['dates']['display']}"
        for e in past
    ]

    section = "\n".join(
        [
            README_EVENTS_START,
            "## Upcoming Events",
            *(upcoming_lines or ["- None"]),
            "",
            "## Past Events",
            *(past_lines or ["- None"]),
            README_EVENTS_END,
        ]
    )

    content = readme_path.read_text()
    block_pattern = re.compile(
        rf"{re.escape(README_EVENTS_START)}.*?{re.escape(README_EVENTS_END)}",
        re.DOTALL,
    )

    if block_pattern.search(content):
        new_content = block_pattern.sub(section, content)
    else:
        insertion_point = content.find("---")
        if insertion_point != -1:
            new_content = (
                content[:insertion_point].rstrip() + "\n\n" + section + "\n\n" + content[insertion_point:]
            )
        else:
            new_content = content.rstrip() + "\n\n" + section + "\n"

    readme_path.write_text(new_content)
    print("  ✓ Updated README event lists")


TRACK_ICONS = {
    "ai": "📊",
    "data": "📊",
    "front": "🎨",
    "ux": "🎨",
    "back": "☁️",
    "cloud": "☁️",
    "dev": "💻",
    "qa": "💻",
    "test": "💻",
    "devops": "🏗️",
    "security": "🏗️",
    "leadership": "👔",
    "people": "👔",
}


def get_track_icon(track_name):
    """Get an emoji icon for a track based on its name."""
    lower = track_name.lower()
    for keyword, icon in TRACK_ICONS.items():
        if keyword in lower:
            return icon
    return "✨"


def generate_event_json(meta, args):
    """Generate config.json configuration."""
    date_display = meta.get("date_display_override") or format_date_display(meta["start_date"], meta["end_date"])

    stats = [
        {
            "icon": "🎙️",
            "number": f"{meta['session_count']}+",
            "label": "Sessions",
            "description": "Tech talks and hands-on workshops",
        },
        {
            "icon": "🗣️",
            "number": str(meta["speakers_count"]),
            "label": "Speakers",
            "description": "Sharing their expertise",
        },
        {
            "icon": "👥",
            "number": str(meta["attendees_count"]),
            "label": "Attendees",
            "description": "To connect with",
        },
        {
            "icon": "🤝",
            "number": str(meta["partners_count"]),
            "label": "Partners",
            "description": "Participating, with booths & demos",
        },
    ]
    if meta["locations"]:
        stats.append(
            {
                "icon": "🌐",
                "number": str(len(meta["locations"])),
                "label": "Sites",
                "description": "Hosting the event",
            }
        )

    tracks = []
    if meta["tracks"]:
        for track_name in meta["tracks"]:
            tracks.append(
                {
                    "icon": get_track_icon(track_name),
                    "name": track_name,
                    "description": "",
                }
            )
    else:
        # CFP mode: provide example tracks for the user to customize
        tracks = [
            {"icon": "🤖", "name": "AI & Data", "description": "Machine learning, data engineering, and AI applications"},
            {"icon": "☁️", "name": "Cloud & DevOps", "description": "Cloud infrastructure, CI/CD, and platform engineering"},
            {"icon": "🎨", "name": "Frontend & UX", "description": "Web development, design systems, and user experience"},
            {"icon": "🔒", "name": "Security", "description": "Application security, compliance, and best practices"},
            {"icon": "👔", "name": "Leadership & People", "description": "Engineering management, culture, and career growth"},
        ]

    session_types = []
    if meta["session_types"]:
        for stype_name, count in sorted(
            meta["session_types"].items(), key=lambda x: -x[1]
        ):
            session_types.append(
                {"name": stype_name, "count": count, "description": ""}
            )
    else:
        # CFP mode: provide example session types
        session_types = [
            {"name": "Talk", "duration": "45 min", "description": "Standard presentation with Q&A"},
            {"name": "Workshop", "duration": "90 min", "description": "Hands-on interactive session"},
            {"name": "Lightning Talk", "duration": "10 min", "description": "Short focused presentation"},
        ]

    return {
        "eventName": args.name,
        "eventSlug": args.slug,
        "tagline": args.tagline,
        "dates": {
            "start": meta["start_date"].isoformat() if meta["start_date"] else "",
            "end": meta["end_date"].isoformat() if meta["end_date"] else "",
            "display": date_display,
        },
        "organizer": args.organizer,
        "contact": args.contact,
        "useLiveProgramStats": False,
        "description": args.description,
        "locations": list(meta["locations"]),
        "stats": stats,
        "tracks": tracks,
        "sessionTypes": session_types,
        "colors": {"primary": "#26005a", "secondary": "#b650ff", "accent": "#ff58ac"},
    }


def generate_index_html(event_config, has_sessions=True):
    """Generate the event index.html."""
    name = event_config["eventName"]
    dates = event_config["dates"]["display"]
    tagline = event_config["tagline"]
    description = event_config["description"]
    organizer = event_config["organizer"]
    contact = event_config["contact"]
    attendee_stat = next(
        (
            stat.get("number", "")
            for stat in event_config.get("stats", [])
            if str(stat.get("label", "")).lower() == "attendees"
        ),
        "",
    )
    locations = event_config.get("locations", [])
    primary_location = locations[0] if locations else "TBD"

    template_path = Path(__file__).parent / "_template" / "index.html"
    template = template_path.read_text()

    replacements = {
        "{{EVENT_NAME}}": name,
        "{{EVENT_DATES}}": dates,
        "{{EVENT_TAGLINE}}": tagline,
        "{{EVENT_DESCRIPTION}}": description,
        "{{ORGANIZER}}": organizer,
        "{{CONTACT_EMAIL}}": contact,
        "{{EVENT_LOCATION}}": primary_location,
        "{{ATTENDEES}}": str(attendee_stat),
    }

    for token, value in replacements.items():
        template = template.replace(token, value)

    return template


# Best-effort keyword -> IANA timezone lookup for the site names/countries
# that typically appear in a pretalx "site" question (e.g. "Nice, France").
SITE_TIMEZONE_KEYWORDS = [
    ("sydney", "Australia/Sydney"),
    ("melbourne", "Australia/Sydney"),
    ("brisbane", "Australia/Sydney"),
    ("australia", "Australia/Sydney"),
    ("bengaluru", "Asia/Kolkata"),
    ("bangalore", "Asia/Kolkata"),
    ("india", "Asia/Kolkata"),
    ("istanbul", "Europe/Istanbul"),
    ("turkey", "Europe/Istanbul"),
    ("nice", "Europe/Paris"),
    ("sophia", "Europe/Paris"),
    ("paris", "Europe/Paris"),
    ("france", "Europe/Paris"),
    ("erding", "Europe/Berlin"),
    ("berlin", "Europe/Berlin"),
    ("germany", "Europe/Berlin"),
    ("madrid", "Europe/Madrid"),
    ("barcelona", "Europe/Madrid"),
    ("spain", "Europe/Madrid"),
    ("antwerp", "Europe/Brussels"),
    ("brussels", "Europe/Brussels"),
    ("belgium", "Europe/Brussels"),
    ("london", "Europe/London"),
    ("united kingdom", "Europe/London"),
    (" uk", "Europe/London"),
    ("dallas", "America/Chicago"),
    ("chicago", "America/Chicago"),
    ("bogot", "America/Bogota"),
    ("colombia", "America/Bogota"),
    ("salt lake", "America/Denver"),
    ("denver", "America/Denver"),
]


def guess_site_timezones(locations):
    """Best-effort mapping of free-text site names to IANA timezones.

    Returns a de-duplicated list, ordered to match SITE_TIMEZONE_KEYWORDS
    (roughly east to west). Locations that can't be matched are ignored;
    if nothing matches, an empty list is returned so the page falls back
    to auto-detecting the visitor's closest known timezone.
    """
    matched = []
    for location in locations:
        text = str(location).lower()
        for keyword, tz in SITE_TIMEZONE_KEYWORDS:
            if keyword in text and tz not in matched:
                matched.append(tz)
                break
    return matched


def generate_program_html(event_config):
    """Generate the event program.html using the rich shared template."""
    name = event_config["eventName"]
    dates = event_config["dates"]["display"]
    organizer = event_config["organizer"]
    contact = event_config["contact"]

    track_colors = ["#2218a8", "#b650ff", "#ff58ac", "#27c93f", "#ffbd2e", "#ff5f56", "#0099cc"]
    track_color_map = {
        track["name"]: track_colors[i % len(track_colors)]
        for i, track in enumerate(event_config.get("tracks", []))
    }

    site_timezones = guess_site_timezones(event_config.get("locations", []))

    template_path = Path(__file__).parent / "_template" / "program-rich.html"
    template = template_path.read_text()

    replacements = {
        "{{EVENT_NAME}}": name,
        "{{EVENT_DATES}}": dates,
        "{{ORGANIZER}}": organizer,
        "{{CONTACT_EMAIL}}": contact,
        "{{YEAR}}": str(datetime.now().year),
        "{{TRACK_COLORS_JSON}}": json.dumps(track_color_map),
        "{{OPENFEEDBACK_BASE}}": event_config.get("openFeedbackBaseUrl", ""),
        "{{SITE_TIMEZONES_JSON}}": json.dumps(site_timezones),
    }

    for token, value in replacements.items():
        template = template.replace(token, value)

    return template
def generate_styles_css(event_config):
    """Generate the event styles.css."""
    colors = event_config.get("colors", {})
    primary = colors.get("primary", "#26005a")
    secondary = colors.get("secondary", "#b650ff")
    accent = colors.get("accent", "#ff58ac")

    # Read from template
    template_path = Path(__file__).parent / "_template" / "styles.css"
    if template_path.exists():
        css = template_path.read_text()
        # Uncomment and set colors if different from default
        if primary != "#26005a" or secondary != "#b650ff" or accent != "#ff58ac":
            css = css.replace(
                "/* :root {\n    --primary: #26005a;\n    --secondary: #b650ff;\n    --accent: #ff58ac;\n} */",
                f":root {{\n    --primary: {primary};\n    --secondary: {secondary};\n    --accent: {accent};\n}}",
            )
        return css
    # Fallback: minimal CSS
    return f"""/* Event styles - extends ../shared/styles-base.css */
:root {{
    --primary: {primary};
    --secondary: {secondary};
    --accent: {accent};
}}
"""


def generate_script_js():
    """Generate event script.js that hydrates page from config.json."""
    template_path = Path(__file__).parent / "_template" / "script.js"
    return template_path.read_text()


def add_to_landing_page(event_config, meta, repo_root):
    """Add or update event entry in root events.json."""
    events_path = repo_root / "events.json"

    # Load existing registry or start fresh
    if events_path.exists():
        events = json.loads(events_path.read_text())
    else:
        events = []

    slug = event_config["eventSlug"]

    # Build the registry entry
    entry = {
        "slug": slug,
        "name": event_config["eventName"],
        "dates": {
            "display": event_config["dates"]["display"],
            "start": meta["start_date"].strftime("%Y-%m-%d") if meta["start_date"] else "",
            "end": meta["end_date"].strftime("%Y-%m-%d") if meta["end_date"] else "",
        },
        "tagline": event_config["tagline"],
        "sessions": meta["session_count"],
        "sites": len(meta["locations"]),
    }

    # Replace existing entry for this slug, or append
    existing_idx = next((i for i, e in enumerate(events) if e["slug"] == slug), None)
    if existing_idx is not None:
        events[existing_idx] = entry
    else:
        events.append(entry)

    events_path.write_text(json.dumps(events, indent=2, ensure_ascii=False) + "\n")
    print("  ✓ Updated root events.json")
    update_readme_events_section(repo_root, events)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a complete event website from a pretalx sessions JSON."
    )
    parser.add_argument("sessions_file", nargs="?", default=None, help="Path to the pretalx sessions JSON export (optional — omit to create event without sessions)")
    parser.add_argument("--name", required=True, help="Event name (e.g., 'Amadeus Engineering Days 2026')")
    parser.add_argument("--slug", help="Event folder name (e.g., 'engineering-days-2026'). Auto-generated from name if omitted.")
    parser.add_argument("--tagline", default="", help="Short tagline for the event")
    parser.add_argument("--description", default="", help="Longer description for the about section")
    parser.add_argument("--organizer", default="DevRel", help="Organizing team name")
    parser.add_argument("--contact", default="devrel@amadeus.com", help="Contact email")
    parser.add_argument("--dates", default="", help="Event dates display string (e.g., '15-16 June 2027'). Used when no sessions JSON.")
    parser.add_argument("--locations", default="", help="Comma-separated list of locations (e.g., 'Nice FR, London UK')")
    args = parser.parse_args()

    # Auto-generate slug if not provided
    if not args.slug:
        args.slug = re.sub(r"[^a-z0-9]+", "-", args.name.lower()).strip("-")

    # Auto-generate tagline/description if not provided
    if not args.tagline:
        args.tagline = f"Join us for {args.name}!"
    if not args.description:
        args.description = f"Welcome to {args.name}, an event organized by the {args.organizer} team at Amadeus."

    # Load sessions (or use empty list if no file provided)
    has_sessions = False
    if args.sessions_file:
        sessions_path = Path(args.sessions_file)
        if not sessions_path.exists():
            print(f"Error: Sessions file not found: {sessions_path}")
            sys.exit(1)
        with open(sessions_path, encoding="utf-8") as f:
            sessions_data = json.load(f)
        has_sessions = len(sessions_data) > 0
    else:
        sessions_data = []
        sessions_path = None

    print(f"📦 Creating event: {args.name}")
    print(f"   Slug: {args.slug}")
    if has_sessions:
        print(f"   Sessions file: {sessions_path.name} ({len(sessions_data)} sessions)")
    else:
        print("   Sessions: None (CFP mode — program will be added later)")

    # Parse metadata from sessions
    meta = parse_sessions(sessions_data)

    # Override dates/locations from CLI if provided (useful when no sessions JSON)
    if args.dates:
        meta["date_display_override"] = args.dates
        if not meta["start_date"] or not meta["end_date"]:
            parsed_start, parsed_end = parse_display_dates(args.dates)
            if parsed_start and not meta["start_date"]:
                meta["start_date"] = parsed_start
            if parsed_end and not meta["end_date"]:
                meta["end_date"] = parsed_end
    if args.locations:
        meta["locations"] = sorted(set(loc.strip() for loc in args.locations.split(",") if loc.strip()))

    print(f"   Dates: {args.dates or format_date_display(meta['start_date'], meta['end_date'])}")
    if has_sessions:
        print(f"   Tracks: {', '.join(meta['tracks'])}")
        print(f"   Session types: {', '.join(meta['session_types'].keys())}")
    print(f"   Locations: {len(meta['locations'])} sites")
    if has_sessions:
        print(f"   Speakers: {meta['speakers_count']}")

    # Generate event config
    event_config = generate_event_json(meta, args)

    # Create event folder
    repo_root = Path(__file__).parent
    event_dir = repo_root / args.slug
    event_dir.mkdir(exist_ok=True)

    # Generate files
    (event_dir / "index.html").write_text(generate_index_html(event_config, has_sessions=has_sessions))
    print(f"  ✓ {args.slug}/index.html")

    if has_sessions:
        (event_dir / "program.html").write_text(generate_program_html(event_config))
        print(f"  ✓ {args.slug}/program.html")

    (event_dir / "styles.css").write_text(generate_styles_css(event_config))
    print(f"  ✓ {args.slug}/styles.css")

    (event_dir / "script.js").write_text(generate_script_js())
    print(f"  ✓ {args.slug}/script.js")

    (event_dir / "config.json").write_text(json.dumps(event_config, indent=2, ensure_ascii=False))
    print(f"  ✓ {args.slug}/config.json")

    # Copy sessions as sessions.json (or create empty one)
    if has_sessions:
        import shutil
        shutil.copy2(sessions_path, event_dir / "sessions.json")
    else:
        (event_dir / "sessions.json").write_text("[]")
    print(f"  ✓ {args.slug}/sessions.json")

    # Update landing page
    add_to_landing_page(event_config, meta, repo_root)

    print(f"\n🎉 Done! Event created at: {event_dir}/")
    print(f"   Preview: open {event_dir}/index.html in a browser")
    if has_sessions:
        print(f"   Program: open {event_dir}/program.html in a browser")
    else:
        print("   ℹ️  No program page yet — add a sessions JSON later to generate it.")


if __name__ == "__main__":
    main()
