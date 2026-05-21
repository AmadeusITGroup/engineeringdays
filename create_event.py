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
import os
import re
import sys
from datetime import datetime
from pathlib import Path


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
    "secur": "🏗️",
    "leader": "👔",
    "people": "👔",
    "manage": "👔",
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
            "icon": "🎤",
            "number": f"{meta['session_count']}+",
            "label": "Sessions",
            "description": "Talks and workshops",
        },
        {
            "icon": "🎙️",
            "number": str(meta["speakers_count"]),
            "label": "Speakers",
            "description": "Sharing their expertise",
        },
    ]
    if meta["locations"]:
        stats.append(
            {
                "icon": "🌐",
                "number": str(len(meta["locations"])),
                "label": "Sites",
                "description": "Hosting locations",
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

    # Build stats HTML
    stats_html = ""
    for stat in event_config["stats"]:
        stats_html += f"""                <div class="stat-card">
                    <div class="stat-icon">{stat['icon']}</div>
                    <div class="stat-number">{stat['number']}</div>
                    <div class="stat-label">{stat['label']}</div>
                    <p class="stat-description">{stat['description']}</p>
                </div>
"""

    # Build tracks HTML
    tracks_html = ""
    for track in event_config["tracks"]:
        tracks_html += f"""                <div class="track-card">
                    <div class="track-icon">{track['icon']}</div>
                    <h3>{track['name']}</h3>
                    <p>{track['description']}</p>
                </div>
"""

    # Build session types HTML
    sessions_html = ""
    for stype in event_config["sessionTypes"]:
        sessions_html += f"""                <div class="session-card">
                    <div class="session-header">
                        <h3>{stype['name']}</h3>
                        <span class="session-duration">{stype.get('count', '')} sessions</span>
                    </div>
                    <p>{stype['description']}</p>
                </div>
"""

    # Build locations string
    locations_str = ", ".join(f"<strong>{loc}</strong>" for loc in event_config["locations"][:5])
    if len(event_config["locations"]) > 5:
        locations_str += f" and {len(event_config['locations']) - 5} more"

    # Build conditional links based on whether sessions exist
    if has_sessions:
        nav_program_link = '<a href="program.html">Program</a>'
        hero_cta = '<a href="program.html" class="btn btn-primary">View Program <span class="arrow">→</span></a>'
        footer_program_link = '<a href="program.html">Program</a>'
    else:
        cfp_mailto = f'mailto:{contact}?subject=Talk proposal for {name}'
        nav_program_link = f'<a href="{cfp_mailto}">Submit a Talk</a>'
        hero_cta = f'<a href="{cfp_mailto}" class="btn btn-primary">Submit a Talk (CFP) <span class="arrow">→</span></a>'
        footer_program_link = f'<a href="{cfp_mailto}">Submit a Talk</a>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} | Amadeus Events</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🚀</text></svg>">
    <link rel="stylesheet" href="../shared/styles-base.css">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="container">
            <div class="nav-brand">
                <div class="nav-logo-line">
                    <span class="logo-bracket">&lt;</span>
                    <span class="logo-text">{name}</span>
                    <span class="logo-bracket">/&gt;</span>
                </div>
                <div class="nav-byline">by {organizer}</div>
            </div>
            <div class="nav-links">
                <a href="../index.html">All Events</a>
                <a href="#about">About</a>
                {nav_program_link}
                <a href="#tracks">Tracks</a>
                <a href="mailto:{contact}">Contact</a>
                <button id="theme-toggle" class="theme-toggle" aria-label="Toggle dark mode">
                    <span class="icon-sun">☀️</span>
                    <span class="icon-moon">🌙</span>
                </button>
            </div>
            <button class="mobile-menu-toggle" id="mobile-menu-toggle">
                <span></span>
                <span></span>
                <span></span>
            </button>
        </div>
    </nav>

    <!-- Hero Section -->
    <header class="hero">
        <div class="container">
            <div class="hero-content">
                <div class="glitch-wrapper">
                    <h1 class="hero-title">{name}</h1>
                </div>
                <div class="hero-date">
                    <span class="date-highlight">{dates}</span>
                </div>
                <p class="hero-subtitle">{tagline}</p>
                <div class="cta-buttons">
                    {hero_cta}
                    <a href="#about" class="btn btn-secondary">Learn More</a>
                </div>
            </div>
            <div class="hero-graphic">
                <div class="code-window">
                    <div class="window-controls">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                    <div class="code-content">
                        <pre><code><span class="code-keyword">const</span> <span class="code-variable">event</span> = {{
  <span class="code-property">name</span>: <span class="code-string">"{name}"</span>,
  <span class="code-property">dates</span>: <span class="code-string">"{dates}"</span>,
  <span class="code-property">sessions</span>: <span class="code-number">{event_config['stats'][0]['number']}</span>,
  <span class="code-property">speakers</span>: <span class="code-number">{event_config['stats'][1]['number']}</span>,
  <span class="code-property">status</span>: <span class="code-string">"awesome"</span>
}};</code></pre>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <!-- About Section -->
    <section id="about" class="section about-section">
        <div class="container">
            <h2 class="section-title">
                <span class="title-accent">//</span> About the Event
            </h2>
            <div class="about-content">
                <p class="lead-text" id="event-description">{description}</p>
                <p id="event-locations">Hosted at {locations_str}.</p>
            </div>

            <div class="stats-grid" id="stats-grid">
{stats_html}            </div>
        </div>
    </section>

    <!-- Sessions Section -->
    <section id="sessions" class="section sessions-section">
        <div class="container">
            <h2 class="section-title">
                <span class="title-accent">//</span> Session Types
            </h2>
            <div class="sessions-grid" id="sessions-grid">
{sessions_html}            </div>
        </div>
    </section>

    <!-- Tracks Section -->
    <section id="tracks" class="section tracks-section">
        <div class="container">
            <h2 class="section-title">
                <span class="title-accent">//</span> Tracks
            </h2>
            <div class="tracks-grid" id="tracks-grid">
{tracks_html}            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="section contact-section">
        <div class="container">
            <h2 class="section-title">
                <span class="title-accent">//</span> Get in Touch
            </h2>
            <div class="contact-content">
                <p class="contact-text">
                    Questions? Reach out to the organizing team.
                </p>
                <a href="mailto:{contact}" class="btn btn-primary btn-large">
                    Contact Us
                </a>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-brand">
                    <span class="logo-bracket">&lt;</span>
                    <span class="logo-text">{name}</span>
                    <span class="logo-bracket">/&gt;</span>
                    <p class="footer-tagline">An Amadeus Event</p>
                </div>
                <div class="footer-links">
                    <a href="../index.html">All Events</a>
                    {footer_program_link}
                    <a href="mailto:{contact}">Contact</a>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; {datetime.now().year} Amadeus. All rights reserved.</p>
            </div>
        </div>
    </footer>

    <script src="../shared/script-base.js"></script>
    <script src="script.js"></script>
</body>
</html>
"""


def generate_program_html(event_config):
    """Generate the event program.html with dynamic session loading."""
    name = event_config["eventName"]
    dates = event_config["dates"]["display"]
    organizer = event_config["organizer"]
    contact = event_config["contact"]

    # Build track colors for CSS
    track_colors = [
        "#2218a8", "#b650ff", "#ff58ac", "#27c93f", "#ffbd2e", "#ff5f56", "#0099cc"
    ]
    track_css = ""
    for i, track in enumerate(event_config["tracks"]):
        color = track_colors[i % len(track_colors)]
        safe_name = track["name"].lower().replace(" ", "-").replace(",", "")
        track_css += f'        .track-{safe_name} {{ background: {color}; }}\n'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Program | {name}</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🚀</text></svg>">
    <link rel="stylesheet" href="../shared/styles-base.css">
    <link rel="stylesheet" href="styles.css">
    <style>
        /* Program-specific styles */
        .program-hero {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--dark-accent) 50%, var(--secondary) 100%);
            padding: calc(80px + var(--spacing-xl)) var(--spacing-md) var(--spacing-xl);
            text-align: center;
        }}
        .program-hero h1 {{
            font-size: clamp(2.5rem, 6vw, 4.5rem);
            font-weight: 900;
            color: #ffffff;
            margin-bottom: var(--spacing-sm);
        }}
        .program-hero .subtitle {{
            font-size: 1.25rem;
            color: var(--highlight-light);
        }}
        .program-schedule {{
            padding: var(--spacing-xl) 0;
            min-height: 60vh;
        }}
        .filters-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: var(--spacing-sm);
            margin-bottom: var(--spacing-lg);
            align-items: center;
        }}
        .filter-select {{
            padding: 0.5rem 1rem;
            border: 2px solid var(--border-color);
            border-radius: var(--radius-md);
            background: var(--card-bg);
            color: var(--text-color);
            font-size: 0.9rem;
            cursor: pointer;
        }}
        .filter-select:focus {{
            border-color: var(--secondary);
            outline: none;
        }}
        .schedule-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: var(--spacing-md);
        }}
        .schedule-card {{
            background: var(--card-bg);
            border: 2px solid var(--border-color);
            border-radius: var(--radius-lg);
            overflow: hidden;
            transition: var(--transition);
        }}
        .schedule-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 40px var(--shadow);
            border-color: var(--secondary);
        }}
        .schedule-card.hidden {{ display: none; }}
        .schedule-track-bar {{
            height: 4px;
            width: 100%;
        }}
        .schedule-card-content {{
            padding: var(--spacing-md);
        }}
        .schedule-card-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-bottom: var(--spacing-sm);
            font-size: 0.75rem;
        }}
        .schedule-card-meta span {{
            padding: 0.2rem 0.5rem;
            border-radius: var(--radius-sm);
            font-weight: 600;
        }}
        .meta-time {{
            background: var(--primary);
            color: white;
            font-family: var(--font-mono);
        }}
        .meta-type {{
            background: var(--bg-light);
            color: var(--text-secondary);
        }}
        [data-theme="dark"] .meta-type {{
            background: var(--dark-accent);
        }}
        .meta-room {{
            background: var(--bg-light);
            color: var(--text-secondary);
        }}
        [data-theme="dark"] .meta-room {{
            background: var(--dark-accent);
        }}
        .schedule-card-title {{
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: var(--spacing-xs);
            line-height: 1.35;
        }}
        .schedule-card-speaker {{
            font-size: 0.85rem;
            color: var(--accent);
            font-weight: 500;
        }}
        .schedule-card-track {{
            display: inline-block;
            margin-top: var(--spacing-xs);
            padding: 0.15rem 0.45rem;
            border-radius: var(--radius-sm);
            font-size: 0.65rem;
            font-weight: 600;
            color: white;
        }}
        .results-info {{
            text-align: center;
            padding: var(--spacing-sm);
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        .results-count {{ font-weight: 700; color: var(--secondary); }}
        .day-header {{
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
            margin: var(--spacing-lg) 0 var(--spacing-md);
            padding-bottom: var(--spacing-sm);
            border-bottom: 3px solid var(--secondary);
        }}
        .day-header h2 {{
            font-size: 1.5rem;
            color: var(--primary);
            margin: 0;
        }}
        [data-theme="dark"] .day-header h2 {{ color: var(--secondary); }}
        .no-results {{
            text-align: center;
            padding: var(--spacing-xl);
            color: var(--text-secondary);
        }}
        .no-results h3 {{ margin-bottom: var(--spacing-sm); color: var(--text-color); }}
{track_css}
        @media (max-width: 768px) {{
            .schedule-grid {{ grid-template-columns: 1fr; }}
            .filters-bar {{ flex-direction: column; align-items: stretch; }}
        }}
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="container">
            <a href="index.html" class="nav-brand">
                <div class="nav-logo-line">
                    <span class="logo-bracket">&lt;</span>
                    <span class="logo-text">{name}</span>
                    <span class="logo-bracket">/&gt;</span>
                </div>
                <div class="nav-byline">by {organizer}</div>
            </a>
            <div class="nav-links">
                <a href="../index.html">All Events</a>
                <a href="index.html">Home</a>
                <a href="#schedule">Schedule</a>
                <a href="mailto:{contact}">Contact</a>
                <button id="theme-toggle" class="theme-toggle" aria-label="Toggle dark mode">
                    <span class="icon-sun">☀️</span>
                    <span class="icon-moon">🌙</span>
                </button>
            </div>
            <button class="mobile-menu-toggle" id="mobile-menu-toggle">
                <span></span>
                <span></span>
                <span></span>
            </button>
        </div>
    </nav>

    <!-- Program Hero -->
    <header class="program-hero">
        <div class="container">
            <h1>Program</h1>
            <p class="subtitle">{name} &mdash; {dates}</p>
        </div>
    </header>

    <!-- Schedule -->
    <section id="schedule" class="program-schedule">
        <div class="container">
            <div class="filters-bar">
                <select id="filter-day" class="filter-select">
                    <option value="all">All Days</option>
                </select>
                <select id="filter-track" class="filter-select">
                    <option value="all">All Tracks</option>
                </select>
                <select id="filter-type" class="filter-select">
                    <option value="all">All Types</option>
                </select>
                <select id="filter-room" class="filter-select">
                    <option value="all">All Rooms</option>
                </select>
            </div>
            <div class="results-info">
                <span class="results-count" id="results-count">0</span> sessions
            </div>
            <div id="schedule-container" class="schedule-grid"></div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-brand">
                    <span class="logo-bracket">&lt;</span>
                    <span class="logo-text">{name}</span>
                    <span class="logo-bracket">/&gt;</span>
                    <p class="footer-tagline">An Amadeus Event</p>
                </div>
                <div class="footer-links">
                    <a href="../index.html">All Events</a>
                    <a href="index.html">Home</a>
                    <a href="mailto:{contact}">Contact</a>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; {datetime.now().year} Amadeus. All rights reserved.</p>
            </div>
        </div>
    </footer>

    <script src="../shared/script-base.js"></script>
    <script>
    (function() {{
        'use strict';

        const TRACK_COLORS = {json.dumps({t['name']: track_colors[i % len(track_colors)] for i, t in enumerate(event_config['tracks'])})};

        function getTrackColor(trackName) {{
            return TRACK_COLORS[trackName] || '#888888';
        }}

        function getTrackClass(trackName) {{
            return 'track-' + trackName.toLowerCase().replace(/[\\s]+/g, '-').replace(/,/g, '');
        }}

        async function loadSessions() {{
            try {{
                const response = await fetch('sessions.json');
                if (!response.ok) throw new Error('No sessions.json found');
                return await response.json();
            }} catch (e) {{
                document.getElementById('schedule-container').innerHTML =
                    '<div class="no-results"><h3>Program coming soon</h3><p>Sessions will be announced shortly.</p></div>';
                return [];
            }}
        }}

        function formatTime(isoString) {{
            if (!isoString) return '';
            const d = new Date(isoString);
            return d.toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }});
        }}

        function formatDate(isoString) {{
            if (!isoString) return '';
            const d = new Date(isoString);
            return d.toLocaleDateString([], {{ weekday: 'long', day: 'numeric', month: 'long' }});
        }}

        function getSessionTrack(session) {{
            const track = session.Track;
            if (typeof track === 'object' && track) return track.en || '';
            return track || '';
        }}

        function getSessionType(session) {{
            const t = session['Session type'];
            if (typeof t === 'object' && t) return t.en || '';
            return t || '';
        }}

        function getSessionRoom(session) {{
            const r = session.Room;
            if (typeof r === 'object' && r) return r.en || '';
            return r || '';
        }}

        function renderSessions(sessions) {{
            const container = document.getElementById('schedule-container');
            const filterDay = document.getElementById('filter-day').value;
            const filterTrack = document.getElementById('filter-track').value;
            const filterType = document.getElementById('filter-type').value;
            const filterRoom = document.getElementById('filter-room').value;

            // Filter
            let filtered = sessions.filter(s => s.Start);
            if (filterDay !== 'all') {{
                filtered = filtered.filter(s => new Date(s.Start).toDateString() === filterDay);
            }}
            if (filterTrack !== 'all') {{
                filtered = filtered.filter(s => getSessionTrack(s) === filterTrack);
            }}
            if (filterType !== 'all') {{
                filtered = filtered.filter(s => getSessionType(s) === filterType);
            }}
            if (filterRoom !== 'all') {{
                filtered = filtered.filter(s => getSessionRoom(s) === filterRoom);
            }}

            // Sort by start time
            filtered.sort((a, b) => new Date(a.Start) - new Date(b.Start));

            document.getElementById('results-count').textContent = filtered.length;

            if (filtered.length === 0) {{
                container.innerHTML = '<div class="no-results"><h3>No sessions match your filters</h3><p>Try adjusting your filters.</p></div>';
                return;
            }}

            // Group by day
            const days = {{}};
            filtered.forEach(s => {{
                const day = new Date(s.Start).toDateString();
                if (!days[day]) days[day] = [];
                days[day].push(s);
            }});

            let html = '';
            Object.entries(days).forEach(([day, daySessions]) => {{
                html += `<div class="day-header" style="grid-column: 1 / -1;"><h2>${{formatDate(daySessions[0].Start)}}</h2></div>`;
                daySessions.forEach(session => {{
                    const track = getSessionTrack(session);
                    const trackColor = getTrackColor(track);
                    const type = getSessionType(session);
                    const room = getSessionRoom(session);
                    const speakers = (session['Speaker names'] || []).join(', ');
                    const title = session['Proposal title'] || session.title || 'Untitled';

                    html += `
                    <div class="schedule-card">
                        <div class="schedule-track-bar" style="background: ${{trackColor}};"></div>
                        <div class="schedule-card-content">
                            <div class="schedule-card-meta">
                                <span class="meta-time">${{formatTime(session.Start)}}</span>
                                ${{type ? `<span class="meta-type">${{type}}</span>` : ''}}
                                ${{room ? `<span class="meta-room">${{room}}</span>` : ''}}
                            </div>
                            <div class="schedule-card-title">${{title}}</div>
                            ${{speakers ? `<div class="schedule-card-speaker">${{speakers}}</div>` : ''}}
                            ${{track ? `<span class="schedule-card-track" style="background: ${{trackColor}}">${{track}}</span>` : ''}}
                        </div>
                    </div>`;
                }});
            }});

            container.innerHTML = html;
        }}

        function populateFilters(sessions) {{
            const days = new Set();
            const tracks = new Set();
            const types = new Set();
            const rooms = new Set();

            sessions.filter(s => s.Start).forEach(s => {{
                days.add(new Date(s.Start).toDateString());
                const track = getSessionTrack(s);
                if (track) tracks.add(track);
                const type = getSessionType(s);
                if (type) types.add(type);
                const room = getSessionRoom(s);
                if (room) rooms.add(room);
            }});

            const daySelect = document.getElementById('filter-day');
            [...days].sort((a, b) => new Date(a) - new Date(b)).forEach(d => {{
                const opt = document.createElement('option');
                opt.value = d;
                opt.textContent = new Date(d).toLocaleDateString([], {{ weekday: 'short', day: 'numeric', month: 'short' }});
                daySelect.appendChild(opt);
            }});

            const trackSelect = document.getElementById('filter-track');
            [...tracks].sort().forEach(t => {{
                const opt = document.createElement('option');
                opt.value = t;
                opt.textContent = t;
                trackSelect.appendChild(opt);
            }});

            const typeSelect = document.getElementById('filter-type');
            [...types].sort().forEach(t => {{
                const opt = document.createElement('option');
                opt.value = t;
                opt.textContent = t;
                typeSelect.appendChild(opt);
            }});

            const roomSelect = document.getElementById('filter-room');
            [...rooms].sort().forEach(r => {{
                const opt = document.createElement('option');
                opt.value = r;
                opt.textContent = r;
                roomSelect.appendChild(opt);
            }});
        }}

        async function init() {{
            const sessions = await loadSessions();
            if (sessions.length === 0) return;

            populateFilters(sessions);
            renderSessions(sessions);

            document.getElementById('filter-day').addEventListener('change', () => renderSessions(sessions));
            document.getElementById('filter-track').addEventListener('change', () => renderSessions(sessions));
            document.getElementById('filter-type').addEventListener('change', () => renderSessions(sessions));
            document.getElementById('filter-room').addEventListener('change', () => renderSessions(sessions));
        }}

        document.addEventListener('DOMContentLoaded', init);
    }})();
    </script>
</body>
</html>
"""


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
    return """// Event-specific JavaScript
// Loads config.json and renders dynamic sections (tracks, session types, stats).
// Non-technical users can edit config.json to update the website content.

document.addEventListener('DOMContentLoaded', () => {
    fetch('config.json')
        .then(r => r.json())
        .then(renderEvent)
        .catch(err => console.warn('Could not load config.json:', err));
});

function renderEvent(event) {
    // Render stats
    const statsGrid = document.getElementById('stats-grid');
    if (statsGrid && event.stats && event.stats.length) {
        statsGrid.innerHTML = event.stats.map(stat => `
            <div class="stat-card">
                <div class="stat-icon">${stat.icon}</div>
                <div class="stat-number">${stat.number}</div>
                <div class="stat-label">${stat.label}</div>
                <p class="stat-description">${stat.description}</p>
            </div>
        `).join('');
    }

    // Render session types
    const sessionsGrid = document.getElementById('sessions-grid');
    if (sessionsGrid && event.sessionTypes && event.sessionTypes.length) {
        sessionsGrid.innerHTML = event.sessionTypes.map(stype => `
            <div class="session-card">
                <div class="session-header">
                    <h3>${stype.name}</h3>
                    <span class="session-duration">${stype.duration || (stype.count ? stype.count + ' sessions' : '')}</span>
                </div>
                <p>${stype.description}</p>
            </div>
        `).join('');
    }

    // Render tracks
    const tracksGrid = document.getElementById('tracks-grid');
    if (tracksGrid && event.tracks && event.tracks.length) {
        tracksGrid.innerHTML = event.tracks.map(track => `
            <div class="track-card">
                <div class="track-icon">${track.icon}</div>
                <h3>${track.name}</h3>
                <p>${track.description}</p>
            </div>
        `).join('');
    }

    // Update description if present
    const descEl = document.getElementById('event-description');
    if (descEl && event.description) {
        descEl.textContent = event.description;
    }

    // Update locations
    const locEl = document.getElementById('event-locations');
    if (locEl && event.locations && event.locations.length) {
        locEl.innerHTML = 'Hosted at ' + event.locations.map(l => `<strong>${l}</strong>`).join(', ') + '.';
    }
}
"""


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
    print(f"  ✓ Updated root events.json")


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
        with open(sessions_path) as f:
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
        print(f"   Sessions: None (CFP mode — program will be added later)")

    # Parse metadata from sessions
    meta = parse_sessions(sessions_data)

    # Override dates/locations from CLI if provided (useful when no sessions JSON)
    if args.dates:
        meta["date_display_override"] = args.dates
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
        print(f"   ℹ️  No program page yet — add a sessions JSON later to generate it.")


if __name__ == "__main__":
    main()
