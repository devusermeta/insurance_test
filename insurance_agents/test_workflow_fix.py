"""
Quick Test for Workflow Logger Fixes
"""

import requests
import json
import time

def test_orchestrator_workflow():
    """Test the orchestrator with a simple claim to verify workflow logging works"""
    
    print("🧪 Testing Orchestrator Workflow Logger")
    print("=" * 50)
    
    # A2A format payload for orchestrator (matching dashboard format)
    test_data = {
        "jsonrpc": "2.0",
        "method": "message/send", 
        "id": f"test-workflow-fix-{int(time.time())}",
        "params": {
            "message": {
                "messageId": f"msg-TEST-FIX-001-{int(time.time())}",
                "role": "user",
                "parts": [
                    {
                        "kind": "text",
                        "text": json.dumps({
                            "action": "process_claim",
                            "claim_id": "TEST-FIX-001",
                            "claim_data": {
                                "claim_id": "TEST-FIX-001",
                                "type": "test",
                                "amount": 100.0,
                                "description": "Test claim for workflow logger fixes",
                                "customer_id": "test123",
                                "policy_number": "POL_TEST_001",
                                "incident_date": "2024-01-15",
                                "location": "Test Environment",
                                "documents": ["test.pdf"],
                                "customer_statement": "Testing workflow logger fixes"
                            }
                        })
                    }
                ]
            }
        }
    }
    
    print("📝 Sending test claim to orchestrator...")
    
    try:
        response = requests.post(
            "http://localhost:8001",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Orchestrator processed the claim successfully")
            print(f"   Status: {result.get('status', 'unknown')}")
            if 'error' in result:
                print(f"   ⚠️ Error: {result['error']}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n⏱️ Waiting 3 seconds for workflow steps to be recorded...")
    time.sleep(3)
    
    # Check workflow steps via dashboard
    print("\n🔍 Checking workflow steps via dashboard...")
    try:
        steps_response = requests.get("http://localhost:3000/api/processing-steps")
        
        if steps_response.status_code == 200:
            steps_data = steps_response.json()
            all_steps = steps_data.get('steps', [])
            
            # Filter for our test claim
            test_steps = [s for s in all_steps if s.get('claim_id') == 'TEST-FIX-001']
            
            print(f"✅ Total steps: {len(all_steps)}, Test claim steps: {len(test_steps)}")
            
            if test_steps:
                print("\n📋 WORKFLOW STEPS FOR TEST CLAIM:")
                for i, step in enumerate(test_steps, 1):
                    print(f"   {i}. {step.get('step_type', 'unknown').replace('_', ' ').upper()}")
                    print(f"      📝 {step.get('description', 'No description')}")
                    print(f"      ⚡ Status: {step.get('status', 'unknown')}")
                    if step.get('agent_name'):
                        print(f"      🤖 Agent: {step.get('agent_name')}")
            else:
                print("⚠️ No workflow steps found for test claim")
        else:
            print(f"❌ Failed to get steps: {steps_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking steps: {e}")
    
    print("\n🎉 Test complete!")

if __name__ == "__main__":
    test_orchestrator_workflow()
