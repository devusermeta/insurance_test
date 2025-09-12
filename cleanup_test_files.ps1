# Insurance Project - Test Files Cleanup Script
# This script removes all test, debug, and development files

Write-Host "Starting cleanup of test and development files..." -ForegroundColor Green
Write-Host ""

# Define the base directory
$baseDir = "d:\Metakaal\insurance"
$removedCount = 0
$skippedCount = 0

# Array of test file patterns to remove
$testPatterns = @(
    "test_*.py",
    "debug_*.py", 
    "demo_*.py",
    "*_test.py",
    "*_debug.py",
    "*comprehensive_debug*",
    "*simple_debug*",
    "*assess_vision_alignment*"
)

# Array of specific files to remove
$specificFiles = @(
    "insurance_agents\comprehensive_debug.py",
    "insurance_agents\simple_debug.py",
    "insurance_agents\assess_vision_alignment.py",
    "insurance_agents\direct_test.py",
    "insurance_agents\content_extractor.py",
    "insurance_agents\format_analyzer.py",
    "insurance_agents\get_agent_id.ps1",
    "insurance_agents\restart_agents.py",
    "insurance_agents\validate_readiness.py",
    "insurance_agents\create_insurance_agents_working.py",
    "insurance_agents\cosmos_setup.py",
    "insurance_agents\check_cosmos_containers.py",
    "insurance_agents\req.txt",
    "insurance_agents\enhanced_intake_clarifier.py",
    "insurance_agents\enhanced_intake_clarifier_fixed.py",
    "insurance_agents\enhanced_document_intelligence.py",
    "insurance_agents\enhanced_claims_dashboard.py",
    "insurance_agents\STEP3_COMPLETION_SUMMARY.md",
    "insurance_agents\STEP4_COMPLETION_SUMMARY.md",
    "insurance_agents\STEP7_STEP8_COMPLETION_SUMMARY.md",
    "insurance_agents\EXECUTION_PLAN_COMPLETE_STATUS.md",
    "insurance_agents\explanation.md",
    "insurance_agents\agents\document_intelligence_agent\document_intelligence_executor_backup.py",
    "insurance_agents\agents\document_intelligence_agent\document_intelligence_executor_clean.py",
    "insurance_agents\agents\coverage_rules_engine\workflow.md",
    "insurance_agents\agents\intake_clarifier\workflow.md",
    "insurance_agents\agents\claims_orchestrator\routing.md",
    "insurance_agents\agents\claims_orchestrator\AGENT_PERSISTENCE_README.md",
    "insurance_agents\agents\claims_orchestrator\check_agent_config.py",
    "insurance_agents\agents\claims_orchestrator\manage_agents.py",
    "insurance_agents\agents\claims_orchestrator\get_agent_id.py",
    "insurance_agents\insurance_agents_registry_dashboard\test_import_context.py",
    "insurance_agents\insurance_agents_registry_dashboard\debug_storage_path.py",
    "insurance_agents\workflow_logs\workflow_steps_backup.json",
    "insurance_agents\static\employee_claims_portal.html",
    "demo_workflow.md",
    "insurance_setup.md",
    "VISION_ROADMAP.md"
)

# Array of directories to remove entirely
$testDirectories = @(
    "remote_agents\time_agent",
    "remote_agents\cosmos_query_agent", 
    "host_agent",
    "Docs",
    "workflow_logs"
)

function Remove-TestFile {
    param($filePath)
    
    if (Test-Path $filePath) {
        try {
            Remove-Item $filePath -Force
            Write-Host "Removed: $filePath" -ForegroundColor Green
            return $true
        }
        catch {
            Write-Host "Failed to remove: $filePath - $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    }
    else {
        Write-Host "File not found: $filePath" -ForegroundColor Yellow
        return $false
    }
}

function Remove-TestDirectory {
    param($dirPath)
    
    if (Test-Path $dirPath) {
        try {
            Remove-Item $dirPath -Recurse -Force
            Write-Host "Removed directory: $dirPath" -ForegroundColor Green
            return $true
        }
        catch {
            Write-Host "Failed to remove directory: $dirPath - $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    }
    else {
        Write-Host "Directory not found: $dirPath" -ForegroundColor Yellow
        return $false
    }
}

# Change to base directory
Set-Location $baseDir

Write-Host "Phase 1: Removing files by pattern..." -ForegroundColor Cyan
Write-Host ""

# Remove files by pattern
foreach ($pattern in $testPatterns) {
    Write-Host "Searching for pattern: $pattern" -ForegroundColor Blue
    $files = Get-ChildItem -Path . -Name $pattern -Recurse -File -ErrorAction SilentlyContinue
    
    foreach ($file in $files) {
        if (Remove-TestFile $file) {
            $removedCount++
        } else {
            $skippedCount++
        }
    }
}

Write-Host ""
Write-Host "Phase 2: Removing specific files..." -ForegroundColor Cyan
Write-Host ""

# Remove specific files
foreach ($file in $specificFiles) {
    $fullPath = Join-Path $baseDir $file
    if (Remove-TestFile $fullPath) {
        $removedCount++
    } else {
        $skippedCount++
    }
}

Write-Host ""
Write-Host "Phase 3: Removing test directories..." -ForegroundColor Cyan
Write-Host ""

# Remove test directories
foreach ($dir in $testDirectories) {
    $fullPath = Join-Path $baseDir $dir
    if (Remove-TestDirectory $fullPath) {
        $removedCount++
    } else {
        $skippedCount++
    }
}

Write-Host ""
Write-Host "Cleanup Summary:" -ForegroundColor Magenta
Write-Host "=================" -ForegroundColor Magenta
Write-Host "Successfully removed: $removedCount items" -ForegroundColor Green
Write-Host "Skipped/Not found: $skippedCount items" -ForegroundColor Yellow
Write-Host ""

# Show remaining essential files
Write-Host "Essential files kept:" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green
Write-Host "Core agents in insurance_agents/agents/" -ForegroundColor Green
Write-Host "Shared libraries in insurance_agents/shared/" -ForegroundColor Green  
Write-Host "Dashboard in insurance_agents/insurance_agents_registry_dashboard/" -ForegroundColor Green
Write-Host "Configuration files (.env.example, requirements.txt)" -ForegroundColor Green
Write-Host "Setup scripts (setup_cosmos_db.py, start_agents.bat)" -ForegroundColor Green
Write-Host "Azure MCP server samples (if needed)" -ForegroundColor Green
Write-Host ""

Write-Host "Cleanup completed! Your project is now clean and production-ready." -ForegroundColor Green
Write-Host ""

# Optional: Show current directory size
Write-Host "Final project structure:" -ForegroundColor Blue
Write-Host ""
Get-ChildItem -Path . -Directory | Select-Object Name, @{Name='Size(MB)';Expression={[math]::Round((Get-ChildItem $_.FullName -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB, 2)}} | Format-Table -AutoSize
