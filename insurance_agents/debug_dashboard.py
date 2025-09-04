"""
Debug Dashboard Issues - Analysis of current problems
"""

import requests
import json

def analyze_current_dashboard():
    """Analyze what's wrong with the current dashboard"""
    
    print("🔍 Analyzing Current Dashboard Issues")
    print("=" * 50)
    
    # 1. Check what claims API returns
    print("\n1. Current Claims API Response:")
    try:
        response = requests.get("http://localhost:3000/api/claims", timeout=5)
        if response.status_code == 200:
            claims = response.json()
            print(f"✅ Got {len(claims)} claims")
            for claim in claims:
                print(f"   • {claim['claimId']}: ${claim['amountBilled']} - {claim.get('category', 'N/A')}")
                missing_fields = []
                if not claim.get('memberId') or claim.get('memberId') == 'N/A':
                    missing_fields.append('memberId')
                if not claim.get('provider') or claim.get('provider') == 'N/A':
                    missing_fields.append('provider')
                if missing_fields:
                    print(f"     ❌ Missing: {', '.join(missing_fields)}")
        else:
            print(f"❌ Claims API returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Claims API error: {str(e)}")
    
    # 2. Check Cosmos MCP server
    print("\n2. Cosmos MCP Server Test:")
    try:
        mcp_payload = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "method": "tools/call",
            "params": {
                "name": "query_cosmos",
                "arguments": {
                    "collection": "claims",
                    "query": "SELECT * FROM c LIMIT 3"
                }
            }
        }
        
        response = requests.post(
            "http://localhost:8080/mcp",
            json=mcp_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ MCP server responding")
            if "result" in data:
                print(f"📊 MCP returned: {len(str(data))} chars of data")
                # Try to extract claims
                if "content" in data.get("result", {}):
                    items = data["result"]["content"]
                    if isinstance(items, list) and len(items) > 0:
                        sample = items[0]
                        print(f"📋 Sample real claim: {sample.get('claimId', 'Unknown')} - Provider: {sample.get('provider', 'Missing')}")
                    else:
                        print("⚠️ No claim items in MCP response")
            else:
                print("⚠️ No result in MCP response")
        else:
            print(f"❌ MCP server returned: {response.status_code}")
            
    except Exception as e:
        print(f"❌ MCP server error: {str(e)}")
    
    # 3. Test orchestrator
    print("\n3. Orchestrator A2A Test:")
    try:
        a2a_payload = {
            "jsonrpc": "2.0",
            "id": "debug-test",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": "debug-msg",
                    "role": "user",
                    "parts": [
                        {
                            "kind": "text",
                            "text": "Hello orchestrator, please confirm you're working and can access other agents."
                        }
                    ]
                }
            }
        }
        
        response = requests.post(
            "http://localhost:8001",
            json=a2a_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📡 Orchestrator response: {response.status_code}")
        if response.text:
            print(f"📄 Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Orchestrator error: {str(e)}")

    # 4. Summary
    print(f"\n{'='*50}")
    print("🎯 DIAGNOSIS SUMMARY")
    print(f"{'='*50}")
    print("❌ CURRENT ISSUES:")
    print("   1. Dashboard uses hardcoded sample data, not Cosmos")
    print("   2. 'Process' button runs fake simulation, not real agents") 
    print("   3. Missing fields (Patient, Provider) because data is fake")
    print("   4. No integration with MCP server or A2A agents")
    
    print("\n✅ SOLUTIONS:")
    print("   1. Replace load_sample_claims() with Cosmos MCP calls")
    print("   2. Replace simulate_claim_processing() with real A2A calls")
    print("   3. Update dashboard to show real Cosmos fields")
    print("   4. Connect process button to orchestrator agent")

if __name__ == "__main__":
    analyze_current_dashboard()
