"""
Quick test to verify agent persistence works
"""
import sys
sys.path.append('..')

from agents.claims_orchestrator.intelligent_orchestrator import IntelligentClaimsOrchestrator

def test_agent_persistence():
    print("🧪 Testing agent persistence...")
    
    # Create orchestrator
    orchestrator = IntelligentClaimsOrchestrator()
    
    if not orchestrator.agents_client:
        print("❌ Azure AI client not available")
        return
        
    # Test get_or_create_azure_agent
    agent = orchestrator.get_or_create_azure_agent()
    
    if agent:
        print(f"✅ Agent ready: {agent.name}")
        print(f"📋 Agent ID: {agent.id}")
        print(f"🧵 Thread created: {orchestrator.current_thread.id if orchestrator.current_thread else 'None'}")
        print("🎉 Agent persistence working perfectly!")
    else:
        print("❌ Agent creation/retrieval failed")

if __name__ == "__main__":
    test_agent_persistence()
