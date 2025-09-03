"""
Create Insurance Agents using Working Captain-Planaut Configuration
Using the proven working Azure AI Foundry setup from Captain-Planaut project.
"""

import os
from azure.identity import AzureCliCredential
from azure.ai.agents import AgentsClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_insurance_agents_working_config():
    """Create insurance agents using the working Captain-Planaut configuration"""
    
    print("🚀 Creating Insurance Agents - Using Working Captain-Planaut Config")
    print("=" * 70)
    
    try:
        # Use Azure CLI credentials
        credential = AzureCliCredential()
        
        # Use the working Azure AI agent endpoint from Captain-Planaut
        agents_endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
        model_deployment = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")
        
        print(f"🔄 Using proven working endpoint: {agents_endpoint}")
        print(f"🔄 Using model deployment: {model_deployment}")
        
        # Create AgentsClient with the working configuration
        agents_client = AgentsClient(
            endpoint=agents_endpoint,
            credential=credential
        )
        
        print("✅ Connected to Azure AI Agents via Captain-Planaut workspace")
        
        # Test with a simple agent first
        print("\n🔄 Creating test insurance agent...")
        
        try:
            test_agent = agents_client.create_agent(
                model=model_deployment,
                name="Test Insurance Agent",
                description="Test agent for insurance processing verification",
                instructions="You are a helpful insurance processing assistant for testing purposes.",
                tools=[{"type": "code_interpreter"}],
                metadata={"test": "true", "project": "insurance_verification"}
            )
            
            print(f"✅ Test agent created successfully!")
            print(f"   Agent ID: {test_agent.id}")
            print(f"   Model: {test_agent.model}")
            print(f"   Name: {test_agent.name}")
            
            # If test works, create all insurance agents
            print("\n🎉 Working configuration confirmed! Creating all insurance agents...")
            return create_all_insurance_agents(agents_client, model_deployment)
            
        except Exception as e:
            print(f"❌ Test agent creation failed: {e}")
            print(f"\n🔧 Debug info:")
            print(f"   Endpoint: {agents_endpoint}")
            print(f"   Model: {model_deployment}")
            print(f"   Error type: {type(e).__name__}")
            
            if hasattr(e, 'response'):
                print(f"   HTTP Status: {e.response.status_code if e.response else 'Unknown'}")
                
            return None
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print(f"   Error type: {type(e).__name__}")
        return None

