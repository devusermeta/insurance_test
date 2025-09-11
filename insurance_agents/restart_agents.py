#!/usr/bin/env python3
"""
Restart all agents to pick up code changes
"""
import subprocess
import time
import requests
import sys
from pathlib import Path

def kill_agents():
    """Kill any existing agent processes"""
    try:
        # Kill processes on the agent ports
        for port in [8001, 8002, 8003, 8004]:
            try:
                result = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                
                for line in result.stdout.split('\n'):
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if len(parts) > 4:
                            pid = parts[-1]
                            print(f"Killing process {pid} on port {port}")
                            subprocess.run(["taskkill", "/PID", pid, "/F"], shell=True)
                            
            except Exception as e:
                print(f"Error killing process on port {port}: {e}")
                
        time.sleep(2)  # Wait for cleanup
        
    except Exception as e:
        print(f"Error in kill_agents: {e}")

def start_agents():
    """Start all agents"""
    try:
        # Define agent configurations
        agents = [
            {"name": "claims_orchestrator", "port": 8001, "script": "intelligent_orchestrator.py"},
            {"name": "intake_clarifier", "port": 8002, "script": "a2a_wrapper.py"},
            {"name": "document_intelligence", "port": 8003, "script": "document_intelligence_executor_fixed.py"},
            {"name": "coverage_rules_engine", "port": 8004, "script": "coverage_rules_executor_fixed.py"}
        ]
        
        current_dir = Path(__file__).parent
        
        for agent in agents:
            script_path = current_dir / "agents" / agent["name"] / agent["script"]
            
            if script_path.exists():
                print(f"Starting {agent['name']} on port {agent['port']}...")
                
                # Start the agent process in background
                subprocess.Popen(
                    [sys.executable, str(script_path)],
                    cwd=str(current_dir),
                    shell=True
                )
                
                # Wait a moment between starts
                time.sleep(1)
            else:
                print(f"Script not found: {script_path}")
        
        print("Waiting for agents to start...")
        time.sleep(5)
        
        # Test agent connectivity
        for agent in agents:
            try:
                response = requests.get(f"http://localhost:{agent['port']}/health", timeout=2)
                print(f"{agent['name']}: {'✅ Running' if response.status_code == 404 else '❌ Issue'}")
            except:
                print(f"{agent['name']}: ❌ Not responding")
                
    except Exception as e:
        print(f"Error starting agents: {e}")

if __name__ == "__main__":
    print("🔄 RESTARTING AGENTS")
    print("=" * 30)
    
    print("Stopping existing agents...")
    kill_agents()
    
    print("Starting agents with updated code...")
    start_agents()
    
    print("Agent restart complete!")
