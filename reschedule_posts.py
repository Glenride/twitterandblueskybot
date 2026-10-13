#!/usr/bin/env python3
"""Reschedule posts with human-like timing (1.5-2 hours between posts)."""

import json
import random
from datetime import datetime, timedelta, timezone

# Load the content library
with open('twikit/bot/content-library.json', 'r') as f:
    content = json.load(f)

# Start from current time (or a specific start time)
# Using Nov 8, 2025 at 9am EST as starting point
start_time = datetime(2025, 11, 8, 14, 0, 0, tzinfo=timezone.utc)  # 9am EST = 2pm UTC

current_time = start_time

def get_human_interval():
    """Return a random interval between 1.5 and 2 hours (90-120 minutes)."""
    # Random interval between 90-120 minutes
    minutes = random.randint(90, 120)
    # Add some minute variation (not always :00, :15, :30, :45)
    minute_offset = random.choice([0, 3, 7, 12, 17, 23, 28, 33, 38, 42, 47, 52, 57])
    return timedelta(minutes=minutes) + timedelta(minutes=minute_offset)

# Reschedule posts
print(f"Rescheduling {len(content['posts'])} posts...")
for i, post in enumerate(content['posts']):
    if i > 0:
        # Add random interval for subsequent posts
        current_time += get_human_interval()
    
    # Create a 15-minute window around the scheduled time
    earliest = current_time
    latest = current_time + timedelta(minutes=15)
    
    post['scheduled_window'] = {
        'earliest': earliest.isoformat().replace('+00:00', 'Z'),
        'latest': latest.isoformat().replace('+00:00', 'Z')
    }
    
    print(f"  {post['id']}: {earliest.strftime('%Y-%m-%d %H:%M UTC')}")

# Reschedule replies with similar logic
print(f"\nRescheduling {len(content['replies'])} replies...")
reply_time = start_time + timedelta(minutes=45)  # Start replies 45 min after first post

for i, reply in enumerate(content['replies']):
    if i > 0:
        reply_time += get_human_interval()
    
    earliest = reply_time
    latest = reply_time + timedelta(minutes=30)  # Wider window for replies
    
    reply['scheduled_window'] = {
        'earliest': earliest.isoformat().replace('+00:00', 'Z'),
        'latest': latest.isoformat().replace('+00:00', 'Z')
    }
    
    print(f"  {reply['id']}: {earliest.strftime('%Y-%m-%d %H:%M UTC')}")

# Reschedule DMs with even longer intervals
if 'dms' in content and content['dms']:
    print(f"\nRescheduling {len(content['dms'])} DMs...")
    dm_time = start_time + timedelta(hours=3)  # Start DMs 3 hours after first post
    
    for i, dm in enumerate(content['dms']):
        if i > 0:
            # DMs should be spaced even further apart (3-4 hours)
            dm_time += timedelta(minutes=random.randint(180, 240))
        
        earliest = dm_time
        latest = dm_time + timedelta(minutes=30)
        
        dm['scheduled_window'] = {
            'earliest': earliest.isoformat().replace('+00:00', 'Z'),
            'latest': latest.isoformat().replace('+00:00', 'Z')
        }
        
        print(f"  {dm['id']}: {earliest.strftime('%Y-%m-%d %H:%M UTC')}")

# Save the updated content library
with open('twikit/bot/content-library.json', 'w') as f:
    json.dump(content, f, indent=2)

print("\n✅ Content library updated with human-like scheduling!")
print(f"📅 First post: {start_time.strftime('%Y-%m-%d %H:%M UTC')}")
print(f"📅 Last post: {current_time.strftime('%Y-%m-%d %H:%M UTC')}")
print(f"⏱️  Total duration: {(current_time - start_time).total_seconds() / 3600:.1f} hours")
print(f"⏱️  Average interval: {(current_time - start_time).total_seconds() / 3600 / len(content['posts']):.2f} hours per post")
