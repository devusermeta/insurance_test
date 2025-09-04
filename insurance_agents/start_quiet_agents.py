"""
Start All Agents with Reduced Logging
This script starts all insurance agents with minimal logging output
"""

import asyncio
import subprocess
import sys
import os
import time
from typing import List, Dict

def start_quiet_agents():
    """Start all agents with reduced logging"""
    
    print("🔇 Starting Insurance Agents with Reduced Logging")
    print("=" * 55)
    
    # Define agents and their startup commands
    agents_config = {
        "orchestrator": {
            "path": "d:\\Metakaal\\insurance\\insurance_agents\\agents\\claims_orchestrator",
            "port": 8001,
            "name": "Claims Orchestrator"
        },
        "clarifier": {
            "path": "d:\\Metakaal\\insurance\\insurance_agents\\agents\\intake_clarifier", 
            "port": 8002,
            "name": "Intake Clarifier"
        },
        "document": {
            "path": "d:\\Metakaal\\insurance\\insurance_agents\\agents\\document_intelligence",
            "port": 8003,
            "name": "Document Intelligence"
        },
        "rules": {
            "path": "d:\\Metakaal\\insurance\\insurance_agents\\agents\\coverage_rules_engine",
            "port": 8004,
            "name": "Coverage Rules Engine"
        }
    }
    
    processes = {}
    
    # Start each agent
    for agent_id, config in agents_config.items():
        print(f"🚀 Starting {config['name']} on port {config['port']}...")
        
        try:
            # Change to agent directory and start with reduced logging
            cmd = [
                "powershell.exe", "-Command",
                f"cd '{config['path']}'; $env:PYTHONPATH='d:\\Metakaal\\insurance\\insurance_agents'; python __main__.py --log-level error"
            ]
            
            # Start process with suppressed output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE,  # New window for each agent
                cwd=config['path']
            )
            
            processes[agent_id] = {
                'process': process,
                'config': config
            }
            
            print(f"   ✅ {config['name']}: PID {process.pid}")
            time.sleep(2)  # Give each agent time to start
            
        except Exception as e:
            print(f"   ❌ Failed to start {config['name']}: {str(e)}")
    
    # Wait a moment for all to start
    print("\n⏳ Waiting for agents to initialize...")
    time.sleep(5)
    
    # Check status
    print("\n📊 Agent Status Check:")
    import requests
    
    for agent_id, info in processes.items():
        config = info['config']
        try:
            response = requests.get(f"http://localhost:{config['port']}/.well-known/agent.json", timeout=3)
            if response.status_code == 200:
                print(f"   ✅ {config['name']}: ONLINE (port {config['port']})")
            else:
                print(f"   ⚠️ {config['name']}: Responding but status {response.status_code}")
        except Exception as e:
            print(f"   ❌ {config['name']}: OFFLINE - {str(e)}")
    
    print("\n🎯 All agents started with reduced logging!")
    print("💡 HTTP access logs and A2A warnings are now suppressed")
    print("📊 Dashboard: python start_dashboard.py")
    print("🧪 Test: python ../test_enhanced_orchestrator.py")
    print("\n🔇 Logging has been reduced. You should see much less noise now!")
    
    return processes

if __name__ == "__main__":
    try:
        processes = start_quiet_agents()
        
        # Keep script running
        print("\n⌨️  Press Ctrl+C to stop all agents...")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping all agents...")
        for agent_id, info in processes.items():
            try:
                info['process'].terminate()
                print(f"   ✅ Stopped {info['config']['name']}")
            except:
                pass
        print("🏁 All agents stopped!")
