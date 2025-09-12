"""
Test script to verify the orchestrator approval logic fix
Tests that orchestrator correctly interprets Intake Clarifier responses
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_orchestrator_approval_logic():
    """Test the fixed _is_claim_approved method"""
    
    print("🧪 TESTING ORCHESTRATOR APPROVAL LOGIC FIX")
    print("=" * 50)
    
    try:
        from agents.claims_orchestrator.intelligent_orchestrator import IntelligentClaimsOrchestrator
        
        # Create orchestrator instance
        orchestrator = IntelligentClaimsOrchestrator()
        print("✅ Orchestrator initialized")
        
        # Test 1: Intake Clarifier response format (the actual format from logs)
        intake_clarifier_response = {
            "status": "approved",
            "response": """✅ **CLAIM APPROVED**

**Claim ID**: OP-03
**Verification Status**: PASSED
**Data Integrity**: All data fields match between claim and extracted data

**Verification Details:**
• ✅ Patient name matches: John Smith
• ✅ Bill amount matches: $100.0
• ✅ Medical condition matches: Knee pain

**Status**: Marked for approval in Cosmos DB""",
            "verification_result": {
                "status": "match",
                "details": ["✅ Patient name matches: John Smith"],
                "issues": []
            },
            "workflow_type": "new_structured"
        }
        
        print("\n📋 TEST 1: Intake Clarifier Response Format")
        print("-" * 40)
        is_approved = orchestrator._is_claim_approved(intake_clarifier_response)
        print(f"🔍 Input: {{'status': 'approved', 'response': '✅ **CLAIM APPROVED**...'}}")
        print(f"📊 Result: {is_approved}")
        
        if is_approved:
            print("✅ PASS - Correctly identified as approved")
        else:
            print("❌ FAIL - Should be approved but detected as denied")
            return False
        
        # Test 2: Legacy message format (backup compatibility)
        legacy_response = {
            "message": "Claim has been marked for approval",
            "status": "success"
        }
        
        print("\n📋 TEST 2: Legacy Message Format")
        print("-" * 40)
        is_approved = orchestrator._is_claim_approved(legacy_response)
        print(f"🔍 Input: {{'message': 'marked for approval', 'status': 'success'}}")
        print(f"📊 Result: {is_approved}")
        
        if is_approved:
            print("✅ PASS - Correctly identified legacy format as approved")
        else:
            print("❌ FAIL - Should be approved but detected as denied")
            return False
        
        # Test 3: Denied response format
        denied_response = {
            "status": "denied",
            "response": "❌ **CLAIM DENIED**\n\nData verification failed",
            "verification_result": {
                "status": "mismatch",
                "issues": ["Patient name mismatch"]
            }
        }
        
        print("\n📋 TEST 3: Denied Response Format")
        print("-" * 40)
        is_approved = orchestrator._is_claim_approved(denied_response)
        print(f"🔍 Input: {{'status': 'denied', 'response': '❌ **CLAIM DENIED**...'}}")
        print(f"📊 Result: {is_approved}")
        
        if not is_approved:
            print("✅ PASS - Correctly identified as denied")
        else:
            print("❌ FAIL - Should be denied but detected as approved")
            return False
        
        # Test 4: Status field priority test
        status_priority_response = {
            "status": "approved",
            "message": "This claim was denied",  # Conflicting message
            "response": "Processing failed"       # Conflicting response
        }
        
        print("\n📋 TEST 4: Status Field Priority")
        print("-" * 40)
        is_approved = orchestrator._is_claim_approved(status_priority_response)
        print(f"🔍 Input: status='approved' but message/response say denied")
        print(f"📊 Result: {is_approved}")
        
        if is_approved:
            print("✅ PASS - Status field takes priority over conflicting content")
        else:
            print("❌ FAIL - Status field should take priority")
            return False
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Orchestrator approval logic fix is working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_workflow_scenario():
    """Test with the exact scenario from the logs"""
    
    print("\n🎯 REAL SCENARIO TEST")
    print("=" * 30)
    
    try:
        from agents.claims_orchestrator.intelligent_orchestrator import IntelligentClaimsOrchestrator
        
        orchestrator = IntelligentClaimsOrchestrator()
        
        # This is exactly what the Intake Clarifier returned in the logs
        real_response = {
            "status": "approved",
            "response": """✅ **CLAIM APPROVED**

**Claim ID**: OP-03
**Verification Status**: PASSED
**Data Integrity**: All data fields match between claim and extracted data

**Verification Details:**
• ✅ Patient name matches: John Smith
• ✅ Bill amount matches: $100.0
• ✅ Medical condition matches: Knee pain

**Status**: Marked for approval in Cosmos DB""",
            "verification_result": {
                "status": "match",
                "details": [
                    "✅ Patient name matches: John Smith",
                    "✅ Bill amount matches: $100.0", 
                    "✅ Medical condition matches: Knee pain"
                ],
                "issues": []
            },
            "workflow_type": "new_structured"
        }
        
        print("📋 Testing with real OP-03 scenario data...")
        is_approved = orchestrator._is_claim_approved(real_response)
        
        print(f"🔍 Real Response Status: {real_response['status']}")
        print(f"📊 Detection Result: {'APPROVED' if is_approved else 'DENIED'}")
        
        if is_approved:
            print("🎉 SUCCESS! OP-03 scenario now correctly identified as APPROVED")
            print("✅ The orchestrator will now show 'CLAIM APPROVED' instead of 'CLAIM DENIED'")
            return True
        else:
            print("❌ FAILED! Still detecting as denied")
            return False
            
    except Exception as e:
        print(f"❌ Real scenario test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Orchestrator Approval Logic Fix Test...")
    
    # Run the logic tests
    logic_test_passed = test_orchestrator_approval_logic()
    
    if logic_test_passed:
        # Run the real scenario test
        scenario_test_passed = test_real_workflow_scenario()
        
        if scenario_test_passed:
            print("\n🎉 ALL TESTS SUCCESSFUL!")
            print("✅ Orchestrator fix resolves the OP-03 approval issue")
            print("🔄 The workflow should now show approved status correctly")
        else:
            print("\n❌ SCENARIO TEST FAILED!")
    else:
        print("\n❌ LOGIC TESTS FAILED!")
    
    exit(0 if logic_test_passed and scenario_test_passed else 1)
