#!/usr/bin/env python3
"""Test script to verify recent workflow steps functionality"""

import requests
import json

def test_recent_workflow_steps():
    try:
        print("🧪 Testing Recent Workflow Steps API...")
        response = requests.get('http://localhost:3000/api/recent-workflow-steps')
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ API Response successful")
            print(f"📊 Total steps returned: {data.get('total_steps', 0)}")
            print(f"🔄 Claims count: {data.get('claims_count', 0)}")
            print(f"📋 Status: {data.get('status', 'unknown')}")
            
            steps = data.get('steps', [])
            if steps:
                print(f"\n📋 Recent Workflow Steps:")
                for i, step in enumerate(steps[:5]):  # Show first 5 steps
                    title = step.get('title', 'No title')
                    claim_id = step.get('claim_id', 'Unknown')
                    timestamp = step.get('timestamp', 'No timestamp')
                    print(f"  {i+1:2d}. [{claim_id}] {title}")
                    print(f"      Time: {timestamp}")
                
                print(f"\n🎯 This data should appear in the 'Recent Workflow Steps' component on the dashboard")
            else:
                print("❌ No recent workflow steps returned")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Error testing API: {e}")

def check_dashboard_page():
    try:
        print("\n🌐 Testing Dashboard Page Load...")
        response = requests.get('http://localhost:3000/')
        
        if response.status_code == 200:
            content = response.text
            
            # Check if our component is in the HTML
            if 'Recent Workflow Steps' in content:
                print("✅ 'Recent Workflow Steps' text found in HTML")
            else:
                print("❌ 'Recent Workflow Steps' text NOT found in HTML")
                
            if 'recent-steps-list' in content:
                print("✅ 'recent-steps-list' ID found in HTML")
            else:
                print("❌ 'recent-steps-list' ID NOT found in HTML")
                
            if 'loadRecentSteps' in content:
                print("✅ 'loadRecentSteps' function found in HTML")
            else:
                print("❌ 'loadRecentSteps' function NOT found in HTML")
                
        else:
            print(f"❌ Dashboard Error: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Error checking dashboard: {e}")

if __name__ == "__main__":
    test_recent_workflow_steps()
    check_dashboard_page()
