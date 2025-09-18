"""
Test Step 1: Simple test to verify A2A agent is responding on port 8007
(Assumes agent is already running)
"""
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent_health():
    """Test that the agent is responding on port 8007"""
    logger.info("🧪 Testing Step 1: A2A Agent Health Check")
    
    try:
        # Test agent root endpoint
        logger.info("🔍 Testing agent root endpoint...")
        response = requests.get("http://localhost:8007/", timeout=5)
        
        if response.status_code == 200:
            logger.info("✅ SUCCESS: Agent root endpoint responding")
            return True
        else:
            logger.error(f"❌ FAIL: Agent responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ FAIL: Could not connect to agent on port 8007")
        logger.info("💡 Make sure the agent is running: python __main__.py")
        return False
    except Exception as e:
        logger.error(f"❌ FAIL: Test error: {e}")
        return False

def test_agent_card():
    """Test that the agent card endpoint is working"""
    logger.info("🔍 Testing agent card endpoint...")
    
    try:
        response = requests.get("http://localhost:8007/agent", timeout=5)
        
        if response.status_code == 200:
            agent_data = response.json()
            logger.info(f"✅ SUCCESS: Agent card retrieved - Name: {agent_data.get('name', 'Unknown')}")
            return True
        else:
            logger.error(f"❌ FAIL: Agent card endpoint responded with status {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ FAIL: Agent card test error: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting Simple Agent Health Tests...")
    
    # Test basic connectivity
    health_ok = test_agent_health()
    
    # Test agent card if health is ok
    card_ok = False
    if health_ok:
        card_ok = test_agent_card()
    
    # Summary
    if health_ok and card_ok:
        print("\n🎉 Step 1 PASSED: A2A Voice Agent is running and responding!")
        print("✅ Agent is accessible on http://localhost:8007")
        print("✅ Agent card endpoint is working")
        print("📋 Ready to proceed to Step 2: Voice Agent Executor")
    elif health_ok:
        print("\n⚠️  Step 1 PARTIAL: Agent is running but some endpoints may need work")
        print("✅ Basic connectivity working")
        print("❌ Agent card endpoint needs attention")
    else:
        print("\n💥 Step 1 FAILED: Agent is not responding")
        print("💡 Make sure to start the agent: python __main__.py")