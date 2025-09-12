#!/usr/bin/env python3
"""
External Workflow Monitor
Continuously sends requests to the current_workflow_steps.json API endpoint
to demonstrate real-time workflow tracking capabilities
"""

import requests
import time
import json
from datetime import datetime
import sys


def monitor_workflow_api(base_url="http://localhost:8001", interval_seconds=3):
    """
    Continuously monitor the workflow API endpoints
    
    Args:
        base_url: Base URL of the claims orchestrator
        interval_seconds: Seconds between requests
    """
    
    print("🔄 Starting External Workflow Monitor")
    print(f"📡 Target API: {base_url}/workflow-steps")
    print(f"⏱️  Polling interval: {interval_seconds} seconds")
    print("🛑 Press Ctrl+C to stop\n")
    
    request_count = 0
    
    try:
        while True:
            request_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            try:
                # Request all workflows
                response = requests.get(f"{base_url}/workflow-steps", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    workflows = data.get("workflows", {})
                    
                    print(f"[{timestamp}] Request #{request_count:03d} - ✅ SUCCESS")
                    print(f"  📊 Found {len(workflows)} workflow sessions")
                    
                    if workflows:
                        for session_id, steps in workflows.items():
                            if steps:
                                claim_id = steps[0].get("claim_id", "Unknown")
                                step_count = len(steps)
                                latest_step = steps[-1]
                                status = latest_step.get("status", "unknown")
                                title = latest_step.get("title", "Unknown Step")
                                
                                print(f"    🏷️  Session: {session_id[:8]}...")
                                print(f"    📋 Claim: {claim_id}")
                                print(f"    📈 Steps: {step_count}")
                                print(f"    🎯 Latest: {title} ({status})")
                    else:
                        print("  📭 No workflow sessions found")
                        
                else:
                    print(f"[{timestamp}] Request #{request_count:03d} - ❌ HTTP {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                print(f"[{timestamp}] Request #{request_count:03d} - 🔌 CONNECTION ERROR")
                print("  💡 Is the Claims Orchestrator running on port 8001?")
                
            except requests.exceptions.Timeout:
                print(f"[{timestamp}] Request #{request_count:03d} - ⏰ TIMEOUT")
                
            except Exception as e:
                print(f"[{timestamp}] Request #{request_count:03d} - ❌ ERROR: {str(e)}")
            
            print()  # Empty line for readability
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Monitoring stopped after {request_count} requests")
        print("👋 Goodbye!")


def test_specific_session(session_id, base_url="http://localhost:8001"):
    """Test a specific session ID"""
    try:
        response = requests.get(f"{base_url}/workflow-steps/{session_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            steps = data.get("steps", [])
            print(f"✅ Session {session_id}: {len(steps)} steps")
            for step in steps:
                print(f"  - {step.get('title', 'Unknown')} ({step.get('status', 'unknown')})")
        else:
            print(f"❌ Session {session_id}: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test" and len(sys.argv) > 2:
            session_id = sys.argv[2]
            test_specific_session(session_id)
        elif command == "fast":
            monitor_workflow_api(interval_seconds=1)
        elif command == "slow":
            monitor_workflow_api(interval_seconds=10)
        else:
            print("Usage:")
            print("  python workflow_monitor.py          # Normal monitoring (3s intervals)")
            print("  python workflow_monitor.py fast     # Fast monitoring (1s intervals)")
            print("  python workflow_monitor.py slow     # Slow monitoring (10s intervals)")
            print("  python workflow_monitor.py test <session_id>  # Test specific session")
    else:
        monitor_workflow_api()
