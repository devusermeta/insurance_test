"""
Test Script: Get Existing Agent ID

This script connects to Azure AI Foundry and finds existing Claims Orchestrator agents,
displaying their IDs so you can add the correct one to your .env file.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Setup minimal logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Reduce Azure SDK noise
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)

def main():
    """Find and display existing Claims Orchestrator agents"""
    print("🔍 Searching for existing Claims Orchestrator agents...")
    print("=" * 60)
    
    # Load environment variables
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    load_dotenv(env_path)
    
    # Get Azure AI configuration
    subscription_id = os.environ.get("AZURE_AI_AGENT_SUBSCRIPTION_ID")
    resource_group = os.environ.get("AZURE_AI_AGENT_RESOURCE_GROUP_NAME")
    project_name = os.environ.get("AZURE_AI_AGENT_PROJECT_NAME")
    endpoint = os.environ.get("AZURE_AI_AGENT_ENDPOINT")
    
    # Check configuration
    missing = []
    if not subscription_id: missing.append("AZURE_AI_AGENT_SUBSCRIPTION_ID")
    if not resource_group: missing.append("AZURE_AI_AGENT_RESOURCE_GROUP_NAME") 
    if not project_name: missing.append("AZURE_AI_AGENT_PROJECT_NAME")
    if not endpoint: missing.append("AZURE_AI_AGENT_ENDPOINT")
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   • {var}")
        print(f"\n📁 Check your .env file at: {env_path}")
        return
    
    print(f"🔧 Connecting to Azure AI Project: {project_name}")
    print(f"🔧 Endpoint: {endpoint}")
    print()
    
    try:
        # Create Azure AI client
        project_client = AIProjectClient(
            endpoint=endpoint,
            credential=DefaultAzureCredential(),
            subscription_id=subscription_id,
            resource_group_name=resource_group,
            project_name=project_name
        )
        
        agents_client = project_client.agents
        print("✅ Successfully connected to Azure AI Foundry")
        print()
        
        # List all agents
        print("📋 Listing all agents...")
        agents_list = agents_client.list_agents()
        agents = list(agents_list)
        
        if not agents:
            print("ℹ️  No agents found in this project")
            return
        
        print(f"Found {len(agents)} total agents:")
        print("-" * 60)
        
        # Look for Claims Orchestrator agents
        orchestrator_agents = []
        
        for i, agent in enumerate(agents, 1):
            is_orchestrator = any(keyword in agent.name.lower() for keyword in [
                'claims', 'orchestrator', 'intelligent-claims'
            ])
            
            status = "🎯 ORCHESTRATOR" if is_orchestrator else "   Other"
            print(f"{i:2d}. {status} | {agent.name}")
            print(f"    📋 ID: {agent.id}")
            print(f"    📅 Created: {getattr(agent, 'created_at', 'Unknown')}")
            
            if hasattr(agent, 'model'):
                print(f"    🤖 Model: {agent.model}")
            
            print()
            
            if is_orchestrator:
                orchestrator_agents.append(agent)
        
        # Summary and recommendations
        print("=" * 60)
        print("📊 SUMMARY:")
        
        if orchestrator_agents:
            print(f"✅ Found {len(orchestrator_agents)} Claims Orchestrator agent(s)")
            print()
            
            if len(orchestrator_agents) == 1:
                agent = orchestrator_agents[0]
                print("💡 RECOMMENDED ACTION:")
                print(f"   Add this to your .env file:")
                print(f"   AZURE_AI_AGENT_ID={agent.id}")
                print()
                print(f"📋 Agent Details:")
                print(f"   Name: {agent.name}")
                print(f"   ID: {agent.id}")
                
            else:
                print("⚠️  MULTIPLE ORCHESTRATOR AGENTS FOUND:")
                print("   You should clean up duplicates. Choose the most recent one:")
                print()
                
                # Sort by creation date if available
                try:
                    sorted_agents = sorted(orchestrator_agents, 
                                         key=lambda x: getattr(x, 'created_at', ''), 
                                         reverse=True)
                    
                    print("   🏆 RECOMMENDED (Most Recent):")
                    agent = sorted_agents[0]
                    print(f"   AZURE_AI_AGENT_ID={agent.id}")
                    print(f"   Name: {agent.name}")
                    print()
                    
                    if len(sorted_agents) > 1:
                        print("   🗑️  Consider deleting these older duplicates:")
                        for old_agent in sorted_agents[1:]:
                            print(f"   - {old_agent.name} ({old_agent.id})")
                        
                except Exception:
                    print("   Choose the one you want to keep and add its ID to .env")
                    
        else:
            print("ℹ️  No Claims Orchestrator agents found")
            print("   When you run the orchestrator next time, it will create one")
        
        print()
        print("🔧 Next Steps:")
        if orchestrator_agents:
            print("1. Copy the recommended AZURE_AI_AGENT_ID to your .env file")
            if len(orchestrator_agents) > 1:
                print("2. Use the management utility to clean up duplicates:")
                print("   python agents/claims_orchestrator/manage_agents.py")
            print("3. Restart your Claims Orchestrator - it will use the existing agent")
        else:
            print("1. Run your Claims Orchestrator - it will create a new agent")
            print("2. Note the agent ID from the logs")
            print("3. Add the ID to your .env file for future use")
            
    except Exception as e:
        print(f"❌ Error connecting to Azure AI: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("1. Check your Azure credentials (az login)")
        print("2. Verify environment variables in .env file")
        print("3. Ensure you have access to the Azure AI project")

if __name__ == "__main__":
    main()
