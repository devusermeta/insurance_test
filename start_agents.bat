@echo off
echo 🤖 Starting All Insurance Agents
echo ================================================================

set PYTHONPATH=D:\Metakaal\insurance\insurance_agents
cd /d "D:\Metakaal\insurance\insurance_agents"
call .venv\Scripts\activate.bat

echo 🚀 Choose which agents to start:
echo 1. Start all agents (4 terminals)
echo 2. Start Claims Orchestrator only
echo 3. Start Document Intelligence only
echo 4. Start Coverage Rules Engine only
echo 5. Start Intake Clarifier only

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo 🎭 Starting Claims Orchestrator...
    start "Claims Orchestrator" cmd /k "python -m agents.claims_orchestrator"
    timeout /t 2 /nobreak >nul
    
    echo ⚖️ Starting Coverage Rules Engine...
    start "Coverage Rules Engine" cmd /k "python -m agents.coverage_rules_engine"
    timeout /t 2 /nobreak >nul
    
    echo 📄 Starting Document Intelligence...
    start "Document Intelligence" cmd /k "python -m agents.document_intelligence"
    timeout /t 2 /nobreak >nul
    
    echo 🔍 Starting Intake Clarifier...
    start "Intake Clarifier" cmd /k "python -m agents.intake_clarifier"
    
    echo ✅ All agents started!
) else if "%choice%"=="2" (
    echo 🎭 Starting Claims Orchestrator...
    python -m agents.claims_orchestrator
) else if "%choice%"=="3" (
    echo 📄 Starting Document Intelligence...
    python -m agents.document_intelligence
) else if "%choice%"=="4" (
    echo ⚖️ Starting Coverage Rules Engine...
    python -m agents.coverage_rules_engine
) else if "%choice%"=="5" (
    echo 🔍 Starting Intake Clarifier...
    python -m agents.intake_clarifier
) else (
    echo ❌ Invalid choice
    pause
)

pause
