"""
Test Workflow Steps Integration
Tests the complete workflow from orchestrator through dashboard processing steps visualization
"""

import asyncio
import requests
import json
from datetime import datetime

async def test_complete_workflow():
    """Test the complete workflow with processing steps tracking"""
    
    print("🧪 Testing Complete Workflow with Processing Steps")
    print("=" * 60)
    
    # Test data for claim processing
    test_claim = {
        "claim_id": "WF-TEST-001",
        "type": "auto",
        "amount": 2500.0,
        "description": "Auto insurance claim for workflow testing",
        "customer_id": "test123",
        "policy_number": "POL_WF_TEST_001",
        "incident_date": "2024-01-20",
        "location": "Workflow Test Processing",
        "documents": ["test_claim_form.pdf", "test_photos.pdf"],
        "customer_statement": "Testing complete workflow with processing steps visualization"
    }
    
    # Step 1: Submit claim to orchestrator
    print("\n📝 STEP 1: Submitting claim to orchestrator...")
    try:
        orchestrator_url = "http://localhost:8001"
        response = requests.post(
            f"{orchestrator_url}/",
            json={
                "action": "process_claim",
                "claim_id": test_claim["claim_id"],
                "claim_data": test_claim
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Claim submitted successfully to orchestrator")
            orchestrator_result = response.json()
            print(f"   📊 Status: {orchestrator_result.get('status', 'unknown')}")
        else:
            print(f"❌ Orchestrator request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error submitting to orchestrator: {e}")
        return
    
    # Step 2: Wait a moment for processing
    print("\n⏱️ STEP 2: Waiting for processing to complete...")
    await asyncio.sleep(3)
    
    # Step 3: Check processing steps via dashboard API
    print("\n🔍 STEP 3: Checking processing steps via dashboard API...")
    try:
        dashboard_url = "http://localhost:5000"
        
        # Check all processing steps
        steps_response = requests.get(f"{dashboard_url}/api/processing-steps")
        if steps_response.status_code == 200:
            steps_data = steps_response.json()
            all_steps = steps_data.get('steps', [])
            print(f"✅ Retrieved {len(all_steps)} total processing steps")
            
            # Filter steps for our test claim
            test_claim_steps = [step for step in all_steps if step.get('claim_id') == test_claim["claim_id"]]
            print(f"   🎯 Found {len(test_claim_steps)} steps for claim {test_claim['claim_id']}")
            
            if test_claim_steps:
                print("\n📋 PROCESSING STEPS FOR TEST CLAIM:")
                for i, step in enumerate(test_claim_steps, 1):
                    print(f"   {i}. {step.get('step_type', 'unknown').replace('_', ' ').upper()}")
                    print(f"      📝 Description: {step.get('description', 'No description')}")
                    print(f"      🤖 Agent: {step.get('agent_name', 'N/A')}")
                    print(f"      ⚡ Status: {step.get('status', 'unknown')}")
                    print(f"      🕒 Time: {step.get('timestamp', 'No timestamp')}")
                    if step.get('details'):
                        print(f"      📖 Details: {step.get('details')}")
                    print()
            else:
                print("⚠️ No processing steps found for test claim")
                
        else:
            print(f"❌ Failed to get processing steps: {steps_response.status_code}")
            print(f"   Response: {steps_response.text}")
            
    except Exception as e:
        print(f"❌ Error checking processing steps: {e}")
    
    # Step 4: Check specific claim steps
    print("\n🔍 STEP 4: Checking claim-specific processing steps...")
    try:
        claim_steps_response = requests.get(f"{dashboard_url}/api/processing-steps/{test_claim['claim_id']}")
        if claim_steps_response.status_code == 200:
            claim_steps_data = claim_steps_response.json()
            claim_steps = claim_steps_data.get('steps', [])
            print(f"✅ Retrieved {len(claim_steps)} steps for specific claim")
            
            if claim_steps:
                print("\n🎯 CLAIM-SPECIFIC PROCESSING STEPS:")
                for i, step in enumerate(claim_steps, 1):
                    print(f"   {i}. [{step.get('status', '?').upper()}] {step.get('step_type', 'unknown').replace('_', ' ').title()}")
                    print(f"      {step.get('description', 'No description')}")
                    if step.get('agent_name'):
                        print(f"      👤 Agent: {step.get('agent_name')}")
                    if step.get('details'):
                        print(f"      ℹ️  Details: {step.get('details')}")
                    print()
        else:
            print(f"❌ Failed to get claim-specific steps: {claim_steps_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking claim-specific steps: {e}")
    
    # Step 5: Test dashboard claims API
    print("\n🔍 STEP 5: Checking claims in dashboard...")
    try:
        claims_response = requests.get(f"{dashboard_url}/api/claims")
        if claims_response.status_code == 200:
            claims_data = claims_response.json()
            claims = claims_data.get('claims', [])
            print(f"✅ Retrieved {len(claims)} total claims from dashboard")
            
            # Look for our test claim
            test_claim_found = any(claim.get('claim_id') == test_claim['claim_id'] for claim in claims)
            if test_claim_found:
                print(f"✅ Test claim {test_claim['claim_id']} found in dashboard")
            else:
                print(f"⚠️ Test claim {test_claim['claim_id']} not found in dashboard")
                
        else:
            print(f"❌ Failed to get claims: {claims_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking claims: {e}")
    
    print("\n🎉 WORKFLOW TEST COMPLETE!")
    print("=" * 60)
    print("\n💡 Next Steps:")
    print("   • Check the dashboard at http://localhost:5000")
    print("   • Look at the 'Processing Steps' section")
    print("   • Process more claims to see real-time workflow visualization")
    print("   • Each orchestrator action should now be visible as processing steps")

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
