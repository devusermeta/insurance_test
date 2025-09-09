#!/usr/bin/env python3
"""
End-to-End Workflow Test
Test the complete flow: Dashboard -> Orchestrator -> Workflow Logger -> Dashboard API
"""

import asyncio
import requests
import json
import time
import sys
from pathlib import Path

# Add path for imports
sys.path.append(str(Path(__file__).parent / "insurance_agents"))

async def test_complete_workflow():
    """Test the complete claim processing workflow"""
    
    print("🧪 COMPLETE WORKFLOW TEST")
    print("=" * 60)
    
    claim_id = "TEST_WORKFLOW_001"  # Use a test claim ID
    
    try:
        # Step 1: Start processing session (simulating dashboard button click)
        print(f"🚀 Step 1: Starting processing session for {claim_id}")
        session_response = requests.post(f'http://localhost:3000/api/start-processing/{claim_id}')
        
        if session_response.status_code == 200:
            print("✅ Processing session started successfully")
            print(f"   Response: {session_response.json()}")
        else:
            print(f"❌ Failed to start session: {session_response.status_code}")
            return
        
        # Step 2: Check if processing steps API shows the session
        print(f"\n🔍 Step 2: Checking processing steps API (should still be empty)")
        steps_response = requests.get('http://localhost:3000/api/processing-steps')
        
        if steps_response.status_code == 200:
            steps_data = steps_response.json()
            print(f"📊 Processing steps: {len(steps_data['steps'])} steps")
            if steps_data['steps']:
                for i, step in enumerate(steps_data['steps'][:3]):
                    print(f"   {i+1}. {step.get('title', 'No title')} - Claim: {step.get('claim_id')}")
        
        # Step 3: Send claim processing request to orchestrator (simulating real processing)
        print(f"\n🎯 Step 3: Sending claim to orchestrator for processing...")
        
        claim_request = {
            "action": "process_claim",
            "claim_id": claim_id,
            "claim_data": {
                "claim_id": claim_id,
                "type": "outpatient", 
                "amount": 250.0,
                "description": f"Test workflow integration for {claim_id}",
                "customer_id": "test_customer",
                "policy_number": f"POL_{claim_id}",
                "incident_date": "2025-01-15",
                "location": "Test Processing",
                "documents": ["test_claim_form.pdf", "test_supporting_docs.pdf"],
                "customer_statement": f"Testing end-to-end workflow integration for {claim_id}",
                "patient_name": "Test Patient",
                "provider": "TEST-PROVIDER", 
                "member_id": "M-TEST",
                "region": "US"
            }
        }
        
        # Send to orchestrator
        orchestrator_response = requests.post(
            'http://localhost:8001', 
            json=claim_request,
            headers={'Content-Type': 'application/json'}
        )
        
        if orchestrator_response.status_code == 200:
            print("✅ Claim sent to orchestrator successfully")
            response_data = orchestrator_response.json()
            print(f"   Orchestrator response: {str(response_data)[:200]}...")
        else:
            print(f"❌ Failed to send to orchestrator: {orchestrator_response.status_code}")
            print(f"   Error: {orchestrator_response.text[:200]}...")
        
        # Step 4: Wait a moment for processing to start, then check steps API
        print(f"\n⏳ Step 4: Waiting 3 seconds for processing to begin...")
        time.sleep(3)
        
        print(f"🔍 Checking processing steps API (should now have real-time steps)")
        steps_response = requests.get('http://localhost:3000/api/processing-steps')
        
        if steps_response.status_code == 200:
            steps_data = steps_response.json()
            print(f"📊 Processing steps: {len(steps_data['steps'])} steps")
            
            if steps_data['steps']:
                print("📋 Real-time workflow steps:")
                for i, step in enumerate(steps_data['steps']):
                    print(f"   {i+1}. {step.get('title', 'No title')}")
                    print(f"      Claim: {step.get('claim_id')} | Status: {step.get('status')}")
                    print(f"      Time: {step.get('timestamp')}")
                    print()
            else:
                print("⚠️  Still no steps found")
        
        # Step 5: Wait for processing to complete
        print(f"\n⏳ Step 5: Waiting 15 seconds for processing to complete...")
        time.sleep(15)
        
        print(f"🔍 Final check of processing steps API")
        steps_response = requests.get('http://localhost:3000/api/processing-steps')
        
        if steps_response.status_code == 200:
            steps_data = steps_response.json()
            print(f"📊 Final processing steps: {len(steps_data['steps'])} steps")
            
            if steps_data['steps']:
                print("📋 Final workflow state:")
                completed_steps = [s for s in steps_data['steps'] if s.get('status') == 'completed']
                print(f"   ✅ Completed steps: {len(completed_steps)}")
                
                # Show the final claim ID being used
                claim_ids = set(s.get('claim_id') for s in steps_data['steps'])
                print(f"   🎯 Claim IDs in workflow: {list(claim_ids)}")
                
                if claim_id in claim_ids:
                    print(f"   ✅ SUCCESS: Our test claim ID {claim_id} is being used!")
                else:
                    print(f"   ❌ ISSUE: Expected {claim_id}, but got {list(claim_ids)}")
        
        # Step 6: Stop the processing session
        print(f"\n🛑 Step 6: Stopping processing session...")
        stop_response = requests.post(f'http://localhost:3000/api/stop-processing/{claim_id}')
        
        if stop_response.status_code == 200:
            print("✅ Processing session stopped")
            print(f"   Response: {stop_response.json()}")
        
        # Final check - steps should now be empty
        print(f"\n🔍 Final verification: Processing steps should now be empty")
        steps_response = requests.get('http://localhost:3000/api/processing-steps')
        
        if steps_response.status_code == 200:
            steps_data = steps_response.json()
            print(f"📊 Steps after session stop: {len(steps_data['steps'])} steps")
            
            if len(steps_data['steps']) == 0:
                print("✅ Perfect! Steps cleared after session ended")
            else:
                print("⚠️  Steps still showing - may need session cleanup fix")
        
        print("\n" + "=" * 60)
        print("🏁 WORKFLOW TEST COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error during workflow test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
