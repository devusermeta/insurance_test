#!/usr/bin/env python3
"""
Test Document Intelligence Agent - Exact Workflow Simulation
Based on the logs from the orchestrator workflow for claim OP-04

This test simulates:
1. Orchestrator retrieving complete claim data via MCP
2. LLM extraction of document URLs 
3. Sending request to Document Intelligence agent
4. Document Intelligence processing documents and creating extracted_patient_data
5. Verifying the document is created in Cosmos DB
"""

import asyncio
import json
import os
import httpx
from datetime import datetime
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DocumentIntelligenceWorkflowTest:
    def __init__(self):
        self.doc_intelligence_url = "http://localhost:8003"
        self.cosmos_client = None
        self.setup_cosmos_client()
    
    def setup_cosmos_client(self):
        """Initialize Cosmos DB client for verification"""
        try:
            endpoint = os.getenv("COSMOS_DB_ENDPOINT")
            key = os.getenv("COSMOS_DB_KEY")
            database_name = os.getenv("COSMOS_DB_DATABASE_NAME", "insurance")
            
            if endpoint and key:
                self.cosmos_client = CosmosClient(endpoint, key)
                self.database = self.cosmos_client.get_database_client(database_name)
                print("✅ Cosmos DB client initialized for verification")
            else:
                print("❌ Missing Cosmos DB credentials")
        except Exception as e:
            print(f"❌ Failed to initialize Cosmos DB client: {e}")
    
    def simulate_orchestrator_request(self, claim_id: str, category: str, document_urls: list) -> str:
        """Simulate the exact request format that orchestrator sends to Document Intelligence"""
        
        # This is the exact format from the logs
        base_task = f"""Process documents and create extracted_patient_data for:
Claim ID: {claim_id}
Category: {category}

Extract from documents and create document in extracted_patient_data container:
- Patient name, Bill amount, Bill date, Medical condition
- Document ID should be: {claim_id}"""
        
        # Add document URLs if provided (after LLM extraction)
        if document_urls:
            base_task += "\n\nDocument URLs to process:"
            for i, url in enumerate(document_urls, 1):
                base_task += f"\n- Document {i}: {url}"
        
        return base_task
    
    async def test_claim_op04_complete_workflow(self):
        """Test complete workflow for claim OP-04 exactly like orchestrator"""
        print("🚀 Testing Document Intelligence Workflow for Claim OP-04")
        print("=" * 70)
        
        # Step 1: Simulate MCP data retrieval (from orchestrator logs)
        claim_id = "OP-04"
        category = "Outpatient"
        
        print(f"📊 STEP 1: Simulating MCP data retrieval for {claim_id}")
        
        # This is the exact data structure from MCP response in logs
        complete_claim_data = {
            "id": "OP-04",
            "claimId": "OP-04", 
            "status": "submitted",
            "category": "Outpatient",
            "billAmount": 85,
            "billDate": "2025-09-03",
            "submittedAt": "2025-09-03T10:00:00Z",
            "lastUpdatedAt": "2025-09-08T14:00:00Z",
            "assignedEmployeeName": "Rajesh Kumar",
            "assignedEmployeeID": "EMP-7002",
            "patientName": "Jane Doe",
            "memberId": "M-004",
            "region": "US",
            "diagnosis": "Influenza-like illness",
            "serviceType": "consultation",
            "memoAttachment": "https://captainpstorage1120d503b.blob.core.windows.net/outpatients/OP-04/OP-04_Memo.pdf",
            "billAttachment": "https://captainpstorage1120d503b.blob.core.windows.net/outpatients/OP-04/OP-04_Medical_Bill.pdf"
        }
        
        print(f"✅ Retrieved complete claim data with attachments")
        print(f"🔗 billAttachment: {complete_claim_data['billAttachment']}")
        print(f"🔗 memoAttachment: {complete_claim_data['memoAttachment']}")
        
        # Step 2: Simulate LLM URL extraction (new feature)
        print(f"\n🧠 STEP 2: Simulating LLM URL extraction")
        
        document_urls = [
            complete_claim_data["billAttachment"],
            complete_claim_data["memoAttachment"]
        ]
        
        print(f"📎 LLM extracted {len(document_urls)} document URLs:")
        for i, url in enumerate(document_urls, 1):
            print(f"   {i}. {url}")
        
        # Step 3: Create orchestrator request with document URLs
        print(f"\n📄 STEP 3: Creating Document Intelligence request")
        
        task_request = self.simulate_orchestrator_request(claim_id, category, document_urls)
        print(f"📝 Task request:\n{task_request}")
        
        # Step 4: Send request to Document Intelligence agent
        print(f"\n🔄 STEP 4: Sending request to Document Intelligence agent")
        
        try:
            # Create proper A2A JSON-RPC payload
            import uuid
            
            payload = {
                "jsonrpc": "2.0",
                "id": f"a2a-document-intelligence-{uuid.uuid4()}",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": f"msg-{uuid.uuid4()}",
                        "role": "user",
                        "parts": [
                            {
                                "kind": "text",
                                "text": task_request
                            }
                        ]
                    },
                    "context_id": f"ctx-{uuid.uuid4()}",
                    "message_id": f"msg-{uuid.uuid4()}"
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.doc_intelligence_url,
                    json=payload,  # Send as JSON instead of plain text
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"📤 Request sent to: {self.doc_intelligence_url}")
                print(f"📥 Response status: {response.status_code}")
                print(f"📄 Response content: {response.text}")
                
                if response.status_code == 200:
                    print("✅ Document Intelligence request completed successfully")
                else:
                    print(f"❌ Document Intelligence request failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error sending request to Document Intelligence: {e}")
            return False
        
        # Step 5: Verify document creation in Cosmos DB
        print(f"\n🔍 STEP 5: Verifying document creation in extracted_patient_data container")
        
        if await self.verify_extracted_data_created(claim_id):
            print("✅ Document successfully created in extracted_patient_data container")
            return True
        else:
            print("❌ Document not found in extracted_patient_data container")
            return False
    
    async def verify_extracted_data_created(self, claim_id: str) -> bool:
        """Verify that the extracted document was created in Cosmos DB"""
        if not self.cosmos_client:
            print("⚠️ Cannot verify - Cosmos DB client not available")
            return False
        
        try:
            container = self.database.get_container_client("extracted_patient_data")
            
            # Query for the extracted document
            query = "SELECT * FROM c WHERE c.claimId = @claim_id"
            parameters = [{"name": "@claim_id", "value": claim_id}]
            
            items = list(container.query_items(query=query, parameters=parameters))
            
            if items:
                document = items[0]
                print(f"📄 Found extracted document in Cosmos DB:")
                print(f"   📋 ID: {document.get('id')}")
                print(f"   📋 Claim ID: {document.get('claimId')}")
                print(f"   📋 Extracted At: {document.get('extractedAt')}")
                print(f"   📋 Extraction Source: {document.get('extractionSource')}")
                
                # Check for document-specific data
                if 'medical_bill_doc' in document:
                    print(f"   📄 Medical Bill Doc: {document['medical_bill_doc']}")
                if 'memo_doc' in document:
                    print(f"   📄 Memo Doc: {document['memo_doc']}")
                
                return True
            else:
                print(f"❌ No extracted document found for claim {claim_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying extracted data: {e}")
            return False
    
    async def test_without_document_urls(self):
        """Test the scenario that was failing - no document URLs provided"""
        print("\n🚨 Testing FAILURE SCENARIO: No Document URLs")
        print("=" * 70)
        
        claim_id = "OP-04"
        category = "Outpatient"
        
        # Create request WITHOUT document URLs (old behavior)
        task_request = self.simulate_orchestrator_request(claim_id, category, [])
        print(f"📝 Task request (no URLs):\n{task_request}")
        
        try:
            # Create proper A2A JSON-RPC payload
            import uuid
            
            payload = {
                "jsonrpc": "2.0",
                "id": f"a2a-document-intelligence-{uuid.uuid4()}",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": f"msg-{uuid.uuid4()}",
                        "role": "user",
                        "parts": [
                            {
                                "kind": "text",
                                "text": task_request
                            }
                        ]
                    },
                    "context_id": f"ctx-{uuid.uuid4()}",
                    "message_id": f"msg-{uuid.uuid4()}"
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.doc_intelligence_url,
                    json=payload,  # Send as JSON instead of plain text
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"📥 Response status: {response.status_code}")
                print(f"📄 Response content: {response.text}")
                
                if "No document URLs provided by orchestrator" in response.text:
                    print("✅ Correctly detected missing document URLs")
                    return True
                else:
                    print("❌ Did not detect missing document URLs")
                    return False
                    
        except Exception as e:
            print(f"❌ Error in failure test: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all workflow tests"""
        print("🧪 Document Intelligence Workflow Tests")
        print("🎯 Testing exact orchestrator workflow based on logs")
        print("=" * 80)
        
        # Test 1: Complete workflow with document URLs
        test1_result = await self.test_claim_op04_complete_workflow()
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Test 2: Failure scenario (no URLs)
        test2_result = await self.test_without_document_urls()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print(f"✅ Complete Workflow Test: {'PASSED' if test1_result else 'FAILED'}")
        print(f"✅ Failure Scenario Test: {'PASSED' if test2_result else 'FAILED'}")
        
        if test1_result and test2_result:
            print("🎉 ALL TESTS PASSED - Document Intelligence workflow is working correctly!")
        else:
            print("❌ SOME TESTS FAILED - Check the logs above for details")
        
        return test1_result and test2_result

async def main():
    """Main test runner"""
    tester = DocumentIntelligenceWorkflowTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    print("🚀 Starting Document Intelligence Workflow Test")
    print("📋 This test simulates the exact orchestrator workflow from your logs")
    print("🎯 Make sure Document Intelligence agent is running on http://localhost:8003")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
