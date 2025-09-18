"""
Test Step 1: Verify A2A agent startup works on port 8007
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import asyncio
import logging
import requests
import time
from multiprocessing import Process

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_agent():
    """Start the voice agent in a separate process"""
    try:
        import __main__ as main_module
        asyncio.run(main_module.main())
    except Exception as e:
        logger.error(f"Agent startup failed: {e}")

async def test_agent_startup():
    """Test that the agent starts and responds on port 8007"""
    logger.info("🧪 Testing Step 1: A2A Agent Startup")
    
    # Start agent in background process
    logger.info("🚀 Starting voice agent process...")
    agent_process = Process(target=start_agent)
    agent_process.start()
    
    # Wait for startup
    await asyncio.sleep(3)
    
    try:
        # Test if agent is responding
        logger.info("🔍 Testing agent health endpoint...")
        response = requests.get("http://localhost:8007/health", timeout=5)
        
        if response.status_code == 200:
            logger.info("✅ SUCCESS: Agent is running and responding on port 8007")
            return True
        else:
            logger.error(f"❌ FAIL: Agent responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ FAIL: Could not connect to agent on port 8007")
        return False
    except Exception as e:
        logger.error(f"❌ FAIL: Test error: {e}")
        return False
    finally:
        # Clean up
        agent_process.terminate()
        agent_process.join(timeout=5)
        if agent_process.is_alive():
            agent_process.kill()

if __name__ == "__main__":
    result = asyncio.run(test_agent_startup())
    if result:
        print("\n🎉 Step 1 PASSED: Basic A2A agent structure is working!")
    else:
        print("\n💥 Step 1 FAILED: Need to fix agent startup issues")