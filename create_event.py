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
    cfp_mailto = f'mailto:{contact}?subject=Talk proposal for {name}'

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

    # Initial links (runtime check can still switch mode based on actual files)
    if has_sessions:
        nav_program_href = "program.html"
        nav_program_text = "Program"
        hero_cta_href = "program.html"
        hero_cta_text = 'View Program <span class="arrow">→</span>'
        footer_program_href = "program.html"
        footer_program_text = "Program"
    else:
        nav_program_href = cfp_mailto
        nav_program_text = "Submit a Talk"
        hero_cta_href = cfp_mailto
        hero_cta_text = 'Submit a Talk (CFP) <span class="arrow">→</span>'
        footer_program_href = cfp_mailto
        footer_program_text = "Submit a Talk"

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
                <a id="program-nav-link" href="{nav_program_href}">{nav_program_text}</a>
                <a href="#tracks">Tracks</a>
                <a id="nav-contact-link" href="mailto:{contact}">Contact</a>
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
                    <a id="program-hero-cta" href="{hero_cta_href}" class="btn btn-primary">{hero_cta_text}</a>
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
                <a id="contact-cta-link" href="mailto:{contact}" class="btn btn-primary btn-large">
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
                    <a id="program-footer-link" href="{footer_program_href}">{footer_program_text}</a>
                    <a id="footer-contact-link" href="mailto:{contact}">Contact</a>
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
    return """// Event-specific JavaScript
// Loads config.json and renders index.html from config-driven data.

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('config.json', { cache: 'no-store' });
        const event = await response.json();
        renderEvent(event);
        await updateProgramLinks(event);
    } catch (err) {
        console.warn('Could not load config.json:', err);
    }
});

function renderEvent(event) {
    applyMetadata(event);
    renderStats(event.stats);
    renderSessionTypes(event.sessionTypes);
    renderTracks(event.tracks);
    renderAboutSection(event);
    renderCodeSnippet(event);
}

function applyMetadata(event) {
    if (event.eventName) {
        document.title = `${event.eventName} | Amadeus Events`;

        const heroTitle = document.querySelector('.hero-title');
        if (heroTitle) {
            heroTitle.textContent = event.eventName;
        }

        const navLogo = document.querySelector('.nav-brand .logo-text');
        if (navLogo) {
            navLogo.textContent = event.eventName;
        }

        const footerLogo = document.querySelector('.footer-brand .logo-text');
        if (footerLogo) {
            footerLogo.textContent = event.eventName;
        }
    }

    if (event.organizer) {
        const navByline = document.querySelector('.nav-byline');
        if (navByline) {
            navByline.textContent = `by ${event.organizer}`;
        }
    }

    if (event.tagline) {
        const heroSubtitle = document.querySelector('.hero-subtitle');
        if (heroSubtitle) {
            heroSubtitle.textContent = event.tagline;
        }

        const footerTagline = document.querySelector('.footer-tagline');
        if (footerTagline) {
            footerTagline.textContent = `A ${event.organizer || 'Amadeus'} Event`;
        }
    }

    const dateEl = document.querySelector('.date-highlight');
    if (dateEl && event.dates && event.dates.display) {
        dateEl.textContent = event.dates.display;
    }

    if (event.contact) {
        const mailto = `mailto:${event.contact}`;
        const navContact = document.getElementById('nav-contact-link');
        const ctaContact = document.getElementById('contact-cta-link');
        const footerContact = document.getElementById('footer-contact-link');

        if (navContact) {
            navContact.href = mailto;
        }
        if (ctaContact) {
            ctaContact.href = mailto;
        }
        if (footerContact) {
            footerContact.href = mailto;
        }
    }

    if (event.dates && event.dates.start) {
        const eventYear = new Date(event.dates.start).getFullYear();
        if (!Number.isNaN(eventYear)) {
            const footerYear = document.querySelector('.footer-bottom p');
            if (footerYear) {
                footerYear.textContent = `(c) ${eventYear} Amadeus. All rights reserved.`;
            }
        }
    }
}

function renderStats(stats) {
    const statsGrid = document.getElementById('stats-grid');
    if (!statsGrid || !Array.isArray(stats) || stats.length === 0) {
        return;
    }

    statsGrid.innerHTML = stats.map(stat => `
        <div class="stat-card">
            <div class="stat-icon">${stat.icon || ''}</div>
            <div class="stat-number">${stat.number || ''}</div>
            <div class="stat-label">${stat.label || ''}</div>
            <p class="stat-description">${stat.description || ''}</p>
        </div>
    `).join('');
}

function renderSessionTypes(sessionTypes) {
    const sessionsGrid = document.getElementById('sessions-grid');
    if (!sessionsGrid || !Array.isArray(sessionTypes) || sessionTypes.length === 0) {
        return;
    }

    sessionsGrid.innerHTML = sessionTypes.map(stype => `
        <div class="session-card">
            <div class="session-header">
                <h3>${stype.name || ''}</h3>
                <span class="session-duration">${stype.duration || (stype.count ? `${stype.count} sessions` : '')}</span>
            </div>
            <p>${stype.description || ''}</p>
        </div>
    `).join('');
}

function renderTracks(tracks) {
    const tracksGrid = document.getElementById('tracks-grid');
    if (!tracksGrid || !Array.isArray(tracks) || tracks.length === 0) {
        return;
    }

    tracksGrid.innerHTML = tracks.map(track => `
        <div class="track-card">
            <div class="track-icon">${track.icon || ''}</div>
            <h3>${track.name || ''}</h3>
            <p>${track.description || ''}</p>
        </div>
    `).join('');
}

function renderAboutSection(event) {
    const descEl = document.getElementById('event-description');
    if (descEl && event.description) {
        descEl.textContent = event.description;
    }

    const locEl = document.getElementById('event-locations');
    if (locEl && Array.isArray(event.locations) && event.locations.length) {
        locEl.innerHTML = `Hosted at ${event.locations.map(location => `<strong>${location}</strong>`).join(', ')}.`;
    }
}

function renderCodeSnippet(event) {
    const codeBlock = document.querySelector('.code-content code');
    if (!codeBlock) {
        return;
    }

    const sessionCount = Array.isArray(event.sessionTypes)
        ? event.sessionTypes.reduce((total, type) => total + (Number(type.count) || 0), 0)
        : 0;

    const speakerStat = Array.isArray(event.stats)
        ? event.stats.find(stat => typeof stat.label === 'string' && stat.label.toLowerCase() === 'speakers')
        : null;
    const speakersValue = speakerStat ? speakerStat.number : 'n/a';

    codeBlock.innerHTML = `<span class="code-keyword">const</span> <span class="code-variable">event</span> = {\\n  <span class="code-property">name</span>: <span class="code-string">"${event.eventName || ''}"</span>,\\n  <span class="code-property">dates</span>: <span class="code-string">"${(event.dates && event.dates.display) || ''}"</span>,\\n  <span class="code-property">sessions</span>: <span class="code-number">${sessionCount || 'n/a'}</span>,\\n  <span class="code-property">speakers</span>: <span class="code-number">${speakersValue}</span>,\\n  <span class="code-property">status</span>: <span class="code-string">"configured"</span>\\n};`;
}

function getCfpHref(eventName, contact) {
    return `mailto:${contact}?subject=${encodeURIComponent(`Talk proposal for ${eventName}`)}`;
}

function switchToCfpMode(cfpHref) {
    const nav = document.getElementById('program-nav-link');
    const hero = document.getElementById('program-hero-cta');
    const footer = document.getElementById('program-footer-link');

    if (nav) {
        nav.href = cfpHref;
        nav.textContent = 'Submit a Talk';
    }
    if (hero) {
        hero.href = cfpHref;
        hero.innerHTML = 'Submit a Talk (CFP) <span class="arrow">→</span>';
    }
    if (footer) {
        footer.href = cfpHref;
        footer.textContent = 'Submit a Talk';
    }
}

function switchToProgramMode() {
    const nav = document.getElementById('program-nav-link');
    const hero = document.getElementById('program-hero-cta');
    const footer = document.getElementById('program-footer-link');

    if (nav) {
        nav.href = 'program.html';
        nav.textContent = 'Program';
    }
    if (hero) {
        hero.href = 'program.html';
        hero.innerHTML = 'View Program <span class="arrow">→</span>';
    }
    if (footer) {
        footer.href = 'program.html';
        footer.textContent = 'Program';
    }
}

async function updateProgramLinks(event) {
    const eventName = event.eventName || 'Amadeus Event';
    const contact = event.contact || 'devrel@amadeus.com';
    const cfpHref = getCfpHref(eventName, contact);

    let hasSessions = false;
    let hasProgramPage = false;

    try {
        const sessionsResponse = await fetch('sessions.json', { cache: 'no-store' });
        if (sessionsResponse.ok) {
            const sessions = await sessionsResponse.json();
            hasSessions = Array.isArray(sessions) && sessions.length > 0;
        }
    } catch (error) {
        hasSessions = false;
    }

    try {
        const programResponse = await fetch('program.html', { method: 'HEAD', cache: 'no-store' });
        hasProgramPage = programResponse.ok;
    } catch (error) {
        hasProgramPage = false;
    }

    if (hasSessions && hasProgramPage) {
        switchToProgramMode();
    } else {
        switchToCfpMode(cfpHref);
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
