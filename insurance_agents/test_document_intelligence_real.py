"""
Test the new REAL Document Intelligence implementation
"""

import asyncio
import json
import sys
import os

# Add the path to find the agents
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

async def test_real_document_intelligence():
    """Test the real Document Intelligence implementation"""
    
    # Mock the necessary classes and dependencies for testing
    class MockCosmosContainer:
        def query_items(self, query, enable_cross_partition_query=True):
            # Return a mock claim document
            return [{
                "id": "IP-02",
                "category": "inpatient",
                "claimant_name": "John Smith",
                "attachments": [
                    {"url": "https://example.com/documents/IP-02_medical_bill.pdf"},
                    {"url": "https://example.com/documents/IP-02_discharge_summary.pdf"},
                    {"url": "https://example.com/documents/IP-02_memo.pdf"}
                ]
            }]
    
    class MockLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    # Import and create the DocumentIntelligenceExecutorFixed
    from agents.document_intelligence_agent.document_intelligence_executor_fixed import DocumentIntelligenceExecutorFixed
    
    # Create a mock instance
    executor = DocumentIntelligenceExecutorFixed()
    executor.logger = MockLogger()
    executor.claims_container = MockCosmosContainer()
    
    # Mock the _store_in_cosmos_db method
    stored_documents = []
    async def mock_store(doc, container_name):
        stored_documents.append((container_name, doc))
        print(f"STORED in {container_name}: {doc['id']}")
    
    executor._store_in_cosmos_db = mock_store
    
    # Test the new workflow document processing
    task_text = "Process Document Intelligence for claim_id: IP-02, patient_name: John Smith, category: inpatient"
    
    print("🧪 Testing REAL Document Intelligence Implementation")
    print("=" * 60)
    
    result = await executor._handle_new_workflow_document_processing(task_text)
    
    print("\n📊 RESULTS:")
    print("=" * 60)
    print(f"Status: {result.get('status')}")
    print(f"Workflow Type: {result.get('workflow_type')}")
    print(f"Extracted Documents: {len(result.get('extracted_documents', {}))}")
    
    print("\n📄 Response Message:")
    print("-" * 60)
    print(result.get('response', 'No response'))
    
    print("\n💾 Stored Documents:")
    print("-" * 60)
    for container, doc in stored_documents:
        print(f"Container: {container}")
        print(f"Document ID: {doc.get('id')}")
        print(f"Document Structure:")
        for key in doc.keys():
            if key.endswith('_doc'):
                print(f"  - {key}: {type(doc[key])}")
        print()
    
    print("\n🔍 Detailed Extracted Documents:")
    print("-" * 60)
    extracted_docs = result.get('extracted_documents', {})
    for doc_type, doc_data in extracted_docs.items():
        print(f"\n{doc_type}:")
        print(f"  Type: {doc_data.get('document_type')}")
        if 'provider_name' in doc_data:
            print(f"  Provider: {doc_data['provider_name']}")
        if 'total_amount' in doc_data:
            print(f"  Amount: ${doc_data['total_amount']}")
        if 'hospital_name' in doc_data:
            print(f"  Hospital: {doc_data['hospital_name']}")
        if 'primary_diagnosis' in doc_data:
            print(f"  Diagnosis: {doc_data['primary_diagnosis']}")
        print(f"  Source: {doc_data.get('source_url', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_real_document_intelligence())
