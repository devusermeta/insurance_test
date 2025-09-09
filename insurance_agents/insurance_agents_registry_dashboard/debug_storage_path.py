#!/usr/bin/env python3
"""
Debug workflow logger storage file path from dashboard context
"""

import sys
import os
from pathlib import Path

# Mimic dashboard app.py setup
current_dir = os.path.dirname(__file__)
parent_dir = os.path.join(current_dir, '..')
sys.path.append(parent_dir)

print(f"🔍 Script directory: {current_dir}")
print(f"🔍 Parent directory: {os.path.abspath(parent_dir)}")

try:
    from shared.workflow_logger import workflow_logger
    print("✅ Successfully imported workflow_logger")
    
    # Check storage file path
    storage_path = workflow_logger.storage_file
    print(f"📁 Storage file path: {storage_path}")
    print(f"📁 Storage file exists: {storage_path.exists()}")
    print(f"📁 Storage file absolute path: {storage_path.absolute()}")
    
    if storage_path.exists():
        # Read the file directly with proper encoding
        with open(storage_path, 'r', encoding='utf-8', errors='ignore') as f:
            import json
            data = json.load(f)
            steps_count = len(data.get('workflow_steps', []))
            print(f"📊 Steps in storage file: {steps_count}")
            
            if steps_count > 0:
                print("📋 Sample steps from storage file:")
                for i, step in enumerate(data['workflow_steps'][:3]):
                    print(f"   {i+1}. Claim: {step['claim_id']}, Type: {step['step_type']}")
        
        # Now try the workflow_logger method
        logger_steps = workflow_logger.get_all_recent_steps(50)
        print(f"📊 Steps from workflow_logger.get_all_recent_steps(): {len(logger_steps)}")
        
        if len(logger_steps) != steps_count:
            print("🚨 MISMATCH! File has different count than logger method!")
        
    else:
        print("❌ Storage file doesn't exist!")
        
        # Check if the workflow_logs directory exists
        workflow_logs_dir = Path.cwd() / "workflow_logs"
        print(f"📁 Looking for workflow_logs at: {workflow_logs_dir}")
        print(f"📁 workflow_logs exists: {workflow_logs_dir.exists()}")
        
        # Check parent directories
        for parent in [Path.cwd(), Path.cwd().parent, Path.cwd().parent.parent]:
            wl_dir = parent / "workflow_logs"
            if wl_dir.exists():
                json_file = wl_dir / "workflow_steps.json"
                print(f"✅ Found workflow_logs at: {wl_dir}")
                print(f"📁 JSON file exists: {json_file.exists()}")
                if json_file.exists():
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        print(f"📊 Steps in found file: {len(data.get('workflow_steps', []))}")
                break
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
