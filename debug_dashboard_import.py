#!/usr/bin/env python3
"""
Test Dashboard Import Issue
Check why workflow_logger import is failing in the dashboard
"""

import os
import sys
from pathlib import Path

print("🧪 Testing Dashboard Import Issue...")
print(f"📍 Current working directory: {os.getcwd()}")
print(f"📍 Script location: {__file__}")

# Simulate the dashboard's import setup
dashboard_dir = Path(__file__).parent / "insurance_agents" / "insurance_agents_registry_dashboard"
parent_dir = dashboard_dir.parent
sys.path.append(str(parent_dir))

print(f"📍 Added to sys.path: {parent_dir}")
print(f"📍 Path exists: {parent_dir.exists()}")

# List what's in the parent directory
print(f"\n📋 Contents of {parent_dir}:")
if parent_dir.exists():
    for item in parent_dir.iterdir():
        print(f"   {'📁' if item.is_dir() else '📄'} {item.name}")

# Check if shared directory exists
shared_dir = parent_dir / "shared"
print(f"\n📋 Shared directory: {shared_dir}")
print(f"📍 Shared exists: {shared_dir.exists()}")

if shared_dir.exists():
    print(f"📋 Contents of shared/:")
    for item in shared_dir.iterdir():
        print(f"   {'📁' if item.is_dir() else '📄'} {item.name}")

# Try the import
print(f"\n🧪 Attempting import...")
try:
    from shared.workflow_logger import workflow_logger, WorkflowStepType, WorkflowStepStatus
    print("✅ SUCCESS: imported real workflow_logger")
    print(f"📊 workflow_logger type: {type(workflow_logger)}")
    
    # Test getting recent steps
    steps = workflow_logger.get_all_recent_steps(5)
    print(f"📊 Recent steps available: {len(steps)}")
    
except ImportError as e:
    print(f"❌ IMPORT FAILED: {e}")
    print("🔍 Let's debug this step by step...")
    
    # Check each step of the import
    try:
        import shared
        print("✅ 'shared' module imported")
        print(f"📍 shared location: {shared.__file__}")
    except ImportError as e:
        print(f"❌ 'shared' module failed: {e}")
    
    try:
        from shared import workflow_logger as wl_module
        print("✅ 'shared.workflow_logger' module imported")
        print(f"📍 workflow_logger location: {wl_module.__file__}")
    except ImportError as e:
        print(f"❌ 'shared.workflow_logger' module failed: {e}")

except Exception as e:
    print(f"❌ OTHER ERROR: {e}")

print("\n🏁 Import test complete")
