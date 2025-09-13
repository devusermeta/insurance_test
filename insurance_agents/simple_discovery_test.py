"""
Simple test for dynamic agent discovery
Tests if Communication Agent is discovered on-demand during claim processing
"""

import asyncio
import httpx
import json
import time

async def test_claim_with_email():
    """Test claim processing that should trigger on-demand Communication Agent discovery"""
    
    print("🧪 Testing On-Demand Communication Agent Discovery")
    print("=" * 60)
    
    # Create a test claim that will trigger the email workflow
    test_claim = {
        "patient_name": "Dynamic Test Patient",
        "patient_email": "purohitabhinav2001@gmail.com",
        "bill_amount": "750.00",
        "service_description": "Emergency room visit for testing dynamic agent discovery",
        "provider": "Test Hospital",
        "category": "Medical",
        "documents": []
    }
    
    print(f"📋 Testing claim for: {test_claim['patient_name']}")
    print(f"💰 Amount: ${test_claim['bill_amount']}")
    print(f"📧 Email: {test_claim['patient_email']}")
    print()
    
    try:
        print("🚀 Sending claim to orchestrator...")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:8001/process",
                json={
                    "message": f"Please process this insurance claim: {json.dumps(test_claim)}",
                    "session_id": f"dynamic_test_{int(time.time())}"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Claim processing completed!")
                print()
                
                # Check the response for email-related information
                message = result.get("message", "")
                print("📋 Response Analysis:")
                print("-" * 40)
                
                if "email" in message.lower():
                    if "sent successfully" in message.lower():
                        print("🎉 ✅ ON-DEMAND DISCOVERY SUCCESS!")
                        print("📧 Communication Agent was discovered and email was sent!")
                    elif "failed" in message.lower() or "error" in message.lower():
                        print("⚠️ Communication Agent discovered but email failed")
                    elif "skipped" in message.lower() or "not available" in message.lower():
                        print("❌ Communication Agent was not discovered (still offline?)")
                        print("💡 Check if Communication Agent is running on port 8005")
                    else:
                        print("📧 Email mentioned but status unclear")
                else:
                    print("❓ No email notification mentioned in response")
                
                print()
                print("📄 Full Response:")
                print("-" * 40)
                print(message[:500] + "..." if len(message) > 500 else message)
                
                return "email" in message.lower() and "sent successfully" in message.lower()
                
            else:
                print(f"❌ Claim processing failed: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error during claim processing: {e}")
        return False

async def main():
    print("🔍 Testing Dynamic Agent Discovery System")
    print("Testing if Communication Agent (just started) can be discovered on-demand")
    print()
    
    # Test on-demand discovery
    success = await test_claim_with_email()
    
    print()
    print("=" * 60)
    print("📊 DYNAMIC DISCOVERY TEST RESULT")
    print("=" * 60)
    
    if success:
        print("🎉 SUCCESS! Dynamic Discovery Working!")
        print("✅ Communication Agent discovered on-demand")
        print("✅ Email notification sent successfully")
        print("✅ No workflow interruption")
    else:
        print("⚠️ Test completed but email status unclear")
        print("💡 Check orchestrator logs for detailed information")
        print("💡 Communication Agent might need time to be discovered")

if __name__ == "__main__":
    asyncio.run(main())