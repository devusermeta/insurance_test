@echo off
echo 🔇 Starting Insurance Agents with Reduced Logging
echo ====================================================

cd /d "d:\Metakaal\insurance\insurance_agents"

REM Set environment to reduce logging
set UVICORN_LOG_LEVEL=warning
set PYTHONPATH=d:\Metakaal\insurance\insurance_agents

echo 🚀 Starting agents in separate windows...

REM Start each agent in a new window with reduced logging
start "Claims Orchestrator" cmd /k "cd agents\claims_orchestrator && python __main__.py"
timeout /t 3 /nobreak > nul

start "Intake Clarifier" cmd /k "cd agents\intake_clarifier && python __main__.py" 
timeout /t 3 /nobreak > nul

start "Document Intelligence" cmd /k "cd agents\document_intelligence && python __main__.py"
timeout /t 3 /nobreak > nul

start "Coverage Rules Engine" cmd /k "cd agents\coverage_rules_engine && python __main__.py"
timeout /t 3 /nobreak > nul

echo ✅ All agents started with reduced logging!
echo 💡 HTTP access logs should now be minimized
echo 📊 Start dashboard: python start_dashboard.py
echo.
pause
