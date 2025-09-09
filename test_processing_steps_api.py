#!/usr/bin/env python3
"""Test script to check if processing steps API is working"""

import requests
import json

def test_processing_steps():
    try:
        print("🧪 Testing Processing Steps API...")
        response = requests.get('http://localhost:3000/api/processing-steps')
        
        if response.status_code == 200:
            data = response.json()
            steps = data.get('steps', [])
            
            print(f"✅ API Response successful")
            print(f"📊 Total steps returned: {len(steps)}")
            print(f"🔄 Active sessions: {data.get('active_sessions', 0)}")
            
            if steps:
                print("\n📋 Workflow Steps:")
                for i, step in enumerate(steps[:10]):  # Show first 10 steps
                    title = step.get('title', 'No title')
                    claim_id = step.get('claim_id', 'Unknown')
                    status = step.get('status', 'unknown')
                    print(f"  {i+1:2d}. [{claim_id}] {title} ({status})")
                
                print(f"\n🎯 First step details:")
                first_step = steps[0]
                for key, value in first_step.items():
                    if key not in ['details']:  # Skip complex nested objects
                        print(f"     {key}: {value}")
            else:
                print("❌ No workflow steps returned")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Error testing API: {e}")

if __name__ == "__main__":
    test_processing_steps()
