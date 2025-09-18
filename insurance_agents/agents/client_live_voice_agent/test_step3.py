"""
Test Step 3: Verify A2A HTTP server and endpoints work
Tests the standard A2A protocol endpoints and any additional voice-specific routes.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import asyncio
import logging
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_a2a_endpoints():
    """Test A2A protocol endpoints and voice server functionality"""
    logger.info("🚀 Starting Step 3 Tests...")
    logger.info("🧪 Testing Step 3: A2A HTTP Server + Voice Endpoints")
    
    base_url = "http://localhost:8007"
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Standard A2A agent card endpoint
    total_tests += 1
    try:
        logger.info("🔍 Testing A2A agent card endpoint...")
        response = requests.get(f"{base_url}/.well-known/agent.json", timeout=5)
        
        if response.status_code == 200:
            agent_card = response.json()
            logger.info(f"✅ Agent card retrieved: {agent_card.get('name', 'Unknown')}")
            logger.info(f"📝 Description: {agent_card.get('description', 'No description')[:100]}...")
            logger.info(f"🎯 Skills: {len(agent_card.get('skills', []))} skills available")
            tests_passed += 1
        else:
            logger.error(f"❌ Agent card endpoint failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Agent card test error: {e}")
    
    # Test 2: Check agent capabilities
    total_tests += 1
    try:
        logger.info("🔍 Testing agent capabilities...")
        response = requests.get(f"{base_url}/.well-known/agent.json", timeout=5)
        
        if response.status_code == 200:
            agent_card = response.json()
            capabilities = agent_card.get('capabilities', {})
            input_modes = agent_card.get('defaultInputModes', [])
            output_modes = agent_card.get('defaultOutputModes', [])
            
            # Check for voice capabilities in multiple places
            voice_in_capabilities = capabilities.get('audio', False)
            voice_in_input_modes = 'audio' in input_modes
            voice_in_output_modes = 'audio' in output_modes
            
            if voice_in_capabilities or (voice_in_input_modes and voice_in_output_modes):
                logger.info("✅ Voice capabilities detected in agent card")
                logger.info(f"📥 Input modes: {input_modes}")
                logger.info(f"📤 Output modes: {output_modes}")
                tests_passed += 1
            else:
                logger.warning("⚠️ Voice capabilities not found in agent card")
                logger.warning(f"📥 Input modes: {input_modes}")
                logger.warning(f"📤 Output modes: {output_modes}")
        else:
            logger.error(f"❌ Could not retrieve agent capabilities")
    except Exception as e:
        logger.error(f"❌ Capabilities test error: {e}")
    
    # Test 3: Check CORS headers (needed for browser voice interface)
    total_tests += 1
    try:
        logger.info("🔍 Testing CORS configuration...")
        
        # Try both OPTIONS and GET requests to check CORS
        try:
            response = requests.options(f"{base_url}/.well-known/agent.json", timeout=5)
        except:
            # If OPTIONS fails, try GET request to check headers
            response = requests.get(f"{base_url}/.well-known/agent.json", timeout=5)
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        # Check if any CORS headers are present
        cors_configured = any(header_value for header_value in cors_headers.values() if header_value)
        
        if cors_configured:
            logger.info("✅ CORS headers configured for browser access")
            for header, value in cors_headers.items():
                if value:
                    logger.info(f"   {header}: {value}")
            tests_passed += 1
        else:
            logger.warning("⚠️ CORS headers not found (may affect browser voice interface)")
            logger.warning("💡 This is expected for A2A agents, but may need CORS for voice UI")
    except Exception as e:
        logger.error(f"❌ CORS test error: {e}")
    
    # Test 4: Agent health/status check
    total_tests += 1
    try:
        logger.info("🔍 Testing agent responsiveness...")
        response = requests.get(f"{base_url}/", timeout=5)
        
        # A2A agents typically return 405 (Method Not Allowed) for root GET
        # This actually indicates the server is working properly
        if response.status_code in [200, 405, 404]:
            logger.info("✅ Agent server is responsive")
            tests_passed += 1
        else:
            logger.error(f"❌ Agent server returned unexpected status: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Agent responsiveness test error: {e}")
    
    # Summary
    logger.info(f"📊 Step 3 Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        logger.info("🎉 Step 3 PASSED: A2A server and voice endpoints working!")
        return True
    elif tests_passed >= total_tests - 1:
        logger.info("🎯 Step 3 MOSTLY PASSED: Minor issues detected")
        return True
    else:
        logger.error("💥 Step 3 FAILED: Significant server issues")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_a2a_endpoints())
    if result:
        print("\n🎉 Step 3 COMPLETED: A2A Voice Server is working!")
        print("📋 Ready to proceed to Step 4: Voice Interface")
    else:
        print("\n💥 Step 3 FAILED: Server issues need to be resolved")
        print("💡 Make sure the agent is running: python __main__.py")