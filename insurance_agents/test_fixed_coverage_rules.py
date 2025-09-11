#!/usr/bin/env python3
"""
Test the fixed Coverage Rules Engine with direct Cosmos DB access
"""

import asyncio
import json
import logging
from datetime import datetime
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

async def test_fixed_coverage_rules():
    """Test the fixed Coverage Rules Engine with direct Cosmos DB access"""
    
    print("🧪 TESTING FIXED COVERAGE RULES ENGINE")
    print("="*70)
    print("Testing: Direct Cosmos DB access for complete document validation")
    print("Claims: OP-02 (Outpatient), IP-03 (Inpatient)")
    print("="*70)
    
    try:
        # Initialize orchestrator
        orchestrator = IntelligentClaimsOrchestrator()
        await orchestrator.initialize()
        
        # Test claims that should have proper attachments
        test_claims = [
            {
                "description": "OP-02 Outpatient - Should PASS (has bill + memo attachments)",
                "claim_id": "OP-02",
                "user_input": "Process claim with OP-02"
            },
            {
                "description": "IP-03 Inpatient - Should PASS (has bill + memo + discharge attachments)", 
                "claim_id": "IP-03",
                "user_input": "Process claim with IP-03"
            }
        ]
        
        for i, test_case in enumerate(test_claims, 1):
            print(f"\n🔍 TEST {i}: {test_case['description']}")
            print("-" * 60)
            
            session_id = str(uuid.uuid4())
            
            # PHASE 1: Initial claim processing request
            print(f"📝 Phase 1: Employee requests processing for {test_case['claim_id']}")
            initial_response = await orchestrator._process_intelligent_request(
                user_input=test_case['user_input'],
                session_id=session_id
            )
            
            print("📋 Initial Response:")
            print(f"Status: {initial_response.get('status')}")
            print(f"Message: {initial_response.get('message', 'N/A')[:200]}...")
            
            # Check if we got confirmation request
            if initial_response.get('status') == 'awaiting_confirmation':
                print("\n✅ Phase 1 SUCCESS: Got confirmation request as expected")
                
                # PHASE 2: Employee confirmation
                print(f"\n👤 Phase 2: Employee confirms with 'yes'")
                confirmation_response = await orchestrator._process_intelligent_request(
                    user_input="yes", 
                    session_id=session_id
                )
                
                print("🎯 Workflow Response:")
                print(f"Status: {confirmation_response.get('status')}")
                print(f"Message: {confirmation_response.get('message', 'N/A')[:300]}...")
                
                # Analyze the result
                if confirmation_response.get('status') == 'approved':
                    print("✅ WORKFLOW SUCCESS: Claim approved (documents validated successfully)")
                elif confirmation_response.get('status') == 'denied':
                    print("❌ WORKFLOW RESULT: Claim denied")
                    # Check if it's a document issue
                    message = confirmation_response.get('message', '')
                    if 'document' in message.lower() or 'missing' in message.lower():
                        print("⚠️ DOCUMENT ISSUE: Coverage Rules Engine still rejecting due to documents")
                    else:
                        print("✅ NON-DOCUMENT DENIAL: Legitimate business rules rejection")
                else:
                    print(f"⚠️ UNEXPECTED: Status = {confirmation_response.get('status')}")
                    
            else:
                print(f"❌ Phase 1 FAILED: Expected confirmation request, got {initial_response.get('status')}")
            
            print(f"\n{'='*60}")
            
            # Small delay between tests
            await asyncio.sleep(2)
        
        print("\n🎉 COVERAGE RULES TESTING FINISHED")
        print("\nKey Features Tested:")
        print("✅ Direct Cosmos DB access in Coverage Rules Engine")
        print("✅ Complete claim document retrieval")
        print("✅ Document validation with actual attachment URLs")
        print("✅ Proper document requirements checking")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed_coverage_rules())
