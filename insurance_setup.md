cd insurance_agents;.\.venv\Scripts\activate;$env:PYTHONPATH = "D:\Metakaal\insurance\insurance_agents"

# Option 1: Run as modules (recommended)
python -m agents.claims_orchestrator
python -m agents.intake_clarifier
python -m agents.document_intelligence
python -m agents.coverage_rules_engine

# Option 2: Run __main__.py directly (now also works)
python agents/claims_orchestrator/__main__.py
python agents/intake_clarifier/__main__.py
python agents/document_intelligence/__main__.py
python agents/coverage_rules_engine/__main__.py