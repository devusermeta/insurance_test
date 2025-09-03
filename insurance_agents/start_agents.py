"""
Agent Startup Script
Easily start individual agents or all agents for testing
"""

import subprocess
import sys
import time
import asyncio
from pathlib import Path

def start_agent(agent_name: str, port: int):
    """Start a specific agent"""
    agent_paths = {
        "orchestrator": "agents/claims_orchestrator/claims_orchestrator_agent.py",
        "clarifier": "agents/intake_clarifier/intake_clarifier_agent.py", 
        "document": "agents/document_intelligence/document_intelligence_agent.py",
        "rules": "agents/coverage_rules_engine/coverage_rules_agent.py"
    }
    
    agent_path = agent_paths.get(agent_name)
    if not agent_path:
        print(f"❌ Unknown agent: {agent_name}")
        print(f"Available agents: {list(agent_paths.keys())}")
        return None
    
    if not Path(agent_path).exists():
        print(f"❌ Agent file not found: {agent_path}")
        return None
    
    print(f"🚀 Starting {agent_name} agent on port {port}...")
    
    try:
        process = subprocess.Popen([
            sys.executable, agent_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        time.sleep(2)  # Give it time to start
        
        if process.poll() is None:
            print(f"✅ {agent_name} agent started successfully (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start {agent_name} agent")
            print(f"Error: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting {agent_name} agent: {str(e)}")
        return None

def main():
    """Main startup function"""
    if len(sys.argv) < 2:
        print("🤖 Insurance Agents Startup Script")
        print("=" * 40)
        print("Usage:")
        print("  python start_agents.py <agent_name>")
        print("  python start_agents.py all")
        print()
        print("Available agents:")
        print("  orchestrator  - Claims Orchestrator (port 8001)")
        print("  clarifier     - Intake Clarifier (port 8002)")
        print("  document      - Document Intelligence (port 8003)")
        print("  rules         - Coverage Rules Engine (port 8004)")
        print("  all           - Start all agents")
        print()
        print("Examples:")
        print("  python start_agents.py orchestrator")
        print("  python start_agents.py all")
        return
    
    agent_name = sys.argv[1].lower()
    
    agent_ports = {
        "orchestrator": 8001,
        "clarifier": 8002,
        "document": 8003,
        "rules": 8004
    }
    
    if agent_name == "all":
        print("🚀 Starting all insurance agents...")
        print("=" * 40)
        
        processes = []
        for name, port in agent_ports.items():
            process = start_agent(name, port)
            if process:
                processes.append((name, process))
                time.sleep(1)  # Stagger startup
        
        if processes:
            print(f"\n✅ Started {len(processes)} agents successfully!")
            print("Running agents:")
            for name, process in processes:
                print(f"  - {name} (PID: {process.pid}, Port: {agent_ports[name]})")
            
            print("\nPress Ctrl+C to stop all agents...")
            try:
                while True:
                    time.sleep(1)
                    # Check if any process died
                    for name, process in processes[:]:
                        if process.poll() is not None:
                            print(f"⚠️ Agent {name} stopped unexpectedly")
                            processes.remove((name, process))
                    
                    if not processes:
                        print("❌ All agents stopped")
                        break
                        
            except KeyboardInterrupt:
                print("\n🛑 Stopping all agents...")
                for name, process in processes:
                    process.terminate()
                    print(f"  Stopped {name}")
                print("✅ All agents stopped")
        
    elif agent_name in agent_ports:
        port = agent_ports[agent_name]
        process = start_agent(agent_name, port)
        
        if process:
            print(f"\n✅ {agent_name} agent is running on port {port}")
            print(f"   PID: {process.pid}")
            print(f"   Test with: python test_agents.py")
            print("\nPress Ctrl+C to stop...")
            
            try:
                while process.poll() is None:
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n🛑 Stopping {agent_name} agent...")
                process.terminate()
                print("✅ Agent stopped")
    
    else:
        print(f"❌ Unknown agent: {agent_name}")
        print(f"Available agents: {list(agent_ports.keys())}")

if __name__ == "__main__":
    main()
