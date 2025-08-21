#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from reclaim_sdk.client import ReclaimClient
from reclaim_sdk.resources.task import Task
from reclaim_sdk.resources.event import Event
from datetime import datetime

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
        now = datetime.now(next_event.event_start.tzinfo)
        time_until = next_event.event_start - now
        
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

print("🔍 TESTING NEXT EVENT FUNCTIONALITY:")
print("="*60)

try:
    # Get some tasks
    tasks = Task.list(client=client)
    print(f"📊 Gefundene Tasks: {len(tasks)}")
    print()
    
    # Test with first 5 tasks that have IDs
    test_tasks = [task for task in tasks if task.id][:5]
    
    for i, task in enumerate(test_tasks, 1):
        print(f"{i}. Task: {task.title}")
        print(f"   Task ID: {task.id}")
        print(f"   Status: {task.status}")
        print(f"   At Risk: {task.at_risk}")
        
        # Get next event
        next_event = get_next_event_for_task(task.id, client)
        
        if next_event:
            print(f"   📅 Nächstes Event: {next_event['title']}")
            print(f"   📅 Start: {next_event['start']}")
            print(f"   📅 Zeit bis Start: {next_event['time_until']}")
            print(f"   📅 Dauer: {next_event['duration_hours']:.1f}h" if next_event['duration_hours'] else "   📅 Dauer: N/A")
            print(f"   📅 Lock State: {next_event['lock_state']}")
        else:
            print("   📅 Nächstes Event: Kein Event geplant")
        
        print()

except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
