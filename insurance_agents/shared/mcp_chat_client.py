"""
Clean Enhanced MCP Chat Client for Insurance Claims Processing

This client implements proper MCP protocol communication with Azure OpenAI integration.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv

# Load .env from the project root (two levels up from shared/)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
load_dotenv(os.path.join(project_root, '.env'))

class EnhancedMCPChatClient:
    """
    Enhanced MCP Chat Client with Azure OpenAI integration.
    
    This client focuses on:
    1. LLM-powered natural language interpretation 
    2. MCP tool orchestration
    3. Letting the cosmos server handle database logic
    """

    def __init__(self, mcp_server_url: str = None):
        self.mcp_server_url = mcp_server_url or os.getenv('MCP_SERVER_URL', 'http://127.0.0.1:8080/mcp')
        self.session_id = None
        self.available_tools = []
        self.logger = logging.getLogger(__name__)

    async def _initialize_mcp_session(self):
        """Initialize MCP session with proper protocol handshake"""
        try:
            self.logger.info("Initializing MCP session")
            
            async with httpx.AsyncClient(timeout=30) as client:
                # Step 1: Initialize session
                init_response = await client.post(
                    self.mcp_server_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": f"init_{datetime.now().isoformat()}",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {
                                "name": "insurance-claims-orchestrator",
                                "version": "1.0.0"
                            }
                        }
                    },
                    headers={
                        "Accept": "application/json, text/event-stream",
                        "Content-Type": "application/json"
                    }
                )
                
                if init_response.status_code == 200:
                    # Extract session ID from response headers
                    self.session_id = init_response.headers.get('mcp-session-id')
                    if not self.session_id:
                        # Try to extract from response body
                        try:
                            response_data = init_response.json()
                            if 'result' in response_data and 'sessionId' in response_data['result']:
                                self.session_id = response_data['result']['sessionId']
                        except:
                            self.session_id = f"session_{datetime.now().isoformat()}"
                    
                    self.logger.info(f"✅ MCP session initialized with ID: {self.session_id}")
                else:
                    raise Exception(f"Failed to initialize: {init_response.status_code}")
                
                # Step 2: Send initialized notification
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
                    self.logger.warning(f"Initialized notification returned {notification_response.status_code}")
                else:
                    self.logger.info("✅ Initialized notification sent successfully")
                    
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP session: {e}")
            raise

    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> str:
        """Call a tool on the MCP server using proper MCP protocol."""
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
                
                self.logger.info(f"Calling MCP tool '{tool_name}' with args: {arguments}")
                
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
            self.logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return f"Error calling tool: {str(e)}"

    async def query_cosmos_data(self, user_query: str) -> str:
        """Process a natural language query using LLM-powered intent recognition."""
        try:
            self.logger.info(f"Processing insurance query with LLM: {user_query}")
            
            if not self.session_id:
                await self._initialize_mcp_session()
            
            # Use LLM to analyze the query and determine intent
            intent_analysis = await self._analyze_query_with_llm(user_query)
            
            if intent_analysis["action"] == "query_cosmos":
                # LLM generated a SQL query
                sql_query = intent_analysis["sql_query"]
                result = await self._call_mcp_tool("query_cosmos", {"query": sql_query})
                return f"{intent_analysis['response_prefix']}:\n{result}"
                
            elif intent_analysis["action"] == "list_collections":
                result = await self._call_mcp_tool("list_collections")
                return f"Available containers in the database:\n{result}"
                
            elif intent_analysis["action"] == "describe_container":
                args = {}
                if intent_analysis.get("container_name"):
                    args["container_name"] = intent_analysis["container_name"]
                result = await self._call_mcp_tool("describe_container", args)
                return f"Container schema information:\n{result}"
                
            elif intent_analysis["action"] == "count_documents":
                args = {}
                if intent_analysis.get("container_name"):
                    args["container_name"] = intent_analysis["container_name"]
                result = await self._call_mcp_tool("count_documents", args)
                return f"Document count:\n{result}"
                
            elif intent_analysis["action"] == "get_partition_key_info":
                result = await self._call_mcp_tool("get_partition_key_info")
                return f"Partition key information:\n{result}"
                
            elif intent_analysis["action"] == "get_indexing_policy":
                result = await self._call_mcp_tool("get_indexing_policy")
                return f"Indexing policy:\n{result}"
                
            elif intent_analysis["action"] == "find_implied_links":
                result = await self._call_mcp_tool("find_implied_links")
                return f"Relationship analysis:\n{result}"
                
            else:
                # Default: provide general help
                return await self._handle_general_query(user_query)
                
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return f"Sorry, I encountered an error while processing your query: {str(e)}"

    async def _analyze_query_with_llm(self, user_query: str) -> dict:
        """Use Azure OpenAI to analyze the user's query and determine the appropriate action."""
        try:
            # Check Azure OpenAI configuration
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            key = os.getenv('AZURE_OPENAI_KEY') 
            deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
            
            if endpoint and key and deployment:
                self.logger.info("🧠 Using Azure OpenAI for intent analysis")
                return await self._call_azure_openai_for_intent(user_query)
            
            # Fallback to smart analysis
            else:
                self.logger.info("🔧 No LLM API configured, using smart fallback analysis")
                return await self._smart_intent_analysis(user_query)
            
        except Exception as e:
            self.logger.warning(f"LLM analysis failed, using fallback: {e}")
            return await self._smart_intent_analysis(user_query)

    async def _call_azure_openai_for_intent(self, user_query: str) -> dict:
        """Call Azure OpenAI for intelligent intent analysis."""
        system_prompt = """You are an expert at understanding database queries for insurance claims data.

Given a user's natural language query, analyze it and return a JSON response with:
- "action": the MCP tool to call (query_cosmos, list_collections, describe_container, count_documents, get_partition_key_info, get_indexing_policy, find_implied_links)
- "sql_query": if action is query_cosmos, provide the SQL query
- "container_name": if relevant, specify container name  
- "response_prefix": how to introduce the response to the user

The database schema includes:
- Container: claim_details
- Key fields: id, claimId, patientName, status, category, billAmount, diagnosis, etc.
- Use Cosmos DB SQL syntax (SELECT * FROM c WHERE..., TOP instead of LIMIT)

Examples:
- "What is the id of patient named John Smith?" -> {"action": "query_cosmos", "sql_query": "SELECT * FROM c WHERE c.patientName = 'John Smith'", "response_prefix": "Patient data for 'John Smith'"}
- "Show me recent high-value claims" -> {"action": "query_cosmos", "sql_query": "SELECT TOP 10 * FROM c WHERE c.billAmount > 1000 ORDER BY c._ts DESC", "response_prefix": "High-value recent claims"}
- "How many pending claims?" -> {"action": "count_documents", "response_prefix": "Pending claims count"}
- "Show me all containers" -> {"action": "list_collections"}

Note: Use "count_documents" action instead of COUNT() queries in SQL, as this Cosmos DB setup doesn't support aggregates.

Return ONLY valid JSON, no other text."""

        async with httpx.AsyncClient(timeout=30) as client:
            headers = {
                "Content-Type": "application/json",
                "api-key": os.getenv('AZURE_OPENAI_KEY')
            }
            
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                "temperature": 0.1,
                "max_tokens": 500
            }
            
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
            url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=2024-02-15-preview"
            
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result["choices"][0]["message"]["content"]
                
                # Parse JSON response
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    # Extract JSON from response if LLM added extra text
                    import re
                    json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    else:
                        raise ValueError("Could not parse LLM response")
            else:
                raise Exception(f"Azure OpenAI API error: {response.status_code}")

    async def _smart_intent_analysis(self, user_query: str) -> dict:
        """Smart intent analysis used as fallback when LLM is not available."""
        import re
        query_lower = user_query.lower()
        
        # Patient name extraction with better regex
        patient_patterns = [
            r'patient\s+(?:named|called)\s+([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)',
            r'named\s+([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)',
            r'(?:patient|for|about|of)\s+([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)',
        ]
        
        # Check for patient queries
        for pattern in patient_patterns:
            match = re.search(pattern, user_query)
            if match:
                patient_name = match.group(1).strip()
                if len(patient_name.split()) <= 3 and patient_name.lower() not in ['patient', 'named', 'called', 'what', 'is', 'the', 'id']:
                    return {
                        "action": "query_cosmos",
                        "sql_query": f"SELECT * FROM c WHERE c.patientName = '{patient_name}'",
                        "response_prefix": f"Patient data for '{patient_name}'"
                    }
        
        # Schema exploration
        if any(word in query_lower for word in ['list', 'show']) and any(word in query_lower for word in ['containers', 'collections']):
            return {"action": "list_collections"}
            
        if any(word in query_lower for word in ['describe', 'schema', 'structure', 'fields']):
            return {"action": "describe_container"}
            
        # Count queries  
        if any(word in query_lower for word in ['count', 'how many', 'number of']):
            return {"action": "count_documents", "response_prefix": "Document count"}
            
        # Sample data
        if any(word in query_lower for word in ['sample', 'example', 'preview']):
            limit = 5
            numbers = re.findall(r'\d+', user_query)
            if numbers:
                limit = min(int(numbers[0]), 10)
            return {
                "action": "query_cosmos", 
                "sql_query": f"SELECT TOP {limit} * FROM c ORDER BY c._ts DESC",
                "response_prefix": "Sample documents"
            }
            
        # Claims queries
        if any(word in query_lower for word in ['claim', 'claims']):
            if 'recent' in query_lower or 'latest' in query_lower:
                sql = "SELECT TOP 10 * FROM c ORDER BY c._ts DESC"
            elif 'pending' in query_lower:
                sql = "SELECT * FROM c WHERE c.status = 'pending'"
            elif 'approved' in query_lower:
                sql = "SELECT * FROM c WHERE c.status = 'approved'"
            else:
                sql = "SELECT TOP 10 * FROM c ORDER BY c._ts DESC"
            
            return {
                "action": "query_cosmos",
                "sql_query": sql,
                "response_prefix": "Claims data"
            }
        
        # Direct SQL
        if 'select' in query_lower and 'from' in query_lower:
            return {
                "action": "query_cosmos",
                "sql_query": user_query,
                "response_prefix": "Query results"
            }
            
        # Technical queries
        if any(word in query_lower for word in ['partition', 'key']):
            return {"action": "get_partition_key_info"}
        if any(word in query_lower for word in ['index', 'policy']):
            return {"action": "get_indexing_policy"}
        if any(word in query_lower for word in ['relationship', 'links']):
            return {"action": "find_implied_links"}
            
        # Default: provide help
        return {"action": "help"}

    async def _handle_general_query(self, user_query: str) -> str:
        """Handle general queries by providing helpful information."""
        return f"""I can help you explore and query the insurance database using these capabilities:

🔍 **Query Operations:**
- Run SQL-like queries: "SELECT * FROM c WHERE c.type = 'claim'"
- Find patient data: "Show me patient John Smith" 
- Search claims: "Show me recent claims"

📋 **Data Exploration:**
- List containers: "Show me all containers"
- Describe schema: "Describe the claims container"
- Get samples: "Show me sample documents"
- Count documents: "How many documents are there?"

🏥 **Insurance Specific:**
- Patient queries: "What is the id of patient named John Smith?"
- Claims analysis: "Show me pending claims"
- Policy information: "List all policies"

🔧 **Technical Info:**
- Partition keys: "Show partition key info"
- Indexing policies: "Show indexing policy" 
- Relationships: "Find relationships in the data"

Your query: "{user_query}"

What would you like to explore? You can ask for any of the above operations or run direct SQL queries."""

# Singleton instance - this is the key pattern from the original system
enhanced_mcp_chat_client = EnhancedMCPChatClient()

# Backward compatibility alias
mcp_chat_client = enhanced_mcp_chat_client
