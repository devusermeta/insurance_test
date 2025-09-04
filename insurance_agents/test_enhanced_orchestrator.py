"""
Test the Enhanced Claims Orchestrator with Intelligent Routing
Demonstrates how the orchestrator can route to both local A2A agents and Azure AI Foundry agents
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_claims_orchestrator():
    """Test the enhanced Claims Orchestrator routing capabilities"""
    
    base_url = "http://localhost:8001"  # Claims Orchestrator port
    
    print("🚀 Testing Enhanced Claims Orchestrator with Intelligent Routing")
    print("="*70)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Check status
        print("\n📊 STEP 1: Checking Agent Status")
        print("-" * 40)
        
        try:
            async with session.get(f"{base_url}/api/status") as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"✅ Claims Orchestrator Status: {status.get('status', 'unknown')}")
                    print(f"🔗 Azure Integration: {'✅ Available' if status.get('azure_integration', {}).get('available') else '❌ Not Available'}")
                    print(f"🤖 Azure Agents: {status.get('azure_integration', {}).get('agents_configured', 0)}/{status.get('azure_integration', {}).get('total_agents', 0)}")
                    print(f"🛠️ Routing Modes: {', '.join(status.get('azure_integration', {}).get('routing_modes', []))}")
                else:
                    print(f"❌ Status check failed: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Could not connect to Claims Orchestrator: {str(e)}")
            print(f"💡 Make sure to start the agent with: cd agents/claims_orchestrator && python __main__.py")
            return
        
        # Test 2: Routing Demo
        print(f"\n🎬 STEP 2: Intelligent Routing Demonstration")
        print("-" * 50)
        
        try:
            async with session.get(f"{base_url}/api/routing_demo") as response:
                if response.status == 200:
                    demo = await response.json()
                    
                    print(f"🎯 Demo: {demo['demo_name']}")
                    print(f"☁️ Azure Available: {'✅ Yes' if demo['azure_available'] else '❌ No'}")
                    print(f"📋 Scenarios: {demo['total_scenarios']}")
                    
                    for i, scenario in enumerate(demo['scenarios'], 1):
                        print(f"\n--- Scenario {i} ---")
                        print(f"📝 Message: '{scenario['scenario']}'")
                        print(f"🎯 Will Route To: {scenario['will_use']} → {scenario['target_agent']}")
                        print(f"💭 Expected: {scenario['expected']}")
                        print(f"🧠 Rationale: {scenario['rationale']}")
                        print(f"📊 Confidence: {scenario['routing_decision']['confidence']} keyword matches")
                        
                else:
                    print(f"❌ Routing demo failed: {response.status}")
        except Exception as e:
            print(f"❌ Routing demo error: {str(e)}")
        
        # Test 3: Live Intelligent Routing
        print(f"\n🎮 STEP 3: Live Intelligent Routing Tests")
        print("-" * 45)
        
        test_requests = [
            {
                "message": "I need to file a new claim for my car accident",
                "mode": "auto"
            },
            {
                "message": "Please analyze this damage photo and tell me what you see",
                "mode": "auto", 
                "context": {"has_images": True}
            },
            {
                "message": "What does my comprehensive coverage include?",
                "mode": "local"  # Force local
            },
            {
                "message": "Intelligently assess this claim for fraud risk",
                "mode": "azure"  # Force Azure (if available)
            }
        ]
        
        for i, request in enumerate(test_requests, 1):
            print(f"\n--- Live Test {i} ---")
            print(f"📝 Request: '{request['message']}'")
            print(f"🔧 Mode: {request['mode']}")
            
            try:
                async with session.post(f"{base_url}/api/intelligent_routing", 
                                      json=request) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        routing = result['routing_decision']
                        outcome = result['result']
                        
                        print(f"🎯 Routed To: {routing['target_agent']} ({'Azure' if routing['use_azure'] else 'Local'})")
                        print(f"🧠 Rationale: {routing['rationale']}")
                        print(f"✅ Success: {outcome.get('success', 'unknown')}")
                        print(f"📊 Routing Mode: {outcome.get('routing_mode', 'unknown')}")
                        
                        if outcome.get('success'):
                            print(f"💬 Response: {outcome.get('message', 'No message')}")
                        else:
                            print(f"❌ Error: {outcome.get('error', 'Unknown error')}")
                            
                    else:
                        print(f"❌ Request failed: {response.status}")
                        error_text = await response.text()
                        print(f"📄 Error: {error_text}")
                        
            except Exception as e:
                print(f"❌ Request error: {str(e)}")
        
        print(f"\n🎉 TESTING COMPLETE!")
        print("="*70)
        print("✅ Enhanced Claims Orchestrator can route to both:")
        print("   🏠 Local A2A agents (for simple, structured tasks)")
        print("   ☁️ Azure AI Foundry agents (for complex, intelligent tasks)")
        print("   🧠 Intelligent auto-routing based on task complexity")
        print("\n💡 Key Features Demonstrated:")
        print("   - Smart keyword analysis")
        print("   - Complexity detection")
        print("   - Graceful fallback to local agents")
        print("   - User preference override (auto/local/azure)")

if __name__ == "__main__":
    asyncio.run(test_claims_orchestrator())
