"""
A2A Method Resolution Test
Find the correct method names for the A2A protocol
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_a2a_methods():
    """Test A2A protocol methods systematically"""
    print("🔍 A2A METHOD RESOLUTION TEST")
    print("=" * 50)
    
    # Standard A2A protocol methods based on the framework
    a2a_methods = [
        # Core A2A methods
        "agent.execute",
        "agent.invoke", 
        "agent.call",
        "agent.request",
        "agent.process",
        
        # Task-based methods
        "task.create",
        "task.execute", 
        "task.submit",
        "task.process",
        
        # Request methods
        "request.handle",
        "request.process",
        "request.execute",
        
        # Direct executor methods
        "execute",
        "invoke",
        "handle",
        "process",
        "submit",
        
        # A2A protocol specific
        "a2a.execute",
        "a2a.request",
        "a2a.invoke"
    ]
    
    async with httpx.AsyncClient(timeout=10) as client:
        
        # Test Claims Orchestrator first
        print("🤖 Testing Claims Orchestrator (port 8001)...")
        
        for method in a2a_methods:
            try:
                # Simple test payload
                request_data = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": {
                        "message": "test",
                        "context": {}
                    },
                    "id": f"test_{method.replace('.', '_')}"
                }
                
                response = await client.post(
                    "http://localhost:8001/",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "error" in result:
                        error_code = result["error"].get("code")
                        if error_code == -32601:
                            continue  # Method not found
                        elif error_code == -32602:
                            print(f"   ⚠️ {method}: Invalid params (method exists!)")
                            break  # Found working method!
                        elif error_code == -32600:
                            print(f"   🔧 {method}: Request validation error (method exists!)")
                            break  # Found working method!
                        else:
                            print(f"   🔧 {method}: Error {error_code} (method exists!)")
                            break
                    else:
                        print(f"   ✅ {method}: SUCCESS!")
                        break
                        
            except Exception as e:
                continue
        
        # Test with message-based approach (A2A typically uses messages)
        print("\n📨 Testing Message-Based A2A Protocol...")
        
        message_methods = [
            "message",
            "send_message", 
            "handle_message",
            "process_message",
            "agent_message"
        ]
        
        for method in message_methods:
            try:
                # A2A Message format
                request_data = {
                    "jsonrpc": "2.0", 
                    "method": method,
                    "params": {
                        "message": {
                            "content": "Process claim OP-1001",
                            "type": "task",
                            "metadata": {
                                "source": "test_client",
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                    },
                    "id": f"msg_test_{method}"
                }
                
                response = await client.post(
                    "http://localhost:8001/",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "error" not in result or result["error"]["code"] != -32601:
                        print(f"   ✅ {method}: Working! {result}")
                        break
                        
            except Exception:
                continue
        
        # Test with RequestContext format
        print("\n🎯 Testing RequestContext A2A Format...")
        
        try:
            # Format based on the TimeAgent example
            request_data = {
                "jsonrpc": "2.0",
                "method": "execute",
                "params": {
                    "context": {
                        "message": {
                            "content": "Process claim OP-1001",
                            "sessionId": "test_session",
                            "type": "user_message"
                        },
                        "user_input": "Process claim OP-1001"
                    },
                    "event_queue": {}
                },
                "id": "context_test"
            }
            
            response = await client.post(
                "http://localhost:8001/",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   📋 RequestContext result: {result}")
                
        except Exception as e:
            print(f"   ❌ RequestContext error: {str(e)}")
    
    print("\n🏁 Method Resolution Test Complete!")
    print("If no methods worked, the A2A framework might use a different routing approach.")

if __name__ == "__main__":
    asyncio.run(test_a2a_methods())
