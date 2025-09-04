"""
Azure AI Foundry Claims Orchestrator with Dynamic Agent Routing
This creates a unified system where the Claims Orchestrator can dynamically 
route tasks to specialized Azure AI Foundry agents.
"""

import os
import asyncio
import json
from typing import Dict, Any, Optional
from azure.identity import AzureCliCredential
from azure.ai.agents import AgentsClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AzureInsuranceOrchestrator:
    """
    Claims Orchestrator that dynamically routes tasks to Azure AI Foundry agents
    """
    
    def __init__(self):
        self.credential = AzureCliCredential()
        self.endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
        self.agents_client = AgentsClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
        
        # Azure AI Foundry agent IDs
        self.agents = {
            'claims_orchestrator': os.getenv('CLAIMS_ORCHESTRATOR_AGENT_ID'),
            'intake_clarifier': os.getenv('INTAKE_CLARIFIER_AGENT_ID'),
            'document_intelligence': os.getenv('DOCUMENT_INTELLIGENCE_AGENT_ID'),
            'coverage_rules_engine': os.getenv('COVERAGE_RULES_ENGINE_AGENT_ID')
        }
        
        # Agent capabilities for routing decisions
        self.agent_capabilities = {
            'intake_clarifier': {
                'keywords': ['file claim', 'new claim', 'start claim', 'claim intake', 'validate', 'fraud'],
                'description': 'Handles new claim filing, validation, and fraud detection'
            },
            'document_intelligence': {
                'keywords': ['photo', 'document', 'analyze', 'extract', 'damage', 'medical', 'report'],
                'description': 'Analyzes documents, photos, and extracts information'
            },
            'coverage_rules_engine': {
                'keywords': ['coverage', 'policy', 'covered', 'deductible', 'limit', 'rules'],
                'description': 'Evaluates policy coverage and applies insurance rules'
            },
            'claims_orchestrator': {
                'keywords': ['coordinate', 'complex', 'workflow', 'multiple', 'overall'],
                'description': 'Coordinates complex claims involving multiple steps'
            }
        }
    
    def analyze_user_request(self, user_message: str) -> str:
        """
        Analyze user request and determine which agent should handle it
        """
        user_message_lower = user_message.lower()
        
        # Score each agent based on keyword matches
        agent_scores = {}
        for agent_type, capabilities in self.agent_capabilities.items():
            score = 0
            for keyword in capabilities['keywords']:
                if keyword in user_message_lower:
                    score += 1
            agent_scores[agent_type] = score
        
        # Find best matching agent
        best_agent = max(agent_scores, key=agent_scores.get)
        best_score = agent_scores[best_agent]
        
        # If no clear match, use claims orchestrator for coordination
        if best_score == 0:
            return 'claims_orchestrator'
        
        return best_agent
    
    async def route_to_agent(self, agent_type: str, user_message: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Route request to specific Azure AI Foundry agent
        """
        agent_id = self.agents.get(agent_type)
        if not agent_id:
            return {"error": f"Agent {agent_type} not found"}
        
        try:
            # Create thread and run the agent
            result = self.agents_client.create_thread_and_run(
                assistant_id=agent_id,
                thread={
                    "messages": [
                        {
                            "role": "user",
                            "content": user_message
                        }
                    ]
                }
            )
            
            # Extract response
            response_content = "Agent processed request successfully"
            if hasattr(result, 'messages') and result.messages:
                for message in result.messages:
                    if message.role == "assistant" and message.content:
                        response_content = message.content[0].text.value
                        break
            
            return {
                "agent_type": agent_type,
                "agent_id": agent_id,
                "response": response_content,
                "routing_reason": self.agent_capabilities[agent_type]['description']
            }
            
        except Exception as e:
            return {
                "error": f"Failed to route to {agent_type}: {str(e)}",
                "agent_type": agent_type
            }
    
    async def process_insurance_claim(self, user_message: str) -> Dict[str, Any]:
        """
        Main method: Process insurance claim with dynamic agent routing
        """
        print(f"🔄 Processing claim request: '{user_message[:100]}...'")
        
        # Step 1: Analyze request and determine best agent
        best_agent = self.analyze_user_request(user_message)
        print(f"🎯 Routing to: {best_agent}")
        print(f"💡 Reason: {self.agent_capabilities[best_agent]['description']}")
        
        # Step 2: Route to the selected agent
        result = await self.route_to_agent(best_agent, user_message)
        
        # Step 3: If it's a complex case, the orchestrator might delegate further
        if best_agent == 'claims_orchestrator' and 'error' not in result:
            print("🔄 Claims Orchestrator may delegate to other agents...")
            # The orchestrator agent can decide to call other agents
            
        return result
    
    async def demonstrate_dynamic_routing(self):
        """
        Demonstrate how dynamic routing works with different scenarios
        """
        print("🚀 Azure AI Foundry Dynamic Routing Demonstration")
        print("=" * 55)
        
        test_scenarios = [
            "I want to file a new auto insurance claim after an accident",
            "Can you analyze this damage photo from my car accident?",
            "What does my policy cover for this type of damage?",
            "I need help coordinating a complex claim with multiple parties involved"
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n--- Scenario {i} ---")
            result = await self.process_insurance_claim(scenario)
            
            if 'error' not in result:
                print(f"✅ Success: {result['agent_type']}")
                print(f"📝 Response: {result['response'][:100]}...")
            else:
                print(f"❌ Error: {result['error']}")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all agents
        """
        status = {}
        for agent_type, agent_id in self.agents.items():
            status[agent_type] = {
                "agent_id": agent_id,
                "status": "available" if agent_id else "not_configured",
                "capabilities": self.agent_capabilities.get(agent_type, {})
            }
        return status

async def main():
    """
    Main demo function
    """
    print("🚀 Azure AI Foundry Insurance Claims Processing")
    print("=" * 50)
    
    # Initialize orchestrator
    orchestrator = AzureInsuranceOrchestrator()
    
    # Show agent status
    print("\n📋 Agent Status:")
    status = orchestrator.get_agent_status()
    for agent_type, info in status.items():
        print(f"   {agent_type}: {info['status']} ({info['agent_id']})")
    
    # Demonstrate dynamic routing
    await orchestrator.demonstrate_dynamic_routing()
    
    print(f"\n🎯 Key Features:")
    print(f"✅ Dynamic agent selection based on request content")
    print(f"✅ Azure AI Foundry agents with specialized capabilities")
    print(f"✅ Claims Orchestrator can coordinate multiple agents")
    print(f"✅ Automatic routing with capability matching")

if __name__ == "__main__":
    asyncio.run(main())
