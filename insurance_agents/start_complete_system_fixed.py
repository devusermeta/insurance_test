"""
Complete System Startup - Fixed Agent Startup
Properly starts all agents using uvicorn and tests the real data workflow
"""

import subprocess
import sys
import time
import requests
import os
from pathlib import Path

def start_agent_properly(agent_name: str, agent_dir: str, port: int):
    """Start an agent using proper uvicorn command"""
    agent_file = f"{agent_name}_agent.py"
    agent_path = Path(agent_dir) / agent_file
    
    if not agent_path.exists():
        print(f"  ❌ Agent file not found: {agent_path}")
        return None
    
    print(f"  📤 Starting {agent_name} on port {port}...")
    
    # Change to agent directory and run uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn",
        f"{agent_name}_agent:app",
        "--host", "0.0.0.0", 
        "--port", str(port),
        "--reload"
    ]
    
    try:
        process = subprocess.Popen(
            cmd, 
            cwd=agent_dir,
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        
        # Store process info
        if not hasattr(start_agent_properly, 'processes'):
            start_agent_properly.processes = []
        start_agent_properly.processes.append((agent_name, process, port))
        
        return process
        
    except Exception as e:
        print(f"  ❌ Failed to start {agent_name}: {str(e)}")
        return None

def check_agent_health(port: int, timeout: int = 2):
    """Check if an agent is responding"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=timeout)
        return response.status_code == 200
    except:
        return False

def main():
    print("🏥 Insurance Claims System - Complete Startup (Fixed)")
    print("=" * 65)
    
    # Ensure we're in the right directory
    base_dir = Path("d:/Metakaal/insurance/insurance_agents")
    os.chdir(base_dir)
    
    # Define agents with proper paths
    agents = [
        ("claims_orchestrator", "agents/claims_orchestrator", 8001),
        ("intake_clarifier", "agents/intake_clarifier", 8002), 
        ("document_intelligence", "agents/document_intelligence", 8003),
        ("coverage_rules_engine", "agents/coverage_rules_engine", 8004)
    ]
    
    print("🚀 Starting all insurance agents with uvicorn...")
    
    # Start all agents
    for agent_name, agent_dir, port in agents:
        full_agent_dir = base_dir / agent_dir
        if full_agent_dir.exists():
            start_agent_properly(agent_name, str(full_agent_dir), port)
            time.sleep(2)  # Give each agent time to start
        else:
            print(f"  ❌ Agent directory not found: {full_agent_dir}")
    
    # Wait for agents to fully start
    print("⏱️  Waiting for agents to start up...")
    time.sleep(10)
    
    # Check agent status
    print("\n📊 Checking agent status...")
    online_agents = 0
    for agent_name, agent_dir, port in agents:
        if check_agent_health(port):
            print(f"  ✅ {agent_name} - ONLINE (port {port})")
            online_agents += 1
        else:
            print(f"  ❌ {agent_name} - OFFLINE (port {port})")
    
    print(f"\n📈 Status: {online_agents}/{len(agents)} agents online")
    
    if online_agents > 0:
        print("  🎉 Some agents are running! Let's test the workflow...")
    else:
        print("  ⚠️ No agents online, but continuing with schema tests...")
    
    # Test real data workflow
    print("\n🧪 Testing real data workflow...")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "test_real_data_workflow.py"
        ], capture_output=False, text=True, cwd=base_dir)
        
        if result.returncode == 0:
            print("\n✅ Real data workflow test completed!")
        else:
            print(f"\n⚠️ Workflow test completed with code: {result.returncode}")
            
    except Exception as e:
        print(f"\n❌ Error running workflow test: {str(e)}")
    
    # Show process status
    if hasattr(start_agent_properly, 'processes'):
        print(f"\n📋 Agent Processes:")
        for agent_name, process, port in start_agent_properly.processes:
            if process.poll() is None:
                status = "🟢 RUNNING"
            else:
                status = "🔴 STOPPED" 
            print(f"  - {agent_name:20} (PID: {process.pid:5}, Port: {port}) {status}")
    
    print("\n💡 Next Steps:")
    print("  🔧 Fix A2A endpoint routing (404 errors)")
    print("  🔧 Resolve MCP session management") 
    print("  🚀 Test with real Cosmos claims data")
    print("  📊 Monitor via: python start_dashboard.py")
    
    print("\n🎯 System diagnostic complete!")
    print("=" * 65)

if __name__ == "__main__":
    main()
