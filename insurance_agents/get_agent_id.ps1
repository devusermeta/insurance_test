# PowerShell script to get existing agent ID
# Usage: .\get_agent_id.ps1

Write-Host "🔍 Getting Claims Orchestrator Agent ID..." -ForegroundColor Cyan
Write-Host "=" * 50

# Activate virtual environment and run the script
& ".\.venv\Scripts\Activate.ps1"
python "agents\claims_orchestrator\get_agent_id.py"

Write-Host ""
Write-Host "✅ Script completed!" -ForegroundColor Green
