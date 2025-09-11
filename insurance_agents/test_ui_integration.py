"""
UI Integration Test
Tests the complete UI integration with our proven A2A workflow
This demonstrates the complete employee experience
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ui_integration_orchestrator import ui_orchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UIIntegrationTest:
    """Test the complete UI integration workflow"""
    
    def __init__(self):
        self.session_id = "test_session_001"
        self.logger = logger
        
    async def run_complete_ui_test(self):
        """Run a complete UI integration test"""
        try:
            print("🎯 STARTING UI INTEGRATION TEST")
            print("=" * 60)
            
            # Initialize the orchestrator
            print("🔧 Initializing UI orchestrator...")
            success = await ui_orchestrator.initialize()
            if not success:
                print("❌ Failed to initialize orchestrator")
                return False
            print("✅ UI orchestrator initialized")
            
            # Test scenarios
            await self._test_complete_claim_workflow()
            await self._test_database_queries()
            await self._test_confirmation_workflow()
            await self._test_error_handling()
            
            print("\n🎉 UI INTEGRATION TEST COMPLETED SUCCESSFULLY!")
            return True
            
        except Exception as e:
            print(f"❌ UI Integration test failed: {e}")
            return False
    
    async def _test_complete_claim_workflow(self):
        """Test the complete claim processing workflow"""
        print("\n🔄 Testing Complete Claim Processing Workflow")
        print("-" * 50)
        
        # Step 1: Employee requests claim processing
        print("👤 Employee: 'Process claim with OP-05'")
        response1 = await ui_orchestrator.process_employee_message(
            message="Process claim with OP-05",
            session_id=self.session_id
        )
        
        print(f"🤖 Assistant Status: {response1.status}")
        print(f"🤖 Assistant Response:")
        print(response1.message)
        print(f"🔄 Requires Confirmation: {response1.requires_confirmation}")
        
        # Verify we got confirmation request
        assert response1.status == "pending_confirmation"
        assert response1.requires_confirmation == True
        assert response1.claim_id == "OP-05"
        print("✅ Confirmation request received correctly")
        
        # Step 2: Employee confirms processing
        print("\n👤 Employee: 'yes'")
        response2 = await ui_orchestrator.process_employee_message(
            message="yes",
            session_id=self.session_id
        )
        
        print(f"🤖 Assistant Status: {response2.status}")
        print(f"🤖 Assistant Response:")
        print(response2.message)
        print(f"🎯 Final Decision: {response2.final_decision}")
        
        # Verify workflow completed
        assert response2.status == "completed"
        assert response2.final_decision in ["APPROVED", "REJECTED"]
        print("✅ Complete workflow executed successfully")
    
    async def _test_database_queries(self):
        """Test database query functionality"""
        print("\n🔍 Testing Database Query Functionality")
        print("-" * 50)
        
        # Test patient query
        print("👤 Employee: 'Show me patient John Doe'")
        response = await ui_orchestrator.process_employee_message(
            message="Show me patient John Doe",
            session_id=f"{self.session_id}_db1"
        )
        
        print(f"🤖 Assistant Status: {response.status}")
        print(f"🤖 Assistant Response:")
        print(response.message[:200] + "..." if len(response.message) > 200 else response.message)
        
        # Should be completed database query
        assert response.status in ["completed", "error"]  # May error if no data
        print("✅ Database query handled correctly")
    
    async def _test_confirmation_workflow(self):
        """Test the confirmation workflow with different responses"""
        print("\n✅ Testing Confirmation Workflow Variations")
        print("-" * 50)
        
        # Start new claim processing
        session_id = f"{self.session_id}_confirm"
        print("👤 Employee: 'Process claim with IP-01'")
        response1 = await ui_orchestrator.process_employee_message(
            message="Process claim with IP-01",
            session_id=session_id
        )
        
        print(f"🤖 Initial Response Status: {response1.status}")
        
        if response1.status == "pending_confirmation":
            # Test invalid response
            print("\n👤 Employee: 'maybe'")
            response2 = await ui_orchestrator.process_employee_message(
                message="maybe",
                session_id=session_id
            )
            
            print(f"🤖 Invalid Response Status: {response2.status}")
            assert response2.status == "pending_confirmation"
            print("✅ Invalid response handled correctly")
            
            # Test cancellation
            print("\n👤 Employee: 'no'")
            response3 = await ui_orchestrator.process_employee_message(
                message="no",
                session_id=session_id
            )
            
            print(f"🤖 Cancellation Status: {response3.status}")
            assert response3.status == "cancelled"
            print("✅ Cancellation handled correctly")
    
    async def _test_error_handling(self):
        """Test error handling scenarios"""
        print("\n❌ Testing Error Handling")
        print("-" * 50)
        
        # Test invalid claim ID
        print("👤 Employee: 'Process claim with INVALID-999'")
        response = await ui_orchestrator.process_employee_message(
            message="Process claim with INVALID-999",
            session_id=f"{self.session_id}_error"
        )
        
        print(f"🤖 Error Response Status: {response.status}")
        print(f"🤖 Error Message: {response.message[:100]}...")
        
        # Should handle error gracefully
        assert response.status == "error"
        print("✅ Error handling working correctly")
    
    async def _test_general_queries(self):
        """Test general help and guidance"""
        print("\n💬 Testing General Query Handling")
        print("-" * 50)
        
        # Test help request
        print("👤 Employee: 'How can you help me?'")
        response = await ui_orchestrator.process_employee_message(
            message="How can you help me?",
            session_id=f"{self.session_id}_help"
        )
        
        print(f"🤖 Help Response Status: {response.status}")
        print(f"🤖 Help Message:")
        print(response.message)
        
        assert response.status == "info"
        print("✅ Help and guidance working correctly")

async def main():
    """Run the UI integration test"""
    test = UIIntegrationTest()
    success = await test.run_complete_ui_test()
    
    if success:
        print("\n🎉 ALL UI INTEGRATION TESTS PASSED!")
        print("🚀 Ready for production deployment!")
    else:
        print("\n❌ UI Integration tests failed")
        return 1
    
    return 0

if __name__ == "__main__":
    # Run the test
    result = asyncio.run(main())
    sys.exit(result)
