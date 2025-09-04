"""
Claims Orchestrator - Main Entry Point for Insurance Claims Processing
This is the PRIMARY agent that receives ALL user requests and dynamically 
routes tasks to specialized agents: Intake Clarifier, Document Intelligence, Coverage Rules Engine
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentThread, ThreadMessage, ThreadRun
from azure.identity import DefaultAzureCredential

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClaimsOrchestrator:
    """
    Main Claims Orchestrator Agent
    - Receives ALL user requests
    - Analyzes request type and complexity  
    - Routes tasks to appropriate specialized agents
    - Coordinates multi-agent workflows
    - Returns consolidated responses to users
    """
    
    def __init__(self):
        """Initialize the Claims Orchestrator with Azure AI Foundry connection"""
        
        # Azure AI Foundry configuration
        self.project_client = AIProjectClient.from_connection_string(
            conn_str=f"https://eastus.api.azureml.ms/agents/v1.0/subscriptions/{os.getenv('AZURE_AI_AGENT_SUBSCRIPTION_ID')}/resourceGroups/{os.getenv('AZURE_AI_AGENT_RESOURCE_GROUP_NAME')}/providers/Microsoft.MachineLearningServices/workspaces/{os.getenv('AZURE_AI_AGENT_PROJECT_NAME')}",
            credential=DefaultAzureCredential()
        )
        
        # Agent IDs for routing
        self.agents = {
            'claims_orchestrator': os.getenv('CLAIMS_ORCHESTRATOR_AGENT_ID'),
            'intake_clarifier': os.getenv('INTAKE_CLARIFIER_AGENT_ID'),
            'document_intelligence': os.getenv('DOCUMENT_INTELLIGENCE_AGENT_ID'),
            'coverage_rules_engine': os.getenv('COVERAGE_RULES_ENGINE_AGENT_ID')
        }
        
        # Specialized agent capabilities for smart routing
        self.specialist_capabilities = {
            'intake_clarifier': {
                'keywords': ['file claim', 'new claim', 'start claim', 'submit claim', 'create claim', 
                           'initial claim', 'first report', 'incident report', 'fraud check', 'validate'],
                'specialization': 'New claim intake, validation, initial processing, and fraud detection',
                'handles': ['claim filing', 'fraud detection', 'initial validation', 'data collection']
            },
            'document_intelligence': {
                'keywords': ['photo', 'document', 'image', 'analyze photo', 'extract data', 'damage photo',
                           'medical report', 'police report', 'receipt', 'invoice', 'estimate', 'scan'],
                'specialization': 'Document analysis, photo damage assessment, data extraction from images/PDFs',
                'handles': ['damage assessment', 'document processing', 'image analysis', 'data extraction']
            },
            'coverage_rules_engine': {
                'keywords': ['coverage', 'policy', 'covered', 'eligible', 'deductible', 'limit', 'benefits',
                           'policy terms', 'what is covered', 'insurance rules', 'payout', 'settlement'],
                'specialization': 'Policy coverage evaluation, eligibility determination, settlement calculations',
                'handles': ['coverage analysis', 'policy interpretation', 'eligibility checks', 'settlement calculation']
            }
        }
        
        logger.info("Claims Orchestrator initialized successfully")
        self._log_agent_status()
    
    def _log_agent_status(self):
        """Log the status of all available agents"""
        logger.info("=== AGENT REGISTRY STATUS ===")
        for agent_type, agent_id in self.agents.items():
            status = "✅ Available" if agent_id else "❌ Not Configured"
            logger.info(f"{agent_type.replace('_', ' ').title()}: {status} (ID: {agent_id})")
    
    def analyze_request(self, user_message: str) -> Dict[str, Any]:
        """
        Analyze user request to determine routing strategy
        Returns routing decision with confidence scores
        """
        
        user_message_lower = user_message.lower()
        
        # Score each specialist agent based on keyword matches
        routing_scores = {}
        
        for agent_type, info in self.specialist_capabilities.items():
            score = 0
            matched_keywords = []
            
            # Check for keyword matches
            for keyword in info['keywords']:
                if keyword in user_message_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            routing_scores[agent_type] = {
                'score': score,
                'matched_keywords': matched_keywords,
                'specialization': info['specialization'],
                'handles': info['handles']
            }
        
        # Determine routing strategy
        best_agent = max(routing_scores, key=lambda x: routing_scores[x]['score'])
        best_score = routing_scores[best_agent]['score']
        
        # Analyze complexity - multiple keywords might indicate need for coordination
        total_keywords = sum(len(info['matched_keywords']) for info in routing_scores.values())
        agents_with_matches = sum(1 for info in routing_scores.values() if info['score'] > 0)
        
        routing_decision = {
            'primary_agent': best_agent if best_score > 0 else None,
            'confidence': best_score,
            'complexity': 'high' if agents_with_matches > 1 or total_keywords > 3 else 'medium' if best_score > 1 else 'low',
            'multi_agent_needed': agents_with_matches > 1,
            'all_scores': {k: v['score'] for k, v in routing_scores.items()},
            'routing_analysis': routing_scores
        }
        
        return routing_decision
    
    def route_to_specialist(self, agent_type: str, user_message: str, context: Dict = None) -> Dict[str, Any]:
        """
        Route a task to a specific specialist agent
        Returns the agent's response
        """
        
        agent_id = self.agents.get(agent_type)
        if not agent_id:
            return {
                'success': False,
                'error': f"Agent {agent_type} not available",
                'agent_type': agent_type
            }
        
        try:
            logger.info(f"🎯 Routing task to {agent_type} (ID: {agent_id})")
            
            # Create a new thread for this interaction
            thread = self.project_client.agents.create_thread()
            
            # Add context to the message if provided
            enhanced_message = user_message
            if context:
                enhanced_message = f"Context: {context}\n\nUser Request: {user_message}"
            
            # Add user message to thread
            message = self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=enhanced_message
            )
            
            # Run the specialist agent
            run = self.project_client.agents.create_run(
                thread_id=thread.id,
                agent_id=agent_id
            )
            
            # Wait for completion (simplified for demo)
            # In production, you'd implement proper polling/webhooks
            logger.info(f"✅ Task routed successfully to {agent_type}")
            
            return {
                'success': True,
                'agent_type': agent_type,
                'thread_id': thread.id,
                'run_id': run.id,
                'message': f"Task successfully routed to {agent_type}",
                'specialization': self.specialist_capabilities[agent_type]['specialization']
            }
            
        except Exception as e:
            logger.error(f"❌ Error routing to {agent_type}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'agent_type': agent_type
            }
    
    def orchestrate_claim_processing(self, user_message: str) -> Dict[str, Any]:
        """
        Main orchestration method - receives user request and coordinates response
        This is the primary entry point for ALL insurance claim requests
        """
        
        logger.info(f"📨 INCOMING REQUEST: {user_message}")
        
        # Step 1: Analyze the request
        routing_decision = self.analyze_request(user_message)
        
        logger.info(f"🧠 ROUTING ANALYSIS:")
        logger.info(f"   Primary Agent: {routing_decision['primary_agent']}")
        logger.info(f"   Confidence: {routing_decision['confidence']} keyword matches")
        logger.info(f"   Complexity: {routing_decision['complexity']}")
        logger.info(f"   Multi-Agent Needed: {routing_decision['multi_agent_needed']}")
        
        # Step 2: Execute routing strategy
        responses = []
        
        if routing_decision['primary_agent']:
            # Route to primary specialist
            primary_response = self.route_to_specialist(
                routing_decision['primary_agent'], 
                user_message
            )
            responses.append(primary_response)
            
            # If complex request, might need additional agents
            if routing_decision['multi_agent_needed']:
                logger.info("🔄 Complex request detected - analyzing for additional agents needed")
                
                # Route to additional agents that had keyword matches
                for agent_type, analysis in routing_decision['routing_analysis'].items():
                    if agent_type != routing_decision['primary_agent'] and analysis['score'] > 0:
                        logger.info(f"🎯 Additional routing to {agent_type} (score: {analysis['score']})")
                        additional_response = self.route_to_specialist(agent_type, user_message, {
                            'primary_agent': routing_decision['primary_agent'],
                            'coordination_mode': True
                        })
                        responses.append(additional_response)
        
        else:
            # No clear match - handle with orchestrator directly
            logger.info("🤔 No clear specialist match - handling with Claims Orchestrator")
            responses.append({
                'success': True,
                'agent_type': 'claims_orchestrator',
                'message': 'Request handled by Claims Orchestrator - general inquiry',
                'specialization': 'General claim coordination and workflow management'
            })
        
        # Step 3: Consolidate response
        result = {
            'timestamp': datetime.now().isoformat(),
            'original_request': user_message,
            'routing_decision': routing_decision,
            'agent_responses': responses,
            'coordination_summary': self._generate_coordination_summary(routing_decision, responses)
        }
        
        logger.info(f"✅ REQUEST COMPLETED - {len(responses)} agent(s) involved")
        return result
    
    def _generate_coordination_summary(self, routing_decision: Dict, responses: List[Dict]) -> str:
        """Generate a summary of how the request was coordinated"""
        
        successful_routes = [r for r in responses if r.get('success')]
        agent_types = [r['agent_type'] for r in successful_routes]
        
        if len(successful_routes) == 1:
            agent = successful_routes[0]['agent_type']
            return f"Request routed to {agent} for specialized handling"
        elif len(successful_routes) > 1:
            agents = ', '.join(agent_types)
            return f"Complex request coordinated across multiple agents: {agents}"
        else:
            return "Request handled directly by Claims Orchestrator"
    
    def demonstrate_orchestration(self):
        """Demonstrate the orchestration capabilities with various scenarios"""
        
        print("\n" + "="*80)
        print("🎯 CLAIMS ORCHESTRATOR - DYNAMIC ROUTING DEMONSTRATION")
        print("="*80)
        
        # Show current agent status
        print(f"\n📋 AVAILABLE AGENTS:")
        for agent_type, agent_id in self.agents.items():
            status = "✅ Available" if agent_id else "❌ Not Configured"
            print(f"   {agent_type.replace('_', ' ').title()}: {status}")
        
        print(f"\n🎬 DEMONSTRATION SCENARIOS:")
        print("-" * 40)
        
        test_scenarios = [
            "I want to file a new car insurance claim for yesterday's accident",
            "Can you analyze this damage photo from my vehicle collision?",
            "What does my auto policy cover for comprehensive damage?", 
            "I need to submit a complex commercial liability claim with multiple vehicles and medical reports",
            "Extract information from this police accident report and check coverage",
            "File a new claim and verify if this looks like potential fraud",
            "Calculate my settlement amount based on policy limits and damage assessment"
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n--- SCENARIO {i} ---")
            print(f"📝 Request: '{scenario}'")
            
            result = self.orchestrate_claim_processing(scenario)
            
            print(f"🎯 Routing Result:")
            print(f"   Primary Agent: {result['routing_decision']['primary_agent']}")
            print(f"   Complexity: {result['routing_decision']['complexity']}")
            print(f"   Agents Involved: {len(result['agent_responses'])}")
            print(f"   Coordination: {result['coordination_summary']}")
            
            # Show successful routes
            for response in result['agent_responses']:
                if response.get('success'):
                    print(f"   ✅ {response['agent_type']}: {response.get('specialization', 'N/A')}")
                else:
                    print(f"   ❌ {response['agent_type']}: {response.get('error', 'Unknown error')}")

def main():
    """Main demonstration function"""
    
    print("🚀 INSURANCE CLAIMS PROCESSING SYSTEM")
    print("Claims Orchestrator - Dynamic Agent Routing")
    print("=" * 60)
    
    try:
        # Initialize the Claims Orchestrator
        orchestrator = ClaimsOrchestrator()
        
        # Run demonstration
        orchestrator.demonstrate_orchestration()
        
        print(f"\n🎉 KEY FEATURES DEMONSTRATED:")
        print(f"✅ Claims Orchestrator as main entry point")
        print(f"✅ Dynamic routing to specialist agents") 
        print(f"✅ Multi-agent coordination for complex requests")
        print(f"✅ Azure AI Foundry integration")
        print(f"✅ Intelligent request analysis and routing")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {str(e)}")
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
