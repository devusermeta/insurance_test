"""
Test script to verify claim approval workflow works correctly
Tests a claim that should pass all business rules and be approved
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from intelligent_claims_orchestrator import IntelligentClaimsOrchestrator

async def test_approval_workflow():
    """Test a claim that should be approved"""
    
    print("🧪 TESTING CLAIM APPROVAL WORKFLOW")
    print("=" * 65)
    print("Testing: A claim with reasonable amount that should be APPROVED")
    print("Expected: Complete workflow with final approval")
    print("=" * 65)
    
    orchestrator = IntelligentClaimsOrchestrator()
    
    try:
        # Phase 1: Employee requests processing for a general claim with reasonable amount
        print("\n📝 Phase 1: Employee requests processing for EYE-01 (eye condition, $300)")
        response1 = await orchestrator.process_query("Process claim with EYE-01")
        print("📋 Initial Response:")
        print(f"Status: {response1.get('status', 'unknown')}")
        
        if response1.get('status') == 'awaiting_confirmation':
            print("✅ Phase 1 SUCCESS: Got confirmation request")
            
            # Phase 2: Employee confirms
            print("\n👤 Phase 2: Employee confirms with 'yes'")
            response2 = await orchestrator.process_query("yes")
            
            print("\n🎯 Final Workflow Response:")
            print(f"Status: {response2.get('status', 'unknown')}")
            print(f"Message: {response2.get('message', 'No message')}")
            
            if response2.get('status') == 'approved':
                print("\n✅ SUCCESS: Claim APPROVED")
                print("ℹ️ All agents processed successfully")
            elif response2.get('status') == 'denied':
                print("\n❌ ISSUE: Claim DENIED")
                print("ℹ️ Need to check business rules or validation logic")
            else:
                print(f"\n❓ UNEXPECTED: Status = {response2.get('status')}")
        else:
            print("❌ Phase 1 FAILED: Expected confirmation request")
            
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await orchestrator.close()

if __name__ == "__main__":
    asyncio.run(test_approval_workflow())
