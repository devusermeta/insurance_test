"""
MCP Cosmos DB Client
Provides standardized MCP tools for Cosmos DB operations as described in the workflow
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class MCPCosmosClient:
    """
    Client for interacting with Cosmos DB through MCP tools via APIM
    Implements the cosmos.read and cosmos.write operations from the workflow
    """
    
    def __init__(self, mcp_server_url: str = "http://localhost:8080/mcp"):
        self.mcp_server_url = mcp_server_url
        self.session_id = None
        
    async def initialize(self) -> bool:
        """Initialize MCP session"""
        try:
            # For now, create a simple session ID
            self.session_id = f"session_{datetime.now().isoformat()}"
            logger.info(f"✅ MCP Cosmos client initialized with session: {self.session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MCP Cosmos client: {e}")
            return False
    
    async def cosmos_read(self, collection: str, key_or_filters: Union[str, Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Read from Cosmos DB collection
        
        Args:
            collection: Collection name (claims, artifacts, extractions, etc.)
            key_or_filters: Either a specific key or filter dictionary
            
        Returns:
            List of documents from the collection
        """
        try:
            if isinstance(key_or_filters, str):
                # Read specific document by ID
                query = f"SELECT * FROM c WHERE c.id = '{key_or_filters}'"
            elif isinstance(key_or_filters, dict):
                # Build query from filters
                conditions = []
                for key, value in key_or_filters.items():
                    if isinstance(value, str):
                        conditions.append(f"c.{key} = '{value}'")
                    else:
                        conditions.append(f"c.{key} = {value}")
                query = f"SELECT * FROM c WHERE {' AND '.join(conditions)}"
            else:
                # Read all documents in collection
                query = "SELECT * FROM c"
            
            result = await self._call_mcp_tool("query_cosmos", {
                "query": query,
                "container": collection
            })
            
            # Parse result
            if isinstance(result, str):
                try:
                    parsed = json.loads(result)
                    return parsed if isinstance(parsed, list) else [parsed]
                except json.JSONDecodeError:
                    return []
            elif isinstance(result, list):
                return result
            else:
                return [result] if result else []
                
        except Exception as e:
            logger.error(f"Error reading from {collection}: {e}")
            return []
    
    async def cosmos_write(self, collection: str, document: Dict[str, Any], upsert: bool = True) -> bool:
        """
        Write to Cosmos DB collection
        
        Args:
            collection: Collection name
            document: Document to write
            upsert: Whether to upsert (default) or insert only
            
        Returns:
            Success boolean
        """
        try:
            # Ensure document has required fields
            if 'id' not in document:
                document['id'] = f"{collection}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Add metadata
            document['_timestamp'] = datetime.now().isoformat()
            document['_collection'] = collection
            
            # Use put_item tool for upsert behavior
            result = await self._call_mcp_tool("put_item", {
                "containerName": collection,
                "item": document
            })
            
            logger.info(f"✅ Written document to {collection}: {document.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing to {collection}: {e}")
            return False
    
    async def cosmos_query(self, collection: str, query: str) -> List[Dict[str, Any]]:
        """
        Execute custom SQL query on collection
        
        Args:
            collection: Collection name
            query: SQL query string
            
        Returns:
            Query results
        """
        try:
            result = await self._call_mcp_tool("query_cosmos", {
                "query": query,
                "container": collection
            })
            
            if isinstance(result, str):
                try:
                    parsed = json.loads(result)
                    return parsed if isinstance(parsed, list) else [parsed]
                except json.JSONDecodeError:
                    return []
            elif isinstance(result, list):
                return result
            else:
                return [result] if result else []
                
        except Exception as e:
            logger.error(f"Error querying {collection}: {e}")
            return []
    
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call MCP tool via HTTP endpoint"""
        if arguments is None:
            arguments = {}
            
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {
                    "Accept": "application/json, text/event-stream", 
                    "Content-Type": "application/json",
                    "mcp-session-id": self.session_id or "default"
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
                    headers=headers
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
                                    result_data = result["result"]
                                    if isinstance(result_data, dict) and "content" in result_data:
                                        content = result_data["content"]
                                        if isinstance(content, list) and len(content) > 0:
                                            return content[0].get("text", str(result_data))
                                        else:
                                            return str(content)
                                    else:
                                        return result_data
                                elif "error" in result:
                                    logger.error(f"MCP tool error: {result['error']}")
                                    return None
                    
                    # Try direct JSON response
                    try:
                        result = response.json()
                        if "result" in result:
                            return result["result"]
                        elif "error" in result:
                            logger.error(f"MCP tool error: {result['error']}")
                            return None
                    except:
                        return response_text
                else:
                    logger.error(f"HTTP Error {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return None

# Convenience functions for common collections
async def read_claims(cosmos_client: MCPCosmosClient, claim_id: str = None) -> List[Dict[str, Any]]:
    """Read from claims collection"""
    filters = {"claimId": claim_id} if claim_id else None
    return await cosmos_client.cosmos_read("claims", filters)

async def write_claim(cosmos_client: MCPCosmosClient, claim_data: Dict[str, Any]) -> bool:
    """Write to claims collection"""
    return await cosmos_client.cosmos_write("claims", claim_data)

async def read_artifacts(cosmos_client: MCPCosmosClient, claim_id: str = None) -> List[Dict[str, Any]]:
    """Read from artifacts collection"""
    filters = {"claimId": claim_id} if claim_id else None
    return await cosmos_client.cosmos_read("artifacts", filters)

async def write_artifact(cosmos_client: MCPCosmosClient, artifact_data: Dict[str, Any]) -> bool:
    """Write to artifacts collection"""
    return await cosmos_client.cosmos_write("artifacts", artifact_data)

async def read_extractions(cosmos_client: MCPCosmosClient, claim_id: str = None) -> List[Dict[str, Any]]:
    """Read from extractions collection"""
    filters = {"claimId": claim_id} if claim_id else None
    return await cosmos_client.cosmos_read("extractions", filters)

async def write_extraction(cosmos_client: MCPCosmosClient, extraction_data: Dict[str, Any]) -> bool:
    """Write to extractions collection"""
    return await cosmos_client.cosmos_write("extractions", extraction_data)

async def read_rules_eval(cosmos_client: MCPCosmosClient, claim_id: str = None) -> List[Dict[str, Any]]:
    """Read from rules_eval collection"""
    filters = {"claimId": claim_id} if claim_id else None
    return await cosmos_client.cosmos_read("rules_eval", filters)

async def write_rules_eval(cosmos_client: MCPCosmosClient, rules_data: Dict[str, Any]) -> bool:
    """Write to rules_eval collection"""
    return await cosmos_client.cosmos_write("rules_eval", rules_data)

async def read_agent_runs(cosmos_client: MCPCosmosClient, task_id: str = None) -> List[Dict[str, Any]]:
    """Read from agent_runs collection"""
    filters = {"taskId": task_id} if task_id else None
    return await cosmos_client.cosmos_read("agent_runs", filters)

async def write_agent_run(cosmos_client: MCPCosmosClient, agent_run_data: Dict[str, Any]) -> bool:
    """Write to agent_runs collection"""
    return await cosmos_client.cosmos_write("agent_runs", agent_run_data)

async def write_event(cosmos_client: MCPCosmosClient, event_data: Dict[str, Any]) -> bool:
    """Write to events collection"""
    return await cosmos_client.cosmos_write("events", event_data)
