#!/usr/bin/env python3
"""
Test the complete workflow through the orchestrator to see document validation
"""

import asyncio
import json
import logging
from pathlib import Path
import sys
import uuid

# Add the project directory to the path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from agents.claims_orchestrator.intelligent_orchestrator import IntelligentClaimsOrchestrator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_document_validation():
    """Test document validation through the orchestrator"""
    
    print("🧪 TESTING DOCUMENT VALIDATION VIA ORCHESTRATOR")
    print("="*65)
    print("Testing: OP-03 (should have bill + memo attachments)")
    print("Expected: Coverage Rules Engine should find attachments and APPROVE")
    print("="*65)
    
    try:
        # Initialize orchestrator
        orchestrator = IntelligentClaimsOrchestrator()
        await orchestrator.initialize()
        
        session_id = str(uuid.uuid4())
        
        # PHASE 1: Request processing for OP-03
        print(f"\n📝 Phase 1: Employee requests processing for OP-03")
        initial_response = await orchestrator._process_intelligent_request(
            user_input="Process claim with OP-03",
            session_id=session_id
        )
        
        print("📋 Initial Response:")
        print(f"Status: {initial_response.get('status')}")
        
        if initial_response.get('status') == 'awaiting_confirmation':
            print("✅ Phase 1 SUCCESS: Got confirmation request")
            
            # PHASE 2: Employee confirmation
            print(f"\n👤 Phase 2: Employee confirms with 'yes'")
            confirmation_response = await orchestrator._process_intelligent_request(
                user_input="yes", 
                session_id=session_id
            )
            
            print("🎯 Final Workflow Response:")
            print(f"Status: {confirmation_response.get('status')}")
            print(f"Message: {confirmation_response.get('message', 'N/A')[:500]}...")
            
            # Analyze the result based on your document sample
            if confirmation_response.get('status') == 'approved':
                print("\n✅ SUCCESS: Claim APPROVED")
                print("🎉 Document validation worked correctly!")
                print("✅ Coverage Rules Engine found the attachments:")
                print("   - billAttachment: OP-03_Medical_Bill.pdf")
                print("   - memoAttachment: OP-03_Memo.pdf") 
            elif confirmation_response.get('status') == 'denied':
                print("\n❌ ISSUE: Claim DENIED")
                message = confirmation_response.get('message', '')
                if 'document' in message.lower() or 'missing' in message.lower():
                    print("🚨 DOCUMENT VALIDATION FAILED")
                    print("❌ Coverage Rules Engine did not find the attachments")
                    print("🔍 Check the debug logs above for attachment detection")
                else:
                    print("ℹ️ Denial was for business rules (amount/classification)")
            else:
                print(f"⚠️ UNEXPECTED STATUS: {confirmation_response.get('status')}")
                
        else:
            print(f"❌ Phase 1 FAILED: Expected confirmation, got {initial_response.get('status')}")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_document_validation())
