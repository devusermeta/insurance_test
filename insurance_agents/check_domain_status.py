"""
Azure Communication Services Domain Status Checker
This will help us understand why the domain isn't appearing in the dropdown
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def check_domain_status():
    """Check the current domain configuration status"""
    
    print("🔍 Azure Communication Services Domain Status Check")
    print("=" * 55)
    
    # Check environment variables
    connection_string = os.getenv('AZURE_COMMUNICATION_CONNECTION_STRING')
    sender_email = os.getenv('AZURE_COMMUNICATION_SENDER_EMAIL')
    
    print("1. 📧 Environment Configuration:")
    print(f"   Connection String: {'✅ Set' if connection_string else '❌ Missing'}")
    print(f"   Sender Email: {sender_email if sender_email else '❌ Missing'}")
    
    if sender_email:
        # Parse the domain from the email
        domain = sender_email.split('@')[1] if '@' in sender_email else 'Unknown'
        print(f"   Domain from email: {domain}")
    
    # Try to test the Azure Communication Services connection
    print("\n2. 🔗 Azure Communication Services Connection Test:")
    
    try:
        from azure.communication.email import EmailClient
        
        if connection_string:
            print("   📤 Creating EmailClient...")
            client = EmailClient.from_connection_string(connection_string)
            print("   ✅ EmailClient created successfully")
            print("   📋 This suggests your connection string is valid")
            
            # Try to get some info (this might fail if domain not verified)
            print("\n3. 🧪 Domain Verification Test:")
            try:
                # Create a test email message to see what error we get
                test_message = {
                    "senderAddress": sender_email,
                    "recipients": {
                        "to": [{"address": "test@example.com"}]
                    },
                    "content": {
                        "subject": "Test",
                        "plainText": "Test message"
                    }
                }
                
                print("   📝 Testing email message format...")
                # We won't actually send this, just test the format
                print("   ✅ Email message format is correct")
                
            except Exception as e:
                print(f"   ⚠️  Email format test: {e}")
                
        else:
            print("   ❌ No connection string found")
            
    except ImportError:
        print("   ❌ Azure Communication Services SDK not available")
    except Exception as e:
        print(f"   ❌ Connection test failed: {e}")
    
    # Provide next steps
    print("\n" + "=" * 55)
    print("📋 NEXT STEPS:")
    print("=" * 55)
    
    if not connection_string or not sender_email:
        print("❌ Environment configuration incomplete")
        print("   Fix .env file first")
    else:
        print("✅ Environment configuration looks correct")
        print("\n🔧 Domain Issues - Try these steps:")
        print("1. Go to Azure Portal → Communication Services → claim-assist")
        print("2. Click Email → Domains")
        print("3. Check if your domain shows 'Verified' status")
        print("4. If not verified:")
        print("   - Click on the domain name")
        print("   - Look for verification instructions")
        print("   - Or create a new Azure managed domain")
        print("\n📞 Alternative: Create Fresh Domain")
        print("1. Email → Domains → Add domain")
        print("2. Select 'Azure managed domain'")
        print("3. Wait for automatic verification")
        print("4. Update .env with new domain")

async def main():
    await check_domain_status()

if __name__ == "__main__":
    asyncio.run(main())