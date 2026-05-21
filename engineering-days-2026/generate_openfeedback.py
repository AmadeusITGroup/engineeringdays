#!/usr/bin/env python3
"""
Generate openfeedback.json from engineering-days-2026_sessions.json

This script transforms the pretalx sessions export format into the OpenFeedback format.
"""

import json
from datetime import datetime
import hashlib


def generate_speaker_id(name):
    """Generate a stable speaker ID from the speaker name."""
    return hashlib.md5(name.encode()).hexdigest()[:12]


def transform_sessions_to_openfeedback(sessions_data):
    """Transform engineering-days-2026_sessions.json format to openfeedback.json format."""
    sessions = {}
    speakers = {}
    
    for session in sessions_data:
        # Skip sessions without scheduled time (like lunch-time booths without a slot)
        if not session.get('Start'):
            continue
            
        session_id = session.get('ID')
        
        # Get speaker IDs from speaker names
        speaker_ids = []
        for speaker_name in session.get('Speaker names', []):
            if speaker_name:
                speaker_guid = generate_speaker_id(speaker_name)
                speaker_ids.append(speaker_guid)
                
                # Add speaker to speakers dict if not already present
                if speaker_guid not in speakers:
                    speakers[speaker_guid] = {
                        'id': speaker_guid,
                        'name': speaker_name,
                        'photoUrl': 'https://amadeusitgroup.github.io/events/engineering-days-2026/image.png',
                        'socials': []
                    }
        
        # Parse start and end times
        start_time = session.get('Start')
        end_time = session.get('End')
        
        # Get track as tag
        track = session.get('Track', {})
        track_name = track.get('en') if isinstance(track, dict) else None
        tags = [track_name] if track_name else []
        
        # Get room name
        room = session.get('Room', {})
        room_name = room.get('en') if isinstance(room, dict) else 'TBD'
        
        sessions[session_id] = {
            'id': session_id,
            'title': session.get('Proposal title', ''),
            'speakers': speaker_ids,
            'tags': tags,
            'startTime': start_time,
            'endTime': end_time,
            'trackTitle': room_name
        }
    
    return {
        'sessions': sessions,
        'speakers': speakers
    }


def main():
    # Read engineering-days-2026_sessions.json
    with open('engineering-days-2026_sessions.json', 'r', encoding='utf-8') as f:
        sessions_data = json.load(f)
    
    # Transform to OpenFeedback format
    openfeedback_data = transform_sessions_to_openfeedback(sessions_data)
    
    # Write openfeedback.json
    with open('openfeedback.json', 'w', encoding='utf-8') as f:
        json.dump(openfeedback_data, f, indent=4, ensure_ascii=False)
    
    print(f"Generated openfeedback.json with {len(openfeedback_data['sessions'])} sessions and {len(openfeedback_data['speakers'])} speakers")


if __name__ == '__main__':
    main()
