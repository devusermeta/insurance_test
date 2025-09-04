"""
Complete System Startup - All in One Command
Starts all agents and tests the real data workflow
"""

import subprocess
import sys
import time
import threading
import requests
from pathlib import Path

def start_agent_background(agent_name: str, script_path: str, port: int):
    """Start an agent in the background"""
    def run_agent():
        try:
            print(f"  📤 Starting {agent_name} on port {port}...")
            process = subprocess.Popen([
                sys.executable, script_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Store process info globally so we can clean up later
            if not hasattr(start_agent_background, 'processes'):
                start_agent_background.processes = []
            start_agent_background.processes.append((agent_name, process, port))
            
        except Exception as e:
            print(f"  ❌ Failed to start {agent_name}: {str(e)}")
    
    thread = threading.Thread(target=run_agent, daemon=True)
    thread.start()
    return thread

def check_agent_health(port: int, timeout: int = 3):
    """Check if an agent is responding"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=timeout)
        return response.status_code == 200
    except:
        return False

def main():
    print("🏥 Insurance Claims System - Complete Startup")
    print("=" * 60)
    
    # Change to correct directory
    import os
    os.chdir("d:\\Metakaal\\insurance\\insurance_agents")
    
    # Define agents
    agents = [
        ("orchestrator", "agents/claims_orchestrator/claims_orchestrator_agent.py", 8001),
        ("clarifier", "agents/intake_clarifier/intake_clarifier_agent.py", 8002),
        ("document", "agents/document_intelligence/document_intelligence_agent.py", 8003),
        ("rules", "agents/coverage_rules_engine/coverage_rules_agent.py", 8004)
    ]
    
    print("🚀 Starting all insurance agents...")
    
    # Start all agents
    threads = []
    for agent_name, script_path, port in agents:
        if Path(script_path).exists():
            thread = start_agent_background(agent_name, script_path, port)
            threads.append(thread)
            time.sleep(1)  # Stagger startup
        else:
            print(f"  ❌ Agent script not found: {script_path}")
    
    # Wait for agents to start
    print("⏱️  Waiting for agents to start up...")
    time.sleep(8)
    
    # Check agent status
    print("\n📊 Checking agent status...")
    online_agents = 0
    for agent_name, script_path, port in agents:
        if check_agent_health(port):
            print(f"  ✅ {agent_name} agent - ONLINE (port {port})")
            online_agents += 1
        else:
            print(f"  ❌ {agent_name} agent - OFFLINE (port {port})")
    
    print(f"\n📈 Status: {online_agents}/{len(agents)} agents online")
    
    # Test real data workflow
    print("\n🧪 Testing real data workflow...")
    print("-" * 40)
    
    try:
        result = subprocess.run([
            sys.executable, "test_real_data_workflow.py"
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ Real data workflow test completed successfully!")
        else:
            print(f"\n⚠️ Real data workflow test completed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"\n❌ Error running workflow test: {str(e)}")
    
    print("\n💡 Management Tips:")
    print("  • Agents are running in background processes")
    print("  • Test again with: python test_real_data_workflow.py")
    print("  • Start dashboard with: python start_dashboard.py")
    print("  • Check MCP server: python -c \"import requests; print(requests.get('http://localhost:8080').text)\"")
    
    print("\n🎯 System startup complete!")
    print("=" * 60)
    
    # Show running processes (if available)
    if hasattr(start_agent_background, 'processes'):
        print(f"\n📋 Background Processes:")
        for agent_name, process, port in start_agent_background.processes:
            status = "RUNNING" if process.poll() is None else "STOPPED"
            print(f"  - {agent_name} (PID: {process.pid}, Port: {port}) - {status}")

if __name__ == "__main__":
    main()
