#!/usr/bin/env python3
"""
Simple debug test for agent responses
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to sys.path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from shared.a2a_client import A2AClient

async def simple_test():
    """Simple test"""
    print("🔍 SIMPLE DEBUG TEST")
    print("=" * 30)
    
    a2a_client = A2AClient("simple_test")
    
    # Test one agent with a simple message
    try:
        print("Testing coverage_rules_engine...")
        result = await a2a_client.send_request(
            target_agent="coverage_rules_engine",
            task="claim_id: OP-05\npatient_name: John Doe",
            parameters={"test": True}
        )
        print(f"Result type: {type(result)}")
        print(f"Success!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(simple_test())
