#!/usr/bin/env python3
"""
Quick test to debug the agent card endpoint issue
"""

import requests
import json

def test_endpoints():
    """Test various endpoints to see which ones work"""
    base_url = "http://localhost:8007"
    
    endpoints = [
        "/api/health",
        "/.well-known/agent.json",
        "/api/conversation/stats",
        "/api/voice/sessions"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"Testing {endpoint}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"  Response: {response.text[:200]}...")
            else:
                print(f"  Error: {response.text[:200]}...")
        except Exception as e:
            print(f"  Exception: {e}")
        print()

if __name__ == "__main__":
    test_endpoints()