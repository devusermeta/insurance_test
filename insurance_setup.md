# Insurance Agents Setup
# There is ONLY ONE virtual environment at insurance_agents\.venv

# Step 1: Activate environment and set PYTHONPATH (always required first)
cd insurance_agents;.\.venv\Scripts\activate;$env:PYTHONPATH = "D:\Metakaal\insurance\insurance_agents"

cd D:\Metakaal\insurance\insurance_agents\insurance_agents_registry_dashboard
cd D:\Metakaal\insurance\azure-cosmos-mcp-server-samples\python


# Option 1: Run as modules (recommended)
python -m agents.claims_orchestrator
python -m agents.intake_clarifier
python -m agents.document_intelligence
python -m agents.coverage_rules_engine
python -m agents.communication_agent

# Option 2: Run __main__.py directly (now also works)
python agents/claims_orchestrator/__main__.py
python agents/intake_clarifier/__main__.py
python agents/document_intelligence/__main__.py
python agents/coverage_rules_engine/__main__.py
python agents/communication_agent/__main__.py