"""
Quick JSON-RPC Test for A2A Multi-Agent System
Tests the agents using the JSON-RPC protocol they actually support
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_jsonrpc_communication():
    """Test agents using JSON-RPC format"""
    print("🔍 Testing JSON-RPC Communication with Agents")
    print("=" * 60)
    
    # Sample test claim
    test_claim = {
        "claim_id": f"TEST_CLAIM_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "customer_id": "CUST_001",
        "policy_number": "POL_12345",
        "incident_date": "2025-09-03",
        "claim_type": "automotive",
        "estimated_amount": 15000.00,
        "description": "Vehicle collision with significant front-end damage",
        "location": "Highway 101, San Francisco, CA",
        "status": "submitted",
        "priority": "normal"
    }
    
    print(f"📋 Test Claim: {test_claim['claim_id']}")
    print(f"💰 Amount: ${test_claim['estimated_amount']:,.0f}")
    
    # Test different JSON-RPC method names to find the correct one
    methods_to_try = [
        "execute",
        "task.execute", 
        "agent.execute",
        "process",
        "handle_request",
        "run_task"
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for method in methods_to_try:
            try:
                print(f"\n🔍 Trying method: {method}")
                
                payload = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": {
                        "task": "process_claim",
                        "parameters": {
                            "claim_data": test_claim
                        }
                    },
                    "id": 1
                }
                
                response = await client.post(
                    "http://localhost:8001/",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                result = response.json()
                
                if "error" not in result or result["error"]["code"] != -32601:
                    print(f"✅ Method {method} worked!")
                    print("Response:", json.dumps(result, indent=2))
                    return result
                else:
                    print(f"❌ Method {method} not found")
                    
            except Exception as e:
                print(f"❌ Error with method {method}: {str(e)}")
    
    print("\n🔍 Let's try to see what the agent server documentation says...")
    
    # Try to get server info
    try:
        info_payload = {
            "jsonrpc": "2.0", 
            "method": "server.info",
            "params": {},
            "id": 2
        }
        
        response = await client.post(
            "http://localhost:8001/",
            json=info_payload,
            headers={"Content-Type": "application/json"}
        )
        
        result = response.json()
        print("Server Info Response:", json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"❌ Could not get server info: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_jsonrpc_communication())
