"""
Test Azure Document Intelligence Integration
Tests the azure_document_intelligence.py client with real Cosmos DB claim data
"""

import asyncio
import json
from shared.azure_document_intelligence import AzureDocumentIntelligenceClient, process_claim_documents
from shared.cosmos_db_client import get_cosmos_client

# Test claim IDs that exist in Cosmos DB
TEST_CLAIM_IDS = {
    'inpatient': 'IP-01',
    'outpatient': 'OP-05'
}

async def get_document_urls_from_cosmos(claim_id: str) -> dict:
    """Get document URLs for a claim from Cosmos DB"""
    try:
        print(f"🔍 Retrieving document URLs for claim: {claim_id}")
        
        # Get claim from Cosmos DB
        cosmos_client = await get_cosmos_client()
        claim = await cosmos_client.get_claim_by_id(claim_id)
        
        if not claim:
            print(f"❌ Claim {claim_id} not found in Cosmos DB")
            return {}
        
        # Extract attachment URLs
        document_urls = {}
        
        # Check for different attachment types
        attachment_fields = ['billAttachment', 'memoAttachment', 'dischargeAttachment']
        for field in attachment_fields:
            if field in claim and claim[field]:
                document_urls[field] = claim[field]
                print(f"✅ Found {field}: {claim[field].split('/')[-1]}")
            else:
                print(f"⚠️ No {field} found for claim {claim_id}")
        
        # Show claim details
        print(f"📋 Claim Details:")
        print(f"   Patient: {claim.get('patientName')}")
        print(f"   Category: {claim.get('category')}")
        print(f"   Status: {claim.get('status')}")
        print(f"   Diagnosis: {claim.get('diagnosis')}")
        print(f"   Bill Amount: ${claim.get('billAmount')}")
        
        return document_urls
        
    except Exception as e:
        print(f"❌ Error retrieving document URLs for {claim_id}: {e}")
        return {}

async def test_document_intelligence_initialization():
    """Test Azure Document Intelligence client initialization"""
    print("🧪 Testing Azure Document Intelligence Initialization...")
    
    try:
        client = AzureDocumentIntelligenceClient()
        success = await client.initialize()
        
        if success:
            print("✅ Azure Document Intelligence client initialized successfully!")
            return True
        else:
            print("❌ Failed to initialize Azure Document Intelligence client")
            print("💡 Please ensure AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY are set")
            return False
            
    except Exception as e:
        print(f"❌ Initialization test error: {e}")
        return False

async def test_single_document_processing():
    """Test processing a single document from Cosmos DB"""
    print("\n🧪 Testing Single Document Processing...")
    
    try:
        # Get document URLs from Cosmos DB for outpatient claim
        claim_id = TEST_CLAIM_IDS['outpatient']
        document_urls = await get_document_urls_from_cosmos(claim_id)
        
        if not document_urls or 'billAttachment' not in document_urls:
            print(f"❌ No bill attachment found for claim {claim_id}")
            return
        
        client = AzureDocumentIntelligenceClient()
        await client.initialize()
        
        # Test with the medical bill from Cosmos DB
        test_url = document_urls['billAttachment']
        
        print(f"📄 Testing medical bill processing: {test_url.split('/')[-1]}")
        result = await client.process_document_from_url(test_url, 'medical_bill')
        
        if result['success']:
            print("✅ Document processed successfully!")
            extracted_data = result['extracted_data']
            print(f"   Patient Name: {extracted_data.get('patient_name')}")
            print(f"   Bill Date: {extracted_data.get('bill_date')}")
            print(f"   Bill Amount: ${extracted_data.get('bill_amount')}")
            print(f"   Model Used: {result.get('model_used')}")
        else:
            print(f"❌ Document processing failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Single document processing test error: {e}")

async def test_inpatient_claim_processing():
    """Test processing all documents for an inpatient claim from Cosmos DB"""
    print("\n🧪 Testing Inpatient Claim Document Processing...")
    
    try:
        # Get document URLs from Cosmos DB for inpatient claim
        claim_id = TEST_CLAIM_IDS['inpatient']
        document_urls = await get_document_urls_from_cosmos(claim_id)
        
        if not document_urls:
            print(f"❌ No document URLs found for inpatient claim {claim_id}")
            return
        
        print(f"🏥 Processing inpatient claim {claim_id} with {len(document_urls)} documents:")
        for doc_type, url in document_urls.items():
            print(f"   - {doc_type}: {url.split('/')[-1]}")
        
        result = await process_claim_documents(document_urls)
        
        if result['success']:
            print(f"✅ Processed {result['documents_processed']} documents successfully!")
            
            # Show extracted data for each document
            for doc_type, doc_result in result['results'].items():
                print(f"\n📋 {doc_type.upper()} Results:")
                if doc_result['success']:
                    extracted = doc_result['extracted_data']
                    for field, value in extracted.items():
                        if value:
                            print(f"   ✓ {field}: {value}")
                else:
                    print(f"   ❌ Failed: {doc_result.get('error')}")
        else:
            print(f"❌ Claim processing failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Inpatient claim processing test error: {e}")

