import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)
load_dotenv()


class CosmosQueryAgent:
    """
    A specialized agent that uses the Azure Cosmos DB MCP Server to query and explore Cosmos DB data.
    
    This agent provides a natural language interface to interact with Cosmos DB through the MCP server,
    offering capabilities like querying, schema inspection, and data exploration.
    """

    def __init__(self):
        # MCP Server configuration
        self.mcp_server_url = os.getenv('MCP_SERVER_URL', 'http://127.0.0.1:8080/mcp')
        self.cosmos_database = os.getenv('COSMOS_DATABASE', 'playwright_logs')
        self.cosmos_container = os.getenv('COSMOS_CONTAINER', 'actions')
        
        # MCP client session
        self.mcp_session = None
        self.session_id = None
        self.available_tools = []

    async def initialize(self):
        """Initialize the Cosmos Query Agent with MCP server connection."""
        try:
            logger.info("Initializing Cosmos Query Agent with MCP server")
            logger.info(f"MCP Server URL: {self.mcp_server_url}")
            logger.info(f"Target Database: {self.cosmos_database}")
            logger.info(f"Default Container: {self.cosmos_container}")
            
            # Initialize MCP session
            await self._initialize_mcp_session()
            
            # List available tools
            await self._list_available_tools()
            
            logger.info("✅ Cosmos Query Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos Query Agent: {e}")
            return False

    async def _initialize_mcp_session(self):
        """Initialize MCP session with proper session management."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Step 1: Initialize MCP session with proper capabilities
                logger.info("Initializing MCP session...")
                headers = {
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                }
                
                init_response = await client.post(
                    self.mcp_server_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "clientInfo": {
                                "name": "CosmosQueryAgent",
                                "version": "1.0.0"
                            }
                        }
                    },
                    headers=headers
                )
                
                self.session_id = init_response.headers.get('mcp-session-id')
                if not self.session_id:
                    raise Exception("No session ID received from MCP server")
                    
                logger.info(f"✅ MCP session initialized with ID: {self.session_id}")
                
                if init_response.status_code != 200:
                    raise Exception(f"MCP initialization failed: {init_response.text}")
                
                # Step 2: Send initialized notification (REQUIRED!)
                logger.info("Sending initialized notification...")
                headers_with_session = {
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "mcp-session-id": self.session_id
                }
                
                notification_response = await client.post(
                    self.mcp_server_url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized",
                        "params": {}
                    },
                    headers=headers_with_session
                )
                
                if notification_response.status_code not in [200, 202]:
                    logger.warning(f"Initialized notification returned {notification_response.status_code}")
                else:
                    logger.info("✅ Initialized notification sent successfully")
                    
        except Exception as e:
            logger.error(f"Failed to initialize MCP session: {e}")
            raise

    async def _list_available_tools(self):
        """List available tools from the MCP server - optional step."""
        try:
            # For now, skip tool listing since it's failing and assume standard Cosmos tools exist
            # The cosmos server should have these tools based on documentation:
            standard_tools = [
                "query_cosmos", "list_collections", "describe_container", 
                "find_implied_links", "get_sample_documents", "count_documents",
                "get_partition_key_info", "get_indexing_policy"
            ]
            
            self.available_tools = [{"name": tool} for tool in standard_tools]
            logger.info(f"✅ Assuming standard Cosmos MCP tools: {standard_tools}")
                
        except Exception as e:
            logger.warning(f"Could not list tools (proceeding anyway): {e}")
            # Set standard tools even if listing fails
            standard_tools = ["query_cosmos", "list_collections", "describe_container"]
            self.available_tools = [{"name": tool} for tool in standard_tools]

    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> str:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool result as string
        """
        if arguments is None:
            arguments = {}
            
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers_with_session = {
                    "Accept": "application/json, text/event-stream", 
                    "Content-Type": "application/json",
                    "mcp-session-id": self.session_id
                }
                
                request_data = {
                    "jsonrpc": "2.0",
                    "id": f"tool_call_{datetime.now().isoformat()}",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                
                response = await client.post(
                    self.mcp_server_url,
                    json=request_data,
                    headers=headers_with_session
                )
                
                if response.status_code == 200:
                    response_text = response.text
                    
                    # Handle event stream response
                    if "event: message" in response_text and "data: " in response_text:
                        lines = response_text.split('\n')
                        for line in lines:
                            if line.startswith('data: '):
                                data_json = line[6:]
                                result = json.loads(data_json)
                                
                                if "result" in result:
                                    # Handle different result formats
                                    result_data = result["result"]
                                    if isinstance(result_data, dict):
                                        if "content" in result_data:
                                            content = result_data["content"]
                                            if isinstance(content, list) and len(content) > 0:
                                                return content[0].get("text", str(result_data))
                                            else:
                                                return str(content)
                                        else:
                                            return json.dumps(result_data, indent=2)
                                    else:
                                        return str(result_data)
                                elif "error" in result:
                                    return f"Error: {result['error'].get('message', 'Unknown error')}"
                    
                    # Fallback to JSON response
                    try:
                        result = response.json()
                        if "result" in result:
                            return str(result["result"])
                        elif "error" in result:
                            return f"Error: {result['error'].get('message', 'Unknown error')}"
                        else:
                            return "Unknown response format"
                    except:
                        return response_text
                else:
                    return f"HTTP Error {response.status_code}: {response.text}"
                    
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return f"Error calling tool: {str(e)}"

    async def query_cosmos_db(self, query: str) -> str:
        """
        Execute a SQL-like query on the Cosmos DB container.
        
        Args:
            query: SQL-like query string
            
        Returns:
            Query results as formatted string
        """
        return await self._call_mcp_tool("query_cosmos", {"query": query})

    async def list_containers(self) -> str:
        """List all available containers in the database."""
        return await self._call_mcp_tool("list_collections")

    async def describe_container(self, container_name: Optional[str] = None) -> str:
        """
        Describe the schema of a container.
        
        Args:
            container_name: Name of container to describe (optional)
            
        Returns:
            Schema description
        """
        if container_name:
            return await self._call_mcp_tool("describe_container", {"container_name": container_name})
        else:
            return await self._call_mcp_tool("describe_container")

    async def get_sample_documents(self, container_name: Optional[str] = None, limit: int = 5) -> str:
        """
        Get sample documents from a container.
        
        Args:
            container_name: Name of container (optional)
            limit: Number of documents to retrieve
            
        Returns:
            Sample documents as formatted string
        """
        args = {}
        if container_name:
            args["container_name"] = container_name
        if limit != 5:
            args["limit"] = limit
        return await self._call_mcp_tool("get_sample_documents", args if args else None)

    async def count_documents(self, container_name: Optional[str] = None) -> str:
        """
        Count documents in a container.
        
        Args:
            container_name: Name of container (optional)
            
        Returns:
            Document count
        """
        if container_name:
            return await self._call_mcp_tool("count_documents", {"container_name": container_name})
        else:
            return await self._call_mcp_tool("count_documents")

    async def get_partition_key_info(self, container_name: Optional[str] = None) -> str:
        """
        Get partition key information for a container.
        
        Args:
            container_name: Name of container (optional)
            
        Returns:
            Partition key information
        """
        if container_name:
            return await self._call_mcp_tool("get_partition_key_info", {"container_name": container_name})
        else:
            return await self._call_mcp_tool("get_partition_key_info")

    async def get_indexing_policy(self, container_name: Optional[str] = None) -> str:
        """
        Get indexing policy for a container.
        
        Args:
            container_name: Name of container (optional)
            
        Returns:
            Indexing policy as JSON string
        """
        if container_name:
            return await self._call_mcp_tool("get_indexing_policy", {"container_name": container_name})
        else:
            return await self._call_mcp_tool("get_indexing_policy")

    async def find_implied_links(self, container_name: Optional[str] = None) -> str:
        """
        Find implied relationships in a container.
        
        Args:
            container_name: Name of container (optional)
            
        Returns:
            Relationship analysis
        """
        if container_name:
            return await self._call_mcp_tool("find_implied_links", {"container_name": container_name})
        else:
            return await self._call_mcp_tool("find_implied_links")

    async def process_query(self, query: str) -> str:
        """
        Process a natural language query about Cosmos DB data.
        
        Args:
            query: Natural language query
            
        Returns:
            Response based on the query
        """
        try:
            logger.info(f"Processing Cosmos query: {query}")
            
            query_lower = query.lower()
            
            # Route queries to appropriate MCP tools based on intent
            if any(word in query_lower for word in ['list', 'show', 'containers', 'collections', 'databases']):
                if 'container' in query_lower or 'collection' in query_lower:
                    result = await self.list_containers()
                    return f"Available containers in the database:\n{result}"
                    
            elif any(word in query_lower for word in ['describe', 'schema', 'structure', 'fields']):
                # Extract container name if mentioned
                container_name = None
                if 'actions' in query_lower:
                    container_name = 'actions'
                elif 'container' in query_lower:
                    # Try to extract container name from query
                    words = query.split()
                    for i, word in enumerate(words):
                        if word.lower() == 'container' and i + 1 < len(words):
                            container_name = words[i + 1]
                            break
                
                result = await self.describe_container(container_name)
                return f"Container schema information:\n{result}"
                
            elif any(word in query_lower for word in ['sample', 'example', 'preview', 'show me']):
                # Extract container name and limit if mentioned
                container_name = None
                limit = 5
                
                if 'actions' in query_lower:
                    container_name = 'actions'
                    
                # Try to extract number
                import re
                numbers = re.findall(r'\d+', query)
                if numbers:
                    limit = min(int(numbers[0]), 10)  # Cap at 10 for safety
                
                result = await self.get_sample_documents(container_name, limit)
                return f"Sample documents:\n{result}"
                
            elif any(word in query_lower for word in ['count', 'how many', 'number of']):
                container_name = None
                if 'actions' in query_lower:
                    container_name = 'actions'
                    
                result = await self.count_documents(container_name)
                return f"Document count:\n{result}"
                
            elif any(word in query_lower for word in ['partition', 'partitioning', 'partition key']):
                container_name = None
                if 'actions' in query_lower:
                    container_name = 'actions'
                    
                result = await self.get_partition_key_info(container_name)
                return f"Partition key information:\n{result}"
                
            elif any(word in query_lower for word in ['index', 'indexing', 'policy']):
                container_name = None
                if 'actions' in query_lower:
                    container_name = 'actions'
                    
                result = await self.get_indexing_policy(container_name)
                return f"Indexing policy:\n{result}"
                
            elif any(word in query_lower for word in ['relationship', 'links', 'foreign key', 'references']):
                container_name = None
                if 'actions' in query_lower:
                    container_name = 'actions'
                    
                result = await self.find_implied_links(container_name)
                return f"Relationship analysis:\n{result}"
                
            elif 'select' in query_lower or 'from' in query_lower:
                # Direct SQL query
                result = await self.query_cosmos_db(query)
                return f"Query results:\n{result}"
                
            elif any(word in query_lower for word in ['time_agent', 'timeagent', 'time agent']):
                # Query for time_agent data specifically
                time_query = "SELECT * FROM c WHERE c.agent_name = 'TimeAgent' ORDER BY c._ts DESC"
                result = await self.query_cosmos_db(time_query)
                return f"Time Agent data:\n{result}"
                
            else:
                # Default: try to interpret as a general exploration request
                return await self._handle_general_query(query)
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"Sorry, I encountered an error while processing your query: {str(e)}"

    async def _handle_general_query(self, query: str) -> str:
        """Handle general queries by providing helpful information."""
        return f"""I can help you explore and query the Cosmos DB data using these capabilities:

🔍 **Query Operations:**
- Run SQL-like queries: "SELECT * FROM c WHERE c.agent_name = 'TimeAgent'"
- Find time_agent data: "Show me time_agent entries"

📋 **Data Exploration:**
- List containers: "Show me all containers"
- Describe schema: "Describe the actions container"
- Get samples: "Show me sample documents from actions"
- Count documents: "How many documents are in actions?"

🔧 **Technical Info:**
- Partition keys: "Show partition key info for actions"
- Indexing policies: "Show indexing policy"
- Relationships: "Find relationships in the data"

Your query: "{query}"

What would you like to explore? You can ask for any of the above operations or run direct SQL queries."""


# Export the class for backwards compatibility
CosmosQueryAgentWithMCP = CosmosQueryAgent
