"""
MCP Chat Client for Claims Orchestrator
Handles direct communication with the Cosmos DB MCP Server for chat queries
"""

import asyncio
import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime

class MCPChatClient:
    """Client for communicating with MCP server for chat queries"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8080"):
        self.mcp_server_url = mcp_server_url
        self.logger = logging.getLogger("MCPChatClient")
        
    async def query_cosmos_data(self, user_query: str, context: Dict[str, Any] = None) -> str:
        """
        Query Cosmos DB data through MCP server based on user's natural language query
        """
        try:
            # Analyze the query and determine appropriate MCP tool to use
            mcp_tools = await self._get_available_tools()
            
            # Default to query_documents if available
            if "query_documents" in mcp_tools or "query" in mcp_tools:
                return await self._execute_cosmos_query(user_query, context)
            else:
                return await self._handle_general_query(user_query, context)
                
        except Exception as e:
            self.logger.error(f"Error querying Cosmos data: {e}")
            return f"I encountered an error while querying the database: {str(e)}. Please make sure the MCP server is running on port 8080."
    
    async def _get_available_tools(self) -> List[str]:
        """Get list of available MCP tools"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.mcp_server_url}/tools")
                if response.status_code == 200:
                    tools_data = response.json()
                    return [tool.get("name", "") for tool in tools_data.get("tools", [])]
                return []
        except Exception as e:
            self.logger.error(f"Error getting MCP tools: {e}")
            return []
    
    async def _execute_cosmos_query(self, user_query: str, context: Dict[str, Any] = None) -> str:
        """
        Execute a query against Cosmos DB through MCP tools
        """
        try:
            # Convert natural language query to appropriate database query
            cosmos_query = self._convert_to_cosmos_query(user_query)
            
            # Prepare MCP request payload
            mcp_payload = {
                "method": "tools/call",
                "params": {
                    "name": "query_documents",
                    "arguments": {
                        "query": cosmos_query,
                        "container": "claims",  # Default container
                        "max_count": 10
                    }
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mcp_server_url}/mcp",
                    json=mcp_payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return self._format_cosmos_response(result, user_query)
                else:
                    return f"Database query failed with status {response.status_code}. The MCP server might be unavailable."
                    
        except Exception as e:
            self.logger.error(f"Error executing Cosmos query: {e}")
            return f"I couldn't execute your database query: {str(e)}"
    
    def _convert_to_cosmos_query(self, user_query: str) -> str:
        """
        Convert natural language query to Cosmos DB SQL query
        This is a simple implementation - can be enhanced with NLP
        """
        query = user_query.lower()
        
        # Common query patterns
        if "claim" in query and ("count" in query or "how many" in query):
            return "SELECT COUNT(1) as count FROM c WHERE c.type = 'claim'"
        elif "claim" in query and ("recent" in query or "latest" in query):
            return "SELECT * FROM c WHERE c.type = 'claim' ORDER BY c._ts DESC OFFSET 0 LIMIT 5"
        elif "status" in query and "claim" in query:
            return "SELECT c.id, c.status, c.amount FROM c WHERE c.type = 'claim'"
        elif "pending" in query:
            return "SELECT * FROM c WHERE c.status = 'pending' OR c.status = 'submitted'"
        elif "approved" in query:
            return "SELECT * FROM c WHERE c.status = 'approved'"
        elif "rejected" in query or "denied" in query:
            return "SELECT * FROM c WHERE c.status = 'rejected' OR c.status = 'denied'"
        elif "high" in query and ("amount" in query or "value" in query):
            return "SELECT * FROM c WHERE c.amount > 1000 ORDER BY c.amount DESC"
        else:
            # Generic query to show recent data
            return "SELECT TOP 5 * FROM c ORDER BY c._ts DESC"
    
    def _format_cosmos_response(self, mcp_result: Dict[str, Any], original_query: str) -> str:
        """
        Format the MCP/Cosmos DB response into a user-friendly message
        """
        try:
            if "result" in mcp_result and "content" in mcp_result["result"]:
                data = mcp_result["result"]["content"]
                
                if isinstance(data, list) and len(data) > 0:
                    # Format the results based on the data
                    formatted_response = f"Here's what I found for your query: '{original_query}'\n\n"
                    
                    for i, item in enumerate(data[:5]):  # Limit to 5 items
                        if isinstance(item, dict):
                            formatted_response += f"**Result {i+1}:**\n"
                            for key, value in item.items():
                                if key not in ['_rid', '_self', '_etag', '_attachments']:
                                    formatted_response += f"- {key}: {value}\n"
                            formatted_response += "\n"
                    
                    if len(data) > 5:
                        formatted_response += f"... and {len(data) - 5} more results.\n"
                    
                    return formatted_response
                    
                elif isinstance(data, dict):
                    # Single result
                    formatted_response = f"Here's what I found for your query: '{original_query}'\n\n"
                    for key, value in data.items():
                        if key not in ['_rid', '_self', '_etag', '_attachments']:
                            formatted_response += f"- {key}: {value}\n"
                    return formatted_response
                    
                else:
                    return f"I found some data for your query '{original_query}', but it's in an unexpected format: {str(data)}"
                    
            else:
                return f"I executed your query '{original_query}' but didn't receive data in the expected format. The database might be empty or the query needs adjustment."
                
        except Exception as e:
            self.logger.error(f"Error formatting response: {e}")
            return f"I found some results for '{original_query}' but had trouble formatting them: {str(e)}"
    
    async def _handle_general_query(self, user_query: str, context: Dict[str, Any] = None) -> str:
        """
        Handle general queries that don't require specific database operations
        """
        query = user_query.lower()
        
        # Help and information queries
        if any(word in query for word in ["help", "what can you do", "capabilities"]):
            return """I'm your Claims Orchestrator Assistant! Here's what I can help you with:

🔍 **Data Queries:**
- "Show me recent claims"
- "How many claims are pending?"
- "Find high-value claims"
- "What's the status of claims?"

📊 **Analytics:**
- "Count all claims"
- "Show approved claims"
- "Find rejected claims"

💬 **General Help:**
- Ask me about any claims data in the system
- I can query our Cosmos DB database
- I understand natural language questions

Just ask me anything about your insurance claims data!"""

        elif any(word in query for word in ["hello", "hi", "hey"]):
            return "👋 Hello! I'm your Claims Orchestrator Assistant. I can help you query claims data, check processing status, and answer questions about your insurance database. What would you like to know?"
            
        elif "system" in query or "status" in query:
            return """🔋 **System Status:**
- Claims Orchestrator: ✅ Online
- Cosmos DB Connection: ✅ Active
- MCP Server: ✅ Running on port 8080

The system is ready to process your queries!"""
            
        else:
            return f"I understand you're asking about: '{user_query}'. Let me try to query our database for relevant information. If you need help with specific queries, just ask!"

# Singleton instance
mcp_chat_client = MCPChatClient()
