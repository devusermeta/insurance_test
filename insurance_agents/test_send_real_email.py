"""
Test Actual Email Sending Through Communication Agent
This will make a real API call to send an actual email
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

async def send_real_email_test():
    """Send a real email through the Communication Agent A2A endpoint"""
    
    print("📧 Sending REAL Email Through Communication Agent")
    print("=" * 55)
    
    # Verify environment
    connection_string = os.getenv('AZURE_COMMUNICATION_CONNECTION_STRING')
    sender_email = os.getenv('AZURE_COMMUNICATION_SENDER_EMAIL')
    
    if not connection_string or not sender_email:
        print("❌ Azure Communication Services environment variables missing")
        return False
    
    print("✅ Azure Communication Services environment configured")
    print(f"   📧 Sender: {sender_email}")
    print(f"   📧 Recipient: purohitabhinav2001@gmail.com")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Verify Communication Agent is running
            print("\n1. 🔍 Checking Communication Agent availability...")
            try:
                discovery_response = await client.get("http://localhost:8005/.well-known/agent.json")
                if discovery_response.status_code != 200:
                    print(f"❌ Communication Agent not responding: {discovery_response.status_code}")
                    return False
                
                agent_info = discovery_response.json()
                print(f"   ✅ Agent found: {agent_info.get('name', 'Unknown')}")
                
                # Check for email skill
                skills = agent_info.get('skills', [])
                email_skill = None
                for skill in skills:
                    if 'notification' in skill.get('id', '').lower():
                        email_skill = skill
                        break
                
                if not email_skill:
                    print("❌ Email notification skill not found")
                    return False
                
                print(f"   📧 Email skill available: {email_skill.get('name')}")
                
            except Exception as e:
                print(f"❌ Cannot connect to Communication Agent: {e}")
                print("💡 Make sure to start the Communication Agent:")
                print("   python -m agents.communication_agent --port 8005")
                return False
            
            # Step 2: Send actual email using the agent's A2A interface
            print("\n2. 📤 Sending real email notification...")
            
            # Prepare claim data for email
            claim_data = {
                "claim_id": "REAL-EMAIL-TEST-001",
                "patient_name": "Test Patient - Real Email",
                "amount": "$999.99",
                "status": "APPROVED",
                "reason": "This is a REAL test email from the Communication Agent integration. The claim has been processed and approved by all validation agents.",
                "service_description": "Integration test for Azure Communication Services",
                "provider": "Test Insurance System",
                "timestamp": datetime.now().isoformat()
            }
            
            print("   📋 Test claim data:")
            print(f"      🆔 Claim ID: {claim_data['claim_id']}")
            print(f"      👤 Patient: {claim_data['patient_name']}")
            print(f"      💰 Amount: {claim_data['amount']}")
            print(f"      ✅ Status: {claim_data['status']}")
            
            # For A2A protocol, we would normally use the MCP client
            # But for testing, let's try to call the agent directly
            # This simulates what the orchestrator would do
            
            # Try to call the agent using a direct HTTP request to test
            # Note: In production, this would be done via A2A protocol
            test_url = "http://localhost:8005"
            
            # Try different possible endpoints
            endpoints_to_try = [
                "/send_claim_notification",
                "/execute", 
                "/api/send_claim_notification",
                "/process"
            ]
            
            email_sent = False
            for endpoint in endpoints_to_try:
                try:
                    print(f"   🔄 Trying endpoint: {endpoint}")
                    
                    payload = {
                        "action": "send_claim_notification",
                        "data": claim_data
                    }
                    
                    response = await client.post(
                        f"{test_url}{endpoint}",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"   📨 Response from {endpoint}: {json.dumps(result, indent=2)}")
                        
                        if result.get("success"):
                            print("   🎉 ✅ REAL EMAIL SENT SUCCESSFULLY!")
                            print(f"   📧 Check purohitabhinav2001@gmail.com for the email")
                            if "message_id" in result:
                                print(f"   🆔 Message ID: {result['message_id']}")
                            email_sent = True
                            break
                        else:
                            print(f"   ⚠️ Email sending failed: {result.get('error', 'Unknown error')}")
                    
                    elif response.status_code == 404:
                        print(f"   ❌ Endpoint {endpoint} not found")
                    else:
                        print(f"   ❌ HTTP error {response.status_code}: {response.text}")
                        
                except Exception as e:
                    print(f"   ❌ Error with endpoint {endpoint}: {e}")
            
            if not email_sent:
                print("\n🔄 All direct endpoints failed. This is expected for A2A agents.")
                print("💡 A2A agents don't expose direct HTTP endpoints like /execute")
                print("📧 Email sending would work through the A2A protocol in production")
                print("🧪 Let's try a different approach...")
                
                # Let's check if we can inspect the agent logs or status
                return await test_agent_functionality()
            
            return email_sent
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

async def test_agent_functionality():
    """Test the agent's functionality in a different way"""
    
    print("\n3. 🔧 Alternative Testing Approach")
    print("=" * 40)
    
    print("Since A2A agents don't expose direct HTTP endpoints,")
    print("let's verify the agent's internal functionality:")
    
    try:
        # Import the agent directly to test its functionality
        import sys
        sys.path.append("agents/communication_agent")
        
        from agents.communication_agent.communication_agent_executor import CommunicationAgentExecutor
        
        # Create agent instance
        agent = CommunicationAgentExecutor()
        
        # Test claim data
        test_claim = {
            "claim_id": "DIRECT-TEST-001",
            "patient_name": "Direct Test Patient",
            "amount": "$500.00",
            "status": "APPROVED", 
            "reason": "Direct test of Communication Agent email functionality with Azure Communication Services",
            "timestamp": datetime.now().isoformat()
        }
        
        print("   🧪 Testing agent directly...")
        print(f"   📧 Sender configured: {agent.sender_email}")
        print(f"   🔗 Azure client: {'✅ Available' if agent.email_client else '❌ Not initialized'}")
        
        # Call the agent method directly
        result = await agent._send_claim_notification(test_claim)
        
        print(f"   📨 Direct call result:")
        print(f"      {json.dumps(result, indent=6)}")
        
        if result.get("success"):
            print("\n🎉 ✅ REAL EMAIL SENT VIA DIRECT AGENT CALL!")
            print("📧 Check purohitabhinav2001@gmail.com for the email")
            return True
        else:
            print(f"\n❌ Email failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Direct agent test error: {e}")
        return False

async def main():
    print("🚀 REAL Email Sending Test")
    print("This will actually send an email to purohitabhinav2001@gmail.com")
    print("\n⚠️  IMPORTANT: Make sure Communication Agent is running:")
    print("   python -m agents.communication_agent --port 8005")
    
    input("\nPress Enter to send a REAL email...")
    
    success = await send_real_email_test()
    
    print("\n" + "=" * 55)
    print("📊 REAL EMAIL TEST RESULT")
    print("=" * 55)
    
    if success:
        print("🎉 SUCCESS! Real email was sent!")
        print("📧 Check purohitabhinav2001@gmail.com inbox")
        print("📁 Also check spam/junk folder")
        print("✅ Communication Agent is working correctly")
    else:
        print("❌ Email sending failed")
        print("🔧 Check Azure Communication Services configuration")
        print("🔍 Check agent logs for detailed error information")

if __name__ == "__main__":
    asyncio.run(main())