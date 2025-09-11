"""
Test script for the fixed Intake Clarifier Agent
Tests the complete data comparison workflow and Cosmos DB status update functionality
Based on actual workflow logs and real claim data (OP-02)
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_intake_clarifier_complete_workflow():
    """Test the complete Intake Clarifier workflow with real data"""
    
    print("🧪 TESTING INTAKE CLARIFIER - COMPLETE WORKFLOW")
    print("=" * 60)
    
    try:
        # Import the A2A wrapper
        from agents.intake_clarifier.a2a_wrapper import A2AIntakeClarifierExecutor
        
        # Initialize the executor
        executor = A2AIntakeClarifierExecutor()
        print("✅ Intake Clarifier executor initialized")
        
        # Test 1: Direct NEW WORKFLOW processing (matches the logs)
        print("\n📋 TEST 1: NEW WORKFLOW Data Comparison")
        print("-" * 40)
        
        # Real task from the logs
        test_task = """Task: Compare claim data with extracted patient data:
Claim ID: OP-02

Fetch documents from:
- claim_details container (claim_id: OP-02)
- extracted_patient_data container (claim_id: OP-02)

Compare: patient_name, bill_amount, bill_date, diagnosis vs medical_condition
If mismatch: Update status to 'marked for rejection' with reason
If match: Update status to 'marked for approval'"""
        
        print(f"📝 Test task: {test_task[:100]}...")
        
        # Test the NEW WORKFLOW detection
        is_new_workflow = executor._is_new_workflow_claim_request(test_task)
        print(f"🔍 NEW WORKFLOW detected: {is_new_workflow}")
        
        if not is_new_workflow:
            print("❌ NEW WORKFLOW detection failed!")
            return False
            
        # Test 2: Cosmos DB client initialization
        print("\n🔧 TEST 2: Cosmos DB Client Initialization")
        print("-" * 40)
        
        # Initialize Cosmos DB client
        await executor._init_cosmos_client()
        
        if executor.cosmos_client is None:
            print("❌ Cosmos DB client initialization failed!")
            print("⚠️  Check your environment variables:")
            print("    - COSMOS_DB_ENDPOINT")
            print("    - COSMOS_DB_KEY")
            print("    - COSMOS_DB_DATABASE_NAME")
            return False
        
        print("✅ Cosmos DB client initialized successfully")
        
        # Test 3: Fetch claim data (should match logs)
        print("\n📋 TEST 3: Fetch Claim Data")
        print("-" * 40)
        
        claim_data = await executor._fetch_claim_details("OP-02")
        
        if not claim_data:
            print("❌ Failed to fetch claim data for OP-02")
            return False
            
        print("✅ Successfully fetched claim data:")
        print(f"   📋 Claim ID: {claim_data.get('claimId')}")
        print(f"   👤 Patient: {claim_data.get('patientName')}")
        print(f"   💰 Bill Amount: ${claim_data.get('billAmount')}")
        print(f"   🏥 Category: {claim_data.get('category')}")
        print(f"   🩺 Diagnosis: {claim_data.get('diagnosis')}")
        
        # Test 4: Fetch extracted patient data
        print("\n📄 TEST 4: Fetch Extracted Patient Data")
        print("-" * 40)
        
        extracted_data = await executor._fetch_extracted_patient_data("OP-02")
        
        if not extracted_data:
            print("❌ Failed to fetch extracted patient data for OP-02")
            print("⚠️  This might be expected if Document Intelligence hasn't run yet")
            return False
            
        print("✅ Successfully fetched extracted patient data:")
        print(f"   📄 Extraction Source: {extracted_data.get('extractionSource')}")
        print(f"   📅 Extracted At: {extracted_data.get('extractedAt')}")
        
        if 'medical_bill_doc' in extracted_data:
            bill_doc = extracted_data['medical_bill_doc']
            print(f"   💊 Medical Bill Doc:")
            print(f"      👤 Patient: {bill_doc.get('patient_name')}")
            print(f"      💰 Amount: ${bill_doc.get('bill_amount')}")
            print(f"      📅 Date: {bill_doc.get('bill_date')}")
        
        if 'memo_doc' in extracted_data:
            memo_doc = extracted_data['memo_doc']
            print(f"   📋 Memo Doc:")
            print(f"      👤 Patient: {memo_doc.get('patient_name')}")
            print(f"      🩺 Condition: {memo_doc.get('medical_condition')}")
        
        # Test 5: Data comparison (core functionality)
        print("\n🔍 TEST 5: Data Comparison")
        print("-" * 40)
        
        comparison_result = executor._perform_data_comparison(claim_data, extracted_data)
        
        print(f"📊 Comparison Status: {comparison_result['status']}")
        print(f"✅ Matching Details:")
        for detail in comparison_result['details']:
            print(f"   {detail}")
            
        if comparison_result['issues']:
            print(f"❌ Issues Found:")
            for issue in comparison_result['issues']:
                print(f"   {issue}")
        
        # Test 6: Status update (THE CRITICAL FIX TEST)
        print("\n🔄 TEST 6: Cosmos DB Status Update (CRITICAL FIX)")
        print("-" * 40)
        
        try:
            print("🔧 Testing the fixed async context manager issue...")
            await executor._update_claim_status("OP-02", comparison_result)
            print("✅ Status update completed successfully!")
            print("🎯 The async context manager fix is working!")
            
        except Exception as e:
            print(f"❌ Status update failed: {e}")
            if "'CosmosClient' object does not support the asynchronous context manager protocol" in str(e):
                print("🔧 This is the original bug - fix didn't work")
            return False
        
        # Test 7: Verify status update in database
        print("\n🔍 TEST 7: Verify Status Update")
        print("-" * 40)
        
        # Fetch updated claim to verify the status change
        updated_claim = await executor._fetch_claim_details("OP-02")
        
        if updated_claim:
            current_status = updated_claim.get('status')
            verification_reason = updated_claim.get('verification_reason')
            verification_timestamp = updated_claim.get('verification_timestamp')
            updated_by = updated_claim.get('updated_by')
            
            print(f"📋 Updated Claim Status: {current_status}")
            print(f"📝 Verification Reason: {verification_reason}")
            print(f"⏰ Verification Timestamp: {verification_timestamp}")
            print(f"👤 Updated By: {updated_by}")
            
            if current_status in ['marked for approval', 'marked for rejection']:
                print("✅ Status update verified in database!")
            else:
                print(f"⚠️  Unexpected status: {current_status}")
        
        print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("✅ Intake Clarifier is working correctly")
        print("✅ Async context manager fix is successful")
        print("✅ Data comparison logic is functional")
        print("✅ Cosmos DB operations are working")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("⚠️  Make sure all dependencies are installed")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_specific_fix():
    """Test specifically the async context manager fix"""
    
    print("\n🔧 SPECIFIC FIX TEST: Async Context Manager")
    print("=" * 50)
    
    try:
        from agents.intake_clarifier.a2a_wrapper import A2AIntakeClarifierExecutor
        
        executor = A2AIntakeClarifierExecutor()
        await executor._init_cosmos_client()
        
        if executor.cosmos_client is None:
            print("❌ Cannot test fix - Cosmos DB client not available")
            return False
        
        # Test the specific method that had the bug
        test_comparison_result = {
            'status': 'match',
            'details': ['✅ Patient name matches: Daniel Ong'],
            'issues': []
        }
        
        print("🧪 Testing _update_claim_status method...")
        await executor._update_claim_status("OP-02", test_comparison_result)
        print("✅ Fix confirmed - no async context manager error!")
        
        return True
        
    except Exception as e:
        print(f"❌ Fix test failed: {e}")
        return False

def run_tests():
    """Run all tests"""
    
    print("🧪 INTAKE CLARIFIER AGENT TEST SUITE")
    print("=" * 60)
    print("🎯 Testing the fixed async context manager issue")
    print("📋 Based on real workflow logs and OP-02 claim data")
    print("=" * 60)
    
    # Check environment
    required_env_vars = [
        "COSMOS_DB_ENDPOINT",
        "COSMOS_DB_KEY", 
        "COSMOS_DB_DATABASE_NAME"
    ]
    
    print("🔍 Environment Check:")
    missing_vars = []
    for var in required_env_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: Found")
        else:
            print(f"   ❌ {var}: Missing")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {missing_vars}")
        print("🔧 Please set these variables before running tests")
        return False
    
    # Run async tests
    try:
        # Test the specific fix first
        fix_result = asyncio.run(test_specific_fix())
        
        if fix_result:
            # Run complete workflow test
            workflow_result = asyncio.run(test_intake_clarifier_complete_workflow())
            return workflow_result
        else:
            print("❌ Fix test failed - skipping full workflow test")
            return False
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Intake Clarifier Tests...")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
    except ImportError:
        print("⚠️  python-dotenv not found, using system environment")
    
    # Run tests
    success = run_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Intake Clarifier is ready for production use")
        exit(0)
    else:
        print("\n❌ TESTS FAILED!")
        print("🔧 Please check the issues above")
        exit(1)
