#!/usr/bin/env python3
"""
Test Dashboard API Response
Check what the dashboard is actually returning vs real workflow data
"""

import requests
import json
import sys
import os
from pathlib import Path

# Add the insurance_agents directory to path for imports
sys.path.append(str(Path(__file__).parent / "insurance_agents"))

try:
    from shared.workflow_logger import workflow_logger
    print("✅ Successfully imported workflow_logger")
except ImportError as e:
    print(f"❌ Failed to import workflow_logger: {e}")
    exit(1)

def test_dashboard_api():
    """Test what the dashboard API is returning"""
    
    print("\n🧪 Testing Dashboard API on Port 3000...")
    
    try:
        # Test the processing steps API
        response = requests.get('http://localhost:3000/api/processing-steps', timeout=5)
        print(f"📊 API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            steps = data.get('steps', [])
            print(f"📊 Steps returned by API: {len(steps)}")
            
            if steps:
                print("\n📋 Steps from Dashboard API:")
                for i, step in enumerate(steps[:5]):  # Show first 5 steps
                    print(f"   {i+1}. {step.get('title', 'No title')}")
                    print(f"      Description: {step.get('description', 'No description')}")
                    print(f"      Claim ID: {step.get('claim_id', 'No claim ID')}")
                    print(f"      Time: {step.get('timestamp', 'No timestamp')}")
                    print()
                    
                return True, steps
            else:
                print("⚠️  API returned empty steps array")
                return False, []
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False, []
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to dashboard on localhost:3000")
        print("   Is the dashboard running? Start it with: python app.py")
        return False, []
    except Exception as e:
        print(f"❌ Error testing dashboard API: {e}")
        return False, []

def test_real_workflow_data():
    """Test what the real workflow logger has"""
    
    print("\n🧪 Testing Real Workflow Logger Data...")
    
    try:
        # Get real workflow steps
        real_steps = workflow_logger.get_all_recent_steps(10)
        print(f"📊 Real workflow steps available: {len(real_steps)}")
        
        if real_steps:
            print("\n📋 Real Workflow Steps:")
            for i, step in enumerate(real_steps[:5]):  # Show first 5 steps
                print(f"   {i+1}. {step.get('title', 'No title')}")
                print(f"      Description: {step.get('description', 'No description')}")
                print(f"      Claim ID: {step.get('claim_id', 'No claim ID')}")
                print(f"      Time: {step.get('timestamp', 'No timestamp')}")
                print()
                
            return True, real_steps
        else:
            print("⚠️  No real workflow steps available")
            return False, []
            
    except Exception as e:
        print(f"❌ Error getting real workflow data: {e}")
        return False, []

def compare_data(api_steps, real_steps):
    """Compare dashboard API data vs real workflow data"""
    
    print("\n🔍 Comparing Dashboard API vs Real Workflow Data...")
    
    if not api_steps and not real_steps:
        print("❌ Both API and real workflow data are empty")
        return
    
    if not api_steps:
        print("❌ Dashboard API has no steps, but real workflow has data!")
        print("   This means the API is not returning real workflow steps")
        return
    
    if not real_steps:
        print("⚠️  Dashboard API has steps, but no real workflow data found")
        print("   This means the API is returning hardcoded/cached data")
        return
    
    # Check if any API steps match real steps
    api_claim_ids = set(step.get('claim_id') for step in api_steps if step.get('claim_id'))
    real_claim_ids = set(step.get('claim_id') for step in real_steps if step.get('claim_id'))
    
    print(f"📊 API Claim IDs: {list(api_claim_ids)}")
    print(f"📊 Real Claim IDs: {list(real_claim_ids)}")
    
    matching_claims = api_claim_ids & real_claim_ids
    
    if matching_claims:
        print(f"✅ Found {len(matching_claims)} matching claim IDs!")
        print(f"   Matching claims: {list(matching_claims)}")
        print("   Dashboard API is returning real workflow data")
    else:
        print("❌ No matching claim IDs found!")
        print("   Dashboard API is NOT returning real workflow data")
        print("   The API is still serving hardcoded/cached steps")

def main():
    """Run the comparison test"""
    
    print("🧪 DASHBOARD API vs REAL WORKFLOW DATA COMPARISON")
    print("=" * 60)
    
    # Test 1: Dashboard API
    api_success, api_steps = test_dashboard_api()
    
    # Test 2: Real workflow data
    real_success, real_steps = test_real_workflow_data()
    
    # Test 3: Compare the data
    if api_success or real_success:
        compare_data(api_steps, real_steps)
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 DIAGNOSIS")
    print("=" * 60)
    
    if api_success and real_success:
        # Check if they match
        api_claim_ids = set(step.get('claim_id') for step in api_steps if step.get('claim_id'))
        real_claim_ids = set(step.get('claim_id') for step in real_steps if step.get('claim_id'))
        
        if api_claim_ids & real_claim_ids:
            print("🎉 WORKING: Dashboard API is returning real workflow data!")
        else:
            print("❌ ISSUE: Dashboard API is not returning real workflow data")
            print("🔧 SOLUTION: Dashboard API needs to be fixed to use real workflow_logger")
    elif not api_success and real_success:
        print("❌ ISSUE: Dashboard is not running, but workflow logger has data")
        print("🔧 SOLUTION: Start the dashboard and check API integration")
    elif api_success and not real_success:
        print("❌ ISSUE: Dashboard API works but no real workflow data exists")  
        print("🔧 SOLUTION: Process more claims to generate real workflow data")
    else:
        print("❌ ISSUE: Both dashboard API and workflow logger have problems")
        print("🔧 SOLUTION: Check both dashboard and orchestrator integration")

if __name__ == "__main__":
    main()
