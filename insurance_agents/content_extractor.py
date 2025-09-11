#!/usr/bin/env python3
"""
Extract and analyze the actual response content from agents
"""
import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to sys.path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from shared.a2a_client import A2AClient

async def extract_response_content():
    """Extract the actual content from agent responses"""
    print("🔍 RESPONSE CONTENT EXTRACTION")
    print("=" * 50)
    
    a2a_client = A2AClient("content_extractor")
    
    # Test with structured message
    structured_message = """NEW WORKFLOW CLAIM EVALUATION REQUEST
claim_id: OP-05
patient_name: John Doe
bill_amount: $850.00
diagnosis: Routine Outpatient Visit
category: outpatient

Task: Evaluate coverage eligibility and benefits for this structured claim data."""
    
    try:
        print("Sending structured message to coverage_rules_engine...")
        result = await a2a_client.send_request(
            target_agent="coverage_rules_engine",
            task=structured_message,
            parameters={"test": True}
        )
        
        # Extract the actual text content
        if result and isinstance(result, dict) and 'result' in result:
            message_result = result['result']
            if isinstance(message_result, dict) and 'parts' in message_result:
                parts = message_result['parts']
                if parts and len(parts) > 0:
                    text_content = parts[0].get('text', '')
                    
                    print("\nActual response text content:")
                    print("=" * 30)
                    print(text_content)
                    print("=" * 30)
                    
                    # Try to parse as JSON
                    try:
                        parsed_content = json.loads(text_content)
                        print("\nParsed JSON content:")
                        for key, value in parsed_content.items():
                            print(f"  {key}: {value}")
                    except json.JSONDecodeError:
                        print("\nNot valid JSON, treating as plain text")
                    
                    # Check for workflow indicators
                    content_lower = text_content.lower()
                    indicators = {
                        "OP-05 mentioned": "op-05" in content_lower,
                        "John Doe mentioned": "john doe" in content_lower,
                        "Outpatient mentioned": "outpatient" in content_lower,
                        "NEW WORKFLOW mentioned": "new workflow" in content_lower,
                        "Structured mentioned": "structured" in content_lower,
                        "Enhanced mentioned": "enhanced" in content_lower,
                        "General evaluation": "general" in content_lower
                    }
                    
                    print("\nContent analysis:")
                    for name, detected in indicators.items():
                        status = "✅" if detected else "❌"
                        print(f"  {status} {name}")
                        
                else:
                    print("No parts found in message result")
            else:
                print("No parts found in result")
        else:
            print("No result found in response")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(extract_response_content())
