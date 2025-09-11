"""
Test Coverage Rules Engine - Vision Alignment
Tests the updated coverage rules engine with your specific business rules
"""

import asyncio
import json
from datetime import datetime

async def test_coverage_rules_vision():
    """Test coverage rules engine with your vision requirements"""
    print("⚖️ Testing Coverage Rules Engine - Vision Alignment")
    print("=" * 60)
    
    # Import the updated coverage rules engine
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'coverage_rules_engine'))
    
    from agents.coverage_rules_engine.coverage_rules_executor_fixed import CoverageRulesExecutorFixed
    
    # Initialize the engine
    engine = CoverageRulesExecutorFixed()
    print("✅ Coverage Rules Engine initialized")
    
    # Test cases for your specific business rules
    test_cases = [
        {
            "name": "Eye Claim - Within Limit",
            "claim_info": {
                "claim_id": "EY-001",
                "category": "outpatient",
                "diagnosis": "Cataract surgery",
                "bill_amount": "800"
            },
            "expected": "approved"
        },
        {
            "name": "Eye Claim - Exceeds Limit", 
            "claim_info": {
                "claim_id": "EY-002",
                "category": "outpatient",
                "diagnosis": "Retinal detachment repair",
                "bill_amount": "1200"
            },
            "expected": "rejected"
        },
        {
            "name": "Dental Claim - Within Limit",
            "claim_info": {
                "claim_id": "DN-001",
                "category": "outpatient", 
                "diagnosis": "Root canal treatment",
                "bill_amount": "400"
            },
            "expected": "approved"
        },
        {
            "name": "Dental Claim - Exceeds Limit",
            "claim_info": {
                "claim_id": "DN-002",
                "category": "outpatient",
                "diagnosis": "Dental implants",
                "bill_amount": "600"
            },
            "expected": "rejected"
        },
        {
            "name": "General Claim - Within Limit",
            "claim_info": {
                "claim_id": "GN-001",
                "category": "inpatient",
                "diagnosis": "Pneumonia treatment",
                "bill_amount": "1800"
            },
            "expected": "approved"
        },
        {
            "name": "General Claim - Exceeds Limit",
            "claim_info": {
                "claim_id": "GN-002",
                "category": "inpatient",
                "diagnosis": "Heart surgery",
                "bill_amount": "2500"
            },
            "expected": "rejected"
        }
    ]
    
    print(f"\n🧪 Running {len(test_cases)} test cases:")
    print("-" * 50)
    
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
            else:
                print(f"   ❌ Test failed - check business rule logic")
            
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
    print(f"\n📊 TEST SUMMARY:")
    print("=" * 50)
    
    passed_tests = sum(1 for r in results if r.get('passed', False))
    total_tests = len(results)
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Coverage Rules Engine is vision-aligned!")
    else:
        print("⚠️ Some tests failed. Review business rule implementation.")
    
    # Test business rule limits
    print(f"\n🔍 BUSINESS RULE VERIFICATION:")
    print("-" * 50)
    
    rule_sets = engine.rule_sets
    print(f"Eye Claims Limit: ${rule_sets['claim_type_limits']['eye']['max_amount']}")
    print(f"Dental Claims Limit: ${rule_sets['claim_type_limits']['dental']['max_amount']}")
    print(f"General Claims Limit: ${rule_sets['claim_type_limits']['general']['max_amount']}")
    
    # Expected limits according to your vision
    expected_limits = {"eye": 1000, "dental": 500, "general": 2000}
    
    for claim_type, expected_limit in expected_limits.items():
        actual_limit = rule_sets['claim_type_limits'][claim_type]['max_amount']
        if actual_limit == expected_limit:
            print(f"✅ {claim_type.title()} limit correct: ${actual_limit}")
        else:
            print(f"❌ {claim_type.title()} limit incorrect: ${actual_limit} (expected ${expected_limit})")

async def test_claim_classification():
    """Test claim type classification logic"""
    print(f"\n🏷️ TESTING CLAIM CLASSIFICATION:")
    print("-" * 50)
    
    from agents.coverage_rules_engine.coverage_rules_executor_fixed import CoverageRulesExecutorFixed
    engine = CoverageRulesExecutorFixed()
    
    classification_tests = [
        ("Cataract surgery", "eye"),
        ("Glaucoma treatment", "eye"), 
        ("Vision correction", "eye"),
        ("Dental cleaning", "dental"),
        ("Root canal", "dental"),
        ("Tooth extraction", "dental"),
        ("Pneumonia", "general"),
        ("Heart surgery", "general"),
        ("Broken leg", "general")
    ]
    
    for diagnosis, expected_type in classification_tests:
        actual_type = engine._classify_claim_type(diagnosis)
        status = "✅" if actual_type == expected_type else "❌"
        print(f"   {status} '{diagnosis}' → {actual_type} (expected: {expected_type})")

if __name__ == "__main__":
    asyncio.run(test_coverage_rules_vision())
    asyncio.run(test_claim_classification())
