"""
Test Step 3 - MCP Chat Client Integration
Tests the new claim detail extraction functionality for the workflow.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to the path so we can import shared modules
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from shared.mcp_chat_client import enhanced_mcp_chat_client

async def test_claim_extraction():
    """Test extracting claim details by claim ID"""
    print("\n" + "="*60)
    print("🧪 TESTING STEP 3 - MCP CHAT CLIENT INTEGRATION")
    print("="*60)
    
    try:
        # Test 1: Extract details for a known claim
        test_claim_id = "OP-05"
        print(f"\n📋 Test 1: Extracting details for claim {test_claim_id}")
        print("-" * 40)
        
        details = await enhanced_mcp_chat_client.extract_claim_details(test_claim_id)
        
        if details.get("success"):
            print("✅ Claim extraction successful!")
            print(f"   Claim ID: {details['claim_id']}")
            print(f"   Patient: {details['patient_name']}")
            print(f"   Amount: ${details['bill_amount']}")
            print(f"   Status: {details['status']}")
            print(f"   Category: {details['category']}")
            print(f"   Diagnosis: {details['diagnosis']}")
            print(f"   Bill Date: {details['bill_date']}")
        else:
            print("❌ Claim extraction failed!")
            print(f"   Error: {details.get('error', 'Unknown error')}")
        
        # Test 2: Parse claim ID from user message
        print(f"\n📝 Test 2: Parsing claim ID from user messages")
        print("-" * 40)
        
        test_messages = [
            "Process claim with IP-01",
            "Process claim IP-01", 
            "Can you handle claim OP-05",
            "Review claim ID IN-123",
            "Just process IP-01",
            "Invalid message without claim"
        ]
        
        for message in test_messages:
            parsed_id = enhanced_mcp_chat_client.parse_claim_id_from_message(message)
            if parsed_id:
                print(f"✅ '{message}' → {parsed_id}")
            else:
                print(f"❌ '{message}' → No claim ID found")
        
        # Test 3: Full workflow simulation
        print(f"\n🔄 Test 3: Simulating full workflow step")
        print("-" * 40)
        
        user_message = "Process claim with OP-05"
        claim_id = enhanced_mcp_chat_client.parse_claim_id_from_message(user_message)
        
        if claim_id:
            print(f"📥 Employee message: '{user_message}'")
            print(f"🎯 Parsed claim ID: {claim_id}")
            
            details = await enhanced_mcp_chat_client.extract_claim_details(claim_id)
            
            if details.get("success"):
                print("\n📊 Claim Details for Employee Confirmation:")
                print(f"   Patient Name: {details['patient_name']}")
                print(f"   Bill Amount: ${details['bill_amount']}")
                print(f"   Current Status: {details['status']}")
                print(f"   Category: {details['category']}")
                print(f"   Diagnosis: {details['diagnosis']}")
                print("\n✅ Ready to show to employee for confirmation!")
            else:
                print(f"❌ Could not extract claim details: {details.get('error')}")
        else:
            print(f"❌ Could not parse claim ID from message")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def test_claim_parsing_only():
    """Test claim ID parsing without async operations"""
    print("\n" + "="*60)
    print("🧪 TESTING CLAIM ID PARSING (Sync)")
    print("="*60)
    
    test_cases = [
        ("Process claim with IP-01", "IP-01"),
        ("Process claim IP-01", "IP-01"),
        ("Handle claim OP-05", "OP-05"),
        ("Review claim ID IN-123", "IN-123"),
        ("claim ip-01", "IP-01"),  # lowercase test
        ("Just IP-01 please", "IP-01"),
        ("No claim here", None),
        ("Process claim", None)
    ]
    
    for message, expected in test_cases:
        result = enhanced_mcp_chat_client.parse_claim_id_from_message(message)
        if result == expected:
            print(f"✅ '{message}' → {result}")
        else:
            print(f"❌ '{message}' → {result} (expected {expected})")

if __name__ == "__main__":
    print("🚀 Starting Step 3 MCP Integration Tests...")
    
    # First test parsing (synchronous)
    test_claim_parsing_only()
    
    # Then test full async functionality
    asyncio.run(test_claim_extraction())
    
    print("\n🎯 Step 3 Tests Complete!")
    print("\nNext: The orchestrator can now:")
    print("1. Parse 'Process claim with IP-01' messages")
    print("2. Extract claim details via MCP")
    print("3. Show details to employee for confirmation")
    print("4. Proceed with A2A workflow execution")
