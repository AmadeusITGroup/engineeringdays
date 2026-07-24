# How to Create a New Event Website

**You don't need to know how to code.** Just follow these steps.

---

## What You'll Need

1. **VS Code** installed on your computer (ask IT if you don't have it)
2. **GitHub Copilot** extension installed in VS Code (your Amadeus license covers it)
3. **The sessions JSON file** — exported from pretalx. Ask your event coordinator or the DevRel team for this file.

---

## Step-by-Step Guide

### Step 1: Open the project

Open VS Code, then open this repository folder (`events/`).

### Step 2: Drop your sessions file into the folder

Take the `.json` file you got from pretalx and drag it into the project folder in VS Code's file explorer (the left panel).

### Step 3: Open Copilot Chat

Click the **Copilot icon** in the left sidebar (it looks like a small robot), or press:
- **Mac:** `Cmd + L`
- **Windows:** `Ctrl + L`

### Step 4: Use the "Create Event" skill

There's a ready-made skill that guides Copilot through event creation. To use it:

1. In the Copilot Chat input box, type **`/`** — a list of available prompts appears
2. Select **`create-event`** from the list
3. Then type your request, for example:

> Create a new event called "Amadeus Hackathon 2027" from the file hackathon_sessions.json

Copilot will read your sessions file, figure out all the details (dates, speakers, tracks, rooms), and generate the full website automatically.

> **Alternative:** You can also skip the `/` command and just ask Copilot directly — it already knows how to create events thanks to the repository instructions. The skill just makes it more reliable.

### Step 5: Check it looks good

Copilot will show you what it created. You can ask it:

> Preview the site for me

Or:

> Show me what the event page looks like

### Step 6: Publish

When you're happy with it, ask Copilot:

> Commit and push this new event

The website will be live within a minute at the GitHub Pages URL.

---

## About the "Create Event" Skill

This repo includes a **reusable Copilot skill** at `.github/prompts/create-event.prompt.md`. It's a set of instructions that tells Copilot exactly how to:

- Ask you for the right information
- Run the automation script with the correct parameters
- Verify the generated site works
- Help you customize anything afterwards

**You don't need to read or edit this file.** It's there for Copilot to follow. Just invoke it with `/create-event` in the chat and let it guide you.

---

## Want to Customize?

Just tell Copilot in plain English. Here are some examples:

| What you want | What to say |
|---------------|-------------|
| Custom tagline | _"Use the tagline: Where builders connect"_ |
| Different description | _"Change the about section to talk about sustainability and innovation"_ |
| Change colors | _"Make the event colors blue and green instead of purple"_ |
| Toggle feedback links | _"Set `showFeedback` to `true` in my event's `config.json`"_ |
| Highlight one session type card | _"In `sessionTypes`, set `highlight: true` for Closing cocktail and use `tag: \"Exclusive\"`"_ |
| Fix the date display | _"The date should say 15-16 June 2027"_ |
| Move between sections | _"This event should be in the upcoming section, not past"_ |
| Update sessions later | _"Update the sessions for hackathon-2027 with this new file"_ |
| Delete an event | _"Remove the hackathon-2027 event completely"_ |

---

## Example Conversations

### Basic event creation

> **You:** Create a new event called "Tech Summit 2027" from summit_sessions.json
>
> **Copilot:** _(creates everything automatically)_ Done! I created the Tech Summit 2027 event with 45 sessions across 6 tracks...

### With more details

> **You:** Create a new event from the file devcon_sessions.json. Call it "Amadeus DevCon 2027". The tagline is "Code. Connect. Create." It's organized by the Platform Engineering team and the contact is platform@amadeus.com
>
> **Copilot:** _(creates everything with your custom details)_

### Fixing something after creation

> **You:** The description on the DevCon page is too generic. Make it mention that this is our flagship developer conference with hands-on workshops and keynotes from industry leaders.
>
> **Copilot:** _(updates the description)_

---

## Frequently Asked Questions

**Where do I get the sessions JSON file?**
From pretalx — the tool used to manage talk submissions. Ask whoever is managing the Call for Papers, or ask the DevRel team.

**What if I don't have the sessions file yet?**
You can still create the event! Just tell Copilot the basics (name, dates, description) and say "I'll add the sessions later." When you get the file, come back and say "Add these sessions to my event."

**What if Copilot makes a mistake?**
Just tell it what's wrong. "The event name is spelled wrong" or "Remove the third track" — it will fix it.

**Can I preview before publishing?**
Yes! Ask Copilot to "preview the site" or "start a local server." It will open a browser preview.

**How do I know it's published?**
After you push, the site auto-deploys in about 60 seconds. The URL is:
`https://amadeusitgroup.github.io/events/<your-event-slug>/`

**Can multiple people work on this?**
Yes, but coordinate with your team so you don't edit the same files at the same time. Standard Git workflow applies.

---

## Need Help?

- Ask in the **#devrel** Slack channel
- Email **devrel@amadeus.com**
- Or just ask Copilot — it knows how this repo works!
