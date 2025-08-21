#!/usr/bin/env python3
"""
Simple test script for the Reclaim Tasks API
"""

import requests
import json
import os
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Is the server running?")
        return False
    return True

def test_root_endpoint():
    """Test the root endpoint"""
    print("\n🏠 Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return True

def test_get_all_tasks():
    """Test getting all tasks"""
    print("\n📋 Testing get all tasks...")
    try:
        response = requests.get(f"{BASE_URL}/tasks")
        if response.status_code == 200:
            tasks = response.json()
            print(f"✅ Successfully retrieved {len(tasks)} tasks")
            
            if tasks:
                print("\n📝 Sample task:")
                sample_task = tasks[0]
                print(f"   ID: {sample_task.get('id')}")
                print(f"   Title: {sample_task.get('title')}")
                print(f"   Priority: {sample_task.get('priority')}")
                print(f"   Completed: {sample_task.get('completed')}")
                
                # Test getting specific task
                test_get_specific_task(sample_task['id'])
            else:
                print("   No tasks found")
        elif response.status_code == 401:
            print("❌ Authentication failed. Check your RECLAIM_TOKEN")
        else:
            print(f"❌ Failed to get tasks: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_get_specific_task(task_id):
    """Test getting a specific task by ID"""
    print(f"\n🎯 Testing get specific task (ID: {task_id})...")
    try:
        response = requests.get(f"{BASE_URL}/tasks/{task_id}")
        if response.status_code == 200:
            task = response.json()
            print("✅ Successfully retrieved specific task")
            print(f"   Title: {task.get('title')}")
            print(f"   Notes: {task.get('notes', 'No notes')}")
        elif response.status_code == 404:
            print("❌ Task not found")
        else:
            print(f"❌ Failed to get task: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("🧪 Reclaim Tasks API Test Suite")
    print("=" * 40)
    
    # Check if server is running
    if not test_health_check():
        print("\n💡 To start the server, run:")
        print("   cd api && ./start.sh")
        return
    
    # Test other endpoints
    test_root_endpoint()
    test_get_all_tasks()
    
    print("\n🎉 Test suite completed!")

if __name__ == "__main__":
    main()
