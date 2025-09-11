"""
Test Cosmos DB Client Operations
Tests the new cosmos_db_client.py utilities for the claim processing workflow
"""

import asyncio
import json
from shared.cosmos_db_client import CosmosDBClient, get_cosmos_client

async def test_cosmos_connection():
    """Test basic Cosmos DB connection"""
    print("🧪 Testing Cosmos DB Connection...")
    
    try:
        client = CosmosDBClient()
        success = await client.initialize()
        
        if success:
            print("✅ Cosmos DB connection successful!")
            
            # Test connection
            connection_ok = await client.check_connection()
            if connection_ok:
                print("✅ Connection test passed!")
            else:
                print("❌ Connection test failed!")
                
        else:
            print("❌ Failed to initialize Cosmos DB client")
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")

async def test_claim_operations():
    """Test claim-related operations"""
    print("\n🧪 Testing Claim Operations...")
    
    try:
        client = await get_cosmos_client()
        
        # Test getting a sample claim (using your example)
        test_claim_id = "IP-01"  # From your sample data
        
        print(f"📋 Testing retrieval of claim: {test_claim_id}")
        claim = await client.get_claim_by_id(test_claim_id)
        
        if claim:
            print(f"✅ Successfully retrieved claim: {test_claim_id}")
            print(f"   Patient: {claim.get('patientName')}")
            print(f"   Status: {claim.get('status')}")
            print(f"   Category: {claim.get('category')}")
            print(f"   Bill Amount: ${claim.get('billAmount')}")
            print(f"   Diagnosis: {claim.get('diagnosis')}")
            
            # Test status update
            print(f"\n📝 Testing status update...")
            old_status = claim.get('status')
            test_status = "processing_test"
            
            success = await client.update_claim_status(
                test_claim_id, 
                test_status, 
                "Test status update from cosmos_db_client test"
            )
            
            if success:
                print(f"✅ Status updated successfully: {old_status} → {test_status}")
                
                # Restore original status
                await client.update_claim_status(test_claim_id, old_status, "Restored original status")
                print(f"🔄 Restored original status: {old_status}")
            else:
                print(f"❌ Failed to update status")
                
        else:
            print(f"⚠️ Claim {test_claim_id} not found - this is expected if claim doesn't exist yet")
            
    except Exception as e:
        print(f"❌ Claim operations test error: {e}")

async def test_extracted_data_operations():
    """Test extracted patient data operations"""
    print("\n🧪 Testing Extracted Data Operations...")
    
    try:
        client = await get_cosmos_client()
        
        test_claim_id = "TEST-001"
        
        # Test saving extracted data
        sample_extracted_data = {
            "discharge_summary_doc": {
                "patient_name": "John Doe Test",
                "hospital_name": "Test Hospital",
                "admit_date": "2024-01-15",
                "discharge_date": "2024-01-18",
                "medical_condition": "Test condition"
            },
            "medical_bill_doc": {
                "patient_name": "John Doe Test",
                "bill_date": "2024-01-18",
                "bill_amount": 1500.00
            },
            "memo_doc": {
                "patient_name": "John Doe Test", 
                "medical_condition": "Test condition"
            }
        }
        
        print(f"💾 Testing save extracted data for claim: {test_claim_id}")
        success = await client.save_extracted_data(test_claim_id, sample_extracted_data)
        
        if success:
            print("✅ Successfully saved extracted data!")
            
            # Test retrieving the data
            print(f"🔍 Testing retrieval of extracted data...")
            retrieved_data = await client.get_extracted_data(test_claim_id)
            
            if retrieved_data:
                print("✅ Successfully retrieved extracted data!")
                print(f"   Extracted at: {retrieved_data.get('extractedAt')}")
                print(f"   Patient name: {retrieved_data.get('discharge_summary_doc', {}).get('patient_name')}")
                print(f"   Bill amount: ${retrieved_data.get('medical_bill_doc', {}).get('bill_amount')}")
            else:
                print("❌ Failed to retrieve extracted data")
                
        else:
            print("❌ Failed to save extracted data")
            
    except Exception as e:
        print(f"❌ Extracted data operations test error: {e}")

async def test_workflow_logging():
    """Test workflow step logging"""
    print("\n🧪 Testing Workflow Logging...")
    
    try:
        client = await get_cosmos_client()
        
        test_claim_id = "TEST-001"
        
        # Log several workflow steps
        workflow_steps = [
            ("claim_extraction", "orchestrator", "success", {"extracted_fields": 5}),
            ("coverage_check", "coverage_rules_engine", "success", {"rules_passed": True}),
            ("document_processing", "document_intelligence", "success", {"documents_processed": 3}),
            ("intake_verification", "intake_clarifier", "success", {"verification_passed": True})
        ]
        
        for step_name, agent, status, details in workflow_steps:
            success = await client.log_workflow_step(test_claim_id, step_name, agent, status, details)
            if success:
                print(f"✅ Logged workflow step: {step_name}")
            else:
                print(f"❌ Failed to log workflow step: {step_name}")
                
    except Exception as e:
        print(f"❌ Workflow logging test error: {e}")

async def main():
    """Run all tests"""
    print("🚀 Starting Cosmos DB Client Tests...")
    print("=" * 50)
    
    await test_cosmos_connection()
    await test_claim_operations()
    await test_extracted_data_operations() 
    await test_workflow_logging()
    
    print("\n" + "=" * 50)
    print("🏁 Cosmos DB Client Tests Complete!")

if __name__ == "__main__":
    asyncio.run(main())
