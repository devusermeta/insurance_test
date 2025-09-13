"""
Quick Email Test After Domain Connection
Run this immediately after connecting the domain in Azure Portal
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the agents path
sys.path.append("agents/communication_agent")

async def quick_email_test():
    """Quick test after domain connection"""
    
    print("🚀 Quick Email Test After Domain Connection")
    print("=" * 50)
    
    try:
        # Import and test the Communication Agent directly
        from agents.communication_agent.communication_agent_executor import CommunicationAgentExecutor
        
        print("1. 🔧 Creating Communication Agent instance...")
        agent = CommunicationAgentExecutor()
        
        print(f"2. ✅ Azure Configuration:")
        print(f"   📧 Sender: {agent.sender_email}")
        print(f"   🔗 Client: {'✅ Ready' if agent.email_client else '❌ Not ready'}")
        
        if not agent.email_client:
            print("❌ Azure Communication Services not properly initialized")
            return False
        
        print("\n3. 📤 Sending test email...")
        
        # Test claim data
        test_claim = {
            "claim_id": "DOMAIN-CONNECTION-TEST-001",
            "patient_name": "Test Patient - Domain Connected",
            "amount": "$1,234.56",
            "status": "APPROVED",
            "reason": "🎉 SUCCESS! This email confirms that the Azure Communication Services domain has been properly connected and email notifications are working correctly.",
            "service_description": "Domain connection verification test",
            "provider": "Azure Communication Services Test",
            "timestamp": datetime.now().isoformat()
        }
        
        print("   📋 Test claim details:")
        print(f"      🆔 ID: {test_claim['claim_id']}")
        print(f"      👤 Patient: {test_claim['patient_name']}")
        print(f"      💰 Amount: {test_claim['amount']}")
        print(f"      ✅ Status: {test_claim['status']}")
        
        # Send the email
        result = await agent._send_claim_notification(test_claim)
        
        print(f"\n4. 📨 Email sending result:")
        print(f"   Success: {result.get('success', False)}")
        
        if result.get('success'):
            print("   🎉 ✅ EMAIL SENT SUCCESSFULLY!")
            print("   📧 Check purohitabhinav2001@gmail.com")
            print("   📁 Also check spam/junk folder")
            if 'message_id' in result:
                print(f"   🆔 Message ID: {result['message_id']}")
            return True
        else:
            print(f"   ❌ Email failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

async def main():
    print("📧 Domain Connection Email Test")
    print("Run this IMMEDIATELY after connecting the domain in Azure Portal")
    
    input("\nPress Enter after you've connected the domain...")
    
    success = await quick_email_test()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SUCCESS! Domain connection working!")
        print("📧 Real email sent to purohitabhinav2001@gmail.com")
        print("✅ Communication Agent is fully functional")
    else:
        print("❌ Still having issues - check Azure Portal domain connection")

if __name__ == "__main__":
    asyncio.run(main())