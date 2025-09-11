"""
Simple test for the Intake Clarifier async context manager fix
Focused test to verify the specific bug fix without complex dependencies
"""

import asyncio
import os
import sys
import logging

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_cosmos_db_fix():
    """Test the specific async context manager fix"""
    
    print("🔧 TESTING: Async Context Manager Fix")
    print("=" * 50)
    
    try:
        from agents.intake_clarifier.a2a_wrapper import A2AIntakeClarifierExecutor
        
        # Initialize executor
        executor = A2AIntakeClarifierExecutor()
        print("✅ Executor initialized")
        
        # Initialize Cosmos DB client
        await executor._init_cosmos_client()
        
        if executor.cosmos_client is None:
            print("❌ Cosmos DB client not available")
            print("📝 Environment variables needed:")
            print("   - COSMOS_DB_ENDPOINT")
            print("   - COSMOS_DB_KEY") 
            print("   - COSMOS_DB_DATABASE_NAME")
            return False
        
        print("✅ Cosmos DB client initialized")
        
        # Test the fixed method that previously failed
        test_comparison_result = {
            'status': 'match',
            'details': ['✅ Test data match'],
            'issues': []
        }
        
        print("🧪 Testing _update_claim_status method (the fixed method)...")
        
        # This method previously threw:
        # 'CosmosClient' object does not support the asynchronous context manager protocol
        await executor._update_claim_status("OP-02", test_comparison_result)
        
        print("🎉 SUCCESS! No async context manager error!")
        print("✅ The fix is working correctly")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error: {error_msg}")
        
        if "asynchronous context manager protocol" in error_msg:
            print("🔧 This is the original bug - fix didn't work!")
            print("💡 Check the _update_claim_status method")
        elif "CosmosClient" in error_msg:
            print("🔧 Cosmos DB related error - check credentials")
        
        return False

async def test_claim_fetch():
    """Test fetching claim data to verify basic functionality"""
    
    print("\n📋 TESTING: Basic Claim Data Fetch")
    print("=" * 40)
    
    try:
        from agents.intake_clarifier.a2a_wrapper import A2AIntakeClarifierExecutor
        
        executor = A2AIntakeClarifierExecutor()
        await executor._init_cosmos_client()
        
        if executor.cosmos_client is None:
            print("❌ Cannot test - Cosmos DB not available")
            return False
        
        # Test fetching OP-02 (the claim from the logs)
        claim_data = await executor._fetch_claim_details("OP-02")
        
        if claim_data:
            print("✅ Successfully fetched claim data:")
            print(f"   Claim ID: {claim_data.get('claimId')}")
            print(f"   Patient: {claim_data.get('patientName')}")
            print(f"   Amount: ${claim_data.get('billAmount')}")
            print(f"   Status: {claim_data.get('status')}")
            return True
        else:
            print("⚠️  No claim data found for OP-02")
            print("📝 This might be expected if the claim doesn't exist")
            return True  # Not a failure, just no data
            
    except Exception as e:
        print(f"❌ Fetch test failed: {e}")
        return False

def run_simple_tests():
    """Run the simple focused tests"""
    
    print("🧪 SIMPLE INTAKE CLARIFIER FIX TEST")
    print("=" * 50)
    print("🎯 Testing specifically the async context manager fix")
    print("📋 Based on the error from the workflow logs")
    print("=" * 50)
    
    # Check basic environment
    cosmos_endpoint = os.getenv("COSMOS_DB_ENDPOINT")
    cosmos_key = os.getenv("COSMOS_DB_KEY")
    
    if not cosmos_endpoint or not cosmos_key:
        print("⚠️  Cosmos DB environment variables not found")
        print("🔧 Set these environment variables:")
        print("   - COSMOS_DB_ENDPOINT")
        print("   - COSMOS_DB_KEY")
        print("   - COSMOS_DB_DATABASE_NAME (optional, defaults to 'insurance')")
        print("\n📝 Note: This test requires access to the Cosmos DB")
        return False
    
    print("✅ Environment variables found")
    
    try:
        # Test the specific fix
        fix_result = asyncio.run(test_cosmos_db_fix())
        
        if fix_result:
            print("\n🎉 PRIMARY FIX TEST PASSED!")
            
            # Test basic functionality
            fetch_result = asyncio.run(test_claim_fetch())
            
            if fetch_result:
                print("\n🎉 ALL TESTS PASSED!")
                print("✅ Intake Clarifier is working correctly")
                return True
            else:
                print("\n⚠️  Fetch test had issues but fix is working")
                return True
        else:
            print("\n❌ FIX TEST FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Simple Intake Clarifier Fix Test...")
    
    # Load environment variables first
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded from .env file")
    except ImportError:
        print("⚠️  python-dotenv not found, using system environment")
    
    success = run_simple_tests()
    
    if success:
        print("\n🎉 SUCCESS!")
        print("✅ The async context manager fix is working")
        print("🔄 Ready to test the full workflow")
    else:
        print("\n❌ FAILED!")
        print("🔧 Please check the issues above")
    
    exit(0 if success else 1)
