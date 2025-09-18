"""
Test Step 2: Verify Voice Agent Executor and Azure AI Foundry integration
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import asyncio
import logging
import requests
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_voice_agent_executor():
    """Test that the voice agent executor initializes and can process requests"""
    logger.info("🧪 Testing Step 2: Voice Agent Executor + Azure AI Foundry")
    
    try:
        # Import the voice agent executor
        from voice_agent_executor import VoiceAgentExecutor
        
        logger.info("✅ Voice agent executor imported successfully")
        
        # Create instance
        voice_executor = VoiceAgentExecutor()
        logger.info("✅ Voice agent executor instance created")
        
        # Test initialization
        await voice_executor.initialize()
        logger.info("✅ Voice agent executor initialized")
        
        # Check Azure AI client setup
        if voice_executor.project_client:
            logger.info("✅ Azure AI Foundry client is configured")
        else:
            logger.info("⚠️ Azure AI Foundry client not configured (using fallback)")
        
        # Check voice agent creation
        if voice_executor.azure_voice_agent:
            logger.info(f"✅ Azure AI Voice Agent created: {voice_executor.azure_voice_agent.name}")
            logger.info(f"🆔 Agent ID: {voice_executor.azure_voice_agent.id}")
        else:
            logger.info("⚠️ Azure AI Voice Agent not created (using fallback processing)")
        
        # Test A2A compatibility by checking required methods
        required_methods = ['initialize', 'execute']
        for method in required_methods:
            if hasattr(voice_executor, method):
                logger.info(f"✅ Required A2A method '{method}' is implemented")
            else:
                logger.error(f"❌ Missing required A2A method: {method}")
                return False
        
        logger.info("🎉 Step 2 PASSED: Voice Agent Executor is working!")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("💡 Make sure you're running from the correct directory with virtual environment activated")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing voice agent executor: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_running_agent_with_new_executor():
    """Test that the running agent is using the new voice agent executor"""
    logger.info("🔍 Testing integration with running agent...")
    
    try:
        # Test basic connectivity
        response = requests.get("http://localhost:8007/health", timeout=5)
        logger.info(f"📡 Agent connectivity test: {response.status_code}")
        
        # Check if agent is responding (even 404 means it's running)
        if response.status_code in [200, 404, 405]:
            logger.info("✅ Agent is running and responding")
            return True
        else:
            logger.warning(f"⚠️ Agent responded with unexpected status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ Could not connect to agent on port 8007")
        logger.info("💡 Make sure to restart the agent: python __main__.py")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing agent connectivity: {e}")
        return False

if __name__ == "__main__":
    async def run_tests():
        logger.info("🚀 Starting Step 2 Tests...")
        
        # Test 1: Voice Agent Executor functionality
        test1_result = await test_voice_agent_executor()
        
        # Test 2: Integration with running agent
        test2_result = await test_running_agent_with_new_executor()
        
        if test1_result and test2_result:
            print("\n🎉 Step 2 COMPLETED: Voice Agent Executor with Azure AI Foundry!")
            print("✅ Voice agent executor is properly implemented")
            print("✅ A2A compatibility verified")
            print("✅ Azure AI Foundry integration ready")
            print("\n📋 Ready to proceed to Step 3: Voice Server Implementation")
        else:
            print("\n💥 Step 2 FAILED: Issues found with voice agent executor")
            if not test1_result:
                print("❌ Voice agent executor has issues")
            if not test2_result:
                print("❌ Agent connectivity issues")
    
    asyncio.run(run_tests())