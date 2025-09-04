"""
Test script to interact with the Cosmos MCP server and create test data for scenarios
"""
import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, List

class CosmosMCPTester:
    def __init__(self, mcp_url: str = "http://127.0.0.1:8080/mcp"):
        self.mcp_url = mcp_url
        self.session_id = None
        
    async def initialize_session(self):
        """Initialize MCP session"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Create session (simplified approach)
                self.session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                print(f"✅ MCP session initialized: {self.session_id}")
                return True
        except Exception as e:
            print(f"❌ Failed to initialize session: {e}")
            return False
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call MCP tool"""
        if arguments is None:
            arguments = {}
            
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                headers = {
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "mcp-session-id": self.session_id or "default"
                }
                
                request_data = {
                    "jsonrpc": "2.0",
                    "id": f"tool_call_{datetime.now().strftime('%H%M%S')}",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                
                print(f"🔧 Calling tool: {tool_name}")
                response = await client.post(
                    self.mcp_url,
                    json=request_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    response_text = response.text
                    print(f"✅ Tool response received")
                    
                    # Handle event stream response
                    if "data: " in response_text:
                        lines = response_text.split('\n')
                        for line in lines:
                            if line.startswith('data: '):
                                try:
                                    data_json = line[6:]
                                    result = json.loads(data_json)
                                    if "result" in result:
                                        return result["result"]
                                    elif "error" in result:
                                        print(f"❌ Tool error: {result['error']}")
                                        return None
                                except json.JSONDecodeError:
                                    continue
                    
                    # Try direct JSON response
                    try:
                        result = response.json()
                        if "result" in result:
                            return result["result"]
                        elif "error" in result:
                            print(f"❌ Tool error: {result['error']}")
                            return None
                    except:
                        pass
                        
                    return response_text
                else:
                    print(f"❌ HTTP Error {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error calling tool {tool_name}: {e}")
            return None
    
    async def list_tools(self):
        """List available MCP tools"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "mcp-session-id": self.session_id or "default"
                }
                
                request_data = {
                    "jsonrpc": "2.0",
                    "id": "list_tools",
                    "method": "tools/list"
                }
                
                response = await client.post(
                    self.mcp_url,
                    json=request_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", {}).get("tools", [])
                else:
                    print(f"❌ Error listing tools: {response.text}")
                    return []
                    
        except Exception as e:
            print(f"❌ Error listing tools: {e}")
            return []
    
    async def test_connection(self):
        """Test basic connection to MCP server"""
        print("🔍 Testing MCP server connection...")
        
        # Initialize session
        if not await self.initialize_session():
            return False
        
        # List available tools
        tools = await self.list_tools()
        print(f"📚 Available tools: {[tool.get('name', 'unknown') for tool in tools]}")
        
        return len(tools) > 0
    
    async def create_test_scenarios(self):
        """Create test data for the scenarios from your workflow"""
        print("\n🎯 Creating test scenarios...")
        
        # Scenario 1: OP-1001 - Clean outpatient visit (should approve)
        await self.create_outpatient_scenario_1001()
        
        # Scenario 2: OP-1002 - Missing memo/report (should pend)
        await self.create_outpatient_scenario_1002()
        
        # Scenario 3: IP-2001 - Complete inpatient (should approve)
        await self.create_inpatient_scenario_2001()
        
        # Scenario 4: IP-2002 - Missing discharge summary (should pend)
        await self.create_inpatient_scenario_2002()
        
        print("✅ Test scenarios created!")
    
    async def create_outpatient_scenario_1001(self):
        """Create OP-1001: Clean outpatient visit (should approve)"""
        print("📋 Creating OP-1001: Clean outpatient visit")
        
        # Create claim
        claim_data = {
            "id": "OP-1001",
            "claimId": "OP-1001",
            "memberId": "M001",
            "category": "Outpatient",
            "submitDate": "2024-09-01T10:00:00Z",
            "provider": "City Medical Center",
            "dosFrom": "2024-08-30T09:00:00Z",
            "dosTo": "2024-08-30T10:30:00Z",
            "amountBilled": 220.00,
            "region": "North",
            "status": "submitted",
            "expectedOutput": "Complete claim processing"
        }
        
        await self.call_mcp_tool("put_item", {
            "containerName": "claims",
            "item": claim_data
        })
        
        # Create artifacts (bill + memo)
        artifacts = [
            {
                "id": "F-OP-1001-BILL",
                "claimId": "OP-1001",
                "fileId": "F-OP-1001-BILL",
                "type": "bill",
                "uri": "blob://storage/bills/op-1001-bill.pdf",
                "hash": "hash1001bill",
                "pages": 2,
                "uploadedBy": "M001"
            },
            {
                "id": "F-OP-1001-MEMO",
                "claimId": "OP-1001",
                "fileId": "F-OP-1001-MEMO",
                "type": "memo",
                "uri": "blob://storage/memos/op-1001-memo.pdf",
                "hash": "hash1001memo",
                "pages": 1,
                "uploadedBy": "M001"
            }
        ]
        
        for artifact in artifacts:
            await self.call_mcp_tool("put_item", {
                "containerName": "artifacts",
                "item": artifact
            })
    
    async def create_outpatient_scenario_1002(self):
        """Create OP-1002: Missing memo/report (should pend)"""
        print("📋 Creating OP-1002: Missing memo/report")
        
        # Create claim
        claim_data = {
            "id": "OP-1002",
            "claimId": "OP-1002",
            "memberId": "M002",
            "category": "Outpatient",
            "submitDate": "2024-09-01T11:00:00Z",
            "provider": "Downtown Clinic",
            "dosFrom": "2024-08-29T14:00:00Z",
            "dosTo": "2024-08-29T15:00:00Z",
            "amountBilled": 180.00,
            "region": "South",
            "status": "submitted",
            "expectedOutput": "Complete claim processing"
        }
        
        await self.call_mcp_tool("put_item", {
            "containerName": "claims",
            "item": claim_data
        })
        
        # Create artifacts (only bill, missing memo) - this should trigger pend
        artifacts = [
            {
                "id": "F-OP-1002-BILL",
                "claimId": "OP-1002",
                "fileId": "F-OP-1002-BILL",
                "type": "bill",
                "uri": "blob://storage/bills/op-1002-bill.pdf",
                "hash": "hash1002bill",
                "pages": 1,
                "uploadedBy": "M002"
            }
        ]
        
        for artifact in artifacts:
            await self.call_mcp_tool("put_item", {
                "containerName": "artifacts",
                "item": artifact
            })
    
    async def create_inpatient_scenario_2001(self):
        """Create IP-2001: Complete inpatient (should approve)"""
        print("📋 Creating IP-2001: Complete inpatient")
        
        # Create claim
        claim_data = {
            "id": "IP-2001",
            "claimId": "IP-2001",
            "memberId": "M003",
            "category": "Inpatient",
            "submitDate": "2024-09-01T12:00:00Z",
            "provider": "Regional Hospital",
            "dosFrom": "2024-08-25T08:00:00Z",
            "dosTo": "2024-08-27T12:00:00Z",
            "amountBilled": 15000.00,
            "region": "East",
            "status": "submitted",
            "expectedOutput": "Complete claim processing"
        }
        
        await self.call_mcp_tool("put_item", {
            "containerName": "claims",
            "item": claim_data
        })
        
        # Create artifacts (bill + discharge summary)
        artifacts = [
            {
                "id": "F-IP-2001-BILL",
                "claimId": "IP-2001",
                "fileId": "F-IP-2001-BILL",
                "type": "bill",
                "uri": "blob://storage/bills/ip-2001-bill.pdf",
                "hash": "hash2001bill",
                "pages": 5,
                "uploadedBy": "M003"
            },
            {
                "id": "F-IP-2001-DISCHARGE",
                "claimId": "IP-2001",
                "fileId": "F-IP-2001-DISCHARGE",
                "type": "discharge_summary",
                "uri": "blob://storage/discharge/ip-2001-discharge.pdf",
                "hash": "hash2001discharge",
                "pages": 3,
                "uploadedBy": "M003"
            }
        ]
        
        for artifact in artifacts:
            await self.call_mcp_tool("put_item", {
                "containerName": "artifacts",
                "item": artifact
            })
    
    async def create_inpatient_scenario_2002(self):
        """Create IP-2002: Missing discharge summary (should pend)"""
        print("📋 Creating IP-2002: Missing discharge summary")
        
        # Create claim
        claim_data = {
            "id": "IP-2002",
            "claimId": "IP-2002",
            "memberId": "M004",
            "category": "Inpatient",
            "submitDate": "2024-09-01T13:00:00Z",
            "provider": "Metro Hospital",
            "dosFrom": "2024-08-28T10:00:00Z",
            "dosTo": "2024-08-30T16:00:00Z",
            "amountBilled": 12000.00,
            "region": "West",
            "status": "submitted",
            "expectedOutput": "Complete claim processing"
        }
        
        await self.call_mcp_tool("put_item", {
            "containerName": "claims",
            "item": claim_data
        })
        
        # Create artifacts (only bill, missing discharge summary)
        artifacts = [
            {
                "id": "F-IP-2002-BILL",
                "claimId": "IP-2002",
                "fileId": "F-IP-2002-BILL",
                "type": "bill",
                "uri": "blob://storage/bills/ip-2002-bill.pdf",
                "hash": "hash2002bill",
                "pages": 4,
                "uploadedBy": "M004"
            }
        ]
        
        for artifact in artifacts:
            await self.call_mcp_tool("put_item", {
                "containerName": "artifacts",
                "item": artifact
            })
    
    async def query_test_data(self):
        """Query the created test data to verify"""
        print("\n🔍 Querying test data...")
        
        # Query claims
        claims_result = await self.call_mcp_tool("query_cosmos", {
            "query": "SELECT * FROM c WHERE c.claimId LIKE 'OP-%' OR c.claimId LIKE 'IP-%'",
            "container": "claims"
        })
        
        if claims_result:
            print(f"📊 Created {len(claims_result) if isinstance(claims_result, list) else 1} test claims")
        
        # Query artifacts
        artifacts_result = await self.call_mcp_tool("query_cosmos", {
            "query": "SELECT * FROM c WHERE c.claimId LIKE 'OP-%' OR c.claimId LIKE 'IP-%'",
            "container": "artifacts"
        })
        
        if artifacts_result:
            print(f"📎 Created {len(artifacts_result) if isinstance(artifacts_result, list) else 1} test artifacts")
        
        return claims_result, artifacts_result

async def main():
    """Main test function"""
    print("🚀 Starting Cosmos MCP Test Setup...")
    
    tester = CosmosMCPTester()
    
    # Test connection
    if not await tester.test_connection():
        print("❌ Failed to connect to MCP server")
        return
    
    # Create test scenarios
    await tester.create_test_scenarios()
    
    # Verify data
    await tester.query_test_data()
    
    print("\n✅ Test setup complete! You can now run your agents to test these scenarios:")
    print("   - OP-1001: Should approve (complete outpatient)")
    print("   - OP-1002: Should pend (missing memo)")
    print("   - IP-2001: Should approve (complete inpatient)")
    print("   - IP-2002: Should pend (missing discharge)")

if __name__ == "__main__":
    asyncio.run(main())
