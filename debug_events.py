#!/usr/bin/env python3

import os
import json
from datetime import datetime
from reclaim_sdk.client import ReclaimClient

# Set token
os.environ["RECLAIM_TOKEN"] = "fbf82296-f6e3-48f7-a70e-613914ce18cc"

# Configure client
client = ReclaimClient.configure(token="fbf82296-f6e3-48f7-a70e-613914ce18cc")

print("🔍 DEBUGGING EVENTS API RAW RESPONSE:")
print("="*60)

try:
    # Test the exact URL from the user
    start_date = "2025-07-06"
    end_date = "2025-11-14"
    
    print(f"📅 Testing URL: /api/events?start={start_date}&end={end_date}&allConnected=true&taskIds=10614949")
    print()
    
    # Make direct API call to see raw response
    params = {
        "start": start_date,
        "end": end_date,
        "allConnected": "true",
        "taskIds": "10614949"
    }
    
    raw_data = client.get("/api/events", params=params)
    
    print(f"📊 Raw API Response - Anzahl Events: {len(raw_data)}")
    print()
    
    # Show first 3 events in detail
    for i, event in enumerate(raw_data[:3], 1):
        print(f"Event {i}:")
        print(json.dumps(event, indent=2, default=str))
        print("-" * 40)
    
    # Also test without taskIds filter
    print("\n🔍 Testing without taskIds filter:")
    print("-" * 40)
    
    params_no_filter = {
        "start": start_date,
        "end": end_date,
        "allConnected": "true"
    }
    
    raw_data_no_filter = client.get("/api/events", params=params_no_filter)
    
    print(f"📊 Events ohne Task-Filter: {len(raw_data_no_filter)}")
    
    # Show first event structure
    if raw_data_no_filter:
        print("\nFirst event structure:")
        print(json.dumps(raw_data_no_filter[0], indent=2, default=str))

except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
