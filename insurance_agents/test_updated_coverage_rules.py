"""
Test Updated Coverage Rules Engine - New Business Rules
Tests the updated coverage rules with your new limits and document requirements
"""

import asyncio
import json
from datetime import datetime

async def test_updated_coverage_rules():
    """Test updated coverage rules with new business limits and document requirements"""
    print("⚖️ Testing Updated Coverage Rules Engine - New Vision")
    print("=" * 70)
    
    # Import the updated coverage rules engine
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'coverage_rules_engine'))
    
    from agents.coverage_rules_engine.coverage_rules_executor_fixed import CoverageRulesExecutorFixed
    
    # Initialize the engine
    engine = CoverageRulesExecutorFixed()
    print("✅ Updated Coverage Rules Engine initialized")
    
    # Test cases with NEW business rules
    test_cases = [
        {
            "name": "Eye Claim - Within NEW $500 Limit",
            "claim_info": {
                "claim_id": "EY-NEW-001",
                "category": "outpatient",
                "diagnosis": "Cataract surgery",
                "bill_amount": "400",
                "billAttachment": "https://example.com/bill.pdf",
                "memoAttachment": "https://example.com/memo.pdf"
            },
            "expected": "approved"
        },
        {
            "name": "Eye Claim - Exceeds NEW $500 Limit", 
            "claim_info": {
                "claim_id": "EY-NEW-002",
                "category": "outpatient",
                "diagnosis": "LASIK surgery",
                "bill_amount": "600",
                "billAttachment": "https://example.com/bill.pdf",
                "memoAttachment": "https://example.com/memo.pdf"
            },
            "expected": "rejected"
        },
        {
            "name": "Dental Claim - Within NEW $1000 Limit",
            "claim_info": {
                "claim_id": "DN-NEW-001",
                "category": "outpatient", 
                "diagnosis": "Root canal treatment",
                "bill_amount": "800",
                "billAttachment": "https://example.com/bill.pdf",
                "memoAttachment": "https://example.com/memo.pdf"
            },
            "expected": "approved"
        },
        {
            "name": "Dental Claim - Exceeds NEW $1000 Limit",
            "claim_info": {
                "claim_id": "DN-NEW-002",
                "category": "outpatient",
                "diagnosis": "Dental implants",
                "bill_amount": "1200",
                "billAttachment": "https://example.com/bill.pdf",
                "memoAttachment": "https://example.com/memo.pdf"
            },
            "expected": "rejected"
        },
        {
            "name": "General Claim - Within NEW $200K Limit",
            "claim_info": {
                "claim_id": "GN-NEW-001",
                "category": "inpatient",
                "diagnosis": "Heart surgery",
                "bill_amount": "150000",
                "billAttachment": "https://example.com/bill.pdf",
                "memoAttachment": "https://example.com/memo.pdf",
                "dischargeAttachment": "https://example.com/discharge.pdf"
            },
            "expected": "approved"
        },
        {
            "name": "General Claim - Exceeds NEW $200K Limit",
            "claim_info": {
                "claim_id": "GN-NEW-002",
                "category": "inpatient",
                "diagnosis": "Complex surgery",
                "bill_amount": "250000",
                "billAttachment": "https://example.com/bill.pdf",
                "memoAttachment": "https://example.com/memo.pdf",
                "dischargeAttachment": "https://example.com/discharge.pdf"
            },
            "expected": "rejected"
        },
        {
            "name": "Outpatient - Missing Memo (Document Check)",
            "claim_info": {
                "claim_id": "DOC-001",
                "category": "outpatient",
                "diagnosis": "Consultation",
                "bill_amount": "100",
                "billAttachment": "https://example.com/bill.pdf"
                # Missing memoAttachment
            },
            "expected": "rejected"
        },
        {
            "name": "Inpatient - Missing Discharge (Document Check)",
            "claim_info": {
                "claim_id": "DOC-002",
                "category": "inpatient",
                "diagnosis": "Surgery",
                "bill_amount": "5000",
                "billAttachment": "https://example.com/bill.pdf",
                "memoAttachment": "https://example.com/memo.pdf"
                # Missing dischargeAttachment
            },
            "expected": "rejected"
        }
    ]
    
    print(f"\n🧪 Running {len(test_cases)} test cases with NEW business rules:")
    print("-" * 70)
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        
        try:
            # Test the evaluation logic
            evaluation = await engine._evaluate_structured_claim(test_case['claim_info'])
            
            # Check if result matches expectation
            actual_status = "approved" if evaluation['eligible'] else "rejected"
            expected_status = test_case['expected']
            
            test_passed = actual_status == expected_status
            
            print(f"   Expected: {expected_status.upper()}")
            print(f"   Actual: {actual_status.upper()}")
            print(f"   Result: {'✅ PASS' if test_passed else '❌ FAIL'}")
            
            if test_passed:
                print(f"   Claim Type: {evaluation.get('claim_type', 'unknown').upper()}")
                print(f"   Max Allowed: ${evaluation.get('max_allowed', 0)}")
                print(f"   Bill Amount: ${evaluation.get('bill_amount', 0)}")
                if not evaluation['eligible'] and evaluation.get('rejection_reason'):
                    print(f"   Rejection Reason: {evaluation['rejection_reason']}")
            
            results.append({
                "test": test_case['name'],
                "passed": test_passed,
                "expected": expected_status,
                "actual": actual_status,
                "evaluation": evaluation
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append({
                "test": test_case['name'],
                "passed": False,
                "error": str(e)
            })
    
    # Summary
    print(f"\n📊 UPDATED BUSINESS RULES TEST SUMMARY:")
    print("=" * 70)
    
    passed_tests = sum(1 for r in results if r.get('passed', False))
    total_tests = len(results)
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Updated Coverage Rules Engine is working perfectly!")
    else:
        print("⚠️ Some tests failed. Review the updated business rule implementation.")
    
    # Show updated business rule limits
    print(f"\n🔍 UPDATED BUSINESS RULE VERIFICATION:")
    print("-" * 70)
    
    rule_sets = engine.rule_sets
    print(f"NEW Eye Claims Limit: ${rule_sets['claim_type_limits']['eye']['max_amount']}")
    print(f"NEW Dental Claims Limit: ${rule_sets['claim_type_limits']['dental']['max_amount']}")
    print(f"NEW General Claims Limit: ${rule_sets['claim_type_limits']['general']['max_amount']}")
    
    # Expected NEW limits according to your updated vision
    expected_limits = {"eye": 500, "dental": 1000, "general": 200000}
    
    print(f"\n✅ Updated Limits Verification:")
    for claim_type, expected_limit in expected_limits.items():
        actual_limit = rule_sets['claim_type_limits'][claim_type]['max_amount']
        if actual_limit == expected_limit:
            print(f"✅ {claim_type.title()} limit correct: ${actual_limit}")
        else:
            print(f"❌ {claim_type.title()} limit incorrect: ${actual_limit} (expected ${expected_limit})")

if __name__ == "__main__":
    asyncio.run(test_updated_coverage_rules())
