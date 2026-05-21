---
mode: agent
description: "Create a new event website from a pretalx sessions JSON export"
---

# Create a New Event Website

You are helping create a new event website for the Amadeus Events hub.
The user will provide a pretalx sessions JSON file. Your job is to run the automation script that generates the complete event site.

## Step 1: Gather Required Information

Ask the user for:
1. **Sessions JSON file** — The pretalx export (a JSON array of session objects). The user should provide the file path or drop it in the repo root.
2. **Event name** — e.g., "Amadeus Hackathon 2027"
3. **Event slug** (optional) — The folder name. If not provided, auto-generate from the name (lowercase, hyphens, include year).

Optional (script will use sensible defaults if not provided):
- **Tagline** — Short phrase for the hero section
- **Description** — Longer about text
- **Organizer** — Team name (default: "DevRel")
- **Contact email** — (default: "devrel@amadeus.com")

## Step 2: Run the Script

Run `create_event.py` with the gathered information:

```bash
python3 create_event.py <sessions.json> \
  --name "Event Name" \
  --slug "event-slug-year" \
  --tagline "Optional tagline" \
  --description "Optional description" \
  --organizer "Team Name" \
  --contact "email@amadeus.com"
```

The script will:
- Parse the sessions JSON to extract dates, tracks, session types, locations, speakers
- Generate the full event folder: `index.html`, `program.html`, `styles.css`, `script.js`, `event.json`, `sessions.json`
- Add an event card to the root `index.html` (upcoming or past based on dates)

## Step 3: Verify

After running the script:
1. Start a local server: `python3 -m http.server 8000`
2. Check the landing page at http://localhost:8000/ — confirm the new event card appears
3. Check the event page at http://localhost:8000/<slug>/index.html
4. Check the program page at http://localhost:8000/<slug>/program.html — confirm sessions load and filters work

## Step 4: Customization (Optional)

If the user wants customization:
- **Colors**: Edit `<slug>/styles.css` to override CSS variables (`--primary`, `--secondary`, `--accent`)
- **Tracks**: The script auto-detects tracks from the sessions JSON
- **Content**: Edit `<slug>/index.html` to update about text, add sections, etc.

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
