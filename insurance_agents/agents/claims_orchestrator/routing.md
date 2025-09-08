🔄 Dynamic Routing Mechanism
The orchestrator uses multiple routing strategies:

1. Agent Discovery Service

# From agent_discovery.py
self.agent_discovery = AgentDiscoveryService(self.logger)
discovered_agents = await self.agent_discovery.discover_all_agents()


How it works:

Discovers agents by checking known endpoints:
intake_clarifier: port 8002
document_intelligence: port 8003
coverage_rules_engine: port 8004
Probes capabilities by calling agent.json endpoints
Selects best agent for each task type


2. A2A Protocol Communication
# Routes tasks via A2A protocol
clarifier_result = await self.agent_discovery.send_task_to_agent(clarifier_agent, clarifier_task)


Process Flow:

Discovery Phase: Find all available agents
Task Routing: Route specific tasks to appropriate agents
Response Handling: Process responses and aggregate results
🏗️ Complete Workflow Architecture


# Phase 1: Agent Discovery
# Discovers all available agents dynamically
discovered_agents = await self.agent_discovery.discover_all_agents()



# Phase 2: Task Dispatch
The orchestrator dispatches 3 parallel tasks:

1. Intake Clarification:
clarifier_task = {
    "description": f"Process claim {claim_id} for initial validation",
    "message": json.dumps({
        "action": "process_claim",
        "claim_id": claim_id,
        "claim_data": claim_data
    })
}

2. Document Analysis (if documents present):
doc_task = {
    "description": f"Analyze documents for claim {claim_id}",
    "message": json.dumps({
        "action": "analyze_documents",
        "claim_id": claim_id,
        "documents": documents
    })
}


3. Coverage Validation:
rules_task = {
    "description": f"Validate coverage and policy compliance for claim {claim_id}",
    "message": json.dumps({
        "action": "validate_coverage",
        "claim_data": combined_data
    })
}


# Phase 3: Decision Making
final_decision = self._make_final_decision(
    claim_data=claim_data,
    processing_results=processing_results,
    coverage_rules=coverage_rules
)

Decision Logic:

Coverage Invalid → DENIED
High Risk Score (>0.8) → DENIED
High Value (>$50k) → REQUIRES_REVIEW
All Checks Pass → APPROVED
🔧 Key Dependencies
A2A Protocol Dependencies:



🎯 Intelligent Task Routing

The orchestrator uses capability-based routing:

clarifier_agent = self.agent_discovery.select_agent_for_task(
    task_description=f"Validate and clarify insurance claim data for claim {claim_id}",
    task_type="claim_validation"
)

# Selection Process:

1. Analyze task requirements
2. Match agent capabilities
3. Select best-fit agent
4. Dispatch task with full context


🔄 Workflow Tracking
Every step is logged for audit and monitoring:
# Start workflow
workflow_logger.start_claim_processing(claim_id)

# Log each step
discovery_step_id = workflow_logger.log_discovery(...)
selection_step_id = workflow_logger.log_agent_selection(...)
dispatch_step_id = workflow_logger.log_task_dispatch(...)
response_step_id = workflow_logger.log_agent_response(...)

# Complete workflow
workflow_logger.log_completion(claim_id=claim_id, ...)




🏆 Advanced Features
1. Parallel Processing
Multiple agents can process different aspects simultaneously
Results are aggregated for final decision
2. Fallback Handling
If an agent is unavailable, the system gracefully handles failures
Workflow continues with available agents
3. Azure Integration
Can route to Azure AI Foundry agents when available
Seamlessly falls back to local A2A agents
4. Real-time Status
Dashboard integration for live workflow tracking
Detailed step-by-step progress monitoring