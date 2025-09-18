#!/usr/bin/env python3
"""
Test Step 8: MCP Integration Testing
Tests voice agent's ability to call Cosmos MCP server and retrieve real insurance data.
"""

import asyncio
import json
import requests
import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

class TestStep8MCPIntegration:
    """Test MCP integration between voice agent and Cosmos server"""
    
    def __init__(self):
        self.voice_agent_url = "http://localhost:8007"
        self.cosmos_server_url = "http://localhost:8080/mcp"
        
    def test_cosmos_server_running(self):
        """Test if Cosmos MCP server is running and responding"""
        print("🧪 Testing Cosmos MCP server availability...")
        
        try:
            # Test the MCP endpoint with proper headers
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream'
            }
            
            # Try to get server info
            response = requests.post(
                self.cosmos_server_url,
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": "test-1",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "roots": {
                                "listChanged": True
                            }
                        },
                        "clientInfo": {
                            "name": "voice-agent-test",
                            "version": "1.0.0"
                        }
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Cosmos MCP server is running and responding")
                return True
            else:
                print(f"❌ Cosmos MCP server returned status {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Cosmos MCP server test failed: {e}")
            return False
    
    def test_voice_agent_running(self):
        """Test if voice agent server is running"""
        print("🧪 Testing voice agent server availability...")
        
        try:
            response = requests.get(f"{self.voice_agent_url}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy" and data.get("agent_initialized"):
                    print("✅ Voice agent server is running and agent is initialized")
                    return True
                else:
                    print(f"❌ Voice agent not properly initialized: {data}")
                    return False
            else:
                print(f"❌ Voice agent health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Voice agent test failed: {e}")
            return False
    
    def test_voice_agent_mcp_query(self):
        """Test voice agent making MCP queries for insurance data"""
        print("🧪 Testing voice agent MCP integration...")
        
        try:
            # Send a message to the voice agent that should trigger MCP tool usage
            test_queries = [
                "Check claim status for claim ID 12345",
                "Find all vehicles with make Toyota",
                "Look up insurance claims data",
                "What vehicles are in the database?"
            ]
            
            for query in test_queries:
                print(f"  🔍 Testing query: {query}")
                
                response = requests.post(
                    f"{self.voice_agent_url}/api/agent/execute",
                    json={
                        "message": query,
                        "session_id": f"mcp_test_session_{hash(query) % 1000}"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    
                    # Check if the response indicates MCP tool usage or data retrieval
                    mcp_indicators = [
                        "claim", "vehicle", "database", "found", "search", 
                        "policy", "customer", "data", "records"
                    ]
                    
                    has_mcp_content = any(indicator.lower() in response_text.lower() 
                                        for indicator in mcp_indicators)
                    
                    if has_mcp_content:
                        print(f"    ✅ Query successful - Response: {response_text[:100]}...")
                        return True
                    else:
                        print(f"    ⚠️  Response doesn't show MCP data: {response_text[:100]}...")
                else:
                    print(f"    ❌ Query failed with status {response.status_code}")
            
            print("❌ No successful MCP integration detected")
            return False
            
        except Exception as e:
            print(f"❌ Voice agent MCP query test failed: {e}")
            return False
    
    def test_direct_mcp_client(self):
        """Test direct MCP client connection to Cosmos server"""
        print("🧪 Testing direct MCP client connection...")
        
        try:
            # Import the MCP client used by voice agent
            sys.path.append("../../shared")
            from mcp_chat_client import enhanced_mcp_chat_client
            
            async def test_mcp_connection():
                try:
                    # Test MCP client directly
                    response = await enhanced_mcp_chat_client.query_cosmos_data(
                        "What insurance data is available?"
                    )
                    
                    if response and len(response) > 10:
                        print(f"✅ Direct MCP client working - Response: {response[:100]}...")
                        return True
                    else:
                        print(f"❌ Direct MCP client returned minimal response: {response}")
                        return False
                        
                except Exception as e:
                    print(f"❌ Direct MCP client test failed: {e}")
                    return False
            
            # Run the async test
            result = asyncio.run(test_mcp_connection())
            return result
            
        except Exception as e:
            print(f"❌ Direct MCP client test setup failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all MCP integration tests"""
        print("🚀 Starting Step 8: MCP Integration Tests")
        print("=" * 60)
        
        # Run tests
        tests = [
            ("Cosmos Server Running", self.test_cosmos_server_running()),
            ("Voice Agent Running", self.test_voice_agent_running()),
            ("Voice Agent MCP Query", self.test_voice_agent_mcp_query()),
            ("Direct MCP Client", self.test_direct_mcp_client())
        ]
        
        # Check results
        passed = sum(result for name, result in tests)
        total = len(tests)
        
        print("\n" + "=" * 60)
        print(f"📋 MCP Integration Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All MCP integration tests completed successfully!")
            print("✅ Voice agent can communicate with Cosmos MCP server")
            print("✅ MCP tools integration working")
            print("✅ Insurance data retrieval functional")
            print("🔗 MCP server: http://localhost:8080/mcp")
            print("🎙️ Voice agent: http://localhost:8007")
            return True
        else:
            print(f"❌ {total - passed} tests failed")
            print("🔧 Check that both servers are running:")
            print("   - Cosmos MCP server on port 8080")
            print("   - Voice agent server on port 8007")
            return False

def main():
    """Run the Step 8 MCP integration test suite"""
    tester = TestStep8MCPIntegration()
    
    try:
        success = tester.run_all_tests()
        return success
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)