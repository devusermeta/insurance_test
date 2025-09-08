# 🏗️ Core Architecture
The system follows a distributed agent architecture where:

Claims Orchestrator - The main coordinator
Specialist Agents - Handle specific tasks
Dashboard - Professional interface for employees
Data Layer - Cosmos DB storage


# 📂 Key Insurance Components

1. Main Insurance Directory (insurance_agents)
Purpose: Core insurance claims processing system
Technologies: A2A Protocol, MCP Protocol, Semantic Kernel, Azure AI Foundry
Architecture: Multi-agent with orchestration pattern

2. Agent Structure (agents)

# 🎯 Claims Orchestrator (claims_orchestrator/)

Role: Main coordinator that plans workflow DAG and routes work
Port: 8001
Key Functions:
Receives claim processing requests
Plans execution workflow using DAG (Directed Acyclic Graph)
Routes work to specialist agents via A2A protocol
Monitors and coordinates the entire process

# 📋 Intake Clarifier (intake_clarifier/)

Role: Validates claim submissions for completeness and consistency
Port: 8002
Functions:
Checks required fields
Validates data consistency
Identifies missing information

# 📄 Document Intelligence (document_intelligence/)

Role: Processes documents and extracts structured data
Port: 8003
Functions:
OCR and document parsing
Extracts structured data with evidence spans
Handles medical documents, invoices, etc.

# ⚖️ Coverage Rules Engine (coverage_rules_engine/)

Role: Evaluates claims against policy rules and benefit coverage
Port: 8004
Functions:
Applies insurance policy rules
Calculates coverage amounts
Makes approve/deny/pend decisions

3. Professional Dashboard (insurance_agents_registry_dashboard/)
Purpose: Web interface for insurance employees
Features:
Claim processing interface
Agent registry management
Workflow step visualization3. Professional Dashboard (insurance_agents_registry_dashboard/)
Purpose: Web interface for insurance employees
Features:
Claim processing interface
Agent registry management
Workflow step visualization


💾 Data Layer (Docs folder contains sample data)
Cosmos DB Collections:

claims: Main claim records (OP-1001, IP-2001, etc.)
artifacts: Supporting documents and files
extractions_files: Raw extracted data
extractions_summary: Processed extraction summaries
rules_eval: Rule evaluation results
agent_runs: Agent execution logs
events: System events
threads: Communication threads


Submission: Customer submits claim (Outpatient/Inpatient) with documents
Employee Initiation: Insurance employee starts processing via dashboard
Orchestration: Claims Orchestrator receives request and plans workflow
Parallel Processing:
Intake Clarifier validates completeness
Document Intelligence extracts data
Coverage Rules Engine evaluates against policies
Decision: System provides recommendation (approve/pend/deny)