---
mode: agent
description: "Create a new event website from a pretalx sessions JSON export (or without one)"
---

# Create a New Event Website

You are helping create a new event website for the Amadeus Events hub.
The user may or may not have a pretalx sessions JSON file. Your job is to gather the required info and run the automation script.

## Step 1: Gather Required Information

Ask the user for:
1. **Event name** — e.g., "Amadeus Hackathon 2027"
2. **Event dates** — e.g., "15-16 June 2027"
3. **Locations** — e.g., "Nice FR, London UK, Bangalore IN"
4. **Sessions JSON file** (optional) — The pretalx export. If not available yet, the event will be created in "CFP mode" (Call for Papers) with a link to submit talks via email.

Optional (script will use sensible defaults if not provided):
- **Event slug** — The folder name. If not provided, auto-generate from the name (lowercase, hyphens, include year).
- **Tagline** — Short phrase for the hero section
- **Description** — Longer about text
- **Organizer** — Team name (default: "DevRel")
- **Contact email** — (default: "devrel@amadeus.com")

## Step 2: Run the Script

### With sessions JSON:
```bash
python3 create_event.py <sessions.json> \
  --name "Event Name" \
  --slug "event-slug-year" \
  --dates "15-16 June 2027" \
  --locations "Nice FR, London UK" \
  --tagline "Optional tagline" \
  --description "Optional description" \
  --organizer "Team Name" \
  --contact "email@amadeus.com"
```

### Without sessions JSON (CFP mode):
```bash
python3 create_event.py \
  --name "Event Name" \
  --slug "event-slug-year" \
  --dates "15-16 June 2027" \
  --locations "Nice FR, London UK" \
  --tagline "Optional tagline" \
  --organizer "Team Name" \
  --contact "email@amadeus.com"
```

When no sessions JSON is provided:
- No `program.html` is generated
- The event page shows a "Submit a Talk (CFP)" button that opens a mailto: link
- An empty `sessions.json` is created (ready to be populated later)

The script will:
- Parse the sessions JSON (if provided) to extract tracks, session types, speakers
- Generate the event folder: `index.html`, `styles.css`, `script.js`, `event.json`, `sessions.json`, and optionally `program.html`
- Add an event card to the root `index.html` (upcoming or past based on dates)

## Step 3: Verify

After running the script:
1. Start a local server: `python3 -m http.server 8000`
2. Check the landing page at http://localhost:8000/ — confirm the new event card appears
3. Check the event page at http://localhost:8000/<slug>/index.html
4. If sessions were provided, check http://localhost:8000/<slug>/program.html

## Step 4: Customization via event.json

The event page reads from `event.json` at runtime. **Non-technical users can edit this file directly** to update the website without re-running the script.

Editable fields in `<slug>/event.json`:
- **`eventName`** — Event title displayed everywhere
- **`tagline`** — Short subtitle shown in the hero
- **`description`** — About section text
- **`dates.display`** — Date string shown on the page
- **`locations`** — Array of location strings (e.g., `["Nice FR", "London UK"]`)
- **`tracks`** — Array of track objects with `icon`, `name`, `description`
- **`sessionTypes`** — Array with `name`, `duration`, `description`
- **`stats`** — Array of stat cards with `icon`, `number`, `label`, `description`
- **`contact`** — Contact email
- **`colors`** — Brand color overrides (`primary`, `secondary`, `accent`)

In CFP mode, tracks and session types are pre-filled with examples — the user should replace them with the real ones for their event.

For CSS-level customization:
- **Colors**: Edit `<slug>/styles.css` to override CSS variables

## Pretalx JSON Format Reference

The sessions JSON must be an array of objects with these fields:
```json
{
  "ID": "ABC123",
  "Proposal title": "Talk Title",
  "Session type": { "en": "Talk" },
  "Track": { "en": "AI, Data" },
  "Description": "Session description...",
  "Speaker names": ["Speaker One", "Speaker Two"],
  "Room": { "en": "Room A" },
  "Start": "2026-04-29T09:00:00+02:00",
  "End": "2026-04-29T09:45:00+02:00"
}
```

## Important Notes

- The event folder is self-contained — all event-specific code stays in the folder
- The `program.html` dynamically loads sessions from `sessions.json` at runtime (no build step)
- Filters (day, track, type, room) are auto-populated from the session data
- The landing page card is automatically classified as "upcoming" or "past" based on dates
- If the event has an OpenFeedback integration, also run `generate_openfeedback.py` in the event folder
