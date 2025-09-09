#!/usr/bin/env python3
"""
Test Workflow Logger Integration
Tests that the orchestrator is properly logging workflow steps during claim processing
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the insurance_agents directory to path for imports
sys.path.append(str(Path(__file__).parent / "insurance_agents"))

try:
    from shared.workflow_logger import workflow_logger, WorkflowStepType, WorkflowStepStatus
    print("✅ Successfully imported workflow_logger")
except ImportError as e:
    print(f"❌ Failed to import workflow_logger: {e}")
    exit(1)

def test_workflow_logger_basic():
    """Test basic workflow logger functionality"""
    print("\n🧪 Testing Basic Workflow Logger Functionality...")
    
    test_claim_id = f"TEST_INTEGRATION_{datetime.now().strftime('%H%M%S')}"
    
    try:
        # Test claim processing start
        workflow_logger.start_claim_processing(test_claim_id)
        print(f"✅ Started claim processing for {test_claim_id}")
        
        # Test discovery logging
        discovery_step_id = workflow_logger.log_discovery(
            agents_found=3,
            agent_details=[
                {"agent_id": "intake_clarifier", "name": "Intake Clarifier", "skills": 2},
                {"agent_id": "document_intelligence", "name": "Document Intelligence", "skills": 4},
                {"agent_id": "coverage_rules_engine", "name": "Coverage Rules Engine", "skills": 4}
            ]
        )
        print(f"✅ Logged discovery step: {discovery_step_id}")
        
        # Test agent selection logging
        selection_step_id = workflow_logger.log_agent_selection(
            task_type="claim_intake",
            selected_agent="intake_clarifier", 
            agent_name="Intake Clarifier Agent",
            reasoning="Best match for fraud detection and validation",
            alternatives=["document_intelligence"]
        )
        print(f"✅ Logged agent selection step: {selection_step_id}")
        
        # Test task dispatch logging
        dispatch_step_id = workflow_logger.log_task_dispatch(
            agent_name="intake_clarifier",
            task_description="Fraud detection and validation",
            agent_url="http://localhost:8002"
        )
        print(f"✅ Logged task dispatch step: {dispatch_step_id}")
        
        # Test agent response logging
        response_step_id = workflow_logger.log_agent_response(
            agent_name="intake_clarifier",
            success=True,
            response_summary="Successfully completed fraud detection",
            response_details={"risk_score": 0.3, "validation": "passed"}
        )
        print(f"✅ Logged agent response step: {response_step_id}")
        
        # Test final decision logging
        decision_step_id = workflow_logger.log_final_decision(
            decision="approved",
            reasoning="All validation checks passed, low risk score",
            confidence=0.95,
            factors={"fraud_risk": 0.3, "coverage_valid": True}
        )
        print(f"✅ Logged final decision step: {decision_step_id}")
        
        # Test completion logging
        completion_step_id = workflow_logger.log_completion(
            claim_id=test_claim_id,
            final_status="completed",
            processing_time_ms=2500
        )
        print(f"✅ Logged completion step: {completion_step_id}")
        
        # Verify steps were saved
        steps = workflow_logger.get_workflow_steps(test_claim_id)
        print(f"✅ Retrieved {len(steps)} workflow steps for {test_claim_id}")
        
        # Verify recent steps are available
        recent_steps = workflow_logger.get_all_recent_steps(10)
        print(f"✅ Retrieved {len(recent_steps)} recent workflow steps across all claims")
        
        return True, f"Created {len(steps)} workflow steps successfully"
        
    except Exception as e:
        print(f"❌ Basic workflow logger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

def test_workflow_storage():
    """Test that workflow steps are properly stored to file"""
    print("\n🧪 Testing Workflow Storage...")
    
    try:
        storage_file = workflow_logger.storage_file
        print(f"📁 Storage file: {storage_file}")
        print(f"📁 Storage exists: {storage_file.exists()}")
        
        if storage_file.exists():
            with open(storage_file, 'r') as f:
                data = json.load(f)
            
            claim_count = len(data.keys())
            total_steps = sum(len(steps) for steps in data.values())
            
            print(f"📊 Total claims in storage: {claim_count}")
            print(f"📊 Total workflow steps in storage: {total_steps}")
            
            # Show recent claim IDs
            recent_claims = list(data.keys())[-5:]  # Last 5 claims
            print(f"📋 Recent claim IDs: {recent_claims}")
            
            return True, f"Storage working: {claim_count} claims, {total_steps} steps"
        else:
            return False, "Storage file does not exist"
            
    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        return False, str(e)

def test_dashboard_api_compatibility():
    """Test that the workflow logger data is compatible with dashboard API"""
    print("\n🧪 Testing Dashboard API Compatibility...")
    
    try:
        # Test recent steps format
        recent_steps = workflow_logger.get_all_recent_steps(5)
        print(f"📊 Recent steps count: {len(recent_steps)}")
        
        if recent_steps:
            sample_step = recent_steps[0]
            required_fields = ['step_id', 'claim_id', 'step_type', 'title', 'description', 'status', 'timestamp']
            
            print(f"📋 Sample step keys: {list(sample_step.keys())}")
            
            missing_fields = []
            for field in required_fields:
                if field not in sample_step:
                    missing_fields.append(field)
            
            if missing_fields:
                return False, f"Missing required fields: {missing_fields}"
            else:
                print(f"✅ All required fields present in workflow steps")
                print(f"📋 Sample step: {sample_step['title']} - {sample_step['description']}")
                return True, "Dashboard API compatibility verified"
        else:
            return False, "No recent steps available for testing"
            
    except Exception as e:
        print(f"❌ Dashboard API compatibility test failed: {e}")
        return False, str(e)

async def test_orchestrator_integration():
    """Test actual orchestrator integration (requires running orchestrator)"""
    print("\n🧪 Testing Live Orchestrator Integration...")
    
    try:
        import aiohttp
        
        # Test if orchestrator is running
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:8001/", timeout=aiohttp.ClientTimeout(total=2)) as response:
                    orchestrator_running = True
                    print("✅ Orchestrator is running on localhost:8001")
            except:
                orchestrator_running = False
                print("⚠️ Orchestrator is not running on localhost:8001")
                return False, "Orchestrator not running - start it first"
        
        if not orchestrator_running:
            return False, "Cannot test integration without running orchestrator"
            
        # Count current workflow steps
        initial_steps = workflow_logger.get_all_recent_steps(100)
        initial_count = len(initial_steps)
        print(f"📊 Initial workflow steps count: {initial_count}")
        
        # Send test claim to orchestrator
        test_payload = {
            "jsonrpc": "2.0",
            "id": f"test-integration-{datetime.now().strftime('%H%M%S')}",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": f"msg-test-{datetime.now().strftime('%H%M%S')}",
                    "role": "user",
                    "parts": [
                        {
                            "kind": "text",
                            "text": json.dumps({
                                "action": "process_claim",
                                "claim_id": "TEST-INTEGRATION-001",
                                "claim_data": {
                                    "claim_id": "TEST-INTEGRATION-001",
                                    "type": "outpatient",
                                    "amount": 250.0,
                                    "description": "Integration test claim",
                                    "customer_id": "test_customer",
                                    "policy_number": "POL_TEST_001"
                                }
                            })
                        }
                    ]
                }
            }
        }
        
        print("📤 Sending test claim to orchestrator...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001",
                json=test_payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_text = await response.text()
                print(f"📥 Orchestrator response status: {response.status}")
                
        # Wait a moment for workflow logging to complete
        await asyncio.sleep(2)
        
        # Check if new workflow steps were created
        final_steps = workflow_logger.get_all_recent_steps(100)
        final_count = len(final_steps)
        new_steps_count = final_count - initial_count
        
        print(f"📊 Final workflow steps count: {final_count}")
        print(f"📊 New steps created: {new_steps_count}")
        
        if new_steps_count > 0:
            print("✅ Orchestrator integration working - new workflow steps created!")
            
            # Show the new steps
            new_steps = final_steps[:new_steps_count]
            for i, step in enumerate(new_steps):
                print(f"   {i+1}. {step['title']} - {step['description']}")
                
            return True, f"Integration working: {new_steps_count} new steps created"
        else:
            return False, "No new workflow steps created by orchestrator"
            
    except Exception as e:
        print(f"❌ Live orchestrator integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

def main():
    """Run all tests"""
    print("🧪 WORKFLOW LOGGER INTEGRATION TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Basic Functionality", test_workflow_logger_basic),
        ("Storage System", test_workflow_storage), 
        ("Dashboard API Compatibility", test_dashboard_api_compatibility),
    ]
    
    results = {}
    
    # Run synchronous tests
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        success, message = test_func()
        results[test_name] = (success, message)
        
        if success:
            print(f"✅ {test_name}: {message}")
        else:
            print(f"❌ {test_name}: {message}")
    
    # Run async test
    print(f"\n🔍 Running: Live Orchestrator Integration")
    try:
        success, message = asyncio.run(test_orchestrator_integration())
        results["Live Orchestrator Integration"] = (success, message)
        
        if success:
            print(f"✅ Live Orchestrator Integration: {message}")
        else:
            print(f"❌ Live Orchestrator Integration: {message}")
    except Exception as e:
        print(f"❌ Live Orchestrator Integration: Failed to run - {e}")
        results["Live Orchestrator Integration"] = (False, str(e))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for success, _ in results.values() if success)
    total = len(results)
    
    for test_name, (success, message) in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not success:
            print(f"      Reason: {message}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Workflow logger integration is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the issues above.")

if __name__ == "__main__":
    main()
