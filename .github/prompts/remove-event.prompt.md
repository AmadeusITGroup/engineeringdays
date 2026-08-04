---
agent: agent
description: "Remove an existing event from the hub"
---

# Remove an Event

You are helping remove an event from the Amadeus Events hub.

## Step 1: Run the removal script

```bash
python3 scripts/events/remove_event.py
```

The script will:
1. List all existing events (reads from `events.json`)
2. Ask the user to pick one by number
3. Confirm the deletion
4. Remove the event folder and its entry from `events.json`

## Important Notes

- This is **irreversible** — the event folder and all its files are deleted
- The root `events.json` registry is updated automatically
- The landing page will no longer show the removed event (it renders from `events.json` at runtime)
- If running non-interactively, you can also just delete the folder and remove the entry from `events.json` manually
