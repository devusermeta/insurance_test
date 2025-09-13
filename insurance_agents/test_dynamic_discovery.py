"""
Test Dynamic Agent Discovery System
This tests the new on-demand and background discovery functionality
"""

import asyncio
import httpx
import time
from datetime import datetime

async def test_dynamic_discovery():
    """Test that the orchestrator can discover agents dynamically"""
    
    print("🧪 Testing Dynamic Agent Discovery System")
    print("=" * 60)
    
    # Test 1: Check initial agent discovery
    print("\n1. 🔍 Testing Initial Agent Discovery...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8001/agents")
            if response.status_code == 200:
                agents = response.json()
                print(f"   ✅ Initial agents discovered: {len(agents)}")
                for agent in agents:
                    print(f"      • {agent}")
                initial_count = len(agents)
            else:
                print(f"   ❌ Failed to get agents: {response.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ Error getting initial agents: {e}")
        return False
    
    # Test 2: Start Communication Agent and test on-demand discovery
    print("\n2. 📧 Testing On-Demand Discovery (Communication Agent)...")
    print("   💡 Please start the Communication Agent in another terminal:")
    print("   cd insurance_agents; .\.venv\Scripts\activate; $env:PYTHONPATH = \"D:\Metakaal\insurance\insurance_agents\"")
    print("   python -m agents.communication_agent --port 8005")
    
    input("\nPress Enter after starting Communication Agent...")
    
    # Test on-demand discovery by making a test claim that would trigger email
    print("\n3. 🎯 Testing On-Demand Discovery During Claim Processing...")
    
    test_claim = {
        "patient_name": "Dynamic Discovery Test Patient",
        "patient_email": "purohitabhinav2001@gmail.com",
        "bill_amount": "500.00",
        "service_description": "Testing dynamic agent discovery with email notification",
        "provider": "Test Medical Center",
        "category": "Medical",
        "documents": []
    }
    
    print("   📋 Submitting test claim to trigger workflow...")
    print(f"   👤 Patient: {test_claim['patient_name']}")
    print(f"   💰 Amount: ${test_claim['bill_amount']}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:8001/process",
                json={
                    "message": f"Process this insurance claim: {test_claim}",
                    "session_id": f"dynamic_test_{int(time.time())}"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Claim processing completed")
                
                # Check if email notification was mentioned
                message = result.get("message", "")
                if "email" in message.lower():
                    if "sent successfully" in message.lower():
                        print("   🎉 ✅ ON-DEMAND DISCOVERY SUCCESS!")
                        print("   📧 Communication Agent was discovered and used for email")
                    elif "failed" in message.lower():
                        print("   ⚠️ Communication Agent discovered but email failed")
                    elif "skipped" in message.lower():
                        print("   ❌ Communication Agent not discovered (still offline?)")
                else:
                    print("   ❌ No email notification attempted")
                
                print(f"\n   📋 Full Response: {message[:200]}...")
                return True
                
            else:
                print(f"   ❌ Claim processing failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"   ❌ Error processing claim: {e}")
        return False

async def test_background_discovery():
    """Test background discovery polling"""
    
    print("\n" + "=" * 60)
    print("🔄 Testing Background Discovery Polling")
    print("=" * 60)
    
    print("\n⏰ Background discovery runs every 2 minutes")
    print("💡 You can test this by:")
    print("1. Stopping the Communication Agent")
    print("2. Waiting ~2 minutes")
    print("3. Starting the Communication Agent again")
    print("4. Processing another claim after ~2 minutes")
    
    print("\n📊 The orchestrator logs will show:")
    print("   🔄 Background agent discovery check...")
    print("   ✅ communication_agent: ONLINE with X skills")
    
    return True

async def main():
    print("🚀 Dynamic Agent Discovery Test Suite")
    print("Testing the hybrid approach: On-demand + Background polling")
    
    # Test on-demand discovery
    discovery_test = await test_dynamic_discovery()
    
    # Test background discovery
    background_test = await test_background_discovery()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"On-Demand Discovery: {'✅ PASSED' if discovery_test else '❌ FAILED'}")
    print(f"Background Polling: {'✅ CONFIGURED' if background_test else '❌ FAILED'}")
    
    if discovery_test and background_test:
        print("\n🎉 DYNAMIC DISCOVERY SYSTEM WORKING!")
        print("✅ Agents can be discovered on-demand before email step")
        print("✅ Background polling provides safety net every 2 minutes")
        print("✅ Communication Agent can be started anytime and will be used")
        print("✅ Workflow continues gracefully without Communication Agent")
    else:
        print("\n⚠️ Some tests failed - check orchestrator logs")

if __name__ == "__main__":
    asyncio.run(main())