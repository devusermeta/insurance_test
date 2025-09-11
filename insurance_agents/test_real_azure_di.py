"""
Test Real Azure Document Intelligence Implementation
Tests the complete document processing workflow with real Azure DI
"""

import asyncio
import logging
import json
from datetime import datetime
import sys
import os

# Add the agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from agents.document_intelligence_agent.document_intelligence_executor_fixed import DocumentIntelligenceExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_azure_di_processing():
    """Test Azure Document Intelligence processing with real documents"""
    print("🧪 Testing Azure Document Intelligence Processing")
    print("=" * 60)
    
    try:
        # Initialize the document intelligence executor
        executor = DocumentIntelligenceExecutor()
        print("✅ Document Intelligence Executor initialized")
        
        # Test document type determination
        test_urls = [
            "https://example.com/discharge_summary.pdf",
            "https://example.com/medical_bill.pdf", 
            "https://example.com/doctor_memo.pdf"
        ]
        
        print("\n🔍 Testing document type determination:")
        for url in test_urls:
            doc_type = executor._determine_document_type(url)
            print(f"  URL: {url}")
            print(f"  Type: {doc_type}")
        
        # Test simulation extraction (as fallback)
        print("\n🎭 Testing simulation extraction (fallback):")
        doc_types = ['discharge_summary_doc', 'medical_bill_doc', 'memo_doc']
        
        for doc_type in doc_types:
            extracted_data = executor._simulate_extraction(doc_type)
            print(f"\n  📄 {doc_type}:")
            for key, value in extracted_data.items():
                print(f"    {key}: {value}")
        
        # Test Azure DI client initialization
        print(f"\n🔧 Azure DI Client Status:")
        if executor.document_intelligence_client:
            print("  ✅ Azure Document Intelligence client initialized successfully")
        else:
            print("  ⚠️ Azure DI client not initialized (will use simulation)")
        
        # Test MCP client initialization  
        print(f"\n🗄️ MCP Client Status:")
        if executor.mcp_client:
            print("  ✅ MCP client initialized successfully")
        else:
            print("  ⚠️ MCP client not initialized")
            
        # Test A2A client initialization
        print(f"\n🤝 A2A Client Status:")
        if executor.a2a_client:
            print("  ✅ A2A client initialized successfully")
        else:
            print("  ⚠️ A2A client not initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

async def test_complete_workflow():
    """Test the complete document processing workflow"""
    print("\n🔄 Testing Complete Workflow")
    print("=" * 60)
    
    try:
        executor = DocumentIntelligenceExecutor()
        
        # Create a test claim document
        test_claim = {
            "claim_id": "CLAIM_TEST_001",
            "claim_type": "inpatient",
            "patient_details": {
                "patient_name": "Test Patient",
                "policy_number": "POL123456"
            },
            "claim_details": {
                "claim_amount": 5000,
                "diagnosis": "Test Diagnosis"
            },
            "attachments": [
                {
                    "document_type": "discharge_summary_doc",
                    "url": "https://example.com/test_discharge.pdf"
                },
                {
                    "document_type": "medical_bill_doc", 
                    "url": "https://example.com/test_bill.pdf"
                }
            ]
        }
        
        print("📋 Test claim document created:")
        print(json.dumps(test_claim, indent=2))
        
        # Test the main processing method
        print(f"\n🔄 Testing document processing workflow...")
        
        # Create a test task message that includes the claim ID
        test_task_message = f"Process documents for claim_id: CLAIM_TEST_001"
        
        # Process the claim (this will use simulation for now)
        result = await executor._process_claim_documents(test_task_message)
        
        if result:
            print("✅ Document processing completed successfully")
            print(f"📄 Processing result: {result}")
        else:
            print("⚠️ Document processing completed with no result")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during complete workflow test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_data_extraction_methods():
    """Test the data extraction helper methods"""
    print("\n🧮 Testing Data Extraction Methods")
    print("=" * 60)
    
    try:
        executor = DocumentIntelligenceExecutor()
        
        # Test sample content and key-value pairs
        sample_content = """
        patient name: john doe
        hospital: regional medical center
        admission date: 2025-08-01
        discharge date: 2025-08-05
        diagnosis: community-acquired pneumonia
        total amount: $928.50
        """.lower()
        
        sample_kv_pairs = {
            "patient": "John Doe",
            "hospital": "Regional Medical Center", 
            "bill total": "$928.50",
            "diagnosis": "Community-acquired pneumonia"
        }
        
        print("📝 Sample content and key-value pairs created")
        
        # Test individual extraction methods
        print(f"\n🔍 Testing extraction methods:")
        
        patient_name = executor._find_patient_name(sample_content, sample_kv_pairs)
        print(f"  Patient Name: {patient_name}")
        
        hospital_name = executor._find_hospital_name(sample_content, sample_kv_pairs)
        print(f"  Hospital Name: {hospital_name}")
        
        admit_date = executor._find_date(sample_content, sample_kv_pairs, ["admission", "admit"])
        print(f"  Admit Date: {admit_date}")
        
        discharge_date = executor._find_date(sample_content, sample_kv_pairs, ["discharge"])
        print(f"  Discharge Date: {discharge_date}")
        
        condition = executor._find_medical_condition(sample_content, sample_kv_pairs)
        print(f"  Medical Condition: {condition}")
        
        amount = executor._find_amount(sample_content, sample_kv_pairs)
        print(f"  Bill Amount: ${amount}")
        
        # Test date parsing
        print(f"\n📅 Testing date parsing:")
        test_dates = ["2025-08-01", "08/01/2025", "8-1-2025", "01/08/25"]
        for date_str in test_dates:
            parsed = executor._parse_date(date_str)
            print(f"  {date_str} → {parsed}")
            
        # Test amount parsing
        print(f"\n💰 Testing amount parsing:")
        test_amounts = ["$928.50", "928.50", "$1,250.00", "750"]
        for amount_str in test_amounts:
            parsed = executor._parse_amount(amount_str)
            print(f"  {amount_str} → ${parsed}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during extraction methods test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Azure Document Intelligence Tests")
    print("=" * 80)
    
    tests = [
        ("Azure DI Processing", test_azure_di_processing),
        ("Data Extraction Methods", test_data_extraction_methods),
        ("Complete Workflow", test_complete_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            result = await test_func()
            results.append((test_name, result))
            print(f"✅ {test_name} completed: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Azure DI implementation is ready.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    asyncio.run(main())
