"""
Dynamic Agent Routing Integration Example
Shows how the Azure AI Foundry router integrates with the insurance registry dashboard
"""

import asyncio
import os
from azure_ai_foundry_router import AzureAIFoundryAgentRouter

async def main():
    """Example of dynamic agent routing in action"""
    
    # Initialize the router with your Azure AI Foundry project
    project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "https://your-project.cognitiveservices.azure.com")
    router = AzureAIFoundryAgentRouter(project_endpoint)
    
    # Step 1: Discover all Azure AI Foundry agents
    print("🔍 Discovering Azure AI Foundry agents...")
    discovered_agents = await router.discover_agents()
    
    print(f"\n📋 Found {len(discovered_agents)} agents:")
    for agent_id, agent_info in discovered_agents.items():
        print(f"  • {agent_info['name']}: {len(agent_info['capabilities'])} capabilities")
    
    # Step 2: Dynamic routing examples
    test_requests = [
        "I need to process a new insurance claim for auto damage",
        "Can you analyze this damage assessment document?", 
        "Validate this claim for potential fraud indicators",
        "Check if this claim is covered under the policy terms",
        "Extract data from this filled claim form"
    ]
    
    print(f"\n🎯 Testing dynamic routing:")
    for request in test_requests:
        print(f"\n📝 Request: {request}")
        
        # Route the request
        decision = await router.route_request(request)
        
        if decision.selected_agent:
            agent_name = discovered_agents[decision.selected_agent]['name']
            print(f"✅ Selected: {agent_name} (confidence: {decision.confidence:.2f})")
            print(f"💭 Reasoning: {decision.reasoning}")
            
            # Execute with the selected agent
            result = await router.execute_with_agent(
                agent_id=decision.selected_agent,
                request=request
            )
            
            if result["status"] == "success":
                print(f"🎉 Result: {result['response'][:100]}...")
            else:
                print(f"❌ Error: {result['error']}")
        else:
            print("⚠️ No suitable agent found")
    
    # Step 3: Get registry data for dashboard
    print(f"\n📊 Registry data for dashboard:")
    registry_data = router.get_agent_registry_data()
    
    for agent_id, data in registry_data.items():
        print(f"  • {data['name']}: {data['status']}, {len(data['capabilities'])} capabilities")
        if data.get('performance'):
            print(f"    Performance: {data['performance'].get('success_rate', 0):.1%} success rate")

if __name__ == "__main__":
    asyncio.run(main())
