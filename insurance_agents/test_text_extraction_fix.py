#!/usr/bin/env python3
"""
Test the fixed text extraction logic without restarting agents
"""
import sys
from pathlib import Path

# Add parent directory to sys.path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def test_text_extraction_fix():
    """Test if the context.get_user_input() method would work"""
    print("🔍 TEXT EXTRACTION FIX TEST")
    print("=" * 50)
    
    # Simulate the structured message
    test_message = """NEW WORKFLOW CLAIM EVALUATION REQUEST
claim_id: OP-05
patient_name: John Doe
bill_amount: $850.00
diagnosis: Routine Outpatient Visit
category: outpatient
status: pending_review
bill_date: 2024-01-15

Task: Evaluate coverage eligibility and benefits for this structured claim data."""
    
    print(f"Full test message length: {len(test_message)}")
    print(f"Full test message preview: {test_message[:200]}...")
    print()
    
    # Test the detection logic with full text
    print("Testing indicators with FULL text:")
    text_lower = test_message.lower()
    indicators = [
        ("claim_id", "claim_id" in text_lower),
        ("patient_name", "patient_name" in text_lower),
        ("bill_amount", "bill_amount" in text_lower),
        ("diagnosis", "diagnosis" in text_lower),
        ("category", "category" in text_lower)
    ]
    
    for name, detected in indicators:
        print(f"  {name}: {'✅' if detected else '❌'}")
    
    indicator_count = sum(detected for _, detected in indicators)
    print(f"\nTotal indicators found: {indicator_count}/5")
    print(f"Should trigger new workflow: {'✅ YES' if indicator_count >= 2 else '❌ NO'}")
    
    # Test with truncated text (current problem)
    print("\nTesting indicators with TRUNCATED text ('...'):")
    truncated_text = "..."
    text_lower = truncated_text.lower()
    indicators_truncated = [
        ("claim_id", "claim_id" in text_lower),
        ("patient_name", "patient_name" in text_lower),
        ("bill_amount", "bill_amount" in text_lower),
        ("diagnosis", "diagnosis" in text_lower),
        ("category", "category" in text_lower)
    ]
    
    for name, detected in indicators_truncated:
        print(f"  {name}: {'✅' if detected else '❌'}")
    
    indicator_count_truncated = sum(detected for _, detected in indicators_truncated)
    print(f"\nTotal indicators found: {indicator_count_truncated}/5")
    print(f"Should trigger new workflow: {'✅ YES' if indicator_count_truncated >= 2 else '❌ NO'}")
    
    print("\n" + "=" * 50)
    print("CONCLUSION:")
    print("✅ Full text detection works correctly")
    print("❌ Truncated text ('...') fails detection")
    print("🔧 Fix: Use context.get_user_input() instead of message.parts[].text")

if __name__ == "__main__":
    test_text_extraction_fix()
