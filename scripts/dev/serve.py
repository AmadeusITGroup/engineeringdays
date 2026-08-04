#!/usr/bin/env python3
"""Serve the Amadeus Events site locally for previewing.

The pages fetch config.json/sessions.json at runtime, so the site must be
served over HTTP (opening index.html via file:// does not work). This serves
the repository root - the same thing GitHub Pages does - no matter which
directory you launch it from.

Usage (from anywhere):
    python scripts/dev/serve.py                # http://127.0.0.1:8000
    python scripts/dev/serve.py --port 9000    # custom port
    python scripts/dev/serve.py --no-browser   # don't auto-open the browser
"""

import argparse
import functools
import json
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# This script lives in scripts/dev/, so the repository root is two levels up.
REPO_ROOT = Path(__file__).resolve().parents[2]


def list_event_slugs():
    """Return event slugs from events.json (best effort, for handy links)."""
    events_path = REPO_ROOT / "events.json"
    try:
        events = json.loads(events_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []
    return [e["slug"] for e in events if isinstance(e, dict) and e.get("slug")]


def print_urls(base):
    print(f"\nServing {REPO_ROOT} at {base}")
    print(f"  Landing page: {base}/")
    for slug in list_event_slugs():
        print(f"  {slug}: {base}/{slug}/index.html")
    print("\nPress Ctrl+C to stop.\n")


def main():
    parser = argparse.ArgumentParser(description="Serve the events site locally.")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser automatically")
    args = parser.parse_args()

    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(REPO_ROOT))

    try:
        server = ThreadingHTTPServer((args.host, args.port), handler)
    except OSError as exc:
        print(f"Error: could not bind to {args.host}:{args.port} ({exc}).")
        print("The port may already be in use - try a different one with --port.")
        sys.exit(1)

    base = f"http://{args.host}:{args.port}"
    print_urls(base)

    if not args.no_browser:
        webbrowser.open(f"{base}/")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
