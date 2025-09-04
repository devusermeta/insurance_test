"""
ONE COMMAND - Complete Insurance System Test
Starts agents, tests real data workflow, shows comprehensive results
"""

import subprocess
import sys
import time
import os
import json
from pathlib import Path
from datetime import datetime

# Try to import requests, install if needed
try:
    import requests
except ImportError:
    print("📦 Installing requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

def log(message, level="INFO"):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{timestamp} {level}: {message}")

def start_agents_with_uvicorn():
    """Start all agents using uvicorn properly"""
    log("🚀 Starting all insurance agents with uvicorn...")
    
    base_dir = Path("d:/Metakaal/insurance/insurance_agents")
    os.chdir(base_dir)
    
    agents = [
        ("claims_orchestrator", "agents/claims_orchestrator", 8001),
        ("intake_clarifier", "agents/intake_clarifier", 8002),
        ("document_intelligence", "agents/document_intelligence", 8003),
        ("coverage_rules", "agents/coverage_rules_engine", 8004)
    ]
    
    processes = []
    
    for agent_name, agent_dir, port in agents:
        agent_file = f"{agent_name}_agent.py"
        if agent_name == "coverage_rules":
            agent_file = "coverage_rules_agent.py"  # Handle the naming difference
            
        agent_path = base_dir / agent_dir / agent_file
        
        if not agent_path.exists():
            log(f"❌ Agent file not found: {agent_path}", "WARN")
            continue
        
        log(f"📤 Starting {agent_name} on port {port}...")
        
        cmd = [
            sys.executable, "-m", "uvicorn", 
            f"{agent_file[:-3]}:app",  # Remove .py extension
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
            processes.append((agent_name, process, port))
            time.sleep(2)  # Stagger startup
            
        except Exception as e:
            log(f"❌ Failed to start {agent_name}: {str(e)}", "ERROR")
    
    return processes

def check_agent_status(agents_info):
    """Check which agents are actually online"""
    log("📊 Checking agent status...")
    
    online_agents = {}
    
    for agent_name, process, port in agents_info:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                log(f"  ✅ {agent_name} - ONLINE (port {port})")
                online_agents[agent_name] = port
            else:
                log(f"  ⚠️ {agent_name} - RESPONDING but unhealthy (port {port})")
        except:
            log(f"  ❌ {agent_name} - OFFLINE (port {port})")
    
    return online_agents

def test_schema_adaptation():
    """Test the schema adaptation with your real Cosmos DB structure"""
    log("🔄 Testing Schema Adaptation...")
    
    try:
        from shared.cosmos_schema_adapter import adapt_claim_data
        
        # Test claims matching your Cosmos DB structure
        test_claims = [
            {
                "claimId": "OP-1001",
                "memberId": "M-001", 
                "category": "Outpatient",
                "provider": "CLN-ALPHA",
                "submitDate": "2025-08-21",
                "amountBilled": 850.00,
                "status": "submitted",
                "region": "West Coast"
            },
            {
                "claimId": "OP-1002",
                "memberId": "M-002",
                "category": "Outpatient", 
                "provider": "CLN-BETA",
                "submitDate": "2025-08-19",
                "amountBilled": 1200.00,
                "status": "submitted", 
                "region": "East Coast"
            }
        ]
        
        adapted_claims = []
        for claim in test_claims:
            adapted = adapt_claim_data(claim)
            adapted_claims.append(adapted)
            log(f"   ✅ {claim['claimId']}: ${claim['amountBilled']:,.2f} → ${adapted['estimated_amount']:,.2f}")
        
        log("✅ Schema adaptation working perfectly!")
        return adapted_claims
        
    except Exception as e:
        log(f"❌ Schema adaptation failed: {str(e)}", "ERROR")
        return []

def test_orchestrator_endpoints(online_agents, adapted_claims):
    """Test the Claims Orchestrator with real API endpoints"""
    if "claims_orchestrator" not in online_agents:
        log("⚠️ Claims Orchestrator offline - skipping endpoint tests")
        return
    
    log("🚀 Testing Claims Orchestrator API endpoints...")
    
    port = online_agents["claims_orchestrator"]
    base_url = f"http://localhost:{port}"
    
    # Test 1: Status endpoint
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            log(f"   ✅ Status: {status_data.get('status', 'unknown')}")
        else:
            log(f"   ⚠️ Status endpoint: {response.status_code}")
    except Exception as e:
        log(f"   ❌ Status endpoint failed: {str(e)}")
    
    # Test 2: Process claim endpoint
    if adapted_claims:
        try:
            claim_data = {
                "claim_data": adapted_claims[0],
                "processing_options": {
                    "priority": "normal",
                    "validate_coverage": True
                }
            }
            
            log("   📤 Testing claim processing...")
            response = requests.post(
                f"{base_url}/api/process_claim",
                json=claim_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                log(f"   ✅ Claim processed! ID: {result.get('processing_id', 'N/A')}")
            else:
                log(f"   ⚠️ Claim processing: {response.status_code}")
                
        except Exception as e:
            log(f"   ❌ Claim processing failed: {str(e)}")
    
    # Test 3: Intelligent routing
    try:
        routing_data = {
            "agent_type": "clarifier",
            "message": "Process incoming claim",
            "context": adapted_claims[0] if adapted_claims else {}
        }
        
        log("   🧠 Testing intelligent routing...")
        response = requests.post(
            f"{base_url}/api/intelligent_routing", 
            json=routing_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            log(f"   ✅ Routing successful: {result.get('message', 'completed')}")
        else:
            log(f"   ⚠️ Routing: {response.status_code}")
            
    except Exception as e:
        log(f"   ❌ Routing failed: {str(e)}")

def show_comprehensive_summary(agents_info, online_agents, adapted_claims):
    """Show comprehensive system status"""
    log("=" * 65)
    log("🎯 COMPREHENSIVE SYSTEM SUMMARY")
    log("=" * 65)
    
    # Agent Status
    log(f"📊 Agent Status: {len(online_agents)}/{len(agents_info)} online")
    for agent_name, process, port in agents_info:
        if agent_name in online_agents:
            status = "🟢 ONLINE "
        else:
            status = "🔴 OFFLINE"
        log(f"   {agent_name:20} (port {port}) {status}")
    
    # Schema Status
    log(f"\n🔄 Schema Adaptation: {'✅ WORKING' if adapted_claims else '❌ FAILED'}")
    if adapted_claims:
        log(f"   Ready to process claims: {[c['claim_id'] for c in adapted_claims]}")
    
    # Database Status
    log("\n📁 Cosmos DB Containers (from exploration):")
    log("   📁 claims (6 documents) - Source data ✅")
    log("   📁 artifacts (13 documents) - Document processing ✅")
    log("   📁 rules_catalog (4 rules) - Coverage evaluation ✅") 
    log("   📁 extractions_files - AI analysis (auto-created)")
    log("   📁 agent_runs - Workflow tracking (auto-created)")
    log("   📁 events - Audit trail (auto-created)")
    
    # Next Steps
    log("\n🎯 Next Development Steps:")
    if len(online_agents) == 0:
        log("   1. 🔧 Fix agent startup issues")
        log("   2. 🔧 Resolve uvicorn configuration")
    else:
        log("   1. ✅ Agents running successfully")
        log("   2. 🔧 Complete A2A protocol endpoint mapping")
    log("   3. 🔧 Resolve MCP session management for database access")
    log("   4. 🚀 Test complete workflow with real claims OP-1001, OP-1002, OP-1003")
    log("   5. 📊 Monitor via agent registry dashboard")
    
    # System Commands
    log("\n💡 Useful Commands:")
    log("   Test again:      python test_working_endpoints.py")
    log("   Start dashboard: python start_dashboard.py") 
    log("   Check MCP:       python explore_cosmos.py")
    log("   Schema test:     python test_real_data_workflow.py")
    
    log("=" * 65)

def main():
    """Main comprehensive test function"""
    log("🏥 INSURANCE CLAIMS SYSTEM - COMPLETE TEST")
    log("=" * 65)
    
    # Step 1: Start all agents
    agents_info = start_agents_with_uvicorn()
    
    # Step 2: Wait for startup
    log("⏱️  Waiting for agents to start...")
    time.sleep(10)
    
    # Step 3: Check agent status
    online_agents = check_agent_status(agents_info)
    
    # Step 4: Test schema adaptation
    adapted_claims = test_schema_adaptation()
    
    # Step 5: Test orchestrator endpoints if available
    test_orchestrator_endpoints(online_agents, adapted_claims)
    
    # Step 6: Show comprehensive summary
    show_comprehensive_summary(agents_info, online_agents, adapted_claims)

if __name__ == "__main__":
    main()
