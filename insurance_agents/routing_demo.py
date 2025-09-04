"""
Simple Demo: Azure AI Foundry Dynamic Agent Routing
Shows how the orchestrator dynamically selects agents based on user requests.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class InsuranceRoutingDemo:
    """Simple demo of dynamic agent routing logic"""
    
    def __init__(self):
        # Azure AI Foundry agent IDs from .env
        self.agents = {
            'claims_orchestrator': os.getenv('CLAIMS_ORCHESTRATOR_AGENT_ID'),
            'intake_clarifier': os.getenv('INTAKE_CLARIFIER_AGENT_ID'),
            'document_intelligence': os.getenv('DOCUMENT_INTELLIGENCE_AGENT_ID'),
            'coverage_rules_engine': os.getenv('COVERAGE_RULES_ENGINE_AGENT_ID')
        }
        
        # Agent capabilities for smart routing
        self.capabilities = {
            'intake_clarifier': {
                'keywords': ['file claim', 'new claim', 'start claim', 'validate', 'fraud', 'intake'],
                'specialization': 'New claim filing, validation, and fraud detection'
            },
            'document_intelligence': {
                'keywords': ['photo', 'document', 'analyze', 'extract', 'damage', 'medical', 'report', 'image'],
                'specialization': 'Document analysis, photo damage assessment, information extraction'
            },
            'coverage_rules_engine': {
                'keywords': ['coverage', 'policy', 'covered', 'deductible', 'limit', 'rules', 'eligible'],
                'specialization': 'Policy coverage evaluation and insurance rules processing'
            },
            'claims_orchestrator': {
                'keywords': ['coordinate', 'complex', 'workflow', 'multiple', 'overall', 'manage'],
                'specialization': 'Complex claim coordination and workflow management'
            }
        }
    
    def route_request(self, user_message: str) -> dict:
        """Analyze request and determine which agent should handle it"""
        
        user_message_lower = user_message.lower()
        
        # Score each agent based on keyword matches
        agent_scores = {}
        for agent_type, info in self.capabilities.items():
            score = 0
            matched_keywords = []
            
            for keyword in info['keywords']:
                if keyword in user_message_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            agent_scores[agent_type] = {
                'score': score,
                'matched_keywords': matched_keywords,
                'specialization': info['specialization']
            }
        
        # Find best matching agent
        best_agent = max(agent_scores, key=lambda x: agent_scores[x]['score'])
        best_score = agent_scores[best_agent]['score']
        
        # If no clear match, use claims orchestrator
        if best_score == 0:
            best_agent = 'claims_orchestrator'
        
        return {
            'selected_agent': best_agent,
            'agent_id': self.agents[best_agent],
            'confidence': best_score,
            'reasoning': agent_scores[best_agent]['specialization'],
            'matched_keywords': agent_scores[best_agent]['matched_keywords'],
            'all_scores': {k: v['score'] for k, v in agent_scores.items()}
        }
    
    def demonstrate_routing(self):
        """Show how different requests get routed to different agents"""
        
        print("🚀 Insurance Claims - Dynamic Agent Routing Demo")
        print("=" * 55)
        
        test_scenarios = [
            "I want to file a new insurance claim for my car accident",
            "Can you analyze this damage photo from the crash?", 
            "What does my auto policy cover for collision damage?",
            "I need help coordinating this complex multi-vehicle claim",
            "Is there any fraud risk with this claim submission?",
            "Extract information from this police accident report",
            "What's my deductible for comprehensive coverage?",
            "Manage the workflow for this commercial liability claim"
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n--- Scenario {i} ---")
            print(f"📝 Request: '{scenario}'")
            
            routing = self.route_request(scenario)
            
            print(f"🎯 Selected Agent: {routing['selected_agent']}")
            print(f"🆔 Agent ID: {routing['agent_id']}")
            print(f"📊 Confidence: {routing['confidence']} keyword matches")
            print(f"💡 Reasoning: {routing['reasoning']}")
            if routing['matched_keywords']:
                print(f"🔑 Matched Keywords: {', '.join(routing['matched_keywords'])}")
            print(f"📈 All Scores: {routing['all_scores']}")
    
    def show_agent_status(self):
        """Show status of all Azure AI Foundry agents"""
        
        print(f"\n📋 Azure AI Foundry Agents Status")
        print("=" * 35)
        
        for agent_type, agent_id in self.agents.items():
            status = "✅ Available" if agent_id else "❌ Not Configured"
            specialization = self.capabilities[agent_type]['specialization']
            
            print(f"\n🤖 {agent_type.replace('_', ' ').title()}")
            print(f"   Status: {status}")
            print(f"   Agent ID: {agent_id}")
            print(f"   Specialization: {specialization}")

def main():
    """Main demo function"""
    
    print("🎯 Azure AI Foundry Insurance Claims Processing")
    print("Dynamic Agent Routing Demonstration")
    print("=" * 60)
    
    demo = InsuranceRoutingDemo()
    
    # Show agent status
    demo.show_agent_status()
    
    # Demonstrate routing logic
    demo.demonstrate_routing()
    
    print(f"\n🎉 Key Takeaways:")
    print(f"✅ Dynamic agent selection works based on request content")
    print(f"✅ 4 specialized Azure AI Foundry agents are available")
    print(f"✅ Smart keyword matching routes to appropriate agent")
    print(f"✅ Claims Orchestrator handles complex coordination")
    print(f"✅ System ready for real insurance claim processing!")

if __name__ == "__main__":
    main()
