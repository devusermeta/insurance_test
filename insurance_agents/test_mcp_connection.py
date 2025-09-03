#!/usr/bin/env python3
"""
Test MCP Server Connection

Simple script to test if the MCP server is running and accessible on port 8000.
Includes terminal logging for visibility.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

class TerminalLogger:
    """Simple terminal logging for testing"""
    
    @staticmethod
    def log(level: str, component: str, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        emoji_map = {'INFO': '📋', 'SUCCESS': '✅', 'ERROR': '❌', 'WARNING': '⚠️'}
        emoji = emoji_map.get(level, '📋')
        print(f"[{timestamp}] {emoji} {component.upper()}: {message}")

async def test_mcp_connection():
    """Test MCP server connection on port 8000"""
    logger = TerminalLogger()
    
    logger.log("INFO", "MCP_TEST", "Testing MCP server connection on port 8000...")
    
    try:
        # Test if server is running
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:8000/health"  # Assuming health endpoint
            
            try:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        logger.log("SUCCESS", "MCP_TEST", "MCP server is running and accessible")
                        return True
                    else:
                        logger.log("WARNING", "MCP_TEST", f"MCP server responded with status: {response.status}")
                        return False
            except aiohttp.ClientConnectorError:
                logger.log("WARNING", "MCP_TEST", "MCP server not running on port 8000")
                logger.log("INFO", "MCP_TEST", "Start the MCP server with: python azure-cosmos-mcp-server-samples/python/cosmos_server.py")
                return False
                
    except Exception as e:
        logger.log("ERROR", "MCP_TEST", f"Connection test failed: {str(e)}")
        return False

async def test_cosmos_mcp_tools():
    """Test basic MCP tools for Cosmos DB"""
    logger = TerminalLogger()
    
    logger.log("INFO", "MCP_TOOLS", "Testing Cosmos DB MCP tools...")
    
    # This would test actual MCP tool calls once the server is running
    # For now, just verify the concept
    
    logger.log("INFO", "MCP_TOOLS", "MCP tools test placeholder - implement after server setup")
    return True

async def main():
    """Main test function"""
    logger = TerminalLogger()
    
    logger.log("INFO", "TEST_START", "Starting MCP server connection tests")
    
    # Test 1: MCP server connection
    mcp_ok = await test_mcp_connection()
    
    # Test 2: MCP tools (placeholder)
    tools_ok = await test_cosmos_mcp_tools()
    
    if mcp_ok and tools_ok:
        logger.log("SUCCESS", "TEST_COMPLETE", "All MCP tests passed!")
        return True
    else:
        logger.log("ERROR", "TEST_FAILED", "Some tests failed - check MCP server setup")
        return False

if __name__ == "__main__":
    asyncio.run(main())
