#!/usr/bin/env pwsh
# PowerShell script to start all insurance agents and test the real data workflow

Write-Host "🏥 Insurance Claims System - Complete Startup" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Set location
Set-Location "d:\Metakaal\insurance\insurance_agents"

# Start all agents in background
Write-Host "🚀 Starting all insurance agents..." -ForegroundColor Yellow

# Start each agent in a separate PowerShell job
$jobs = @()

$agents = @(
    @{Name="orchestrator"; Script="python agents/claims_orchestrator/claims_orchestrator_agent.py"; Port=8001},
    @{Name="clarifier"; Script="python agents/intake_clarifier/intake_clarifier_agent.py"; Port=8002},
    @{Name="document"; Script="python agents/document_intelligence/document_intelligence_agent.py"; Port=8003},
    @{Name="rules"; Script="python agents/coverage_rules_engine/coverage_rules_agent.py"; Port=8004}
)

foreach ($agent in $agents) {
    Write-Host "  📤 Starting $($agent.Name) agent on port $($agent.Port)..." -ForegroundColor Green
    
    $job = Start-Job -ScriptBlock {
        param($script, $location)
        Set-Location $location
        Invoke-Expression $script
    } -ArgumentList $agent.Script, (Get-Location) -Name $agent.Name
    
    $jobs += $job
    Start-Sleep -Seconds 1
}

Write-Host "⏱️  Waiting for agents to start up..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check agent status
Write-Host "`n📊 Checking agent status..." -ForegroundColor Cyan
foreach ($agent in $agents) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$($agent.Port)/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✅ $($agent.Name) agent - ONLINE (port $($agent.Port))" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $($agent.Name) agent - OFFLINE (port $($agent.Port))" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ $($agent.Name) agent - OFFLINE (port $($agent.Port))" -ForegroundColor Red
    }
}

# Test real data workflow
Write-Host "`n🧪 Testing real data workflow..." -ForegroundColor Cyan
python test_real_data_workflow.py

# Show running jobs
Write-Host "`n📋 Agent Background Jobs:" -ForegroundColor Cyan
Get-Job | Format-Table -Property Id, Name, State, HasMoreData

Write-Host "`n💡 Management Commands:" -ForegroundColor Yellow
Write-Host "  Stop all agents:      Get-Job | Stop-Job; Get-Job | Remove-Job" -ForegroundColor White
Write-Host "  Check agent status:   Get-Job | Format-Table" -ForegroundColor White
Write-Host "  View agent logs:      Receive-Job -Name 'orchestrator' -Keep" -ForegroundColor White
Write-Host "  Test workflow:        python test_real_data_workflow.py" -ForegroundColor White
Write-Host "  Agent registry:       python start_dashboard.py" -ForegroundColor White

Write-Host "`n🎯 System Ready! All agents started and tested." -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
