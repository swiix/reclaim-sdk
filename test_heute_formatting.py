#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from reclaim_sdk.client import ReclaimClient
from reclaim_sdk.resources.event import Event
from datetime import datetime, timezone, timedelta

# Set token
os.environ["RECLAIM_TOKEN"] = "fbf82296-f6e3-48f7-a70e-613914ce18cc"

# Configure client
client = ReclaimClient.configure(token="fbf82296-f6e3-48f7-a70e-613914ce18cc")

def get_next_event_for_task(task_id: int, client: ReclaimClient) -> dict:
    """Get the next scheduled event for a task"""
    try:
        # Get future events for this task
        future_events = Event.list_future_events(client=client, task_ids=[task_id])
        
        if not future_events:
            return None
        
        # Sort by start time and get the earliest
        future_events.sort(key=lambda e: e.event_start if e.event_start else datetime.max.replace(tzinfo=datetime.now().tzinfo))
        next_event = future_events[0]
        
        if not next_event.event_start:
            return None
        
        # Calculate time until start
        now = datetime.now(timezone.utc)
        time_until = next_event.event_start.astimezone(timezone.utc) - now
        
        # Format time until start
        if time_until.days > 0:
            time_until_text = f"in {time_until.days} Tagen"
        elif time_until.total_seconds() > 3600:
            hours = int(time_until.total_seconds() // 3600)
            time_until_text = f"in {hours}h"
        elif time_until.total_seconds() > 60:
            minutes = int(time_until.total_seconds() // 60)
            time_until_text = f"in {minutes}min"
        else:
            time_until_text = "jetzt"
        
        # Check if event is today and add "HEUTE" indicator
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Convert event start to UTC for comparison
        event_start_utc = next_event.event_start.astimezone(timezone.utc)
        
        print(f"DEBUG: Now: {now}")
        print(f"DEBUG: Event Start: {next_event.event_start}")
        print(f"DEBUG: Event Start UTC: {event_start_utc}")
        print(f"DEBUG: Today Start: {today_start}")
        print(f"DEBUG: Today End: {today_end}")
        print(f"DEBUG: Is Today: {today_start <= event_start_utc < today_end}")
        
        if today_start <= event_start_utc < today_end:
            time_until_text = f"HEUTE {time_until_text}"
        
        return {
            "event_id": next_event.event_id,
            "title": next_event.title,
            "start": next_event.event_start.isoformat(),
            "end": next_event.event_end.isoformat() if next_event.event_end else None,
            "duration_hours": next_event.get_duration_hours(),
            "time_until": time_until_text,
            "lock_state": next_event.lock_state,
            "defended": next_event.defended
        }
    except Exception as e:
        print(f"Error getting next event for task {task_id}: {e}")
        return None

print("🔍 TESTING HEUTE FORMATTING:")
print("="*60)

try:
    # Test with a task that has an event for tomorrow (should show "in Xh")
    print("🎯 TESTING TASK WITH EVENT TOMORROW:")
    print("-" * 40)
    
    next_event = get_next_event_for_task(10751263, client)  # Sunny work
    if next_event:
        print(f"✅ Event: {next_event['title']}")
        print(f"📅 Start: {next_event['start']}")
        print(f"⏰ Time Until: {next_event['time_until']}")
    else:
        print("❌ Kein Event gefunden")
    
    print()
    
    # Test with a task that has an event for today (if any)
    print("🎯 TESTING TASK WITH EVENT TODAY:")
    print("-" * 40)
    
    # Get all tasks with events today
    now = datetime.now(timezone.utc)
    today_events = Event.list_today_events(client=client)
    task_events = [e for e in today_events if e.task_id and e.event_start and e.event_start.astimezone(timezone.utc) > now]
    
    if task_events:
        task_id = task_events[0].task_id
        print(f"Testing Task ID: {task_id}")
        next_event = get_next_event_for_task(task_id, client)
        if next_event:
            print(f"✅ Event: {next_event['title']}")
            print(f"📅 Start: {next_event['start']}")
            print(f"⏰ Time Until: {next_event['time_until']}")
        else:
            print("❌ Kein Event gefunden")
    else:
        print("❌ Keine Tasks mit Events für heute gefunden")

except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
