"""
MCP Client for Insurance Agents
Provides MCP tool integration for accessing Cosmos DB through the MCP server
"""

import asyncio
import json
import httpx
import logging
from typing import Dict, Any, List, Optional

class MCPClient:
    """
    Client for communicating with MCP servers
    Handles tool execution and data retrieval from Cosmos DB
    """
    
    def __init__(self, mcp_server_url: str = "http://localhost:8080"):
        self.mcp_server_url = mcp_server_url
        self.logger = logging.getLogger(f"MCPClient")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.session_id = None
    
    async def _initialize_session(self):
        """Initialize MCP session if not already done"""
        if self.session_id is None:
            try:
                # Create a new session with the MCP server
                init_payload = {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {}
                    },
                    "id": "init"
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                response = await self.client.post(
                    f"{self.mcp_server_url}/mcp",
                    json=init_payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Extract session ID from response headers if available
                    self.session_id = response.headers.get('X-Session-ID', 'default-session')
                    self.logger.info(f"✅ MCP session initialized: {self.session_id}")
                else:
                    self.logger.warning(f"⚠️ Session init failed, using default session")
                    self.session_id = 'default-session'
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Session init error, using default: {str(e)}")
                self.session_id = 'default-session'
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute an MCP tool on the server
        
        Args:
            tool_name: Name of the MCP tool to execute
            parameters: Parameters to pass to the tool
            
        Returns:
            Tool execution result
        """
        try:
            # Initialize session if needed
            await self._initialize_session()
            
            if parameters is None:
                parameters = {}
                
            self.logger.info(f"🔧 Executing MCP tool: {tool_name}")
            
            # Prepare the request payload for FastMCP with proper JSON-RPC format
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": parameters
                },
                "id": 1
            }
            
            # Make request to MCP server with session ID
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "X-Session-ID": self.session_id
            }
            
            response = await self.client.post(
                f"{self.mcp_server_url}/mcp",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"✅ MCP tool {tool_name} executed successfully")
                return result
            else:
                error_msg = f"MCP tool execution failed: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Error executing MCP tool {tool_name}: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    async def query_cosmos(self, query: str) -> Dict[str, Any]:
        """
        Execute a Cosmos DB query using the MCP server
        
        Args:
            query: SQL-like query string
            
        Returns:
            Query results
        """
        return await self.execute_tool("query_cosmos", {"query": query})
    
    async def list_collections(self) -> Dict[str, Any]:
        """
        List all available Cosmos DB collections
        
        Returns:
            List of collection names
        """
        return await self.execute_tool("list_collections")
    
    async def describe_container(self, container_name: str = None) -> Dict[str, Any]:
        """
        Describe the schema of a Cosmos DB container
        
        Args:
            container_name: Name of the container to describe
            
        Returns:
            Container schema description
        """
        params = {}
        if container_name:
            params["container_name"] = container_name
        return await self.execute_tool("describe_container", params)
    
    async def count_documents(self, container_name: str = None) -> Dict[str, Any]:
        """
        Count documents in a Cosmos DB container
        
        Args:
            container_name: Name of the container
            
        Returns:
            Document count
        """
        params = {}
        if container_name:
            params["container_name"] = container_name
        return await self.execute_tool("count_documents", params)
    
    async def sample_documents(self, container_name: str = None, limit: int = 5) -> Dict[str, Any]:
        """
        Get sample documents from a Cosmos DB container
        
        Args:
            container_name: Name of the container
            limit: Number of sample documents to retrieve
            
        Returns:
            Sample documents
        """
        params = {"limit": limit}
        if container_name:
            params["container_name"] = container_name
        return await self.execute_tool("sample_documents", params)
    
    async def get_claims(self, claim_id: str = None) -> Dict[str, Any]:
        """
        Get claims data from Cosmos DB
        
        Args:
            claim_id: Specific claim ID to retrieve (optional)
            
        Returns:
            Claims data
        """
        if claim_id:
            query = f"SELECT * FROM c WHERE c.claimId = '{claim_id}'"
        else:
            query = "SELECT * FROM c"
        
        return await self.query_cosmos(query)
    
    async def get_claim_artifacts(self, claim_id: str) -> Dict[str, Any]:
        """
        Get artifacts associated with a claim
        
        Args:
            claim_id: The claim ID to get artifacts for
            
        Returns:
            Claim artifacts data
        """
        query = f"SELECT * FROM c WHERE c.claimId = '{claim_id}'"
        return await self.query_cosmos(query)
    
    async def get_coverage_rules(self, rule_type: str = None) -> Dict[str, Any]:
        """
        Get coverage rules from Cosmos DB
        
        Args:
            rule_type: Type of coverage rules to retrieve
            
        Returns:
            Coverage rules data
        """
        if rule_type:
            query = f"SELECT * FROM c WHERE c.ruleType = '{rule_type}'"
        else:
            query = "SELECT * FROM c"
        
        return await self.query_cosmos(query)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
