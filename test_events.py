#!/usr/bin/env python3

import os
from datetime import datetime, timedelta
from reclaim_sdk.client import ReclaimClient
from reclaim_sdk.resources.event import Event

# Set token
os.environ["RECLAIM_TOKEN"] = "fbf82296-f6e3-48f7-a70e-613914ce18cc"

# Configure client
client = ReclaimClient.configure(token="fbf82296-f6e3-48f7-a70e-613914ce18cc")

print("🔍 TESTING EVENTS API:")
print("="*60)

try:
    # Test 1: List events for a date range (like the provided URL)
    start_date = datetime(2025, 7, 6)
    end_date = datetime(2025, 11, 14)
    
    print(f"📅 Testing events from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print()
    
    events = Event.list_by_date_range(
        start_date=start_date,
        end_date=end_date,
        client=client,
        all_connected=True
    )
    
    print(f"📊 Gefundene Events: {len(events)}")
    print()
    
    for i, event in enumerate(events[:10], 1):  # Show first 10 events
        print(f"{i}. {event.title}")
        print(f"   Event ID: {event.event_id}")
        print(f"   Start: {event.event_start}")
        print(f"   End: {event.event_end}")
        print(f"   Time Chunks: {event.time_chunks}" if event.time_chunks else "   Time Chunks: N/A")
        print(f"   Category: {event.category}")
        print(f"   Color: {event.color}")
        print(f"   Task ID: {event.task_id}")
        print(f"   Private: {event.private}")
        print(f"   Type: {event.type}")
        print()
    
    # Test 2: Filter by specific task ID (like in the provided URL)
    print("🔍 Testing events filtered by task ID 10614949:")
    print("-" * 40)
    
    task_specific_events = Event.list_by_date_range(
        start_date=start_date,
        end_date=end_date,
        client=client,
        all_connected=True,
        task_ids=[10614949]
    )
    
    print(f"📊 Events für Task 10614949: {len(task_specific_events)}")
    print()
    
    for i, event in enumerate(task_specific_events, 1):
        print(f"{i}. {event.title}")
        print(f"   Event ID: {event.event_id}")
        print(f"   Start: {event.event_start}")
        print(f"   End: {event.event_end}")
        print(f"   Time Chunks: {event.time_chunks}" if event.time_chunks else "   Time Chunks: N/A")
        print()
    
    # Test 3: Test basic list method
    print("🔍 Testing basic Event.list() method:")
    print("-" * 40)
    
    basic_events = Event.list(client=client)
    print(f"📊 Basic events (no filters): {len(basic_events)}")
    print()
    
    for i, event in enumerate(basic_events[:5], 1):  # Show first 5
        print(f"{i}. {event.title}")
        print(f"   Event ID: {event.event_id}")
        print(f"   Start: {event.event_start}")
        print()

except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
