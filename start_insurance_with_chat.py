#!/usr/bin/env python3
"""
Complete Insurance System Startup Script with Chat Integration

This script will start all the required components in the correct order for the
insurance claims system with the new chat functionality.
"""

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path

def print_banner():
    print("=" * 70)
    print("🏥 INSURANCE CLAIMS SYSTEM WITH CHAT INTEGRATION")
    print("=" * 70)
    print()

def check_requirements():
    """Check if required dependencies are installed"""
    print("📦 Checking requirements...")
    
    required_packages = {
        "httpx": "For MCP communication",
        "aiohttp": "For agent communication", 
        "fastapi": "For web API",
        "uvicorn": "For web server"
    }
    
    missing = []
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"  ✅ {package} - {description}")
        except ImportError:
            print(f"  ❌ {package} - {description} (MISSING)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install them with: pip install " + " ".join(missing))
        return False
    
    print("✅ All requirements satisfied!")
    return True

def start_cosmos_mcp_server():
    """Start the Cosmos DB MCP Server"""
    print("\n🗄️  Starting Cosmos DB MCP Server...")
    
    mcp_dir = Path(__file__).parent / "azure-cosmos-mcp-server-samples" / "python"
    
    if not mcp_dir.exists():
        print(f"❌ MCP Server directory not found: {mcp_dir}")
        return None
    
    try:
        # Start the MCP server in the background
        process = subprocess.Popen(
            [sys.executable, "cosmos_server.py"],
            cwd=str(mcp_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give it a moment to start
        time.sleep(3)
        
        # Check if it's running
        if process.poll() is None:
            print("✅ Cosmos DB MCP Server started on port 8080")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ MCP Server failed to start")
            print(f"   stdout: {stdout.decode()}")
            print(f"   stderr: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting MCP Server: {e}")
        return None

def start_claims_orchestrator():
    """Start the Claims Orchestrator Agent"""
    print("\n🤖 Starting Claims Orchestrator...")
    
    agents_dir = Path(__file__).parent / "insurance_agents"
    
    if not agents_dir.exists():
        print(f"❌ Insurance agents directory not found: {agents_dir}")
        return None
    
    try:
        # Start the orchestrator
        process = subprocess.Popen(
            [sys.executable, "-m", "agents.claims_orchestrator"],
            cwd=str(agents_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give it a moment to start
        time.sleep(5)
        
        # Check if it's running
        if process.poll() is None:
            print("✅ Claims Orchestrator started on port 8001")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Claims Orchestrator failed to start")
            print(f"   stdout: {stdout.decode()}")
            print(f"   stderr: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting Claims Orchestrator: {e}")
        return None

def start_dashboard():
    """Start the main dashboard with chat integration"""
    print("\n🌐 Starting Dashboard with Chat Integration...")
    
    dashboard_dir = Path(__file__).parent / "insurance_agents" / "insurance_agents_registry_dashboard"
    
    if not dashboard_dir.exists():
        print(f"❌ Dashboard directory not found: {dashboard_dir}")
        return None
    
    # Check if app.py exists
    app_py = dashboard_dir / "app.py"
    if not app_py.exists():
        print(f"❌ Main app.py not found: {app_py}")
        return None
    
    try:
        # Start the dashboard
        process = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd=str(dashboard_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give it a moment to start
        time.sleep(3)
        
        # Check if it's running
        if process.poll() is None:
            print("✅ Dashboard started on http://localhost:3000")
            print("   - Main dashboard: http://localhost:3000")
            print("   - Claims view: http://localhost:3000/claims")  
            print("   - Agent registry: http://localhost:3000/agents")
            print("   - 💬 Chat available on all pages!")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Dashboard failed to start")
            print(f"   stdout: {stdout.decode()}")
            print(f"   stderr: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting Dashboard: {e}")
        return None

def main():
    """Main startup sequence"""
    print_banner()
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Please install missing requirements and try again.")
        return
    
    processes = []
    
    try:
        # Step 1: Start Cosmos DB MCP Server
        mcp_process = start_cosmos_mcp_server()
        if mcp_process:
            processes.append(("Cosmos MCP Server", mcp_process))
        
        # Step 2: Start Claims Orchestrator
        orchestrator_process = start_claims_orchestrator()
        if orchestrator_process:
            processes.append(("Claims Orchestrator", orchestrator_process))
        
        # Step 3: Start Dashboard
        dashboard_process = start_dashboard()
        if dashboard_process:
            processes.append(("Dashboard", dashboard_process))
        
        if not processes:
            print("\n❌ No processes started successfully. Please check the errors above.")
            return
        
        print(f"\n🎉 SUCCESS! {len(processes)} processes started successfully.")
        print("\n📋 SYSTEM STATUS:")
        for name, process in processes:
            status = "✅ RUNNING" if process.poll() is None else "❌ STOPPED"
            print(f"   {name}: {status}")
        
        print("\n💬 CHAT INTEGRATION READY!")
        print("   - Click the 'Chat with Orchestrator' button on any page")
        print("   - Ask questions about claims data")
        print("   - The orchestrator will query Cosmos DB via MCP tools")
        print("   - Enjoy real-time conversational AI!")
        
        print("\n⚡ QUICK TEST:")
        print("   1. Open http://localhost:3000")
        print("   2. Click 'Chat with Orchestrator' button")
        print("   3. Try: 'Hello, show me recent claims'")
        print("   4. Try: 'How many claims are pending?'")
        
        print("\n🛑 To stop all services, press Ctrl+C")
        
        # Keep the script running and monitor processes
        while True:
            time.sleep(5)
            failed_processes = []
            
            for name, process in processes:
                if process.poll() is not None:
                    failed_processes.append(name)
            
            if failed_processes:
                print(f"\n⚠️  Process(es) stopped: {', '.join(failed_processes)}")
                break
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down all services...")
        
        for name, process in processes:
            try:
                process.terminate()
                print(f"   Stopped {name}")
            except Exception as e:
                print(f"   Error stopping {name}: {e}")
        
        print("✅ All services stopped. Goodbye!")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
if __name__ == "__main__":
    main()
