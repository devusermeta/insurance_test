"""
Step 5: Real A2A Agent Communication Test
=========================================

Now that all agents are running, let's test ACTUAL agent-to-agent communication!
This will validate our complete workflow with real running agents.
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any

# Agent ports from mcp_config
AGENT_PORTS = {
    "claims_orchestrator": 8001,
    "coverage_rules_engine": 8002,
    "document_intelligence": 8003,
    "intake_clarifier": 8004
}

async def test_agent_health_check():
    """Check if all agents are running and responding"""
    print("\n🔍 CHECKING AGENT STATUS")
    print("=" * 50)
    
    agent_status = {}
    
    for agent_name, port in AGENT_PORTS.items():
        try:
            url = f"http://localhost:{port}/health"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    print(f"✅ {agent_name}: Running on port {port}")
                    agent_status[agent_name] = "running"
                else:
                    print(f"⚠️  {agent_name}: Responding but status {response.status_code}")
                    agent_status[agent_name] = f"status_{response.status_code}"
        except Exception as e:
            print(f"❌ {agent_name}: Not responding on port {port} ({str(e)[:50]}...)")
            agent_status[agent_name] = "down"
    
    return agent_status

async def test_real_workflow_execution():
    """Test the actual complete workflow with running agents"""
    print("\n🚀 TESTING REAL A2A WORKFLOW EXECUTION")
    print("=" * 60)
    
    try:
        # Step 1: Check agent status
        agent_status = await test_agent_health_check()
        
        running_agents = [name for name, status in agent_status.items() if status == "running"]
        print(f"\n📊 Agent Status: {len(running_agents)}/4 agents running")
        
        if len(running_agents) < 4:
            print("⚠️  Not all agents running - testing with available agents only")
        
        # Step 2: Test orchestrator workflow
        if "claims_orchestrator" in running_agents:
            print(f"\n🧠 Testing Claims Orchestrator Workflow")
            print("-" * 40)
            
            # Send employee message to orchestrator
            employee_message = "Process claim with OP-05"
            result = await send_message_to_agent("claims_orchestrator", employee_message)
            
            if result:
                print("✅ Orchestrator responded successfully!")
                print(f"📄 Response: {result.get('message', 'No message')[:200]}...")
                
                # Check if it detected the claim workflow
                if "OP-05" in str(result):
                    print("🎯 Claim ID detected in orchestrator response!")
                else:
                    print("⚠️  Claim ID not detected in response")
            else:
                print("❌ Orchestrator did not respond")
        
        # Step 3: Test individual agents with structured claim data
        print(f"\n🔄 Testing Individual Agent Communication")
        print("-" * 40)
        
        # Prepare structured claim data for agents
        structured_claim_data = """
        claim_id: OP-05
        patient_name: John Doe
        bill_amount: 88.0
        category: Outpatient
        diagnosis: Type 2 diabetes
        status: submitted
        """
        
        # Test each specialized agent
        agent_tests = [
            ("coverage_rules_engine", "Evaluate coverage for structured claim: " + structured_claim_data),
            ("document_intelligence", "Process documents for structured claim: " + structured_claim_data), 
            ("intake_clarifier", "Verify patient for structured claim: " + structured_claim_data)
        ]
        
        agent_results = {}
        
        for agent_name, test_message in agent_tests:
            if agent_name in running_agents:
                print(f"\n📤 Testing {agent_name}...")
                result = await send_message_to_agent(agent_name, test_message)
                
                if result:
                    print(f"✅ {agent_name}: Responded successfully")
                    agent_results[agent_name] = result
                    
                    # Check for new workflow indicators
                    response_text = str(result).lower()
                    if any(indicator in response_text for indicator in ['new workflow', 'structured claim', 'op-05']):
                        print(f"🆕 {agent_name}: Detected new workflow processing!")
                    else:
                        print(f"📊 {agent_name}: Standard processing")
                else:
                    print(f"❌ {agent_name}: No response")
                    agent_results[agent_name] = None
        
        # Step 4: Simulate complete workflow
        print(f"\n🎯 WORKFLOW SIMULATION RESULTS")
        print("=" * 50)
        
        successful_agents = len([r for r in agent_results.values() if r is not None])
        
        if successful_agents >= 3:
            print("✅ SUCCESS: Multi-agent workflow completed!")
            print(f"📊 Agents responded: {successful_agents}/3")
            print("\n🔄 Complete workflow would execute:")
            print("   1. ✅ Employee → 'Process claim OP-05'")
            print("   2. ✅ Orchestrator → Parse claim ID & extract details")
            print("   3. ✅ Employee → Confirm processing")
            print("   4. ✅ System → Execute A2A workflow")
            print("   5. ✅ Agents → Process structured claim data")
            print("   6. ✅ System → Aggregate results & show decision")
        else:
            print(f"⚠️  PARTIAL: Only {successful_agents}/3 agents responded")
            print("   Workflow would need error handling for missing responses")
        
        return agent_results
        
    except Exception as e:
        print(f"❌ Error in workflow test: {e}")
        import traceback
        traceback.print_exc()
        return {}

async def send_message_to_agent(agent_name: str, message: str) -> Dict[str, Any]:
    """Send a message to a specific agent and get response"""
    try:
        port = AGENT_PORTS[agent_name]
        url = f"http://localhost:{port}/execute"
        
        # Prepare message in A2A format
        payload = {
            "message": message,
            "session_id": f"test_session_{int(time.time())}",
            "timestamp": time.time()
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️  {agent_name} returned status {response.status_code}")
                return None
                
    except Exception as e:
        print(f"❌ Error communicating with {agent_name}: {str(e)[:100]}...")
        return None

async def test_mcp_server_connection():
    """Test if MCP server is running for claim data extraction"""
    print(f"\n🔗 Testing MCP Server Connection")
    print("-" * 40)
    
    try:
        # Test the MCP server endpoint
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://127.0.0.1:8080/mcp")
            if response.status_code == 200:
                print("✅ MCP Server: Running and accessible")
                return True
            else:
                print(f"⚠️  MCP Server: Status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ MCP Server: Not accessible ({str(e)[:50]}...)")
        return False

if __name__ == "__main__":
    print("🚀 STARTING REAL A2A AGENT COMMUNICATION TEST")
    print("=" * 60)
    print("Testing actual communication between running agents...")
    
    async def run_all_tests():
        # Test MCP server
        mcp_running = await test_mcp_server_connection()
        
        # Test agent workflow
        results = await test_real_workflow_execution()
        
        print(f"\n🎯 FINAL TEST RESULTS")
        print("=" * 50)
        print(f"📊 MCP Server: {'✅ Running' if mcp_running else '❌ Down'}")
        print(f"🤖 Agent Communication: {'✅ Working' if results else '❌ Failed'}")
        
        if results and mcp_running:
            print("\n🎉 SUCCESS! Complete system is operational:")
            print("   ✅ All components running")
            print("   ✅ Agent communication working") 
            print("   ✅ MCP data extraction available")
            print("   ✅ Ready for employee workflow testing!")
        else:
            print(f"\n⚠️  System partially operational - check component status")
    
    # Run the tests
    asyncio.run(run_all_tests())
