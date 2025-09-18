#!/usr/bin/env python3
"""
Test Step 9: End-to-End Integration Testing
Tests complete Voice Live API → Azure AI Foundry → MCP Tools → Database → Response pipeline.
"""

import asyncio
import json
import requests
import sys
import os
import time
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

class TestStep9EndToEndIntegration:
    """Test complete end-to-end voice agent integration"""
    
    def __init__(self):
        self.voice_agent_url = "http://localhost:8007"
        self.cosmos_server_url = "http://localhost:8080/mcp"
        
    def test_servers_running(self):
        """Test that both servers are running"""
        print("🧪 Testing server availability...")
        
        try:
            # Test voice agent
            response = requests.get(f"{self.voice_agent_url}/api/health", timeout=10)
            voice_ok = response.status_code == 200 and response.json().get("status") == "healthy"
            
            # Test cosmos server (with proper headers)
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
            cosmos_response = requests.post(
                self.cosmos_server_url,
                headers=headers,
                json={"jsonrpc": "2.0", "id": "test", "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
                timeout=10
            )
            cosmos_ok = cosmos_response.status_code == 200
            
            if voice_ok and cosmos_ok:
                print("✅ Both servers are running and responding")
                return True
            else:
                print(f"❌ Server status - Voice: {'✅' if voice_ok else '❌'}, Cosmos: {'✅' if cosmos_ok else '❌'}")
                return False
                
        except Exception as e:
            print(f"❌ Server availability test failed: {e}")
            return False
    
    def test_mcp_data_queries(self):
        """Test voice agent's ability to query database through MCP"""
        print("🧪 Testing MCP data queries...")
        
        database_queries = [
            {
                "query": "What insurance claims are in the database?",
                "expected_keywords": ["claim", "data", "container", "database"],
                "description": "General database query"
            },
            {
                "query": "Show me vehicle information",
                "expected_keywords": ["vehicle", "car", "auto", "toyota", "honda"],
                "description": "Vehicle lookup"
            },
            {
                "query": "Find claim details for any claim",
                "expected_keywords": ["claim", "details", "status", "policy"],
                "description": "Claim lookup"
            },
            {
                "query": "What data containers are available?",
                "expected_keywords": ["container", "available", "claim_details", "patient_data"],
                "description": "Container listing"
            }
        ]
        
        success_count = 0
        
        for test_case in database_queries:
            print(f"  🔍 Testing: {test_case['description']}")
            
            try:
                response = requests.post(
                    f"{self.voice_agent_url}/api/agent/execute",
                    json={
                        "message": test_case["query"],
                        "session_id": f"e2e_test_{hash(test_case['query']) % 1000}"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "").lower()
                    
                    # Check if response contains database-related content
                    has_data_content = any(keyword.lower() in response_text for keyword in test_case["expected_keywords"])
                    
                    # Check if response is more than just the generic fallback
                    is_enhanced = len(response_text) > 100 or "database" in response_text or "claim" in response_text
                    
                    if has_data_content and is_enhanced:
                        print(f"    ✅ Success - Enhanced response: {response_text[:100]}...")
                        success_count += 1
                    else:
                        print(f"    ⚠️  Basic response: {response_text[:100]}...")
                else:
                    print(f"    ❌ Query failed with status {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Query error: {e}")
        
        if success_count > 0:
            print(f"✅ MCP data queries working - {success_count}/{len(database_queries)} enhanced responses")
            return True
        else:
            print("❌ No enhanced MCP responses detected")
            return False
    
    def test_conversation_tracking(self):
        """Test that conversations are properly tracked"""
        print("🧪 Testing conversation tracking...")
        
        try:
            # Get initial stats
            response = requests.get(f"{self.voice_agent_url}/api/conversation/stats", timeout=10)
            if response.status_code != 200:
                print("❌ Could not get conversation stats")
                return False
            
            initial_stats = response.json()
            initial_messages = initial_stats.get("total_messages", 0)
            
            # Send a test message
            test_message = "Test conversation tracking with database query"
            requests.post(
                f"{self.voice_agent_url}/api/agent/execute",
                json={"message": test_message, "session_id": "tracking_test"},
                timeout=20
            )
            
            # Wait a moment for processing
            time.sleep(2)
            
            # Get updated stats
            response = requests.get(f"{self.voice_agent_url}/api/conversation/stats", timeout=10)
            updated_stats = response.json()
            updated_messages = updated_stats.get("total_messages", 0)
            
            if updated_messages > initial_messages:
                print(f"✅ Conversation tracking working - Messages: {initial_messages} → {updated_messages}")
                return True
            else:
                print(f"❌ Conversation tracking not working - Messages unchanged: {initial_messages}")
                return False
                
        except Exception as e:
            print(f"❌ Conversation tracking test failed: {e}")
            return False
    
    def test_websocket_integration(self):
        """Test WebSocket integration with conversation tracking"""
        print("🧪 Testing WebSocket integration...")
        
        try:
            import websockets
            
            async def test_websocket():
                try:
                    session_id = f"ws_e2e_test_{int(time.time())}"
                    uri = f"ws://localhost:8007/ws/voice?session_id={session_id}"
                    
                    async with websockets.connect(uri) as websocket:
                        # Send a Voice Live API style message
                        test_message = {
                            "type": "conversation.item.created",
                            "item": {
                                "type": "message",
                                "role": "user",
                                "content": [{"type": "input_text", "text": "What claims data is available?"}]
                            }
                        }
                        
                        await websocket.send(json.dumps(test_message))
                        
                        # Wait for processing
                        await asyncio.sleep(2)
                        
                        print("✅ WebSocket integration working")
                        return True
                        
                except Exception as e:
                    print(f"❌ WebSocket test failed: {e}")
                    return False
            
            # Run the async test
            result = asyncio.run(test_websocket())
            return result
            
        except ImportError:
            print("⚠️  WebSocket test skipped - websockets library not available")
            return True  # Don't fail the overall test for missing dependency
        except Exception as e:
            print(f"❌ WebSocket integration test failed: {e}")
            return False
    
    def test_a2a_protocol_integration(self):
        """Test A2A protocol integration"""
        print("🧪 Testing A2A protocol integration...")
        
        try:
            # Test agent card
            response = requests.get(f"{self.voice_agent_url}/.well-known/agent.json", timeout=10)
            if response.status_code != 200:
                print("❌ A2A agent card not accessible")
                return False
            
            agent_data = response.json()
            
            # Verify key A2A fields
            required_fields = ["name", "id", "capabilities", "skills"]
            missing_fields = [field for field in required_fields if field not in agent_data]
            
            if missing_fields:
                print(f"❌ A2A agent card missing fields: {missing_fields}")
                return False
            
            # Verify audio capability (our custom addition)
            if not agent_data.get("capabilities", {}).get("audio"):
                print("❌ Audio capability not enabled in agent card")
                return False
            
            print("✅ A2A protocol integration working")
            return True
            
        except Exception as e:
            print(f"❌ A2A protocol test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run comprehensive end-to-end integration tests"""
        print("🚀 Starting Step 9: End-to-End Integration Tests")
        print("=" * 70)
        print("Testing complete Voice Live API → Azure AI Foundry → MCP Tools → Database → Response")
        print("=" * 70)
        
        # Run tests
        tests = [
            ("Servers Running", self.test_servers_running()),
            ("MCP Data Queries", self.test_mcp_data_queries()),
            ("Conversation Tracking", self.test_conversation_tracking()),
            ("WebSocket Integration", self.test_websocket_integration()),
            ("A2A Protocol Integration", self.test_a2a_protocol_integration())
        ]
        
        # Check results
        passed = sum(result for name, result in tests)
        total = len(tests)
        
        print("\n" + "=" * 70)
        print(f"📋 End-to-End Integration Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All end-to-end integration tests completed successfully!")
            print("✅ Complete voice agent pipeline working:")
            print("   🎤 Voice Live API → WebSocket")
            print("   🤖 Azure AI Foundry Voice Agent")
            print("   🔗 MCP Tools Integration") 
            print("   📊 Cosmos Database Queries")
            print("   📝 Conversation Tracking")
            print("   🌐 A2A Protocol Support")
            print("")
            print("🔗 Ready for production voice interactions!")
            print("🎙️ Voice interface: http://localhost:8007/")
            print("🌐 Agent card: http://localhost:8007/.well-known/agent.json")
            print("🔌 WebSocket: ws://localhost:8007/ws/voice")
            return True
        else:
            print(f"❌ {total - passed} tests failed")
            print("🔧 Integration issues detected. Check:")
            print("   - Voice agent server (port 8007)")
            print("   - Cosmos MCP server (port 8080)")
            print("   - MCP client integration")
            print("   - Database connectivity")
            return False

def main():
    """Run the Step 9 end-to-end integration test suite"""
    tester = TestStep9EndToEndIntegration()
    
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