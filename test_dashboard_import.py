#!/usr/bin/env python3
"""
Test to see what's happening with the dashboard's workflow logger import
"""

import sys
import os

# Add the path that the dashboard uses
dashboard_path = os.path.join(os.getcwd(), "insurance_agents", "insurance_agents_registry_dashboard")
sys.path.insert(0, os.path.join(os.getcwd(), "insurance_agents"))

print(f"🔍 Current working directory: {os.getcwd()}")
print(f"🔍 Dashboard path: {dashboard_path}")
print(f"🔍 Python path entries:")
for i, path in enumerate(sys.path[:5]):
    print(f"   {i}: {path}")

# Try to import workflow logger the same way the dashboard does
try:
    print("\n📦 Attempting to import shared.workflow_logger...")
    from shared.workflow_logger import WorkflowLogger
    print("✅ Import successful!")
    
    # Test if it can create an instance
    logger = WorkflowLogger()
    print("✅ WorkflowLogger instance created!")
    
    # Test if it can get steps
    steps = logger.get_all_recent_steps()
    print(f"✅ Retrieved {len(steps)} workflow steps")
    
    if steps:
        print("📋 Sample of real workflow steps:")
        for i, step in enumerate(steps[:3]):
            print(f"   {i+1}. Claim: {step['claim_id']}, Type: {step['step_type']}, Status: {step['status']}")
    else:
        print("⚠️  No workflow steps found")
        
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("🔍 This explains why dashboard is using MockWorkflowLogger!")
    
except Exception as e:
    print(f"❌ Error creating or using WorkflowLogger: {e}")

print("\n" + "="*60)
print("🧪 TESTING MOCK WORKFLOW LOGGER FALLBACK")

# Now test the mock version that dashboard is probably using
try:
    class MockWorkflowLogger:
        def get_all_recent_steps(self):
            return [
                {
                    "id": "test_001",
                    "claim_id": "TEST", 
                    "title": "🧪 Test Step",
                    "description": "Dashboard workflow system initialized",
                    "status": "completed",
                    "timestamp": "2025-09-09T13:42:37.021596",
                    "step_type": "system"
                }
            ]
    
    mock_logger = MockWorkflowLogger()
    mock_steps = mock_logger.get_all_recent_steps()
    print(f"📋 Mock logger returns {len(mock_steps)} steps:")
    for step in mock_steps:
        print(f"   - Claim: {step['claim_id']}, Title: {step['title']}")
        
except Exception as e:
    print(f"❌ Error with mock logger: {e}")
