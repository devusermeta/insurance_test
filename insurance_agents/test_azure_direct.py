"""
Final Email Test - Direct Azure API Test
This bypasses our agent and tests Azure Communication Services directly
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

async def test_azure_communication_directly():
    """Test Azure Communication Services directly to isolate the issue"""
    
    print("🔧 Direct Azure Communication Services Test")
    print("=" * 50)
    
    connection_string = os.getenv('AZURE_COMMUNICATION_CONNECTION_STRING')
    sender_email = os.getenv('AZURE_COMMUNICATION_SENDER_EMAIL')
    
    if not connection_string or not sender_email:
        print("❌ Missing environment variables")
        return False
    
    print(f"✅ Connection String: {connection_string[:50]}...")
    print(f"✅ Sender Email: {sender_email}")
    
    try:
        from azure.communication.email import EmailClient
        
        print("\n1. 🔧 Creating EmailClient...")
        client = EmailClient.from_connection_string(connection_string)
        print("   ✅ EmailClient created successfully")
        
        print("\n2. 📧 Preparing test email...")
        message = {
            "senderAddress": sender_email,
            "recipients": {
                "to": [{"address": "purohitabhinav2001@gmail.com"}]
            },
            "content": {
                "subject": "🎉 Azure Communication Services Test - SUCCESS!",
                "plainText": """
Hello!

This is a test email from your Azure Communication Services integration.

If you're reading this, it means:
✅ Azure Communication Services is properly configured
✅ Domain is correctly linked
✅ Email sending is working perfectly
✅ Your Communication Agent is ready for production!

Insurance Claim Notifications will now be sent automatically when claims are processed.

Best regards,
Your Insurance Communication Agent
                """,
                "html": """
                <html>
                <body>
                    <h2>🎉 Azure Communication Services Test - SUCCESS!</h2>
                    <p>Hello!</p>
                    <p>This is a test email from your Azure Communication Services integration.</p>
                    
                    <div style="background-color: #d4edda; padding: 15px; margin: 20px 0; border-left: 4px solid #28a745;">
                        <h3>If you're reading this, it means:</h3>
                        <ul>
                            <li>✅ Azure Communication Services is properly configured</li>
                            <li>✅ Domain is correctly linked</li>
                            <li>✅ Email sending is working perfectly</li>
                            <li>✅ Your Communication Agent is ready for production!</li>
                        </ul>
                    </div>
                    
                    <p><strong>Insurance Claim Notifications</strong> will now be sent automatically when claims are processed.</p>
                    
                    <p>Best regards,<br>
                    Your Insurance Communication Agent</p>
                </body>
                </html>
                """
            }
        }
        
        print("   📋 Test email prepared")
        print(f"   📧 To: purohitabhinav2001@gmail.com")
        print(f"   📨 Subject: {message['content']['subject']}")
        
        print("\n3. 🚀 Sending email...")
        try:
            poller = client.begin_send(message)
            result = poller.result()
            
            print(f"   🎉 ✅ EMAIL SENT SUCCESSFULLY!")
            print(f"   📧 Check purohitabhinav2001@gmail.com inbox")
            print(f"   📁 Also check spam/junk folder")
            print(f"   🆔 Message ID: {getattr(result, 'id', 'N/A')}")
            print(f"   📊 Status: {getattr(result, 'status', 'Sent')}")
            
            return True
            
        except Exception as send_error:
            print(f"   ❌ Email sending failed: {send_error}")
            print(f"   🔍 Error type: {type(send_error).__name__}")
            
            # Check if it's still a domain linking issue
            if "DomainNotLinked" in str(send_error):
                print("\n🔧 Domain Linking Issue Detected:")
                print("   The domain is not properly linked to the Communication Services resource")
                print("   Try these steps:")
                print("   1. Go to Communication Services → claim-assist → Email → Domains")
                print("   2. Click 'Connect domains'")
                print("   3. Select your domain and connect it")
                print("   4. Wait 5-10 minutes for propagation")
            
            return False
            
    except ImportError:
        print("❌ Azure Communication Email SDK not installed")
        return False
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False

async def main():
    print("🧪 Final Azure Communication Services Email Test")
    print("This will attempt to send a real email directly through Azure")
    
    success = await test_azure_communication_directly()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SUCCESS! Email integration is working!")
        print("📧 Check your email inbox")
        print("✅ Communication Agent is ready for production")
    else:
        print("❌ Email sending failed")
        print("🔧 Check domain linking in Azure Portal")

if __name__ == "__main__":
    asyncio.run(main())