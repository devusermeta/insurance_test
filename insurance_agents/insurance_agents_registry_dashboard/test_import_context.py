#!/usr/bin/env python3
"""
Test workflow logger import from dashboard directory context
"""

import sys
import os
from pathlib import Path

# This mimics exactly what the dashboard app.py does
current_dir = os.path.dirname(__file__)
parent_dir = os.path.join(current_dir, '..')
sys.path.append(parent_dir)

print(f"🔍 Current script directory: {current_dir}")
print(f"🔍 Parent directory added to path: {os.path.abspath(parent_dir)}")
print(f"🔍 Python path entries:")
for i, path in enumerate(sys.path[:8]):
    print(f"   {i}: {path}")

# Try the exact import that dashboard does
try:
    print("\n📦 Attempting to import shared.workflow_logger...")
    from shared.workflow_logger import workflow_logger, WorkflowStepType, WorkflowStepStatus
    print("✅ Successfully imported real workflow_logger with enums")
    
    # Test getting recent steps
    steps = workflow_logger.get_all_recent_steps(50)
    print(f"✅ Retrieved {len(steps)} workflow steps")
    
    if steps:
        print("📋 Real workflow steps from dashboard context:")
        for i, step in enumerate(steps[:3]):
            print(f"   {i+1}. ID: {step['id']}, Claim: {step['claim_id']}, Type: {step['step_type']}")
    else:
        print("⚠️  No workflow steps found")
        
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("🔍 This is why dashboard uses MockWorkflowLogger!")
    
    # Show what files exist in the shared directory
    shared_path = os.path.join(parent_dir, 'shared')
    print(f"\n📁 Contents of shared directory ({shared_path}):")
    if os.path.exists(shared_path):
        for file in os.listdir(shared_path):
            print(f"   - {file}")
    else:
        print("   ❌ Shared directory doesn't exist!")
        
except Exception as e:
    print(f"❌ Error: {e}")
