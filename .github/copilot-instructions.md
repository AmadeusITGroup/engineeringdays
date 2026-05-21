# Copilot Instructions for Amadeus Events Repository

This repository hosts multiple event websites under a single GitHub Pages deployment.
Deployed at: `https://amadeusitgroup.github.io/events/`

## Repository Structure
- `index.html` — Landing page linking to all events (upcoming + past sections)
- `shared/` — Shared CSS (`styles-base.css`) and JS (`script-base.js`) used by all events
- `_template/` — Reference template for event structure
- `create_event.py` — **Automation script** to generate a new event from a pretalx JSON export
- Each event lives in its own subfolder (e.g., `engineering-days-2026/`)
- `.github/prompts/create-event.prompt.md` — Reusable Copilot skill for event creation

## Creating a New Event (Preferred Method)

**Use the automation script.** When asked to create a new event:

```bash
python3 create_event.py <sessions.json> --name "Event Name" --slug "event-slug-year"
```

This single command:
1. Parses the pretalx sessions JSON to extract all metadata (dates, tracks, types, locations, speakers)
2. Generates a complete event folder: `index.html`, `program.html`, `styles.css`, `script.js`, `config.json`, `sessions.json`
3. Adds an event card to the root `index.html` (auto-classifies as upcoming/past)

Optional flags: `--tagline`, `--description`, `--organizer`, `--contact`

## Updating an Event (after CFP closes)

When the Call for Papers is done and you have the finalized pretalx JSON:

```bash
python3 update_event.py <sessions.json> --slug "event-slug-year"
```

This command:
1. Parses the sessions JSON for real tracks, types, speakers
2. Updates `config.json` (replaces CFP example data with real metadata)
3. Regenerates `index.html` (removes CFP links, adds "View Program")
4. Generates `program.html` with filters
5. Copies sessions into `sessions.json`
6. Updates `events.json` registry with session count

If you need the full guided flow, use the **Create Event** prompt skill (`.github/prompts/create-event.prompt.md`).

## Pretalx Sessions JSON Format

All events use a pretalx JSON export as source of truth. Required fields per session:
- `Proposal title` — Session title
- `Session type` — Object with `en` key (e.g., `{"en": "Talk"}`)
- `Track` — Object with `en` key (e.g., `{"en": "AI, Data"}`)
- `Speaker names` — Array of strings
- `Room` — Object with `en` key
- `Start` / `End` — ISO 8601 timestamps

## Style Guidelines
- Amadeus brand colors: primary `#26005a`, secondary `#b650ff`, accent `#ff58ac`
- Events reference `../shared/styles-base.css` for common styles
- Event-specific overrides go in the event's own `styles.css`
- Every event navbar must include an "All Events" link pointing to `../index.html`
- Dark mode is supported via `[data-theme="dark"]` selectors

## File Naming Conventions
- Event folders: `{event-name}-{year}` (e.g., `hackathon-2027`)
- Sessions data: `sessions.json` (inside event folder)
- Config: `config.json` (inside event folder)
- OpenFeedback: `openfeedback.json` + `generate_openfeedback.py` (if applicable)

## GitHub Actions
- `deploy.yml` — Auto-deploys to GitHub Pages on push to `main`
- `update-openfeedback.yml` — Regenerates openfeedback.json when sessions change

## Key Principles
- Zero build step — pure HTML/CSS/JS, served as static files
- Program pages load sessions dynamically from `sessions.json` at runtime
- Each event is self-contained in its folder (can be deleted cleanly)
- Non-technical users should be able to create events via AI + the script
