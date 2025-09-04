"""
A2A Protocol Test using Agent Skills
Tests the A2A agents using their declared skills from agent.json
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_a2a_skills():
    """Test agents using their declared skills"""
    print("🎯 Testing A2A Skills-Based Communication")
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
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # From agent.json, the skills are:
        # - claims_orchestration
        # - workflow_management
        
        skills_to_try = [
            "claims_orchestration",
            "workflow_management",
            "skills/claims_orchestration",
            "skills/workflow_management"
        ]
        
        for skill in skills_to_try:
            try:
                print(f"\n🔍 Trying skill: {skill}")
                
                payload = {
                    "jsonrpc": "2.0",
                    "method": skill,
                    "params": {
                        "claim_data": test_claim,
                        "action": "process_claim"
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
                    print(f"✅ Skill {skill} worked!")
                    print("Response:", json.dumps(result, indent=2))
                    return result
                else:
                    print(f"❌ Skill {skill} not found (code: {result['error']['code']})")
                    
            except Exception as e:
                print(f"❌ Error with skill {skill}: {str(e)}")
        
        # Try some other A2A standard methods
        print(f"\n🔍 Trying A2A standard methods...")
        
        a2a_methods = [
            "execute_skill",
            "invoke_skill", 
            "call_skill",
            "task",
            "request"
        ]
        
        for method in a2a_methods:
            try:
                print(f"\n🔍 Trying A2A method: {method}")
                
                payload = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": {
                        "skill": "claims_orchestration",
                        "input": test_claim,
                        "action": "process_claim"
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
                    print(f"❌ Method {method} not found (code: {result['error']['code']})")
                    
            except Exception as e:
                print(f"❌ Error with method {method}: {str(e)}")
    
    print("\n❓ No working method found. The agent might need specific A2A protocol implementation.")

if __name__ == "__main__":
    asyncio.run(test_a2a_skills())
