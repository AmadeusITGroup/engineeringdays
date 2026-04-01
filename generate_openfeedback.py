#!/usr/bin/env python3
"""
Generate openfeedback.json from schedule.json

This script transforms the pretalx/c3voc schedule format into the OpenFeedback format.
"""

import json
from datetime import datetime, timedelta
import re


def parse_duration(duration_str):
    """Parse duration string like '00:25' or '02:00' into timedelta."""
    parts = duration_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    return timedelta(hours=hours, minutes=minutes)


def calculate_end_time(start_datetime_str, duration_str):
    """Calculate end time from start datetime and duration."""
    # Parse the ISO format datetime
    start_dt = datetime.fromisoformat(start_datetime_str)
    duration = parse_duration(duration_str)
    end_dt = start_dt + duration
    return end_dt.isoformat()


def transform_schedule_to_openfeedback(schedule_data):
    """Transform schedule.json format to openfeedback.json format."""
    sessions = {}
    speakers = {}
    
    conference = schedule_data.get('schedule', {}).get('conference', {})
    days = conference.get('days', [])
    
    for day in days:
        rooms = day.get('rooms', {})
        for room_name, room_sessions in rooms.items():
            for session in room_sessions:
                session_id = str(session.get('id'))
                
                # Get speaker IDs from persons
                speaker_ids = []
                for person in session.get('persons', []):
                    speaker_guid = person.get('guid')
                    if speaker_guid:
                        speaker_ids.append(speaker_guid)
                        
                        # Add speaker to speakers dict if not already present
                        if speaker_guid not in speakers:
                            speakers[speaker_guid] = {
                                'id': speaker_guid,
                                'name': person.get('public_name', ''),
                                'socials': []
                            }
                
                # Build session entry
                start_time = session.get('date')
                duration = session.get('duration', '00:25')
                end_time = calculate_end_time(start_time, duration)
                
                # Use track as tag
                track = session.get('track')
                tags = [track] if track else []
                
                sessions[session_id] = {
                    'id': session_id,
                    'title': session.get('title', ''),
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
    # Read schedule.json
    with open('schedule.json', 'r', encoding='utf-8') as f:
        schedule_data = json.load(f)
    
    # Transform to OpenFeedback format
    openfeedback_data = transform_schedule_to_openfeedback(schedule_data)
    
    # Write openfeedback.json
    with open('openfeedback.json', 'w', encoding='utf-8') as f:
        json.dump(openfeedback_data, f, indent=4, ensure_ascii=False)
    
    print(f"Generated openfeedback.json with {len(openfeedback_data['sessions'])} sessions and {len(openfeedback_data['speakers'])} speakers")


if __name__ == '__main__':
    main()
