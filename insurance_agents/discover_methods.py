"""
Quick JSON-RPC Method Discovery
Find what methods the running agents actually support
"""

import asyncio
import httpx
import json

async def discover_methods():
    """Discover available methods on running agents"""
    print("🔍 Discovering A2A Agent Methods")
    print("=" * 40)
    
    agents = {
        "claims_orchestrator": 8001,
        "intake_clarifier": 8002,
        "document_intelligence": 8003,
        "coverage_rules_engine": 8004
    }
    
    # Common A2A and JSON-RPC method names
    methods_to_try = [
        "execute",
        "process",
        "handle", 
        "call",
        "invoke",
        "submit",
        "run",
        "task",
        "system.listMethods",
        "rpc.discover",
        "__methods__",
        "help",
        "info",
        "status",
        "ping",
        "hello"
    ]
    
    async with httpx.AsyncClient(timeout=5) as client:
        for agent_name, port in agents.items():
            print(f"\n🤖 Testing {agent_name} (port {port})...")
            
            working_methods = []
            
            for method in methods_to_try:
                try:
                    request_data = {
                        "jsonrpc": "2.0",
                        "method": method,
                        "params": {},
                        "id": f"discovery_{method}"
                    }
                    
                    response = await client.post(
                        f"http://localhost:{port}/",
                        json=request_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Check if method exists (not "method not found")
                        if "error" in result:
                            error_code = result["error"].get("code")
                            if error_code == -32601:  # Method not found
                                continue
                            else:
                                print(f"   🔧 {method}: Other error ({error_code})")
                                working_methods.append(f"{method} (error {error_code})")
                        else:
                            print(f"   ✅ {method}: SUCCESS!")
                            working_methods.append(method)
                    
                except Exception as e:
                    continue
            
            if working_methods:
                print(f"   📋 Found methods: {working_methods}")
            else:
                print(f"   ❌ No working methods found")
    
    print("\n🎯 Method Discovery Complete!")

if __name__ == "__main__":
    asyncio.run(discover_methods())
