#!/usr/bin/env python3
"""
Test file to validate the orchestrator approval detection fix
Tests the _is_claim_approved method with real A2A response structures
"""

import json
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_orchestrator_approval_detection():
    """Test the enhanced approval detection logic"""
    
    # Mock the logger for testing
    class MockLogger:
        def info(self, msg): print(f"ℹ️  {msg}")
        def warning(self, msg): print(f"⚠️  {msg}")
    
    # Create a mock orchestrator with just the approval detection method
    class MockOrchestrator:
        def __init__(self):
            self.logger = MockLogger()
            
        def _is_claim_approved(self, result):
            """Enhanced approval detection with A2A structure parsing"""
            self.logger.info(f"🔍 Checking approval status for result type: {type(result)}")
            
            if isinstance(result, dict):
                # Handle nested A2A response structure
                if 'result' in result and 'artifacts' in result['result']:
                    artifacts = result['result']['artifacts']
                    self.logger.info(f"📋 Found {len(artifacts)} artifacts in A2A response")
                    
                    for artifact in artifacts:
                        if 'parts' in artifact:
                            for part in artifact['parts']:
                                if part.get('kind') == 'text':
                                    text_content = part.get('text', '')
                                    self.logger.info(f"📝 Analyzing artifact text: {text_content[:200]}...")
                                    
                                    try:
                                        # Try to parse as JSON if it looks like JSON
                                        if text_content.strip().startswith('{'):
                                            parsed_content = json.loads(text_content)
                                            
                                            # Check status in parsed JSON
                                            status = parsed_content.get("status", "").lower()
                                            response = parsed_content.get("response", "").lower()
                                            
                                            self.logger.info(f"📊 Parsed JSON - Status: '{status}', Response preview: '{response[:100]}...'")
                                            
                                            if status == "approved":
                                                self.logger.info(f"✅ CLAIM APPROVED via JSON status field")
                                                return True
                                                
                                            if "approved" in response or "claim approved" in response:
                                                self.logger.info(f"✅ CLAIM APPROVED via JSON response field")
                                                return True
                                                
                                    except json.JSONDecodeError:
                                        # If not JSON, check as plain text
                                        text_lower = text_content.lower()
                                        if "approved" in text_lower or "claim approved" in text_lower:
                                            self.logger.info(f"✅ CLAIM APPROVED via artifact text analysis")
                                            return True
                
                # Original field checks for backwards compatibility
                status = result.get("status", "").lower()
                self.logger.info(f"📊 Status field: '{status}'")
                if status == "approved":
                    self.logger.info(f"✅ CLAIM APPROVED via status field")
                    return True
                
                # Check message field
                message = result.get("message", "").lower()
                self.logger.info(f"📊 Message field: '{message}'")
                if "approved" in message or "marked for approval" in message:
                    self.logger.info(f"✅ CLAIM APPROVED via message field")
                    return True
                    
                # Check response field
                response = result.get("response", "").lower()
                self.logger.info(f"📊 Response field: '{response}'")
                if "approved" in response or "marked for approval" in response:
                    self.logger.info(f"✅ CLAIM APPROVED via response field")
                    return True
            
            self.logger.warning(f"❌ CLAIM NOT APPROVED - No approval indicators found in result")
            return False

    # Test with the real A2A response structure from the logs
    real_a2a_response = {
        'id': 'a2a-intake_clarifier-1b36dd7b-6f17-46f9-a6e9-e2253da506e8',
        'jsonrpc': '2.0',
        'result': {
            'artifacts': [
                {
                    'artifactId': 'a8fb5159-8edc-4fd7-b617-80a52df26440',
                    'description': 'Result of intake clarification process.',
                    'name': 'intake_clarification_result',
                    'parts': [
                        {
                            'kind': 'text',
                            'text': '{\n  "status": "approved",\n  "response": "✅ **CLAIM APPROVED**\\n\\n**Claim ID**: OP-01\\n**Verification Status**: PASSED\\n**Data Integrity**: All data fields match between claim and extracted data\\n\\n**Verification Details:**\\n• ✅ Patient name matches: Priya Singh\\n• ✅ Bill amount matches: $91.8\\n• ✅ Medical condition matches: Gastritis\\n\\n**Status**: Marked for approval in Cosmos DB",\n  "verification_result": {\n    "status": "match",\n    "details": [\n      "✅ Patient name matches: Priya Singh",\n      "✅ Bill amount matches: $91.8",\n      "✅ Medical condition matches: Gastritis"\n    ],\n    "issues": []\n  },\n  "workflow_type": "new_structured"\n}'
                        }
                    ]
                }
            ],
            'contextId': '772850ec-b53c-49a8-825c-ff9b81fc9e5e',
            'id': '1dafb02c-51d0-46fc-9ffa-5fed19ca87ff',
            'kind': 'task',
            'status': {'state': 'completed'}
        }
    }

    print("🧪 Testing Orchestrator Approval Detection Fix")
    print("=" * 60)
    
    orchestrator = MockOrchestrator()
    
    print("\n🔍 Test 1: Real A2A Response Structure")
    print("-" * 40)
    result1 = orchestrator._is_claim_approved(real_a2a_response)
    print(f"📊 Result: {'✅ APPROVED' if result1 else '❌ DENIED'}")
    
    print("\n🔍 Test 2: Simple Status Field")
    print("-" * 40)
    simple_response = {"status": "approved", "message": "Claim is good"}
    result2 = orchestrator._is_claim_approved(simple_response)
    print(f"📊 Result: {'✅ APPROVED' if result2 else '❌ DENIED'}")
    
    print("\n🔍 Test 3: Response Field with Approval")
    print("-" * 40)
    response_field = {"response": "CLAIM APPROVED - all checks passed"}
    result3 = orchestrator._is_claim_approved(response_field)
    print(f"📊 Result: {'✅ APPROVED' if result3 else '❌ DENIED'}")
    
    print("\n🔍 Test 4: Denied Claim")
    print("-" * 40)
    denied_response = {"status": "rejected", "message": "Data mismatch found"}
    result4 = orchestrator._is_claim_approved(denied_response)
    print(f"📊 Result: {'✅ APPROVED' if result4 else '❌ DENIED'}")
    
    print("\n📋 Summary:")
    print(f"✅ A2A Response: {'PASS' if result1 else 'FAIL'}")
    print(f"✅ Simple Status: {'PASS' if result2 else 'FAIL'}")
    print(f"✅ Response Field: {'PASS' if result3 else 'FAIL'}")
    print(f"✅ Denied Claim: {'PASS' if not result4 else 'FAIL'}")
    
    # Overall test result
    all_passed = result1 and result2 and result3 and not result4
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    test_orchestrator_approval_detection()