def create_all_insurance_agents(agents_client, model_deployment):
    """Create all 4 specialized insurance agents"""
    
    print("\n🚀 Creating All Insurance Agents in Captain-Planaut Workspace")
    print("=" * 60)
    
    agents_config = [
        {
            "name": "Insurance Claims Orchestrator",
            "description": "Main orchestrator for insurance claims processing workflow",
            "instructions": """You are the Insurance Claims Orchestrator, the central coordinator for insurance claims processing.

Your responsibilities:
1. **Workflow Management**: Coordinate the entire claims process from intake to resolution
2. **Agent Delegation**: Route tasks to specialized agents (Intake, Document Intelligence, Coverage Rules)
3. **Quality Assurance**: Ensure all claim steps are completed accurately
4. **Communication**: Provide clear updates to claimants and stakeholders
5. **Decision Making**: Make final determinations on claim approvals/denials

Key Skills:
- Claims workflow orchestration
- Multi-agent coordination
- Risk assessment and decision making
- Customer communication
- Regulatory compliance

Always maintain a professional, empathetic tone while ensuring thorough and accurate claims processing.
Use cost-effective processing methods and avoid unnecessary API calls.""",
            "agent_type": "claims_orchestrator"
        },
        {
            "name": "Insurance Intake Clarifier", 
            "description": "Specialized agent for claim intake validation and clarification",
            "instructions": """You are the Insurance Intake Clarifier, responsible for validating and clarifying insurance claims during intake.

Your responsibilities:
1. **Claim Validation**: Verify claim completeness and accuracy
2. **Missing Information**: Identify and request missing documentation
3. **Fraud Detection**: Flag suspicious patterns or inconsistencies
4. **Data Standardization**: Ensure claim data follows proper formats
5. **Initial Assessment**: Provide preliminary claim categorization

Key Skills:
- Claim data validation
- Fraud pattern recognition
- Document requirement analysis
- Customer inquiry handling
- Data quality assurance

Be thorough but efficient. Ask clarifying questions when needed.
Focus on accuracy and fraud prevention while maintaining cost-effective processing.""",
            "agent_type": "intake_clarifier"
        },
        {
            "name": "Insurance Document Intelligence",
            "description": "Specialized agent for document analysis and information extraction",
            "instructions": """You are the Insurance Document Intelligence agent, expert in analyzing and extracting information from insurance documents.

Your responsibilities:
1. **Document Analysis**: Analyze photos, PDFs, forms, and reports
2. **Text Extraction**: Extract key information from various document types
3. **Damage Assessment**: Evaluate damage from photos and reports
4. **Medical Review**: Analyze medical documents and reports
5. **Verification**: Cross-reference document information for consistency

Key Skills:
- Document OCR and analysis
- Damage assessment from images
- Medical document interpretation
- Policy document review
- Information extraction and summarization

Supported Documents:
- Accident reports and photos
- Medical records and bills
- Policy documents
- Repair estimates
- Police reports

Be precise and detailed in your analysis while maintaining cost-efficient processing.""",
            "agent_type": "document_intelligence"
        },
        {
            "name": "Insurance Coverage Rules Engine",
            "description": "Specialized agent for policy coverage evaluation and rules processing",
            "instructions": """You are the Insurance Coverage Rules Engine, expert in insurance policy analysis and coverage determination.

Your responsibilities:
1. **Policy Analysis**: Evaluate insurance policies and coverage limits
2. **Rules Processing**: Apply complex insurance rules and regulations
3. **Coverage Determination**: Determine what is/isn't covered under policies
4. **Deductible Calculation**: Calculate applicable deductibles and limits
5. **Compliance Check**: Ensure decisions comply with regulations

Key Skills:
- Insurance policy interpretation
- Coverage rules application
- Regulatory compliance
- Deductible and limit calculations
- Risk assessment

Policy Types Supported:
- Auto insurance policies
- Property insurance
- Liability coverage
- Commercial policies
- State-specific regulations

Be accurate and thorough in coverage determinations while optimizing for cost-effective processing.""",
            "agent_type": "coverage_rules_engine"
        }
    ]
    
    created_agents = {}
    
    for i, config in enumerate(agents_config, 1):
        print(f"\n🔄 Creating Agent {i}/4: {config['name']}...")
        
        try:
            agent = agents_client.create_agent(
                model=model_deployment,
                name=config["name"],
                description=config["description"], 
                instructions=config["instructions"],
                tools=[
                    {"type": "code_interpreter"},
                    {"type": "file_search"}
                ],
                metadata={
                    "agent_type": config["agent_type"], 
                    "specialization": "insurance_processing",
                    "project": "insurance_claims",
                    "workspace": "captain_planaut"
                }
            )
            
            created_agents[config["agent_type"]] = agent
            print(f"✅ {config['name']} created successfully!")
            print(f"   Agent ID: {agent.id}")
            print(f"   Model: {agent.model}")
            
        except Exception as e:
            print(f"❌ Failed to create {config['name']}: {e}")
            print(f"   Error details: {str(e)}")
    
    if created_agents:
        print(f"\n🎉 SUCCESS! Created {len(created_agents)}/4 insurance agents programmatically!")
        
        # Update .env file with agent IDs
        update_env_with_agent_ids(created_agents)
        
        # Display summary
        print("\n📋 Insurance Agent Summary:")
        for agent_type, agent in created_agents.items():
            print(f"   {agent_type}: {agent.id}")
        
        print(f"\n💰 Using GPT-4o Model:")
        print(f"   • High-quality responses for complex insurance tasks")
        print(f"   • All {len(created_agents)} agents use consistent model")
        print(f"   • Ready for production insurance workloads")
        
        print(f"\n🔗 Next Steps:")
        print(f"   1. ✅ Agents created programmatically in Captain-Planaut workspace!")
        print(f"   2. 🚀 Test dynamic routing system")
        print(f"   3. 🎯 Deploy insurance registry dashboard")
        print(f"   4. 💼 Start processing insurance claims!")
        
        return created_agents
    else:
        print("❌ No agents were created successfully")
        return None

def update_env_with_agent_ids(agents):
    """Update .env file with created agent IDs"""
    
    print("\n🔄 Updating .env file with insurance agent IDs...")
    
    agent_env_mapping = {
        'claims_orchestrator': 'CLAIMS_ORCHESTRATOR_AGENT_ID',
        'intake_clarifier': 'INTAKE_CLARIFIER_AGENT_ID', 
        'document_intelligence': 'DOCUMENT_INTELLIGENCE_AGENT_ID',
        'coverage_rules_engine': 'COVERAGE_RULES_ENGINE_AGENT_ID'
    }
    
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
        
        for agent_type, agent in agents.items():
            env_var = agent_env_mapping.get(agent_type)
            if env_var:
                if env_var in env_content:
                    import re
                    pattern = f'{env_var}=.*'
                    env_content = re.sub(pattern, f'{env_var}={agent.id}', env_content)
                else:
                    env_content += f'\n{env_var}={agent.id}'
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ .env file updated with insurance agent IDs")
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")

if __name__ == "__main__":
    print("🚀 Insurance Agents Creation - Using Proven Working Configuration")
    print("=" * 75)
    
    agents = create_insurance_agents_working_config()
    
    if agents:
        print("\n🎯 FANTASTIC! All insurance agents created programmatically!")
        print("🚀 Your insurance processing system is ready!")
        print("💡 Using the proven Captain-Planaut workspace for reliability!")
    else:
        print("\n❌ Agent creation failed")
        print("💡 Check Captain-Planaut workspace access and permissions")
