#!/usr/bin/env python3
"""
Comprehensive agent workflow detection debug test
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to sys.path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from shared.a2a_client import A2AClient

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

async def comprehensive_test():
    """Comprehensive test to identify workflow detection issues"""
    print("🔍 COMPREHENSIVE WORKFLOW DEBUG TEST")
    print("=" * 50)
    
    print(f"Test message:\n{test_message}")
    print("=" * 50)
    
    # Manually test the detection logic
    test_text = test_message.lower()
    indicators = [
        ("claim_id", "claim_id" in test_text),
        ("patient_name", "patient_name" in test_text),
        ("bill_amount", "bill_amount" in test_text),
        ("diagnosis", "diagnosis" in test_text),
        ("category", "category" in test_text)
    ]
    
    print("Manual indicator detection:")
    for name, detected in indicators:
        print(f"  {name}: {'✅' if detected else '❌'}")
    
    indicator_count = sum(detected for _, detected in indicators)
    print(f"Total indicators: {indicator_count}/5")
    print(f"Should trigger new workflow: {'✅' if indicator_count >= 2 else '❌'}")
    print()
    
    # Test the agent
    a2a_client = A2AClient("comprehensive_test")
    
    try:
        print("Sending to coverage_rules_engine...")
        result = await a2a_client.send_request(
            target_agent="coverage_rules_engine",
            task=test_message,
            parameters={"debug": True}
        )
        
        if result and isinstance(result, dict):
            print("Response received successfully")
            # Look for indicators of new workflow in response
            result_str = str(result).lower()
            new_workflow_indicators = [
                ("OP-05 mentioned", "op-05" in result_str),
                ("John Doe mentioned", "john doe" in result_str),
                ("Structured response", "claim analysis" in result_str),
                ("Coverage percentage", "coverage percentage" in result_str),
                ("Enhanced processing", "new workflow" in result_str or "structured" in result_str)
            ]
            
            print("\nResponse analysis:")
            for name, detected in new_workflow_indicators:
                print(f"  {name}: {'✅' if detected else '❌'}")
                
        else:
            print("No response received")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(comprehensive_test())
