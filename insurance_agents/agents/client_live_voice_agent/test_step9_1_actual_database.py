#!/usr/bin/env python3
"""
Test Step 9.1: Verify Actual Database Data in Voice Agent Response
This test verifies that the voice agent is returning actual database data, not pattern matching
"""

import asyncio
import logging
import requests
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def test_actual_database_response():
    """Test that voice agent returns actual database data"""
    logger.info("🚀 Testing Voice Agent Database Integration")
    logger.info("=" * 70)
    
    try:
        # Test with a specific query that should return database data
        test_query = "What insurance claims are in the database?"
        
        logger.info(f"🔍 Querying: {test_query}")
        
        response = requests.post(
            "http://localhost:8007/api/agent/execute",
            json={
                "message": test_query,
                "session_id": "database_test"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "")
            
            logger.info(f"📝 Voice Agent Response:")
            logger.info(f"   {response_text}")
            logger.info("")
            
            # Check if response contains actual database data indicators
            database_indicators = [
                "IP-01", "IP-02", "OP-01", "OP-02",  # Claim IDs from database
                "John Smith", "Jane Doe",  # Patient names from database
                "inpatient", "outpatient",  # Claim types from database
                "approval", "rejection"  # Claim statuses from database
            ]
            
            found_indicators = [indicator for indicator in database_indicators if indicator.lower() in response_text.lower()]
            
            if found_indicators:
                logger.info("✅ SUCCESS: Voice agent returned actual database data!")
                logger.info(f"   Found database indicators: {found_indicators}")
                return True
            else:
                logger.info("❌ FAILURE: Voice agent returned pattern matching response, not database data")
                logger.info("   This indicates MCP integration is not working in voice agent execution")
                return False
                
        else:
            logger.error(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test Error: {e}")
        return False

async def main():
    """Main test function"""
    success = await test_actual_database_response()
    
    if success:
        logger.info("\n🎉 Voice agent successfully integrated with database!")
        logger.info("   Users will get real insurance data in voice interactions")
    else:
        logger.info("\n⚠️  Voice agent needs MCP integration debugging")
        logger.info("   Currently returning pattern matching responses instead of database queries")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())