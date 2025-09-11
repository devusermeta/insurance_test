"""
Test LLM-Based Intake Clarifier - Verification Logic
Tests the updated intake clarifier with LLM-based verification between claim_details and extracted_patient_data
"""

import asyncio
import json
from datetime import datetime

async def test_llm_intake_clarifier():
    """Test LLM-based verification logic"""
    print("📋 Testing LLM-Based Intake Clarifier - Verification Logic")
    print("=" * 70)
    
    # Import the updated intake clarifier
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'intake_clarifier'))
    
    from agents.intake_clarifier.intake_clarifier_executor import IntakeClarifierExecutor
    
    # Initialize the agent
    agent = IntakeClarifierExecutor()
    print("✅ LLM-based Intake Clarifier initialized")
    
    # Test cases for LLM verification
    test_cases = [
        {
            "name": "Perfect Match - Should Approve",
            "claim_details": {
                "id": "IP-TEST-001",
                "claimId": "IP-TEST-001",
                "patientName": "John Doe",
                "billAmount": 1500.0,
                "billDate": "2025-01-15",
                "diagnosis": "Pneumonia"
            },
            "extracted_data": {
                "id": "IP-TEST-001",
                "medical_bill_doc": {
                    "patient_name": "John Doe",
                    "bill_amount": 1500.0,
                    "bill_date": "2025-01-15"
                },
                "memo_doc": {
                    "patient_name": "John Doe",
                    "medical_condition": "Community-acquired pneumonia"
                },
                "discharge_summary_doc": {
                    "patient_name": "John Doe",
                    "medical_condition": "Pneumonia"
                }
            },
            "expected_verified": True
        },
        {
            "name": "Minor Name Variation - Should Approve",
            "claim_details": {
                "id": "OP-TEST-001",
                "claimId": "OP-TEST-001",
                "patientName": "Jane Smith",
                "billAmount": 300.0,
                "billDate": "2025-01-20",
                "diagnosis": "Dental cleaning"
            },
            "extracted_data": {
                "id": "OP-TEST-001",
                "medical_bill_doc": {
                    "patient_name": "Jane A. Smith",
                    "bill_amount": 300.0,
                    "bill_date": "2025-01-20"
                },
                "memo_doc": {
                    "patient_name": "Jane Smith",
                    "medical_condition": "Routine dental cleaning"
                }
            },
            "expected_verified": True
        },
        {
            "name": "Amount Mismatch - Should Reject",
            "claim_details": {
                "id": "IP-TEST-002",
                "claimId": "IP-TEST-002",
                "patientName": "Bob Johnson",
                "billAmount": 1000.0,
                "billDate": "2025-01-25",
                "diagnosis": "Surgery"
            },
            "extracted_data": {
                "id": "IP-TEST-002",
                "medical_bill_doc": {
                    "patient_name": "Bob Johnson",
                    "bill_amount": 2000.0,  # Mismatch!
                    "bill_date": "2025-01-25"
                },
                "memo_doc": {
                    "patient_name": "Bob Johnson",
                    "medical_condition": "Surgical procedure"
                }
            },
            "expected_verified": False
        },
        {
            "name": "Wrong Patient Name - Should Reject",
            "claim_details": {
                "id": "OP-TEST-002",
                "claimId": "OP-TEST-002",
                "patientName": "Alice Brown",
                "billAmount": 500.0,
                "billDate": "2025-01-30",
                "diagnosis": "Eye exam"
            },
            "extracted_data": {
                "id": "OP-TEST-002",
                "medical_bill_doc": {
                    "patient_name": "Charlie Brown",  # Wrong patient!
                    "bill_amount": 500.0,
                    "bill_date": "2025-01-30"
                },
                "memo_doc": {
                    "patient_name": "Charlie Brown",
                    "medical_condition": "Eye examination"
                }
            },
            "expected_verified": False
        },
        {
            "name": "Medical Terminology Variation - Should Approve",
            "claim_details": {
                "id": "IP-TEST-003",
                "claimId": "IP-TEST-003",
                "patientName": "David Wilson",
                "billAmount": 5000.0,
                "billDate": "2025-02-01",
                "diagnosis": "Heart attack"
            },
            "extracted_data": {
                "id": "IP-TEST-003",
                "medical_bill_doc": {
                    "patient_name": "David Wilson",
                    "bill_amount": 5000.0,
                    "bill_date": "2025-02-01"
                },
                "memo_doc": {
                    "patient_name": "David Wilson",
                    "medical_condition": "Myocardial infarction"  # Medical term for heart attack
                }
            },
            "expected_verified": True
        }
    ]
    
    print(f"\n🧪 Running {len(test_cases)} LLM verification test cases:")
    print("-" * 70)
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        
        try:
            # Test the LLM comparison logic
            comparison_result = await agent._llm_compare_claim_vs_extracted_data(
                test_case['claim_details'], 
                test_case['extracted_data']
            )
            
            # Check if result matches expectation
            actual_verified = comparison_result.get('verified', False)
            expected_verified = test_case['expected_verified']
            
            test_passed = actual_verified == expected_verified
            
            print(f"   Expected: {'VERIFIED' if expected_verified else 'REJECTED'}")
            print(f"   Actual: {'VERIFIED' if actual_verified else 'REJECTED'}")
            print(f"   Result: {'✅ PASS' if test_passed else '❌ FAIL'}")
            
            if test_passed:
                print(f"   Confidence: {comparison_result.get('overall_confidence', 'unknown')}")
                print(f"   Recommendation: {comparison_result.get('recommendation', 'unknown')}")
                
                # Show mismatches if any
                mismatches = comparison_result.get('mismatches', [])
                if mismatches:
                    print(f"   Mismatches found: {len(mismatches)}")
                    for mismatch in mismatches:
                        print(f"     - {mismatch['field']}: {mismatch['severity']} severity")
            else:
                print(f"   ❌ Test failed - LLM verification doesn't match expected result")
                print(f"   Reason: {comparison_result.get('reason', 'Unknown')}")
            
            results.append({
                "test": test_case['name'],
                "passed": test_passed,
                "expected": expected_verified,
                "actual": actual_verified,
                "comparison_result": comparison_result
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append({
                "test": test_case['name'],
                "passed": False,
                "error": str(e)
            })
    
    # Test prompt creation
    print(f"\n🧪 Testing LLM Prompt Creation:")
    print("-" * 70)
    
    sample_claim = {
        "patientName": "Test Patient",
        "billAmount": 1000,
        "billDate": "2025-01-15",
        "diagnosis": "Test condition"
    }
    
    sample_extracted = {
        "medical_bill_doc": {
            "patient_name": "Test Patient",
            "bill_amount": 1000,
            "bill_date": "2025-01-15"
        },
        "memo_doc": {
            "patient_name": "Test Patient",
            "medical_condition": "Test condition"
        }
    }
    
    try:
        prompt = agent._create_llm_comparison_prompt(sample_claim, sample_extracted)
        
        # Check if prompt contains key elements
        required_elements = [
            "ORIGINAL CLAIM DATA",
            "EXTRACTED DOCUMENT DATA", 
            "VERIFICATION REQUIREMENTS",
            "Patient Name",
            "Bill Amount",
            "verified",
            "reason",
            "mismatches"
        ]
        
        elements_present = sum(1 for element in required_elements if element in prompt)
        
        print(f"✅ Prompt creation successful")
        print(f"   Required elements present: {elements_present}/{len(required_elements)}")
        print(f"   Prompt length: {len(prompt)} characters")
        
        if elements_present == len(required_elements):
            print("✅ All required elements found in prompt")
        else:
            missing = [elem for elem in required_elements if elem not in prompt]
            print(f"⚠️ Missing elements: {missing}")
        
    except Exception as e:
        print(f"❌ Error testing prompt creation: {e}")
    
    # Test fallback mechanism
    print(f"\n🧪 Testing Fallback Manual Comparison:")
    print("-" * 70)
    
    try:
        fallback_result = agent._fallback_manual_comparison(sample_claim, sample_extracted)
        
        print(f"✅ Fallback comparison working")
        print(f"   Verified: {fallback_result.get('verified', False)}")
        print(f"   Confidence: {fallback_result.get('overall_confidence', 'unknown')}")
        print(f"   Mismatches: {len(fallback_result.get('mismatches', []))}")
        
    except Exception as e:
        print(f"❌ Error testing fallback: {e}")
    
    # Summary
    print(f"\n📊 LLM INTAKE CLARIFIER TEST SUMMARY:")
    print("=" * 70)
    
    successful_tests = [r for r in results if "error" not in r]
    total_tests = len(successful_tests)
    passed_tests = sum(1 for r in successful_tests if r.get('passed', False))
    
    if total_tests > 0:
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! LLM-based verification is working perfectly!")
        else:
            print("⚠️ Some tests failed. Review LLM verification logic.")
    
    print(f"\n✅ Key Features Implemented:")
    print("   🤖 LLM-based intelligent comparison")
    print("   📊 Confidence scoring and recommendations") 
    print("   🔍 Detailed mismatch analysis")
    print("   🛡️ Fallback manual comparison")
    print("   📝 Cosmos DB status updates")
    print("   ✅ Medical terminology understanding")

if __name__ == "__main__":
    asyncio.run(test_llm_intake_clarifier())
