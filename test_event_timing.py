#!/usr/bin/env python3

import os
from datetime import datetime, timedelta
from reclaim_sdk.client import ReclaimClient
from reclaim_sdk.resources.event import Event

# Set token
os.environ["RECLAIM_TOKEN"] = "fbf82296-f6e3-48f7-a70e-613914ce18cc"

# Configure client
client = ReclaimClient.configure(token="fbf82296-f6e3-48f7-a70e-613914ce18cc")

print("🔍 TESTING EVENT TIMING (Zukunft/Vergangenheit):")
print("="*60)

try:
    # Test 1: Future events
    print("🚀 ZUKÜNFTIGE EVENTS:")
    print("-" * 40)
    
    future_events = Event.list_future_events(client=client)
    print(f"📊 Zukünftige Events gefunden: {len(future_events)}")
    print()
    
    for i, event in enumerate(future_events[:5], 1):  # Show first 5
        time_until = event.get_time_until_start()
        duration_hours = event.get_duration_hours()
        
        print(f"{i}. {event.title}")
        print(f"   Start: {event.event_start}")
        print(f"   Ende: {event.event_end}")
        print(f"   Dauer: {duration_hours:.1f}h" if duration_hours else "   Dauer: N/A")
        print(f"   Zeit bis Start: {time_until}" if time_until else "   Zeit bis Start: N/A")
        print(f"   Task ID: {event.task_id}")
        print(f"   Typ: {event.type}")
        print()
    
    # Test 2: Past events
    print("📅 VERGANGENE EVENTS (letzte 30 Tage):")
    print("-" * 40)
    
    past_events = Event.list_past_events(client=client, days_back=30)
    print(f"📊 Vergangene Events gefunden: {len(past_events)}")
    print()
    
    for i, event in enumerate(past_events[:5], 1):  # Show first 5
        duration_hours = event.get_duration_hours()
        
        print(f"{i}. {event.title}")
        print(f"   Start: {event.event_start}")
        print(f"   Ende: {event.event_end}")
        print(f"   Dauer: {duration_hours:.1f}h" if duration_hours else "   Dauer: N/A")
        print(f"   Task ID: {event.task_id}")
        print(f"   Typ: {event.type}")
        print()
    
    # Test 3: Today's events
    print("📆 HEUTIGE EVENTS:")
    print("-" * 40)
    
    today_events = Event.list_today_events(client=client)
    print(f"📊 Heutige Events gefunden: {len(today_events)}")
    print()
    
    for i, event in enumerate(today_events[:5], 1):  # Show first 5
        duration_hours = event.get_duration_hours()
        
        print(f"{i}. {event.title}")
        print(f"   Start: {event.event_start}")
        print(f"   Ende: {event.event_end}")
        print(f"   Dauer: {duration_hours:.1f}h" if duration_hours else "   Dauer: N/A")
        print(f"   Task ID: {event.task_id}")
        print(f"   Typ: {event.type}")
        print()
    
    # Test 4: Individual event timing checks
    print("⏰ INDIVIDUELLE EVENT-TIMING CHECKS:")
    print("-" * 40)
    
    # Get a few events to test individual methods
    sample_events = Event.list_by_date_range(
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now() + timedelta(days=7),
        client=client
    )
    
    for i, event in enumerate(sample_events[:3], 1):
        print(f"Event {i}: {event.title}")
        print(f"   Ist Zukunft: {event.is_future()}")
        print(f"   Ist Vergangenheit: {event.is_past()}")
        print(f"   Ist heute: {event.is_today()}")
        print(f"   Dauer: {event.get_duration_hours():.1f}h" if event.get_duration_hours() else "   Dauer: N/A")
        print(f"   Zeit bis Start: {event.get_time_until_start()}" if event.get_time_until_start() else "   Zeit bis Start: N/A")
        print()
    
    # Test 5: Task-specific future events
    print("🎯 ZUKÜNFTIGE EVENTS FÜR TASK 10614949 (Keller aufräumen):")
    print("-" * 40)
    
    task_future_events = Event.list_future_events(client=client, task_ids=[10614949])
    print(f"📊 Zukünftige Events für Task 10614949: {len(task_future_events)}")
    print()
    
    for i, event in enumerate(task_future_events, 1):
        time_until = event.get_time_until_start()
        duration_hours = event.get_duration_hours()
        
        print(f"{i}. {event.title}")
        print(f"   Start: {event.event_start}")
        print(f"   Ende: {event.event_end}")
        print(f"   Dauer: {duration_hours:.1f}h" if duration_hours else "   Dauer: N/A")
        print(f"   Zeit bis Start: {time_until}" if time_until else "   Zeit bis Start: N/A")
        print(f"   Lock State: {event.lock_state}")
        print(f"   Defended: {event.defended}")
        print()

except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
