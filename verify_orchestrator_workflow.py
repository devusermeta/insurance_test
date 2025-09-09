#!/usr/bin/env python3
"""
Simple Orchestrator Workflow Test
Tests if orchestrator actually creates workflow steps when processing claims
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import sys
import os
from pathlib import Path

# Add the insurance_agents directory to path for imports
sys.path.append(str(Path(__file__).parent / "insurance_agents"))

try:
    from shared.workflow_logger import workflow_logger
    print("✅ Successfully imported workflow_logger")
except ImportError as e:
    print(f"❌ Failed to import workflow_logger: {e}")
    exit(1)

async def test_orchestrator_workflow_creation():
    """Send a claim to orchestrator and verify workflow steps are created"""
    
    print("\n🧪 Testing Real Orchestrator Workflow Step Creation...")
    
    # 1. Check initial state
    print("📊 Checking initial workflow state...")
    initial_steps = workflow_logger.get_all_recent_steps(50)
    initial_count = len(initial_steps)
    print(f"   Initial workflow steps count: {initial_count}")
    
    if initial_count > 0:
        print(f"   Latest step: {initial_steps[0]['title']} ({initial_steps[0]['timestamp']})")
    
    # 2. Send test claim to orchestrator
    test_claim_id = f"WORKFLOW_TEST_{datetime.now().strftime('%H%M%S')}"
    
    test_payload = {
        "jsonrpc": "2.0",
        "id": f"test-{datetime.now().strftime('%H%M%S')}",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": f"msg-{datetime.now().strftime('%H%M%S')}",
                "role": "user",
                "parts": [
                    {
                        "kind": "text",
                        "text": json.dumps({
                            "action": "process_claim",
                            "claim_id": test_claim_id,
                            "claim_data": {
                                "claim_id": test_claim_id,
                                "type": "outpatient",
                                "amount": 199.0,
                                "description": "Workflow logger integration test",
                                "customer_id": "test_workflow",
                                "policy_number": "POL_WORKFLOW_TEST"
                            }
                        })
                    }
                ]
            }
        }
    }
    
    print(f"📤 Sending test claim {test_claim_id} to orchestrator...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001",
                json=test_payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_text = await response.text()
                print(f"📥 Orchestrator response: {response.status}")
                if response.status != 200:
                    print(f"❌ Error response: {response_text}")
                    return False
                
    except Exception as e:
        print(f"❌ Failed to send request to orchestrator: {e}")
        return False
    
    # 3. Wait for processing to complete
    print("⏱️  Waiting for orchestrator to complete processing...")
    await asyncio.sleep(3)
    
    # 4. Check final state
    print("📊 Checking final workflow state...")
    final_steps = workflow_logger.get_all_recent_steps(50)
    final_count = len(final_steps)
    new_steps_count = final_count - initial_count
    
    print(f"   Final workflow steps count: {final_count}")
    print(f"   New steps created: {new_steps_count}")
    
    if new_steps_count > 0:
        print("✅ SUCCESS: New workflow steps detected!")
        print("📋 New steps created:")
        
        for i, step in enumerate(final_steps[:new_steps_count]):
            print(f"   {i+1}. [{step['step_id']}] {step['title']}")
            print(f"      Description: {step['description']}")
            print(f"      Status: {step['status']}")
            print(f"      Claim: {step['claim_id']}")
            print(f"      Time: {step['timestamp']}")
            print()
        
        # Check if our test claim is in the steps
        test_claim_steps = [step for step in final_steps if step['claim_id'] == test_claim_id]
        if test_claim_steps:
            print(f"✅ Found {len(test_claim_steps)} steps specifically for test claim {test_claim_id}")
        else:
            print(f"⚠️  No steps found for test claim {test_claim_id}, but other steps were created")
        
        return True
    else:
        print("❌ FAILED: No new workflow steps were created")
        print("🔍 This means the orchestrator is not calling workflow_logger methods")
        return False

def check_storage_file():
    """Check if workflow steps are being saved to storage file"""
    print("\n🧪 Checking Workflow Storage File...")
    
    storage_file = workflow_logger.storage_file
    print(f"📁 Storage file: {storage_file}")
    print(f"📁 File exists: {storage_file.exists()}")
    
    if storage_file.exists():
        try:
            with open(storage_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"📄 File size: {len(content)} characters")
                
                if content.strip() == '{}':
                    print("⚠️  File contains only empty JSON object")
                    return False
                else:
                    try:
                        data = json.loads(content)
                        claim_count = len(data)
                        total_steps = sum(len(steps) for steps in data.values()) if isinstance(data, dict) else 0
                        print(f"📊 Claims in storage: {claim_count}")
                        print(f"📊 Total steps in storage: {total_steps}")
                        
                        if claim_count > 0:
                            # Show recent claim IDs
                            recent_claims = list(data.keys())[-3:]
                            print(f"📋 Recent claims: {recent_claims}")
                            return True
                        else:
                            print("⚠️  No claims found in storage")
                            return False
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                        return False
                        
        except Exception as e:
            print(f"❌ Error reading storage file: {e}")
            return False
    else:
        print("❌ Storage file does not exist")
        return False

async def main():
    """Run the workflow integration test"""
    
    print("🧪 ORCHESTRATOR WORKFLOW INTEGRATION VERIFICATION")
    print("=" * 60)
    
    # Check if orchestrator is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8001/", timeout=aiohttp.ClientTimeout(total=2)) as response:
                print("✅ Orchestrator is running on localhost:8001")
    except:
        print("❌ Orchestrator is NOT running on localhost:8001")
        print("   Please start the orchestrator first with: python -m agents.claims_orchestrator")
        return
    
    # Test 1: Check current storage state
    storage_working = check_storage_file()
    
    # Test 2: Send claim and verify workflow steps are created
    workflow_working = await test_orchestrator_workflow_creation()
    
    # Test 3: Verify storage after claim processing
    storage_after = check_storage_file()
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 VERIFICATION RESULTS")
    print("=" * 60)
    
    print(f"📊 Storage Before: {'✅ Working' if storage_working else '❌ Empty/Failed'}")
    print(f"📊 Workflow Creation: {'✅ Working' if workflow_working else '❌ Failed'}")  
    print(f"📊 Storage After: {'✅ Working' if storage_after else '❌ Empty/Failed'}")
    
    if workflow_working and storage_after:
        print("\n🎉 CONCLUSION: Orchestrator workflow logger integration is WORKING!")
        print("   ✅ Orchestrator creates workflow steps")
        print("   ✅ Steps are saved to storage file") 
        print("   ✅ Dashboard should be able to display real workflow steps")
    elif workflow_working:
        print("\n⚠️  CONCLUSION: Orchestrator creates workflow steps but storage has issues")
        print("   ✅ Orchestrator creates workflow steps")
        print("   ❌ Storage file issues need to be resolved")
    else:
        print("\n❌ CONCLUSION: Orchestrator workflow logger integration is NOT working")
        print("   ❌ Orchestrator is not calling workflow_logger methods")
        print("   🔍 Debug the orchestrator code to see why workflow_logger calls aren't executing")

if __name__ == "__main__":
    asyncio.run(main())
