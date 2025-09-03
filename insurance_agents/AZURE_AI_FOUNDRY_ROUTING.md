# Dynamic Azure AI Foundry Agent Routing System

## Overview
This system provides **dynamic agent selection and routing** similar to the `host_agent`, but for **Azure AI Foundry agents**. It automatically discovers agents, analyzes their capabilities, and routes user requests to the most appropriate agent.

## How It Works

### 1. **Agent Discovery** 
```python
# Discovers all Azure AI Foundry agents in your project
discovered_agents = await router.discover_agents()

# Example discovered agents:
{
    "asst_claims_orch_123": {
        "name": "Claims Orchestrator",
        "capabilities": ["workflow_orchestration", "coordination"],
        "endpoint": "https://your-project.cognitiveservices.azure.com/agents/asst_claims_orch_123"
    },
    "asst_intake_456": {
        "name": "Intake Clarifier", 
        "capabilities": ["claim_clarification", "fraud_detection"],
        "endpoint": "https://your-project.cognitiveservices.azure.com/agents/asst_intake_456"
    }
}
```

### 2. **Dynamic Routing**
```python
# User makes a request
user_request = "I need to analyze this damage assessment document"

# System automatically routes to best agent
decision = await router.route_request(user_request)

# Result:
{
    "selected_agent": "asst_doc_intel_789",
    "confidence": 0.95,
    "reasoning": "matches document analysis; has OCR capabilities",
    "fallback_agents": ["asst_claims_orch_123"]
}
```

### 3. **Execution with Thread Management**
```python
# Execute with selected agent (automatic thread management)
result = await router.execute_with_agent(
    agent_id=decision.selected_agent,
    request=user_request,
    thread_id=existing_thread_id  # Maintains conversation context
)
```

## Registry Dashboard Integration

### **API Endpoints**

1. **`GET /api/agents`** - Get all discovered Azure AI Foundry agents
2. **`POST /api/route-request`** - Get routing decision for a request
3. **`POST /api/process-claim`** - Process claim with dynamic routing
4. **`GET /api/agent-performance`** - Agent performance analytics
5. **`GET /api/capabilities`** - Capability index for all agents

### **Example API Usage**

```javascript
// Frontend can request routing decision
const response = await fetch('/api/route-request', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        request: "Validate this auto insurance claim",
        context: {
            priority: "high",
            claim_type: "auto"
        }
    })
});

const routing = await response.json();
// Returns: best agent, confidence, reasoning
```

## Key Benefits

### ✅ **Dynamic Discovery**
- Automatically finds all Azure AI Foundry agents
- No manual configuration needed
- Agents can be added/removed without code changes

### ✅ **Intelligent Routing**
- Analyzes request content to determine needed capabilities
- Scores agents based on capability match
- Considers performance history for better decisions

### ✅ **Thread Management**
- Maintains conversation context per claim
- Same thread used for follow-up questions
- Automatic thread creation and management

### ✅ **Performance Tracking**
- Tracks agent success rates
- Adjusts routing based on performance
- Provides analytics for optimization

### ✅ **Registry Integration**
- Works with existing dashboard
- Live agent status updates
- Routing history and analytics

## Comparison with host_agent

| Feature | host_agent | Azure AI Foundry Router |
|---------|------------|-------------------------|
| Agent Discovery | Static config files | Dynamic Azure AI discovery |
| Routing Logic | Rule-based | AI-powered capability matching |
| Thread Management | Manual | Automatic Azure threads |
| Agent Hosting | Local/remote servers | Azure cloud-hosted |
| Performance Tracking | Basic | Advanced analytics |
| Scalability | Limited | Cloud-scale |

## Next Steps

1. **Install Azure AI SDK**:
   ```bash
   pip install azure-ai-projects azure-identity
   ```

2. **Set up Azure AI Foundry project**:
   - Create project in https://ai.azure.com
   - Get project endpoint and credentials

3. **Create Azure AI Foundry agents**:
   - Claims Orchestrator
   - Intake Clarifier  
   - Document Intelligence
   - Coverage Rules Engine

4. **Replace local agents** with Azure AI Foundry routing

5. **Update registry dashboard** to use new routing system

This gives you the **dynamic routing intelligence of host_agent** with the **scalability and thread management of Azure AI Foundry**!
