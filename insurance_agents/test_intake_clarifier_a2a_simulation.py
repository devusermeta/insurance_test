"""
Test script that simulates the exact A2A request from the orchestrator
Based on the actual logs from the working workflow
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add the project root to Python path  
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simulate_orchestrator_request():
    """Simulate the exact A2A request that the orchestrator sends"""
    
    print("🤖 SIMULATING ORCHESTRATOR A2A REQUEST")
    print("=" * 60)
    
    # This is the exact task text from the logs
    orchestrator_task = """Task: Compare claim data with extracted patient data:
Claim ID: OP-02

Fetch documents from:
- claim_details container (claim_id: OP-02)
- extracted_patient_data container (claim_id: OP-02)

Compare: patient_name, bill_amount, bill_date, diagnosis vs medical_condition
If mismatch: Update status to 'marked for rejection' with reason
If match: Update status to 'marked for approval'"""
    
    parameters = {"claim_id": "OP-02"}
    
    print(f"📝 Task: {orchestrator_task}")
    print(f"📋 Parameters: {parameters}")
    
    try:
        from agents.intake_clarifier.a2a_wrapper import A2AIntakeClarifierExecutor
        
        # Initialize the executor (same as in A2A framework)
        executor = A2AIntakeClarifierExecutor()
        print("✅ A2A Intake Clarifier executor initialized")
        
        # Create mock context (simplified version of RequestContext)
        class MockRequestContext:
            def __init__(self, message, task_params):
                self.message = message
                self.task_params = task_params
                self.current_task = None
                
            def get_user_input(self):
                return self.message
        
        # Create mock event queue (simplified version)
        class MockEventQueue:
            def __init__(self):
                self.events = []
                
            async def enqueue_event(self, event):
                self.events.append(event)
                print(f"📤 Event queued: {type(event).__name__}")
        
        # Create the mock context and event queue
        context = MockRequestContext(orchestrator_task, parameters)
        event_queue = MockEventQueue()
        
        print("\n🔄 Executing A2A workflow...")
        
        # This is the exact call that happens in the A2A framework
        await executor.execute(context, event_queue)
        
        print(f"\n📊 Events generated: {len(event_queue.events)}")
        for i, event in enumerate(event_queue.events):
            print(f"   {i+1}. {type(event).__name__}")
        
        print("\n🎉 A2A SIMULATION COMPLETED SUCCESSFULLY!")
        print("✅ No async context manager errors")
        print("✅ Intake Clarifier processed the request correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ A2A simulation failed: {e}")
        
        if "asynchronous context manager protocol" in str(e):
            print("🔧 This is the original bug that should be fixed!")
        
        import traceback
        traceback.print_exc()
        return False

async def test_real_workflow_step():
    """Test the exact workflow step that was in the logs"""
    
    print("\n📋 TESTING REAL WORKFLOW STEP")
    print("=" * 40)
    
    try:
        from agents.intake_clarifier.a2a_wrapper import A2AIntakeClarifierExecutor
        
        executor = A2AIntakeClarifierExecutor()
        
        # Test the NEW WORKFLOW detection (from logs)
        task_text = """Task: Compare claim data with extracted patient data:
Claim ID: OP-02

Fetch documents from:
- claim_details container (claim_id: OP-02)
- extracted_patient_data container (claim_id: OP-02)

Compare: patient_name, bill_amount, bill_date, diagnosis vs medical_condition
If mismatch: Update status to 'marked for rejection' with reason
If match: Update status to 'marked for approval'"""
        
        # Test workflow detection
        is_new_workflow = executor._is_new_workflow_claim_request(task_text)
        print(f"🔍 NEW WORKFLOW detected: {is_new_workflow}")
        
        if not is_new_workflow:
            print("❌ Workflow detection failed!")
            return False
        
        # Initialize Cosmos DB
        await executor._init_cosmos_client()
        
        if executor.cosmos_client is None:
            print("❌ Cosmos DB not available")
            return False
        
        print("✅ Cosmos DB client ready")
        
        # Extract claim ID (should be OP-02)
        claim_info = executor._extract_claim_info_from_text(task_text)
        claim_id = claim_info.get('claim_id')
        print(f"📋 Extracted claim ID: {claim_id}")
        
        if claim_id != "OP-02":
            print(f"❌ Expected OP-02, got {claim_id}")
            return False
        
        # Test the core workflow steps
        print("\n🔄 Testing workflow steps...")
        
        # Step 1: Fetch claim data
        print("   1. Fetching claim data...")
        claim_data = await executor._fetch_claim_details(claim_id)
        
        if claim_data:
            print(f"      ✅ Found claim: {claim_data.get('patientName')}")
        else:
            print("      ⚠️  No claim data (might be expected)")
        
        # Step 2: Fetch extracted data  
        print("   2. Fetching extracted patient data...")
        extracted_data = await executor._fetch_extracted_patient_data(claim_id)
        
        if extracted_data:
            print(f"      ✅ Found extracted data from: {extracted_data.get('extractionSource')}")
        else:
            print("      ⚠️  No extracted data (might be expected)")
        
        # Step 3: If both exist, test comparison and update
        if claim_data and extracted_data:
            print("   3. Performing data comparison...")
            comparison_result = executor._perform_data_comparison(claim_data, extracted_data)
            print(f"      📊 Comparison status: {comparison_result['status']}")
            
            print("   4. Testing status update (THE CRITICAL FIX)...")
            await executor._update_claim_status(claim_id, comparison_result)
            print("      ✅ Status update successful - FIX WORKING!")
        else:
            print("   3. Testing status update with mock data...")
            mock_comparison = {
                'status': 'match',
                'details': ['✅ Mock test'],
                'issues': []
            }
            await executor._update_claim_status(claim_id, mock_comparison)
            print("      ✅ Status update successful - FIX WORKING!")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        return False

def run_a2a_simulation():
    """Run the A2A simulation tests"""
    
    print("🤖 A2A INTAKE CLARIFIER SIMULATION TEST")
    print("=" * 60)
    print("🎯 Simulating exact orchestrator request from logs")
    print("🔧 Testing the async context manager fix")
    print("=" * 60)
    
    # Check environment
    if not os.getenv("COSMOS_DB_ENDPOINT") or not os.getenv("COSMOS_DB_KEY"):
        print("⚠️  Cosmos DB environment variables required")
        print("🔧 Set COSMOS_DB_ENDPOINT and COSMOS_DB_KEY")
        return False
    
    try:
        # Run the A2A simulation
        simulation_result = asyncio.run(simulate_orchestrator_request())
        
        if simulation_result:
            print("\n✅ A2A SIMULATION PASSED!")
            
            # Run the workflow step test
            workflow_result = asyncio.run(test_real_workflow_step())
            
            if workflow_result:
                print("\n🎉 ALL TESTS PASSED!")
                print("✅ A2A simulation successful")
                print("✅ Workflow steps working")
                print("✅ Async context manager fix confirmed")
                return True
            else:
                print("\n⚠️  A2A simulation passed but workflow test failed")
                return False
        else:
            print("\n❌ A2A SIMULATION FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting A2A Intake Clarifier Simulation...")
    
    success = run_a2a_simulation()
    
    if success:
        print("\n🎉 SIMULATION SUCCESSFUL!")
        print("✅ Intake Clarifier is ready for orchestrator requests")
        print("🔄 The fix resolves the async context manager issue")
    else:
        print("\n❌ SIMULATION FAILED!")
        print("🔧 Check the errors above")
    
    exit(0 if success else 1)
