#!/usr/bin/env python3
"""Debug processing steps data structure"""

import requests
import json

def debug_processing_steps():
    response = requests.get('http://localhost:3000/api/processing-steps')
    data = response.json()
    
    print("=== Current API Response ===")
    print(f"Steps count: {len(data.get('steps', []))}")
    print(f"Active sessions: {data.get('active_sessions', 0)}")
    print(f"Session details: {data.get('session_details', {})}")
    
    steps = data.get('steps', [])
    if steps:
        print("\n=== First Step Analysis ===")
        first_step = steps[0]
        print(f"Claim ID in step: {first_step.get('claim_id')}")
        print(f"Step data keys: {list(first_step.keys())}")
        print(f"Step details type: {type(first_step.get('details'))}")
        print(f"Step details value: {first_step.get('details')}")
        print(f"Step title: {first_step.get('title')}")
        print(f"Step timestamp: {first_step.get('timestamp')}")
        
        print("\n=== All Step Claim IDs ===")
        for i, step in enumerate(steps[:5]):
            print(f"Step {i+1}: {step.get('claim_id')} - {step.get('title')}")

if __name__ == "__main__":
    debug_processing_steps()
