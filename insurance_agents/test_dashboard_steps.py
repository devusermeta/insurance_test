"""
Test Dashboard Processing Steps
"""

import requests
import time

def test_dashboard_processing_steps():
    print("🧪 Testing Dashboard Processing Steps")
    print("=" * 50)
    
    print("📝 Step 1: Check if workflow logger has any existing steps...")
    try:
        # Try to connect to dashboard first
        response = requests.get("http://localhost:3000/api/processing-steps", timeout=5)
        if response.status_code == 200:
            data = response.json()
            steps = data.get('steps', [])
            print(f"✅ Dashboard connected - {len(steps)} existing steps found")
            
            if steps:
                print("📋 Recent processing steps:")
                for i, step in enumerate(steps[-3:], 1):  # Show last 3 steps
                    print(f"   {i}. {step.get('step_type', 'unknown')}: {step.get('description', 'No desc')}")
                    print(f"      🏷️ Claim: {step.get('claim_id', 'Unknown')}")
            else:
                print("⚠️ No processing steps found in dashboard")
        else:
            print(f"❌ Dashboard not responding: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Dashboard connection failed: {e}")
        return
    
    print("\n📝 Step 2: Submit a test claim via dashboard...")
    try:
        # Submit claim via dashboard
        submit_response = requests.post(
            "http://localhost:3000/api/claims/TEST-DASHBOARD-001/process",
            json={"action": "process_claim"},
            timeout=30
        )
        
        print(f"📊 Claim submission response: {submit_response.status_code}")
        if submit_response.status_code == 200:
            print("✅ Claim submitted successfully")
        else:
            print(f"⚠️ Claim submission returned: {submit_response.status_code}")
            print(f"Response: {submit_response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error submitting claim: {e}")
    
    print("\n⏱️ Waiting 5 seconds for processing...")
    time.sleep(5)
    
    print("\n📝 Step 3: Check for new processing steps...")
    try:
        response = requests.get("http://localhost:3000/api/processing-steps", timeout=5)
        if response.status_code == 200:
            data = response.json()
            new_steps = data.get('steps', [])
            
            print(f"📊 Total steps after processing: {len(new_steps)}")
            
            # Look for our test claim specifically
            test_steps = [s for s in new_steps if 'TEST-DASHBOARD-001' in s.get('claim_id', '')]
            if test_steps:
                print(f"✅ Found {len(test_steps)} steps for our test claim!")
                for i, step in enumerate(test_steps, 1):
                    print(f"   {i}. {step.get('step_type', 'unknown')}: {step.get('description', 'No desc')}")
            else:
                print("⚠️ No steps found for our test claim")
                print("📋 Most recent steps:")
                for step in new_steps[-5:]:  # Show last 5 steps
                    print(f"   - {step.get('step_type', 'unknown')} for {step.get('claim_id', 'unknown')}")
        else:
            print(f"❌ Failed to get updated steps: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking updated steps: {e}")
    
    print("\n🎉 Test complete!")

if __name__ == "__main__":
    test_dashboard_processing_steps()
