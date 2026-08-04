---
agent: agent
description: "Update an existing event with the finalized program from a pretalx sessions JSON (after CFP closes)"
---

# Update an Event with Finalized Program

You are helping update an existing event that was created in CFP mode. The Call for Papers is now closed and the user has the finalized sessions JSON from pretalx.

## Step 1: Gather Required Information

Ask the user for:
1. **Sessions JSON file** — The pretalx export with finalized sessions (preferred)
2. **Event slug** — The folder name of the event to update (e.g., "engineering-days-2026")

If no sessions JSON is available yet, collect talks manually and generate one:
```bash
python3 scripts/events/build_sessions_json.py --out sessions-manual.json
```

Then continue with:
```bash
python3 scripts/events/update_event.py sessions-manual.json --slug "event-slug-year"
```

If the user doesn't know the slug, list available events:
```bash
ls -d */config.json | sed 's|/config.json||'
```

## Step 2: Run the Script

```bash
python3 scripts/events/update_event.py <sessions.json> --slug "event-slug-year"
```

The script will:
1. Parse the sessions JSON for real tracks, types, speakers
2. Update `config.json` (replaces CFP example data with real metadata)
3. Regenerate `index.html` (removes "Submit a talk (CFP)" links, adds "View Program")
4. Generate `program.html` with day/track/type/room filters
5. Copy sessions into `sessions.json`
6. Update the root `events.json` registry with session count

User-edited fields are preserved: event name, tagline, description, colors, locations, `showFeedback`, and per-session-type `highlight` flags (matched by session type name).

## Step 3: Verify

After running the script:
1. Start a local server: `python3 scripts/dev/serve.py`
2. Check the event page at http://localhost:8000/<slug>/index.html — confirm:
   - No more "Submit a talk (CFP)" button
   - "View Program" button is shown instead
   - Stats reflect real session/speaker counts
   - Tracks section shows actual tracks from the sessions
3. Check the program at http://localhost:8000/<slug>/program.html — confirm:
   - Sessions are listed and filterable
   - Day/track/type/room filters work

## Step 4: What Changed

| Before (CFP mode) | After (updated) |
|---|---|
| "Submit a talk (CFP)" button | "View Program" button |
| Example placeholder tracks | Real tracks from sessions |
| Example session types | Real types with counts |
| 0+ sessions, 0 speakers | Actual numbers |
| No program.html | Full program with filters |
| Empty sessions.json | Populated with all sessions |

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

If you generated the file via `scripts/events/build_sessions_json.py`, it already follows this format.

## Important Notes

- The script preserves custom edits made to `config.json` fields (name, tagline, description, colors, `showFeedback`, and matching `sessionTypes[].highlight` values)
- `styles.css` is NOT overwritten — any custom CSS tweaks are preserved
- If the event doesn't exist yet, use the **Create Event** prompt instead
- After updating, you can still manually edit `config.json` to tweak track descriptions, icons, etc.
