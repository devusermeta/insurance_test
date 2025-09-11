#!/usr/bin/env python3
"""
Simple IP-02 Claim Test with Running Agents
Tests the complete workflow for the problematic IP-02 claim to verify our fixes
"""

import asyncio
import json
import httpx
import sys
import os
sys.path.append('.')

async def test_ip02_with_simple_request():
    """Test IP-02 claim processing with a simple HTTP request to the orchestrator"""
    
    print("🧪 TESTING IP-02 CLAIM WITH RUNNING AGENTS")
    print("=" * 60)
    
    # Test data for IP-02 claim processing
    employee_message = "Process claim with IP-02 using complete workflow"
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            
            # Test 1: Send request to orchestrator agent using the basic HTTP interface
            print(f"📤 Sending request to orchestrator: {employee_message}")
            
            # Try different endpoints that might work with A2A agents
            endpoints_to_try = [
                "http://localhost:8001/tasks",  # A2A task endpoint
                "http://localhost:8001/execute", # Direct execution
                "http://localhost:8001/",        # Root endpoint
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    print(f"🔍 Trying endpoint: {endpoint}")
                    
                    # Standard A2A task format
                    payload = {
                        "text": employee_message,
                        "user_id": "test_employee",
                        "session_id": "test_ip02_session"
                    }
                    
                    response = await client.post(endpoint, json=payload)
                    print(f"📨 Response Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"✅ SUCCESS! Response received from {endpoint}")
                        print(f"📋 Response: {json.dumps(result, indent=2)[:1000]}...")
                        break
                    else:
                        print(f"❌ Failed: {response.status_code} - {response.text[:200]}...")
                        
                except Exception as e:
                    print(f"❌ Error with {endpoint}: {e}")
            
            # Test 2: Check MCP server to verify IP-02 data exists
            print("\n🔍 CHECKING IP-02 DATA VIA MCP SERVER")
            print("-" * 40)
            
            try:
                mcp_response = await client.get("http://localhost:8080/health")
                print(f"📊 MCP Server Status: {mcp_response.status_code}")
                
                if mcp_response.status_code == 200:
                    print("✅ MCP Server is running")
                    
                    # Quick test of our enhanced MCP client
                    sys.path.append('.')
                    from shared.mcp_chat_client import enhanced_mcp_chat_client
                    
                    await enhanced_mcp_chat_client._initialize_mcp_session()
                    
                    # Check IP-02 claim details
                    claim_query = "Get details for claim IP-02 from claim_details container"
                    claim_result = await enhanced_mcp_chat_client.query_cosmos_data(claim_query)
                    print(f"📊 IP-02 Claim Details: {claim_result[:300]}...")
                    
                    # Check extracted patient data
                    patient_query = "Check extracted_patient_data for claim IP-02"
                    patient_result = await enhanced_mcp_chat_client.query_cosmos_data(patient_query)
                    print(f"📄 IP-02 Patient Data: {patient_result[:300]}...")
                    
            except Exception as e:
                print(f"❌ MCP Test Error: {e}")
                
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting IP-02 Claim Test...")
    asyncio.run(test_ip02_with_simple_request())
    print("🎯 Test Complete!")