async def test_outpatient_claim_processing():
    """Test processing all documents for an outpatient claim from Cosmos DB"""
    print("\n🧪 Testing Outpatient Claim Document Processing...")
    
    try:
        # Get document URLs from Cosmos DB for outpatient claim
        claim_id = TEST_CLAIM_IDS['outpatient']
        document_urls = await get_document_urls_from_cosmos(claim_id)
        
        if not document_urls:
            print(f"❌ No document URLs found for outpatient claim {claim_id}")
            return
        
        print(f"🏥 Processing outpatient claim {claim_id} with {len(document_urls)} documents:")
        for doc_type, url in document_urls.items():
            print(f"   - {doc_type}: {url.split('/')[-1]}")
        
        result = await process_claim_documents(document_urls)
        
        if result['success']:
            print(f"✅ Processed {result['documents_processed']} documents successfully!")
            
            # Show extracted data for each document
            for doc_type, doc_result in result['results'].items():
                print(f"\n📋 {doc_type.upper()} Results:")
                if doc_result['success']:
                    extracted = doc_result['extracted_data']
                    for field, value in extracted.items():
                        if value:
                            print(f"   ✓ {field}: {value}")
                else:
                    print(f"   ❌ Failed: {doc_result.get('error')}")
        else:
            print(f"❌ Claim processing failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Outpatient claim processing test error: {e}")

async def test_data_structure_format():
    """Test that extracted data matches the required structure for Cosmos DB"""
    print("\n🧪 Testing Data Structure Format...")
    
    try:
        # Process inpatient documents from Cosmos DB
        claim_id = TEST_CLAIM_IDS['inpatient']
        document_urls = await get_document_urls_from_cosmos(claim_id)
        
        if not document_urls:
            print(f"❌ No document URLs found for claim {claim_id}")
            return
        
        result = await process_claim_documents(document_urls)
        
        if result['success']:
            # Format data according to Cosmos DB schema for inpatient
            cosmos_document = {
                'claimId': claim_id,
                'extractedAt': result['processing_time'],
                'extractionSource': 'Azure Document Intelligence'
            }
            
            # Add structured data for each document type
            for doc_type, doc_result in result['results'].items():
                if doc_result['success']:
                    if doc_type == 'discharge_summary':
                        cosmos_document['discharge_summary_doc'] = doc_result['extracted_data']
                    elif doc_type == 'medical_bill':
                        cosmos_document['medical_bill_doc'] = doc_result['extracted_data']
                    elif doc_type == 'memo':
                        cosmos_document['memo_doc'] = doc_result['extracted_data']
            
            print("✅ Successfully formatted data for Cosmos DB:")
            print(f"📋 Structure Preview:")
            print(f"   - claimId: {cosmos_document.get('claimId')}")
            print(f"   - extractedAt: {cosmos_document.get('extractedAt')}")
            print(f"   - discharge_summary_doc: {len(cosmos_document.get('discharge_summary_doc', {}))} fields")
            print(f"   - medical_bill_doc: {len(cosmos_document.get('medical_bill_doc', {}))} fields")
            print(f"   - memo_doc: {len(cosmos_document.get('memo_doc', {}))} fields")
            
            # Show sample fields
            if 'medical_bill_doc' in cosmos_document:
                bill_doc = cosmos_document['medical_bill_doc']
                print(f"\n💰 Sample Bill Fields:")
                print(f"   - Patient: {bill_doc.get('patient_name')}")
                print(f"   - Amount: ${bill_doc.get('bill_amount')}")
                print(f"   - Date: {bill_doc.get('bill_date')}")
                
        else:
            print(f"❌ Could not test data structure: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Data structure test error: {e}")

async def main():
    """Run all Document Intelligence tests"""
    print("🚀 Starting Azure Document Intelligence Tests...")
    print("=" * 60)
    
    # Test initialization first
    init_success = await test_document_intelligence_initialization()
    
    if init_success:
        await test_single_document_processing()
        await test_inpatient_claim_processing() 
        await test_outpatient_claim_processing()
        await test_data_structure_format()
    else:
        print("❌ Skipping further tests due to initialization failure")
        print("\n🔧 Setup Required:")
        print("1. Set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT in your .env file")
        print("2. Set AZURE_DOCUMENT_INTELLIGENCE_KEY in your .env file")
        print("3. Ensure the Azure Document Intelligence resource is created and accessible")
    
    print("\n" + "=" * 60)
    print("🏁 Azure Document Intelligence Tests Complete!")

if __name__ == "__main__":
    asyncio.run(main())
