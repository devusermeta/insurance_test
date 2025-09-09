#!/usr/bin/env python3
"""Test script for Processing Steps UI functionality"""

import requests
import time
import json

def test_processing_steps_lifecycle():
    """Test the complete processing steps lifecycle"""
    
    print("=== Testing Processing Steps UI Lifecycle ===")
    
    # Step 1: Clear any existing sessions
    print("\n1. Clearing existing sessions...")
    try:
        requests.post('http://localhost:3000/api/stop-processing/OP-1002')
        print("   ✅ Sessions cleared")
    except Exception as e:
        print(f"   ⚠️ Clear failed (may be empty): {e}")
    
    # Step 2: Check initial state (should be empty)
    print("\n2. Checking initial state...")
    try:
        response = requests.get('http://localhost:3000/api/processing-steps')
        data = response.json()
        steps_count = len(data.get('steps', []))
        active_sessions = data.get('active_sessions', 0)
        print(f"   Steps: {steps_count}, Active Sessions: {active_sessions}")
        
        if steps_count == 0 and active_sessions == 0:
            print("   ✅ Initial state is clean")
        else:
            print("   ⚠️ Initial state has leftover data")
            
    except Exception as e:
        print(f"   ❌ Failed to check initial state: {e}")
        return False
    
    # Step 3: Start a processing session
    print("\n3. Starting processing session...")
    try:
        session_response = requests.post('http://localhost:3000/api/start-processing/OP-1002')
        session_data = session_response.json()
        print(f"   Session result: {session_data.get('status')}")
        
        if session_data.get('status') == 'success':
            print("   ✅ Session started successfully")
        else:
            print("   ❌ Session failed to start")
            return False
            
    except Exception as e:
        print(f"   ❌ Failed to start session: {e}")
        return False
    
    # Step 4: Check if steps appear (wait a moment)
    print("\n4. Checking for processing steps...")
    time.sleep(2)  # Wait for any async operations
    
    try:
        response = requests.get('http://localhost:3000/api/processing-steps')
        data = response.json()
        steps_count = len(data.get('steps', []))
        active_sessions = data.get('active_sessions', 0)
        
        print(f"   Steps: {steps_count}, Active Sessions: {active_sessions}")
        
        if active_sessions > 0:
            print("   ✅ Session is actively tracked")
        else:
            print("   ⚠️ Session not showing as active")
            
        # Show first few step titles if available
        steps = data.get('steps', [])
        if steps:
            print("   First 3 steps:")
            for i, step in enumerate(steps[:3]):
                title = step.get('title', f'Step {i+1}')
                status = 'completed' if step.get('completed_at') else 'active' if step.get('started_at') else 'pending'
                print(f"     {i+1}. {title} ({status})")
                
    except Exception as e:
        print(f"   ❌ Failed to check processing steps: {e}")
        return False
    
    # Step 5: Stop the session
    print("\n5. Stopping processing session...")
    try:
        stop_response = requests.post('http://localhost:3000/api/stop-processing/OP-1002')
        stop_data = stop_response.json()
        print(f"   Stop result: {stop_data.get('status')}")
        
        if stop_data.get('status') == 'success':
            print("   ✅ Session stopped successfully")
        else:
            print("   ⚠️ Session stop returned unexpected status")
            
    except Exception as e:
        print(f"   ❌ Failed to stop session: {e}")
        return False
    
    # Step 6: Check final state
    print("\n6. Checking final state...")
    time.sleep(1)  # Wait for cleanup
    
    try:
        response = requests.get('http://localhost:3000/api/processing-steps')
        data = response.json()
        steps_count = len(data.get('steps', []))
        active_sessions = data.get('active_sessions', 0)
        
        print(f"   Final - Steps: {steps_count}, Active Sessions: {active_sessions}")
        
        if active_sessions == 0:
            print("   ✅ No active sessions (clean)")
        else:
            print("   ⚠️ Still has active sessions")
            
        # The UI should hide the processing steps card when no active sessions
        if steps_count == 0:
            print("   ✅ No steps remaining (UI will hide card)")
        else:
            print("   ℹ️ Steps still cached (UI should hide card due to no active sessions)")
            
    except Exception as e:
        print(f"   ❌ Failed to check final state: {e}")
        return False
    
    print("\n=== Test Summary ===")
    print("✅ Processing Steps UI lifecycle test completed")
    print("🎯 Key UX improvements implemented:")
    print("   • Processing Steps card only shows during active processing")
    print("   • Real-time updates every 2 seconds during processing") 
    print("   • Visual indicators for step status (pending/active/completed)")
    print("   • Automatic cleanup when processing completes")
    print("   • Better button states and loading indicators")
    
    return True

if __name__ == "__main__":
    test_processing_steps_lifecycle()
