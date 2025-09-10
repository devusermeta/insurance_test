"""
Agent Management Utility for Claims Orchestrator

This script helps manage Azure AI Foundry agents for the Claims Orchestrator:
- List existing agents
- Clean up duplicate agents  
- Update .env file with correct agent ID
- Show agent status and recommendations
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import asyncio
import logging
from dotenv import load_dotenv, set_key
from agents.claims_orchestrator.intelligent_orchestrator import IntelligentClaimsOrchestrator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce Azure SDK logging noise
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)

async def main():
    """Main agent management interface"""
    print("🤖 Claims Orchestrator Agent Manager")
    print("=" * 50)
    
    # Load environment
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    load_dotenv(env_path)
    
    # Initialize orchestrator
    orchestrator = IntelligentClaimsOrchestrator()
    
    if not orchestrator.agents_client:
        print("❌ Azure AI client not available. Check your environment configuration.")
        return
    
    while True:
        print("\n📋 Available Actions:")
        print("1. Show current agent status")
        print("2. List all agents")  
        print("3. Get or create agent (with persistence)")
        print("4. Clean up duplicate agents")
        print("5. Update .env file with current agent ID")
        print("6. Exit")
        
        choice = input("\nSelect an option (1-6): ").strip()
        
        if choice == "1":
            await show_agent_status(orchestrator)
        elif choice == "2":
            await list_all_agents(orchestrator)
        elif choice == "3":
            await get_or_create_agent(orchestrator, env_path)
        elif choice == "4":
            await cleanup_agents(orchestrator)
        elif choice == "5":
            await update_env_file(orchestrator, env_path)
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-6.")

async def show_agent_status(orchestrator):
    """Show current agent status"""
    print("\n📊 Agent Status:")
    print("-" * 30)
    
    status = orchestrator.get_agent_status()
    print(f"Azure AI Available: {'✅' if status['azure_ai_available'] else '❌'}")
    print(f"Agent Configured: {'✅' if status['agent_configured'] else '❌'}")
    
    if status['agent_configured']:
        print(f"Agent ID: {status['agent_id']}")
        print(f"Agent Name: {status['agent_name']}")
        print(f"Active Sessions: {status['active_sessions']}")
        
        if status['recommendations']:
            print("\n💡 Recommendations:")
            for rec in status['recommendations']:
                print(f"   • {rec}")

async def list_all_agents(orchestrator):
    """List all agents in Azure AI Foundry"""
    print("\n📋 All Agents:")
    print("-" * 30)
    
    try:
        agents_list = orchestrator.agents_client.list_agents()
        agents = list(agents_list)
        
        if not agents:
            print("No agents found.")
            return
            
        for i, agent in enumerate(agents, 1):
            print(f"{i}. {agent.name}")
            print(f"   ID: {agent.id}")
            print(f"   Created: {getattr(agent, 'created_at', 'Unknown')}")
            print()
            
    except Exception as e:
        print(f"❌ Error listing agents: {e}")

async def get_or_create_agent(orchestrator, env_path):
    """Get existing or create new agent with persistence"""
    print("\n🔄 Getting or Creating Agent...")
    print("-" * 35)
    
    try:
        agent = orchestrator.get_or_create_azure_agent()
        if agent:
            print(f"✅ Agent ready: {agent.name} (ID: {agent.id})")
            
            # Ask if user wants to update .env
            update = input(f"\nUpdate .env file with this agent ID? (y/n): ").strip().lower()
            if update == 'y':
                set_key(env_path, 'AZURE_AI_AGENT_ID', agent.id)
                print(f"✅ Updated .env file with AZURE_AI_AGENT_ID={agent.id}")
        else:
            print("❌ Failed to get or create agent")
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def cleanup_agents(orchestrator):
    """Clean up duplicate agents"""
    print("\n🧹 Cleaning Up Duplicate Agents...")
    print("-" * 40)
    
    confirm = input("This will DELETE duplicate agents. Continue? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ Cleanup cancelled")
        return
        
    try:
        orchestrator.cleanup_old_agents()
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

async def update_env_file(orchestrator, env_path):
    """Update .env file with current agent ID"""
    print("\n💾 Updating .env File...")
    print("-" * 25)
    
    if not orchestrator.azure_agent:
        print("❌ No agent configured. Run option 3 first.")
        return
        
    try:
        agent_id = orchestrator.azure_agent.id
        set_key(env_path, 'AZURE_AI_AGENT_ID', agent_id)
        print(f"✅ Updated .env file with AZURE_AI_AGENT_ID={agent_id}")
        print(f"📁 File: {env_path}")
    except Exception as e:
        print(f"❌ Error updating .env: {e}")

if __name__ == "__main__":
    asyncio.run(main())
