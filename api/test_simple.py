#!/usr/bin/env python3
"""
Simple test to debug reclaim-sdk connection
"""

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set token from environment variable
token = os.environ.get("RECLAIM_TOKEN")
if not token:
    print("❌ Error: RECLAIM_TOKEN environment variable is not set")
    print("Please set your Reclaim API token:")
    print("export RECLAIM_TOKEN='your_token_here'")
    exit(1)
os.environ["RECLAIM_TOKEN"] = token

print("🔍 Testing reclaim-sdk connection...")
print(f"Token: {os.environ.get('RECLAIM_TOKEN')}")

try:
    from reclaim_sdk.client import ReclaimClient
    from reclaim_sdk.resources.task import Task
    
    print("✅ Imports successful")
    
    # Configure client
    client = ReclaimClient.configure(token=token)
    print("✅ Client configured")
    
    # Test getting tasks
    print("📋 Fetching tasks...")
    tasks = Task.list()
    print(f"✅ Successfully retrieved {len(tasks)} tasks")
    
    if tasks:
        print("\n📝 Sample task:")
        task = tasks[0]
        print(f"   ID: {task.id}")
        print(f"   Title: {task.title}")
        print(f"   Priority: {task.priority}")
        print(f"   Completed: {task.completed}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
