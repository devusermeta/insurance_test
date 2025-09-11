#!/usr/bin/env python3
"""
Test Document Intelligence workflow with a new claim ID to see actual processing
"""

import asyncio
import httpx
import uuid
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

async def test_new_claim_processing():
    """Test Document Intelligence with a fresh claim ID"""
    
    # Use a new claim ID that doesn't exist yet
    new_claim_id = "OP-01"
    
    print(f"🧪 Testing Document Intelligence with NEW claim: {new_claim_id}")
    print("=" * 70)
    
    # Create the task request with document URLs
    task_request = f"""Process documents and create extracted_patient_data for:
Claim ID: {new_claim_id}
Category: Outpatient

Extract from documents and create document in extracted_patient_data container:
- Patient name, Bill amount, Bill date, Medical condition
- Document ID should be: {new_claim_id}

Document URLs to process:
- Document 1: https://captainpstorage1120d503b.blob.core.windows.net/outpatients/OP-04/OP-04_Medical_Bill.pdf 
- Document 2: https://captainpstorage1120d503b.blob.core.windows.net/outpatients/OP-04/OP-04_Memo.pdf"""

    print(f"📝 Task request:\n{task_request}\n")
    
    # Create proper A2A JSON-RPC payload
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
    
    # Send request to Document Intelligence agent
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"🔄 Sending request to Document Intelligence agent...")
            response = await client.post(
                "http://localhost:8003",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📄 Response content: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                message_text = result.get("result", {}).get("parts", [{}])[0].get("text", "")
                print(f"\n✅ Agent Response: {message_text}")
                
                # Check if processing was successful
                if "successfully processed" in message_text.lower():
                    print(f"\n🎉 SUCCESS: Document Intelligence processed {new_claim_id}")
                    
                    # Verify the document was created in Cosmos DB
                    await verify_document_in_cosmos(new_claim_id)
                else:
                    print(f"\n⚠️ Processing result: {message_text}")
            else:
                print(f"❌ Request failed with status {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error sending request: {e}")

async def verify_document_in_cosmos(claim_id: str):
    """Verify that the document was created in Cosmos DB"""
    try:
        from azure.cosmos import CosmosClient
        
        endpoint = os.getenv("COSMOS_ENDPOINT")
        key = os.getenv("COSMOS_KEY")
        database_name = os.getenv("COSMOS_DATABASE_NAME", "insurance")
        
        if not endpoint or not key:
            print("❌ Missing Cosmos DB credentials")
            return
        
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client("extracted_patient_data")
        
        # Query for the document
        query = f"SELECT * FROM c WHERE c.claimId = '{claim_id}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if items:
            document = items[0]
            print(f"\n🔍 Document found in Cosmos DB:")
            print(f"   📋 ID: {document.get('id')}")
            print(f"   📋 Claim ID: {document.get('claimId')}")
            print(f"   📋 Extracted At: {document.get('extractedAt')}")
            print(f"   📋 Extraction Source: {document.get('extractionSource')}")
            
            # Check for extracted document data
            for key, value in document.items():
                if key.endswith('_doc') and isinstance(value, dict):
                    print(f"   📄 {key}: {value}")
            
            return True
        else:
            print(f"\n❌ No document found for claim {claim_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying document: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_new_claim_processing())
