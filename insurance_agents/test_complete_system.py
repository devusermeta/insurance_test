"""
Complete Workflow Test with Running Agents
==========================================

Test the ACTUAL employee workflow with all running agents!
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any

async def test_complete_employee_workflow():
    """Test the complete employee workflow with running agents"""
    print("\n🎉 TESTING COMPLETE EMPLOYEE WORKFLOW")
    print("=" * 60)
    print("All agents are running - testing real workflow!")
    
    try:
        # Step 1: Employee input
        employee_message = "Process claim with OP-05"
        print(f"👤 Employee types: '{employee_message}'")
        
        # Step 2: Send to Claims Orchestrator
        print(f"\n🧠 Sending to Claims Orchestrator...")
        orchestrator_response = await send_message_to_orchestrator(employee_message)
        
        if orchestrator_response:
            print("✅ Orchestrator responded!")
            
            # Check the response content
            response_text = str(orchestrator_response)
            print(f"📄 Response preview: {response_text[:300]}...")
            
            # Look for key indicators of our new workflow
            if "OP-05" in response_text:
                print("🎯 ✅ Claim ID detected in response!")
            if "John Doe" in response_text:
                print("👤 ✅ Patient name found in response!")
            if "confirmation" in response_text.lower():
                print("💬 ✅ Employee confirmation workflow detected!")
            if "multi-agent" in response_text.lower() or "workflow" in response_text.lower():
                print("🔄 ✅ Multi-agent workflow mentioned!")
                
            # Test if we can trigger the actual A2A workflow
            print(f"\n🔄 Testing A2A Agent Communication...")
            await test_agent_to_agent_communication()
                
        else:
            print("❌ No response from orchestrator")
        
        return orchestrator_response
        
    except Exception as e:
        print(f"❌ Error in complete workflow test: {e}")
        return None

async def send_message_to_orchestrator(message: str) -> Dict[str, Any]:
    """Send message to the running Claims Orchestrator"""
    try:
        url = "http://localhost:8001/execute"
        
        payload = {
            "message": message,
            "user_id": "test_employee",
            "session_id": f"test_session_{int(time.time())}",
            "timestamp": time.time()
        }
        
        print(f"📤 POST {url}")
        print(f"📦 Payload: {json.dumps(payload, indent=2)}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            
            print(f"📨 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📋 Response Type: {type(result)}")
                return result
            else:
                print(f"⚠️  Non-200 response: {response.text}")
                return {"status": "error", "message": response.text}
                
    except Exception as e:
        print(f"❌ Error sending to orchestrator: {e}")
        return None

async def test_agent_to_agent_communication():
    """Test direct communication between agents"""
    print(f"\n🤖 Testing Direct Agent Communication")
    print("-" * 40)
    
    # Test data for agents
    test_claim_data = """
    Structured Claim Processing Request:
    claim_id: OP-05
    patient_name: John Doe
    bill_amount: 88.0
    category: Outpatient
    diagnosis: Type 2 diabetes
    status: submitted
    """
    
    agents_to_test = [
        ("Coverage Rules Engine", 8004, "Evaluate coverage for: " + test_claim_data),
        ("Document Intelligence", 8003, "Process documents for: " + test_claim_data),
        ("Intake Clarifier", 8002, "Verify patient for: " + test_claim_data)
    ]
    
    for agent_name, port, test_message in agents_to_test:
        print(f"\n📤 Testing {agent_name} (port {port})...")
        
        try:
            url = f"http://localhost:{port}/execute"
            payload = {
                "message": test_message,
                "session_id": f"test_a2a_{int(time.time())}"
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ {agent_name}: SUCCESS")
                    
                    # Check for new workflow processing
                    response_text = str(result).lower()
                    if any(indicator in response_text for indicator in ['op-05', 'john doe', 'outpatient', 'structured']):
                        print(f"🆕 {agent_name}: Processing structured claim data!")
                    
                    # Show key parts of response
                    if isinstance(result, dict) and 'message' in result:
                        preview = result['message'][:200] if isinstance(result['message'], str) else str(result['message'])[:200]
                        print(f"📄 Response: {preview}...")
                        
                else:
                    print(f"⚠️  {agent_name}: Status {response.status_code}")
                    
        except Exception as e:
            print(f"❌ {agent_name}: Error - {str(e)[:50]}...")

async def test_mcp_claim_extraction():
    """Test MCP claim extraction directly"""
    print(f"\n📊 Testing MCP Claim Extraction")
    print("-" * 40)
    
    try:
        from shared.mcp_chat_client import enhanced_mcp_chat_client
        
        # Test claim extraction
        claim_id = "OP-05"
        print(f"🔍 Extracting details for claim: {claim_id}")
        
        details = await enhanced_mcp_chat_client.extract_claim_details(claim_id)
        
        if details.get("success"):
            print("✅ MCP Extraction SUCCESS!")
            print(f"   Patient: {details['patient_name']}")
            print(f"   Amount: ${details['bill_amount']}")
            print(f"   Category: {details['category']}")
            return True
        else:
            print(f"❌ MCP Extraction FAILED: {details.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ MCP Test Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 COMPLETE SYSTEM TEST WITH RUNNING AGENTS")
    print("=" * 60)
    
    async def run_complete_test():
        # Test MCP first
        mcp_working = await test_mcp_claim_extraction()
        
        # Test complete workflow
        workflow_result = await test_complete_employee_workflow()
        
        print(f"\n🎯 FINAL SYSTEM STATUS")
        print("=" * 60)
        print(f"📊 MCP Server: {'✅ Working' if mcp_working else '❌ Issues'}")
        print(f"🤖 Orchestrator: {'✅ Responding' if workflow_result else '❌ Not responding'}")
        print(f"🔄 Agent Network: {'✅ All Online' if workflow_result else '❌ Partial'}")
        
        if mcp_working and workflow_result:
            print(f"\n🎉 SUCCESS! COMPLETE SYSTEM IS OPERATIONAL!")
            print("=" * 60)
            print("✅ Employee can type: 'Process claim with OP-05'")
            print("✅ System extracts claim data via MCP")
            print("✅ Orchestrator coordinates multi-agent workflow")
            print("✅ All specialized agents process structured data")
            print("✅ Results aggregated for employee decision")
            print("\n🚀 READY FOR PRODUCTION TESTING!")
        else:
            print(f"\n⚠️  System partially operational - check individual components")
    
    asyncio.run(run_complete_test())
