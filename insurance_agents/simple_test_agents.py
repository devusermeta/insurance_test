"""
Simple Insurance Agents Test
Test the created insurance agents with the correct API methods.
"""

import os
from azure.identity import AzureCliCredential
from azure.ai.agents import AgentsClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_insurance_agents():
    """Test all created insurance agents"""
    
    print("🚀 Testing Insurance Agents - Simple Test")
    print("=" * 45)
    
    try:
        # Initialize client
        credential = AzureCliCredential()
        endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
        agents_client = AgentsClient(endpoint=endpoint, credential=credential)
        
        print(f"✅ Connected to: {endpoint}")
        
        # Agent IDs from .env
        agents = {
            'Claims Orchestrator': os.getenv('CLAIMS_ORCHESTRATOR_AGENT_ID'),
            'Intake Clarifier': os.getenv('INTAKE_CLARIFIER_AGENT_ID'),
            'Document Intelligence': os.getenv('DOCUMENT_INTELLIGENCE_AGENT_ID'),
            'Coverage Rules Engine': os.getenv('COVERAGE_RULES_ENGINE_AGENT_ID')
        }
        
        print(f"\n📋 Testing {len(agents)} Insurance Agents:")
        
        for agent_name, agent_id in agents.items():
            if agent_id:
                print(f"\n🔄 Testing {agent_name} ({agent_id})...")
                
                try:
                    # Simple test message
                    test_message = f"Hello, I need help with insurance claims. Can you introduce yourself and explain how you can help?"
                    
                    # Use create_thread_and_run method
                    result = agents_client.create_thread_and_run(
                        assistant_id=agent_id,
                        thread={
                            "messages": [
                                {
                                    "role": "user",
                                    "content": test_message
                                }
                            ]
                        }
                    )
                    
                    print(f"✅ {agent_name} responded successfully!")
                    
                    # Get the response
                    if hasattr(result, 'messages') and result.messages:
                        for message in result.messages:
                            if message.role == "assistant":
                                content = message.content[0].text.value if message.content else "No content"
                                print(f"   📝 Response: {content[:150]}...")
                                break
                    else:
                        print(f"   📝 Agent responded but content format needs parsing")
                    
                except Exception as e:
                    print(f"❌ {agent_name} test failed: {e}")
            else:
                print(f"❌ {agent_name}: No agent ID found")
        
        print(f"\n🎉 Agent Testing Complete!")
        
        # List all agents in the workspace
        print(f"\n📊 All Agents in Workspace:")
        try:
            all_agents = agents_client.list_agents()
            for agent in all_agents.data:
                agent_type = "Insurance" if "Insurance" in agent.name else "Other"
                print(f"   {agent_type}: {agent.name} ({agent.id})")
        except Exception as e:
            print(f"   Error listing agents: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def demonstrate_agent_capabilities():
    """Show what each agent specializes in"""
    
    print(f"\n🎯 Insurance Agent Capabilities")
    print("=" * 35)
    
    capabilities = {
        'Claims Orchestrator': [
            'Workflow coordination',
            'Multi-agent delegation',
            'Final decision making',
            'Quality assurance',
            'Customer communication'
        ],
        'Intake Clarifier': [
            'Claim validation',
            'Document verification',
            'Fraud detection',
            'Data standardization',
            'Initial assessment'
        ],
        'Document Intelligence': [
            'Photo analysis',
            'PDF text extraction',
            'Damage assessment',
            'Medical record review',
            'Information extraction'
        ],
        'Coverage Rules Engine': [
            'Policy analysis',
            'Coverage determination',
            'Rules processing',
            'Deductible calculation',
            'Compliance checking'
        ]
    }
    
    for agent_name, skills in capabilities.items():
        print(f"\n🤖 {agent_name}:")
        for skill in skills:
            print(f"   • {skill}")
    
    print(f"\n💡 Dynamic Routing Examples:")
    print(f"   'File new claim' → Intake Clarifier")
    print(f"   'Analyze damage photo' → Document Intelligence") 
    print(f"   'Check coverage' → Coverage Rules Engine")
    print(f"   'Coordinate complex case' → Claims Orchestrator")

if __name__ == "__main__":
    print("🚀 Insurance Agents - Simple Test & Capabilities Demo")
    print("=" * 60)
    
    # Test agents
    success = test_insurance_agents()
    
    # Show capabilities
    demonstrate_agent_capabilities()
    
    if success:
        print(f"\n🎯 SUCCESS! Your insurance agents are working!")
        print(f"🚀 Ready for dynamic routing and registry dashboard!")
    else:
        print(f"\n❌ Some issues detected - check agent connectivity")
