#!/usr/bin/env python3
"""
Test document intelligence agent specifically
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to sys.path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from shared.a2a_client import A2AClient

async def test_document_agent_only():
    """Test document intelligence agent with structured message"""
    print("🔍 DOCUMENT INTELLIGENCE SPECIFIC TEST")
    print("=" * 50)
    
    a2a_client = A2AClient("doc_specific_test")
    
    # Structured message specifically for document intelligence
    structured_message = """NEW WORKFLOW DOCUMENT PROCESSING REQUEST
claim_id: OP-05
patient_name: John Doe
bill_amount: $850.00
diagnosis: Routine Outpatient Visit
category: outpatient
status: pending_review
bill_date: 2024-01-15

Task: Process documents and extract medical codes for this structured claim data."""
    
    print(f"Sending message to document_intelligence:")
    print(f"Message length: {len(structured_message)}")
    print(f"Message preview: {structured_message[:200]}...")
    print()
    
    try:
        result = await a2a_client.send_request(
            target_agent="document_intelligence",
            task=structured_message,
            parameters={"debug": True}
        )
        
        if result and isinstance(result, dict) and 'result' in result:
            message_result = result['result']
            if isinstance(message_result, dict) and 'parts' in message_result:
                parts = message_result['parts']
                if parts and len(parts) > 0:
                    text_content = parts[0].get('text', '')
                    
                    print("Document Intelligence Response:")
                    print("=" * 40)
                    print(text_content)
                    print("=" * 40)
                    
                    # Detailed analysis
                    content_lower = text_content.lower()
                    
                    print("\nDetailed Response Analysis:")
                    print(f"Response type: {'Enhanced' if 'claim analysis' in content_lower or 'op-05' in content_lower else 'Legacy'}")
                    print(f"Contains OP-05: {'✅' if 'op-05' in content_lower else '❌'}")
                    print(f"Contains John Doe: {'✅' if 'john doe' in content_lower else '❌'}")
                    print(f"Contains outpatient: {'✅' if 'outpatient' in content_lower else '❌'}")
                    print(f"Contains 'general document intelligence': {'✅' if 'general document intelligence' in content_lower else '❌'}")
                    print(f"Contains structured content: {'✅' if 'document analysis' in content_lower or 'claim id' in content_lower else '❌'}")
                    
                    # Determine status
                    if 'general document intelligence' in content_lower:
                        print("\n❌ STATUS: Using LEGACY processing")
                        print("   - Agent is not detecting enhanced workflow")
                        print("   - Need to check text extraction in agent")
                    else:
                        print("\n✅ STATUS: Using ENHANCED processing")
                        print("   - Agent successfully detected new workflow")
                        
            else:
                print("❌ No parts found in result")
        else:
            print("❌ No result found in response")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_document_agent_only())
