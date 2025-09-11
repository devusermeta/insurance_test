"""
Agent Logic Debugging - Why aren't agents using new workflow?
============================================================
"""

import asyncio
import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from shared.a2a_client import A2AClient

async def debug_agent_responses():
    """Debug what agents are actually returning"""
    print("\n🔍 DEBUGGING AGENT RESPONSES")
    print("=" * 50)
    
    a2a_client = A2AClient("debug_test")
    
    # Test structured messages that match orchestrator format
    test_tasks = {
        "coverage_rules_engine": """NEW WORKFLOW CLAIM EVALUATION REQUEST
claim_id: OP-05
patient_name: John Doe
bill_amount: $850.00
diagnosis: Routine Outpatient Visit
category: outpatient
status: pending_review
bill_date: 2024-01-15

Task: Evaluate coverage eligibility and benefits for this structured claim data.""",
        
        "document_intelligence": """NEW WORKFLOW DOCUMENT PROCESSING REQUEST
claim_id: OP-05
patient_name: John Doe
bill_amount: $850.00
diagnosis: Routine Outpatient Visit
category: outpatient
status: pending_review
bill_date: 2024-01-15

Task: Process documents and extract medical codes for this structured claim data.""",
        
        "intake_clarifier": """NEW WORKFLOW PATIENT VERIFICATION REQUEST
claim_id: OP-05
patient_name: John Doe
bill_amount: $850.00
diagnosis: Routine Outpatient Visit
category: outpatient
status: pending_review
bill_date: 2024-01-15

Task: Verify patient information and assess risk for this structured claim data."""
    }
    
    agents = ["coverage_rules_engine", "document_intelligence", "intake_clarifier"]
    
    for agent_name in agents:
        print(f"\n🤖 {agent_name.upper()}:")
        print("-" * 30)
        
        # Get the structured task for this agent
        test_request = test_tasks.get(agent_name, "Generic test request")
        
        try:
            result = await a2a_client.send_request(
                target_agent=agent_name,
                task=test_request,
                parameters={"debug": True}
            )
            
            if result:
                print(f"✅ Response received")
                
                # Show full response for debugging
                if isinstance(result, dict):
                    print(f"📋 Response keys: {list(result.keys())}")
                    
                    # Check different possible response formats
                    response_content = None
                    if 'result' in result:
                        response_content = result['result']
                        print(f"📄 Found 'result' key: {type(response_content)}")
                    elif 'message' in result:
                        response_content = result['message']
                        print(f"📄 Found 'message' key: {type(response_content)}")
                    
                    if response_content:
                        print(f"📄 Content preview:")
                        print(f"    {str(response_content)[:500]}...")
                        
                        # Check for specific indicators
                        content_lower = str(response_content).lower()
                        indicators = {
                            "OP-05 detected": "op-05" in content_lower,
                            "John Doe detected": "john doe" in content_lower,
                            "Outpatient detected": "outpatient" in content_lower,
                            "New workflow mentioned": "new workflow" in content_lower,
                            "Structured claim mentioned": "structured" in content_lower,
                            "Enhanced mentioned": "enhanced" in content_lower
                        }
                        
                        print(f"📊 Content analysis:")
                        for indicator, detected in indicators.items():
                            status = "✅" if detected else "❌"
                            print(f"    {status} {indicator}")
                    else:
                        print(f"📄 No recognizable content found")
                        print(f"📄 Full result: {str(result)}")
                        
                else:
                    print(f"📄 Non-dict response: {str(result)[:500]}...")
            else:
                print(f"❌ No response received")
                
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}...")

if __name__ == "__main__":
    asyncio.run(debug_agent_responses())
