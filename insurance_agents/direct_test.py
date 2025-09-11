#!/usr/bin/env python3
"""
Direct test of workflow detection logic
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to sys.path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import the executor class directly
from agents.coverage_rules_engine.coverage_rules_executor_fixed import CoverageRulesExecutorFixed

def test_workflow_detection():
    """Test workflow detection logic directly"""
    print("🔍 DIRECT WORKFLOW DETECTION TEST")
    print("=" * 50)
    
    # Create an instance of the executor
    executor = CoverageRulesExecutorFixed()
    
    # Test message with all required indicators
    test_message = """NEW WORKFLOW CLAIM EVALUATION REQUEST
claim_id: OP-05
patient_name: John Doe
bill_amount: $850.00
diagnosis: Routine Outpatient Visit
category: outpatient
status: pending_review
bill_date: 2024-01-15

Task: Evaluate coverage eligibility and benefits for this structured claim data."""
    
    print(f"Test message length: {len(test_message)} characters")
    print(f"First 200 chars: {test_message[:200]}...")
    print()
    
    # Test the detection method directly
    print("Testing _is_new_workflow_claim_request...")
    try:
        is_detected = executor._is_new_workflow_claim_request(test_message)
        print(f"Detection result: {is_detected}")
    except Exception as e:
        print(f"Detection method error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test the extraction method directly
    print("Testing _extract_claim_info_from_text...")
    try:
        claim_info = executor._extract_claim_info_from_text(test_message)
        print(f"Extracted info: {claim_info}")
    except Exception as e:
        print(f"Extraction method error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_workflow_detection()
