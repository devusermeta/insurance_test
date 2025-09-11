#!/usr/bin/env python3
"""
Check agent response format to understand what we're getting
"""
import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to sys.path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from shared.a2a_client import A2AClient

async def analyze_response_format():
    """Analyze the exact response format from agents"""
    print("🔍 RESPONSE FORMAT ANALYSIS")
    print("=" * 50)
    
    a2a_client = A2AClient("format_analyzer")
    
    # Simple test message
    simple_message = "Test: claim_id OP-05 patient_name John Doe"
    
    try:
        print(f"Sending simple message: '{simple_message}'")
        result = await a2a_client.send_request(
            target_agent="coverage_rules_engine",
            task=simple_message,
            parameters={"test": True}
        )
        
        print("\nFull response structure:")
        print(f"Type: {type(result)}")
        
        if isinstance(result, dict):
            print("Keys:", list(result.keys()))
            
            for key, value in result.items():
                print(f"\n{key}:")
                print(f"  Type: {type(value)}")
                if isinstance(value, dict):
                    print(f"  Keys: {list(value.keys())}")
                    if key == 'result':
                        print(f"  Content preview: {str(value)[:300]}...")
                elif isinstance(value, str):
                    print(f"  Content: {value[:100]}...")
                else:
                    print(f"  Content: {value}")
        else:
            print(f"Non-dict response: {str(result)[:500]}...")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_response_format())
