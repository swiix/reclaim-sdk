#!/usr/bin/env python3

import os
from reclaim_sdk.client import ReclaimClient
from reclaim_sdk.resources.hours import Hours

# Set token
os.environ["RECLAIM_TOKEN"] = "fbf82296-f6e3-48f7-a70e-613914ce18cc"

# Configure client
client = ReclaimClient.configure(token="fbf82296-f6e3-48f7-a70e-613914ce18cc")

print("🔍 TESTING TIMESCHEMES API:")
print("="*60)

try:
    # Get all timeschemes
    timeschemes = Hours.list(client=client)
    
    print(f"📊 Gefundene Timeschemes: {len(timeschemes)}")
    print()
    
    for i, scheme in enumerate(timeschemes, 1):
        print(f"{i}. {scheme.title}")
        print(f"   ID: {scheme.id}")
        print(f"   Status: {scheme.status}")
        print(f"   Beschreibung: {scheme.description}")
        print(f"   Task Category: {scheme.task_category}")
        print(f"   Features: {scheme.features}")
        if scheme.task_target_calendar:
            print(f"   Target Calendar: {scheme.task_target_calendar}")
        print()
        
except Exception as e:
    print(f"❌ Fehler: {e}")
