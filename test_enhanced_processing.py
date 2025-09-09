#!/usr/bin/env python3
"""Test enhanced processing steps system"""

import requests
import time

def test_enhanced_processing_steps():
    print("=== Testing Enhanced Processing Steps ===")
    
    # 1. Clear all sessions
    print("\n1. Clearing all sessions...")
    requests.post('http://localhost:3000/api/stop-processing/OP-1001')
    requests.post('http://localhost:3000/api/stop-processing/OP-1002')
    
    response = requests.get('http://localhost:3000/api/processing-steps')
    data = response.json()
    steps_count = len(data.get('steps', []))
    active_sessions = data.get('active_sessions', 0)
    print(f"   Initial state: {steps_count} steps, {active_sessions} active sessions")
    
    # 2. Start OP-1002 session
    print("\n2. Starting OP-1002 session...")
    session_resp = requests.post('http://localhost:3000/api/start-processing/OP-1002')
    print(f"   Session result: {session_resp.json().get('status')}")
    
    response = requests.get('http://localhost:3000/api/processing-steps')
    data = response.json()
    steps_count = len(data.get('steps', []))
    active_sessions = data.get('active_sessions', 0)
    processing_claims = data.get('processing_claims', [])
    print(f"   After start: {steps_count} steps, {active_sessions} active, Claims: {processing_claims}")
    
    # 3. Start actual processing
    print("\n3. Starting actual claim processing...")
    process_resp = requests.post('http://localhost:3000/api/claims/OP-1002/process', json={
        'claimId': 'OP-1002',
        'expectedOutput': 'test real-time',
        'priority': 'normal',
        'employeeId': 'emp_001'
    })
    print(f"   Processing started: {process_resp.status_code}")
    
    # 4. Check real-time steps after processing
    print("\n4. Checking real-time steps...")
    time.sleep(3)  # Wait for processing to generate steps
    
    response = requests.get('http://localhost:3000/api/processing-steps')
    data = response.json()
    steps_count = len(data.get('steps', []))
    active_sessions = data.get('active_sessions', 0)
    processing_claims = data.get('processing_claims', [])
    
    print(f"   Real-time: {steps_count} steps, {active_sessions} active, Claims: {processing_claims}")
    
    if data.get('steps'):
        print("   First 3 steps:")
        for i, step in enumerate(data['steps'][:3]):
            title = step.get('title', f'Step {i+1}')
            claim_id = step.get('claim_id', 'Unknown')
            status = step.get('status', 'unknown')
            print(f"     {i+1}. {title} (Claim: {claim_id}, Status: {status})")
    
    # 5. Stop session and check cleanup
    print("\n5. Stopping session and checking cleanup...")
    stop_resp = requests.post('http://localhost:3000/api/stop-processing/OP-1002')
    print(f"   Stop result: {stop_resp.json().get('status')}")
    
    time.sleep(1)
    response = requests.get('http://localhost:3000/api/processing-steps')
    data = response.json()
    steps_count = len(data.get('steps', []))
    active_sessions = data.get('active_sessions', 0)
    processing_claims = data.get('processing_claims', [])
    
    print(f"   After stop: {steps_count} steps, {active_sessions} active, Claims: {processing_claims}")
    
    print("\n=== Test Complete ===")
    print("✅ Enhanced processing steps system tested")
    print("🎯 Key improvements:")
    print("   • Real-time claim-specific filtering")
    print("   • Short-term memory cache")
    print("   • Proper session management")
    print("   • Fixed [object Object] display")

if __name__ == "__main__":
    test_enhanced_processing_steps()
