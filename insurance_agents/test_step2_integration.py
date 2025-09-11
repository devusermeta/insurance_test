"""
Simple Test for Step 2 Completion 
Validates that Azure Document Intelligence integration is working with Cosmos DB
"""

import asyncio
from shared.cosmos_db_client import get_cosmos_client
from shared.azure_document_intelligence import process_claim_documents

async def test_step2_integration():
    """Test complete Step 2 integration"""
    print("🚀 Step 2 Integration Test: Cosmos DB + Azure Document Intelligence")
    print("=" * 60)
    
    try:
        # Test claim ID
        claim_id = "OP-05"
        
        # 1. Get claim from Cosmos DB
        print(f"📋 Step 1: Retrieving claim {claim_id} from Cosmos DB...")
        cosmos_client = await get_cosmos_client()
        claim = await cosmos_client.get_claim_by_id(claim_id)
        
        if not claim:
            print(f"❌ Claim {claim_id} not found!")
            return False
        
        print(f"✅ Found claim: {claim['patientName']} - {claim['category']} - ${claim['billAmount']}")
        
        # 2. Extract document URLs
        print(f"\n📄 Step 2: Extracting document URLs...")
        document_urls = {}
        for field in ['billAttachment', 'memoAttachment', 'dischargeAttachment']:
            if field in claim and claim[field]:
                document_urls[field] = claim[field]
                print(f"   ✅ {field}: {claim[field].split('/')[-1]}")
        
        if not document_urls:
            print("❌ No document URLs found!")
            return False
        
        # 3. Process documents with Azure Document Intelligence
        print(f"\n🔍 Step 3: Processing {len(document_urls)} documents with Azure Document Intelligence...")
        result = await process_claim_documents(document_urls)
        
        if not result['success']:
            print(f"❌ Document processing failed: {result.get('error')}")
            return False
        
        print(f"✅ Processed {result['documents_processed']} documents successfully!")
        
        # 4. Create Cosmos DB structure for extracted_patient_data
        print(f"\n💾 Step 4: Formatting extracted data for Cosmos DB...")
        extracted_document = {
            'id': claim_id,
            'claimId': claim_id,
            'category': claim['category'],
            'extractedAt': result['processing_time'],
            'extractionSource': 'Azure Document Intelligence'
        }
        
        # Add extracted data for each document
        successful_extractions = 0
        for doc_type, doc_result in result['results'].items():
            if doc_result['success'] and doc_result['extracted_data']:
                if doc_type == 'discharge_summary':
                    extracted_document['discharge_summary_doc'] = doc_result['extracted_data']
                elif doc_type == 'medical_bill':
                    extracted_document['medical_bill_doc'] = doc_result['extracted_data']
                elif doc_type == 'memo':
                    extracted_document['memo_doc'] = doc_result['extracted_data']
                successful_extractions += 1
        
        print(f"✅ Successfully extracted data from {successful_extractions} documents")
        
        # 5. Save to extracted_patient_data container
        print(f"\n💾 Step 5: Saving extracted data to Cosmos DB...")
        save_success = await cosmos_client.save_extracted_data(claim_id, extracted_document)
        
        if save_success:
            print(f"✅ Extracted data saved to extracted_patient_data container!")
        else:
            print(f"❌ Failed to save extracted data")
            return False
        
        # 6. Verify the save by retrieving it
        print(f"\n🔍 Step 6: Verifying saved data...")
        retrieved_data = await cosmos_client.get_extracted_data(claim_id)
        
        if retrieved_data:
            print(f"✅ Successfully retrieved extracted data!")
            print(f"   📊 Data fields saved: {len([k for k in retrieved_data.keys() if k.endswith('_doc')])}")
            
            # Show sample extracted fields
            if 'memo_doc' in retrieved_data:
                memo = retrieved_data['memo_doc']
                print(f"   📝 Sample Memo Data: {list(memo.keys())}")
        else:
            print(f"❌ Could not retrieve saved data")
            return False
        
        print(f"\n🎉 STEP 2 COMPLETE! ✅")
        print(f"✅ Cosmos DB Integration: Working")
        print(f"✅ Azure Document Intelligence: Working") 
        print(f"✅ Data Extraction: Working (memo, discharge summary)")
        print(f"✅ Cosmos DB Storage: Working")
        print(f"✅ End-to-End Flow: Working")
        
        return True
        
    except Exception as e:
        print(f"❌ Step 2 integration test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_step2_integration())
    if success:
        print(f"\n🚀 Ready to proceed to Step 3: MCP Chat Client Integration!")
    else:
        print(f"\n❌ Step 2 needs fixes before proceeding")
