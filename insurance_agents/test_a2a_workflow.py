"""
Test Script for A2A Claims Processing Workflow
Tests the complete multi-agent system with MCP integration
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_complete_workflow():
    """
    Test the complete claims processing workflow using A2A communication
    """
    print("🚀 Starting A2A Claims Processing Workflow Test")
    print("=" * 60)
    
    # Test claim data
    test_claim = {
        "claim_id": f"TEST_CLAIM_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "type": "automotive",
        "amount": 15000,
        "description": "Vehicle collision damage on Highway 101",
        "customer_id": "CUST_12345",
        "policy_number": "POL_AUTO_789",
        "date": datetime.now().isoformat(),
        "documents": [
            {"type": "photo", "name": "damage_front.jpg"},
            {"type": "police_report", "name": "accident_report.pdf"},
            {"type": "estimate", "name": "repair_estimate.pdf"}
        ]
    }
    
    print(f"📋 Test Claim: {test_claim['claim_id']}")
    print(f"💰 Amount: ${test_claim['amount']:,}")
    print(f"🚗 Type: {test_claim['type']}")
    print(f"📄 Documents: {len(test_claim['documents'])} files")
    print()
    
    # Send claim to Claims Orchestrator using A2A protocol
    try:
        print("📤 Sending claim to Claims Orchestrator...")
        
        # Import and use A2A client
        from shared.a2a_client import A2AClient
        a2a_client = A2AClient("test_client")
        
        # Send A2A request
        result = await a2a_client.send_request(
            "claims_orchestrator",
            "process_claim",
            {"claim_data": test_claim}
        )
        
        if "error" not in result:
            print("✅ Claims Orchestrator Response:")
            print(json.dumps(result, indent=2))
            
            # Check the processing status
            status = result.get('status', 'unknown')
            if status == 'completed':
                decision = result.get('final_decision', {})
                print(f"\n🎯 Final Decision: {decision.get('decision', 'unknown')}")
                print(f"📊 Confidence: {decision.get('confidence', 0)*100:.1f}%")
                print(f"💭 Reason: {decision.get('reason', 'N/A')}")
            elif status == 'failed':
                print(f"\n❌ Processing Failed: {result.get('error', 'Unknown error')}")
            else:
                print(f"\n⏳ Status: {status}")
        else:
            print(f"❌ A2A Request failed: {result.get('error')}")
            
        # Clean up A2A client
        await a2a_client.client.aclose()
            
    except Exception as e:
        print(f"❌ Error testing workflow: {str(e)}")

async def test_individual_agents():
    """
    Test individual agent responses
    """
    print("\n🔧 Testing Individual Agent Communications")
    print("=" * 60)
    
    agents = [
        {"name": "Claims Orchestrator", "port": 8001},
        {"name": "Intake Clarifier", "port": 8002},
        {"name": "Document Intelligence", "port": 8003},
        {"name": "Coverage Rules Engine", "port": 8004}
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for agent in agents:
            try:
                print(f"🤖 Testing {agent['name']} (Port {agent['port']})...")
                
                # Test agent status
                response = await client.get(f"http://localhost:{agent['port']}/.well-known/agent.json")
                
                if response.status_code == 200:
                    agent_info = response.json()
                    print(f"   ✅ {agent['name']}: Online")
                    print(f"   📝 Description: {agent_info.get('description', 'N/A')}")
                else:
                    print(f"   ❌ {agent['name']}: Offline (HTTP {response.status_code})")
                    
            except Exception as e:
                print(f"   ❌ {agent['name']}: Error - {str(e)}")
    
    print()

async def test_mcp_connection():
    """
    Test MCP server connection
    """
    print("🔌 Testing MCP Cosmos Server Connection")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test MCP server with proper headers
            headers = {
                "Accept": "text/event-stream",
                "Content-Type": "application/json"
            }
            response = await client.get("http://localhost:8080/mcp", headers=headers)
            
            if response.status_code in [200, 400]:  # 400 is expected for GET without proper MCP protocol
                print("✅ MCP Cosmos Server: Online")
                
                # Test a simple MCP tool
                mcp_request = {
                    "method": "tools/call",
                    "params": {
                        "name": "list_collections",
                        "arguments": {}
                    }
                }
                
                response = await client.post(
                    "http://localhost:8080/mcp",
                    json=mcp_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ MCP Tool Execution: Success")
                    print(f"📦 Collections Response: {result}")
                else:
                    print(f"❌ MCP Tool Execution Failed: {response.status_code}")
                    print(f"Response: {response.text}")
            else:
                print(f"❌ MCP Cosmos Server: Offline (HTTP {response.status_code})")
                
    except Exception as e:
        print(f"❌ MCP Connection Error: {str(e)}")
    
    print()

async def main():
    """
    Main test function
    """
    print("🧪 A2A Multi-Agent System Testing Suite")
    print("🕒 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    print()
    
    # Test 1: Individual agent status
    await test_individual_agents()
    
    # Test 2: MCP connection
    await test_mcp_connection()
    
    # Test 3: Complete workflow
    await test_complete_workflow()
    
    print("\n🏁 Testing Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
