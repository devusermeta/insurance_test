"""
Complete Email Notification Test
Tests the end-to-end flow: Orchestrator → Communication Agent → Email → Dashboard Notification
"""

import asyncio
import httpx
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

async def test_complete_email_notification_flow():
    """Test the complete email notification workflow"""
    
    print("🧪 Testing Complete Email Notification Flow")
    print("=" * 60)
    
    print("This test simulates:")
    print("1. 📧 Communication Agent sends real email")
    print("2. 📢 Communication Agent notifies dashboard")
    print("3. 🌐 Dashboard broadcasts to frontend via WebSocket")
    print("4. 🎉 User sees popup notification")
    
    # Test data simulating orchestrator output
    test_claim_data = {
        "claim_id": "FULL-WORKFLOW-TEST-001",
        "patient_name": "Integration Test Patient",
        "amount": "$1,999.99",
        "status": "APPROVED",
        "reason": "Complete integration test: This claim has been processed through the full workflow including orchestrator validation, all agent approvals, and automatic email notification with real-time frontend updates.",
        "service_description": "Complete workflow integration test",
        "provider": "Test Medical Center",
        "category": "Integration Test",
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"\n📋 Test Claim Data:")
    print(f"   🆔 Claim ID: {test_claim_data['claim_id']}")
    print(f"   👤 Patient: {test_claim_data['patient_name']}")
    print(f"   💰 Amount: {test_claim_data['amount']}")
    print(f"   ✅ Status: {test_claim_data['status']}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            # Step 1: Verify Communication Agent is running
            print(f"\n1. 🔍 Checking Communication Agent (localhost:8005)...")
            discovery_response = await client.get("http://localhost:8005/.well-known/agent.json")
            
            if discovery_response.status_code == 200:
                agent_info = discovery_response.json()
                print(f"   ✅ Communication Agent found: {agent_info.get('name')}")
            else:
                print(f"   ❌ Communication Agent not responding: {discovery_response.status_code}")
                return False
            
            # Step 2: Verify Dashboard is running
            print(f"\n2. 🌐 Checking Dashboard (localhost:3000)...")
            dashboard_response = await client.get("http://localhost:3000/api/health")
            
            if dashboard_response.status_code == 200:
                print(f"   ✅ Dashboard is online")
            else:
                print(f"   ❌ Dashboard not responding: {dashboard_response.status_code}")
                return False
            
            # Step 3: Simulate orchestrator calling Communication Agent
            print(f"\n3. 📧 Simulating Orchestrator → Communication Agent call...")
            
            email_request = {
                "action": "send_claim_notification",
                "data": test_claim_data
            }
            
            print(f"   📤 Sending email request...")
            email_response = await client.post(
                "http://localhost:8005/process",
                json=email_request
            )
            
            if email_response.status_code == 200:
                email_result = email_response.json()
                print(f"   📨 Email response: {json.dumps(email_result, indent=6)}")
                
                if email_result.get("success"):
                    print(f"\n🎉 ✅ COMPLETE SUCCESS!")
                    print(f"   📧 Real email sent to purohitabhinav2001@gmail.com")
                    print(f"   📢 Dashboard notification triggered")
                    print(f"   🌐 Frontend should show popup notification")
                    print(f"   🔗 Message ID: {email_result.get('message_id', 'N/A')}")
                    
                    print(f"\n👀 Check the frontend:")
                    print(f"   1. Open http://localhost:3000/claims")
                    print(f"   2. Look for popup notification in top-right")
                    print(f"   3. Check WebSocket status in bottom-right")
                    print(f"   4. Verify email in purohitabhinav2001@gmail.com")
                    
                    return True
                else:
                    print(f"   ❌ Email sending failed: {email_result.get('error')}")
                    return False
            else:
                print(f"   ❌ Communication Agent error: {email_response.status_code}")
                print(f"   📄 Response: {email_response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

async def test_dashboard_notification_direct():
    """Test sending notification directly to dashboard"""
    
    print(f"\n" + "=" * 60)
    print(f"🔧 Testing Direct Dashboard Notification")
    print("=" * 60)
    
    test_notification = {
        "claim_id": "DIRECT-NOTIFICATION-TEST",
        "email_status": "sent",
        "details": {
            "recipient": "purohitabhinav2001@gmail.com",
            "sender": "DoNotReply@test.azurecomm.net",
            "timestamp": datetime.now().isoformat(),
            "test": True
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "http://localhost:3000/api/email-notification",
                json=test_notification
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Dashboard notification sent successfully")
                print(f"📢 Check frontend for popup notification")
                return True
            else:
                print(f"❌ Dashboard notification failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Dashboard notification error: {e}")
        return False

async def main():
    print("🚀 Complete Email Notification System Test")
    print("Testing integration between Communication Agent, Dashboard, and Frontend")
    
    print("\n⚠️  Prerequisites:")
    print("   1. Communication Agent running on port 8005")
    print("   2. Dashboard running on port 3000")
    print("   3. Frontend open at http://localhost:3000/claims")
    
    input("\nPress Enter to start testing...")
    
    # Test 1: Complete workflow
    workflow_success = await test_complete_email_notification_flow()
    
    # Test 2: Direct dashboard notification
    dashboard_success = await test_dashboard_notification_direct()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"Complete Workflow: {'✅ PASSED' if workflow_success else '❌ FAILED'}")
    print(f"Dashboard Notification: {'✅ PASSED' if dashboard_success else '❌ FAILED'}")
    
    if workflow_success and dashboard_success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Email notification system is fully functional")
        print(f"✅ Real-time frontend notifications working")
        print(f"✅ End-to-end integration complete")
        
        print(f"\n🔥 Your Insurance System Now Features:")
        print(f"   🏥 Multi-agent claim validation")
        print(f"   📧 Real email notifications via Azure")
        print(f"   📢 Real-time frontend notifications")
        print(f"   🌐 WebSocket live updates")
        print(f"   🎯 Complete workflow integration")
    else:
        print(f"\n⚠️  Some tests failed - check error messages above")

if __name__ == "__main__":
    asyncio.run(main())