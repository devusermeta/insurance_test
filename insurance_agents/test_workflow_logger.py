"""
Simple test to verify workflow logging is working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.workflow_logger import workflow_logger

def test_workflow_logger():
    print("🧪 Testing Workflow Logger")
    print("=" * 40)
    
    # Test starting a claim
    claim_id = "TEST-WORKFLOW-001"
    workflow_logger.start_claim_processing(claim_id)
    print(f"✅ Started workflow for claim: {claim_id}")
    
    # Test adding some steps
    step1 = workflow_logger.log_discovery(
        agents_found=3,
        agent_details=[
            {"agent_id": "test1", "name": "Test Agent 1", "skills": 2},
            {"agent_id": "test2", "name": "Test Agent 2", "skills": 3}
        ]
    )
    print(f"✅ Added discovery step: {step1}")
    
    step2 = workflow_logger.log_agent_selection(
        task_type="test_task",
        selected_agent="test1", 
        agent_name="Test Agent 1",
        reasoning="Best match for testing"
    )
    print(f"✅ Added selection step: {step2}")
    
    # Get workflow steps
    steps = workflow_logger.get_workflow_steps(claim_id)
    print(f"\n📋 Workflow steps for {claim_id}: {len(steps)} steps")
    
    for i, step in enumerate(steps, 1):
        step_dict = step.to_dict() if hasattr(step, 'to_dict') else step
        print(f"   {i}. {step_dict.get('step_type', 'unknown')}: {step_dict.get('description', 'No description')}")
    
    # Get all recent steps
    all_steps = workflow_logger.get_all_recent_steps(10)
    print(f"\n📋 All recent steps: {len(all_steps)} steps")
    
    print("\n🎉 Workflow logger test complete!")
    
    return len(steps) > 0

if __name__ == "__main__":
    success = test_workflow_logger()
    if success:
        print("✅ Workflow logger is working correctly!")
    else:
        print("❌ Workflow logger has issues!")
