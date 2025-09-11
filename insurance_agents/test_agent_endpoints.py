"""
Test A2A Agent Endpoints
========================
Check what endpoints are actually available on the running agents
"""

import asyncio
import httpx
import json

async def check_agent_endpoints():
    """Check what endpoints are available on running agents"""
    print("🔍 CHECKING AGENT ENDPOINTS")
    print("=" * 50)
    
    agents = [
        ("Claims Orchestrator", 8001),
        ("Intake Clarifier", 8002), 
        ("Document Intelligence", 8003),
        ("Coverage Rules Engine", 8004)
    ]
    
    common_endpoints = [
        "/",
        "/health", 
        "/status",
        "/execute",
        "/api/v1/execute",
        "/.well-known/agent.json",
        "/docs",
        "/openapi.json"
    ]
    
    for agent_name, port in agents:
        print(f"\n🤖 {agent_name} (port {port}):")
        print("-" * 30)
        
        working_endpoints = []
        
        for endpoint in common_endpoints:
            try:
                url = f"http://localhost:{port}{endpoint}"
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(url)
                    
                    if response.status_code < 400:
                        working_endpoints.append(f"✅ {endpoint} ({response.status_code})")
                        
                        # If it's the agent.json, show what's available
                        if endpoint == "/.well-known/agent.json":
                            try:
                                agent_info = response.json()
                                if "capabilities" in agent_info:
                                    print(f"   📋 Agent Info Available!")
                            except:
                                pass
                    else:
                        # Don't show 404s to keep output clean
                        pass
                        
            except Exception as e:
                # Silently skip errors
                pass
        
        if working_endpoints:
            for endpoint in working_endpoints:
                print(f"   {endpoint}")
        else:
            print("   ❌ No standard endpoints found")

async def test_agent_json_endpoints():
    """Test the A2A agent.json endpoints specifically"""
    print(f"\n🔍 TESTING A2A AGENT.JSON ENDPOINTS")
    print("=" * 50)
    
    agents = [
        ("Claims Orchestrator", 8001),
        ("Intake Clarifier", 8002), 
        ("Document Intelligence", 8003),
        ("Coverage Rules Engine", 8004)
    ]
    
    for agent_name, port in agents:
        try:
            url = f"http://localhost:{port}/.well-known/agent.json"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    agent_info = response.json()
                    print(f"\n✅ {agent_name}:")
                    print(f"   Name: {agent_info.get('name', 'Unknown')}")
                    print(f"   Description: {agent_info.get('description', 'None')}")
                    
                    if "capabilities" in agent_info:
                        caps = agent_info["capabilities"]
                        if "skills" in caps:
                            skills = caps["skills"]
                            print(f"   Skills ({len(skills)}):")
                            for skill in skills:
                                print(f"     • {skill.get('name', 'Unnamed skill')}")
                    
                else:
                    print(f"❌ {agent_name}: Status {response.status_code}")
                    
        except Exception as e:
            print(f"❌ {agent_name}: Error - {str(e)[:50]}...")

if __name__ == "__main__":
    print("🚀 CHECKING A2A AGENT ENDPOINTS")
    print("=" * 50)
    
    async def run_checks():
        await check_agent_endpoints()
        await test_agent_json_endpoints()
    
    asyncio.run(run_checks())
