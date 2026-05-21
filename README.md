# Amadeus Events

Multi-event website for Amadeus tech conferences and community events, hosted on GitHub Pages.

**Live site:** https://amadeusitgroup.github.io/events/

## Quick Start — Create a New Event

All you need is a **pretalx sessions JSON export**. Then run one command:

```bash
python3 create_event.py sessions.json --name "My Event 2027" --slug "my-event-2027"
```

That's it. The script generates a complete event website and adds it to the landing page.  
See [CREATING_AN_EVENT.md](CREATING_AN_EVENT.md) for full details and options.

### Update an Event (after CFP closes)

Once you have the finalized sessions JSON from pretalx:

```bash
python3 update_event.py sessions.json --slug "my-event-2027"
```

This replaces CFP placeholders with real data, generates `program.html`, and links it from the homepage.

### Using GitHub Copilot

Open Copilot Chat and say:

> "Create a new event from this sessions JSON" (attach the file)

Or use the reusable prompt skill at `.github/prompts/create-event.prompt.md`.

## Repository Structure

```
/
├── index.html                          # Landing page (links to all events)
├── create_event.py                     # 🚀 Create event (one command → full event)
├── update_event.py                     # 🔄 Update event with finalized program
├── shared/                             # Shared assets used by all events
│   ├── styles-base.css                 # Common CSS (variables, nav, footer, buttons)
│   └── script-base.js                  # Common JS (dark mode, mobile menu, scroll)
├── engineering-days-2026/              # Example: Engineering Days 2026
│   ├── index.html                      # Event homepage
│   ├── program.html                    # Program with dynamic session loading
│   ├── styles.css                      # Event-specific styles
│   ├── script.js                       # Event-specific JS
│   ├── sessions.json                   # Session data (loaded at runtime)
│   ├── config.json                     # Event configuration/metadata
│   ├── generate_openfeedback.py        # OpenFeedback integration
│   └── openfeedback.json               # Generated feedback data
├── _template/                          # Reference template (used by script)
├── .github/
│   ├── copilot-instructions.md         # AI instructions for this repo
│   ├── prompts/
│   │   └── create-event.prompt.md      # Reusable Copilot skill for event creation
│   └── workflows/
│       ├── deploy.yml                  # GitHub Pages auto-deployment
│       └── update-openfeedback.yml     # Auto-regenerate OpenFeedback data
├── CREATING_AN_EVENT.md                # Detailed event creation guide
└── README.md                           # This file
```

## How It Works

- **Zero build step** — pure HTML/CSS/JS, served as static files
- **Dynamic programs** — `program.html` loads sessions from `sessions.json` at runtime with filters (day, track, type, room)
- **Self-contained events** — each event folder can be deleted cleanly without affecting others
- **Automated generation** — `create_event.py` parses pretalx data and generates everything

## Development

```bash
# Local preview
python3 -m http.server 8000
# Then open http://localhost:8000
```

## Deployment

Pushing to `main` triggers automatic deployment via GitHub Actions → GitHub Pages.

## Brand

| Token | Color | Usage |
|-------|-------|-------|
| Primary | `#26005a` | Deep purple — headings, navbar, hero backgrounds |
| Secondary | `#b650ff` | Bright purple — accents, hover states, highlights |
| Accent | `#ff58ac` | Pink — CTAs, badges, emphasis |

Dark mode is supported via `[data-theme="dark"]` selectors.
