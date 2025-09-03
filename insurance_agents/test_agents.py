"""
Test script for Claims Orchestrator Agent
Tests basic functionality and A2A communication
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_claims_orchestrator():
    """Test the Claims Orchestrator Agent"""
    
    print("🧪 Testing Claims Orchestrator Agent...")
    print("=" * 50)
    
    # Test data
    test_claim = {
        "claim_id": f"TEST_CLAIM_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "claim_type": "auto",
        "customer_id": "CUST_001",
        "description": "Vehicle damaged in parking lot collision. Front bumper and headlight need replacement.",
        "documents": ["photo_damage_1.jpg", "police_report.pdf"],
        "priority": "normal"
    }
    
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Check agent status
            print("📊 Test 1: Checking agent status...")
            async with session.get(f"{base_url}/api/status") as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"✅ Agent Status: {status['status']}")
                    print(f"   Agent: {status['agent']}")
                    print(f"   Port: {status['port']}")
                else:
                    print(f"❌ Status check failed: {response.status}")
                    return
            
            print()
            
            # Test 2: Process a test claim
            print("🏥 Test 2: Processing test claim...")
            print(f"   Claim ID: {test_claim['claim_id']}")
            print(f"   Type: {test_claim['claim_type']}")
            print(f"   Customer: {test_claim['customer_id']}")
            
            async with session.post(f"{base_url}/api/process_claim", json=test_claim) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Claim processing initiated successfully")
                    print(f"   Status: {result['status']}")
                    print(f"   Message: {result['message']}")
                    
                    # Print workflow details
                    workflow = result.get('workflow_status', {})
                    if workflow:
                        print(f"   Workflow Status: {workflow['status']}")
                        print(f"   Total Steps: {workflow.get('total_steps', 0)}")
                else:
                    print(f"❌ Claim processing failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return
            
            print()
            
            # Test 3: Check claim status
            print("📋 Test 3: Checking claim status...")
            await asyncio.sleep(1)  # Give time for processing
            
            async with session.get(f"{base_url}/api/claims/{test_claim['claim_id']}/status") as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"✅ Claim status retrieved")
                    print(f"   Claim ID: {status['claim_id']}")
                    print(f"   Status: {status['status']}")
                    print(f"   Last Updated: {status['last_updated']}")
                else:
                    print(f"❌ Status retrieval failed: {response.status}")
            
            print()
            
            # Test 4: Send A2A message
            print("📡 Test 4: Testing A2A communication...")
            test_message = {
                "type": "test_message",
                "source": "test_script",
                "message": "Hello from test script",
                "timestamp": datetime.now().isoformat()
            }
            
            async with session.post(f"{base_url}/api/message", json=test_message) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ A2A message sent successfully")
                    print(f"   Response: {result.get('message', 'No message')}")
                else:
                    print(f"❌ A2A message failed: {response.status}")
            
            print()
            print("🎉 All tests completed!")
            
        except aiohttp.ClientConnectorError:
            print("❌ Connection failed - Is the Claims Orchestrator running on port 8001?")
            print("   Start it with: python agents/claims_orchestrator/claims_orchestrator_agent.py")
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")

async def test_intake_clarifier():
    """Test the Intake Clarifier Agent"""
    
    print("\n🧪 Testing Intake Clarifier Agent...")
    print("=" * 50)
    
    base_url = "http://localhost:8002"
    
    # Test claim data for clarification
    test_claim_data = {
        "claim_id": f"CLARIFY_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "claim_type": "auto",
        "customer_id": "CUST_002", 
        "description": "Car accident",  # Intentionally brief to trigger clarification
        "documents": []
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Check agent status
            print("📊 Test 1: Checking Intake Clarifier status...")
            async with session.get(f"{base_url}/api/status") as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"✅ Agent Status: {status['status']}")
                    print(f"   Agent: {status['agent']}")
                else:
                    print(f"❌ Status check failed: {response.status}")
                    return
            
            print()
            
            # Test 2: Clarify claim
            print("📋 Test 2: Testing claim clarification...")
            async with session.post(f"{base_url}/api/clarify_claim", json=test_claim_data) as response:
                if response.status == 200:
                    result = await response.json()
                    clarification = result['clarification_result']
                    
                    print(f"✅ Claim clarification completed")
                    print(f"   Validation Status: {clarification['validation_status']}")
                    print(f"   Completeness Score: {clarification['completeness_score']}")
                    print(f"   Fraud Risk Score: {clarification['fraud_risk_score']}")
                    print(f"   Issues Found: {len(clarification['issues'])}")
                    print(f"   Questions Generated: {len(clarification['questions'])}")
                    
                    if clarification['questions']:
                        print("   Sample Questions:")
                        for q in clarification['questions'][:2]:
                            print(f"     - {q}")
                    
                else:
                    print(f"❌ Clarification failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
            
            print()
            print("🎉 Intake Clarifier tests completed!")
            
        except aiohttp.ClientConnectorError:
            print("❌ Connection failed - Is the Intake Clarifier running on port 8002?")
            print("   Start it with: python agents/intake_clarifier/intake_clarifier_agent.py")
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")

async def main():
    """Run all tests"""
    print("🚀 Starting Insurance Agents Test Suite")
    print("=" * 60)
    
    await test_claims_orchestrator()
    await test_intake_clarifier()
    
    print("\n" + "=" * 60)
    print("✅ Test suite completed!")
    print("\nTo start the agents:")
    print("  1. Claims Orchestrator: python agents/claims_orchestrator/claims_orchestrator_agent.py")
    print("  2. Intake Clarifier: python agents/intake_clarifier/intake_clarifier_agent.py")

if __name__ == "__main__":
    asyncio.run(main())
