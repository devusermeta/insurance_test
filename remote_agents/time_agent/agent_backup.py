import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

import httpx
from dotenv import load_dotenv


logger = logging.getLogger(__name__)

load_dotenv()


class TimeAgentWithCosmosLogging:
    """Time Agent that provides time/date services and logs everything to Cosmos DB via Azure MCP Server."""

    def __init__(self):
        self.mcp_session = None
        self.mcp_url = os.getenv('MCP_SERVER_URL', 'http://127.0.0.1:8080/mcp')
        self.cosmos_database = os.getenv('COSMOS_DATABASE', 'playwright_logs') 
        self.cosmos_container = os.getenv('COSMOS_CONTAINER', 'actions')
        self.session_id = None
        self.client = None

    async def initialize(self):
        """Initialize the MCP connection to Azure MCP Server for Cosmos DB logging."""
        try:
            logger.info("Initializing connection to Azure MCP Server for Cosmos DB logging")
            logger.info(f"Target MCP Server: {self.mcp_url}")
            logger.info(f"Target Cosmos DB: {self.cosmos_database}/{self.cosmos_container}")
            
            # Create HTTP client
            self.client = httpx.AsyncClient(timeout=30)
            
            # Test MCP server connectivity with a simple tools/list call
            headers = {
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }
            
            # Test with tools/list to verify MCP server is working
            test_response = await self.client.post(
                self.mcp_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {}
                },
                headers=headers
            )
            
            if test_response.status_code == 200:
                result = test_response.json()
                if "result" in result and "tools" in result["result"]:
                    tools = result["result"]["tools"]
                    cosmos_tool = next((t for t in tools if "cosmos" in t.get("name", "").lower()), None)
                    if cosmos_tool:
                        logger.info(f"MCP server connected successfully. Found Cosmos DB tool: {cosmos_tool['name']}")
                        self.session_id = "direct-connection"  # Use direct connection approach
                        return True
                    else:
                        logger.warning("MCP server connected but no Cosmos DB tools found")
                        return False
                else:
                    logger.warning(f"MCP server responded but unexpected format: {result}")
                    return False
            else:
                logger.error(f"Failed to connect to MCP server: HTTP {test_response.status_code}")
                logger.error(f"Response: {test_response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize MCP connection: {e}")
            return False

    async def log_to_cosmos(self, event_type: str, data: Dict[str, Any]):
        """Log an event to Cosmos DB via Azure MCP Server."""
        if not self.client or not self.session_id:
            logger.warning("MCP client not initialized, falling back to console logging")
            # Fallback to console logging
            log_entry = {
                "id": f"time_agent_{datetime.now(timezone.utc).isoformat()}_{event_type}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_name": "TimeAgent",
                "event_type": event_type,
                "data": data,
                "partition_key": "time_agent"
            }
            logger.info(f"[COSMOS_LOG] {json.dumps(log_entry, indent=2)}")
            return True
            
        try:
            # Create log entry
            log_entry = {
                "id": f"time_agent_{datetime.now(timezone.utc).isoformat()}_{event_type}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_name": "TimeAgent",
                "event_type": event_type,
                "data": data,
                "partition_key": "time_agent"
            }
            
            # Headers for MCP call - include both application/json and text/event-stream
            headers = {
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }
            
            # Call Azure Cosmos DB MCP server to log the action
            response = await self.client.post(
                "http://localhost:8080/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": int(datetime.now().timestamp()),
                    "method": "tools/call",
                    "params": {
                        "name": "log_action",
                        "arguments": {
                            "agent": "time_agent",
                            "action": event_type,
                            "details": json.dumps(data)
                        }
                    }
                },
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    logger.info(f"✅ Successfully logged to Simple MCP Server: {event_type}")
                    return True
                else:
                    logger.error(f"MCP call succeeded but unexpected response: {result}")
                    # Fallback to console logging
                    logger.info(f"[MCP_LOG_FALLBACK] {json.dumps(log_entry, indent=2)}")
                    return False
            else:
                logger.error(f"Failed to log to Simple MCP Server: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
                # Fallback to console logging
                logger.info(f"[MCP_LOG_FALLBACK] {json.dumps(log_entry, indent=2)}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to log to Simple MCP Server: {e}")
            # Fallback to console logging
            log_entry = {
                "id": f"time_agent_{datetime.now(timezone.utc).isoformat()}_{event_type}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_name": "TimeAgent",
                "event_type": event_type,
                "data": data,
                "partition_key": "time_agent"
            }
            logger.info(f"[MCP_LOG_FALLBACK] {json.dumps(log_entry, indent=2)}")
            return False

    async def get_current_time(self, timezone_name: str = "UTC") -> Dict[str, Any]:
        """Get the current time with optional timezone."""
        try:
            # Log the request
            await self.log_to_cosmos("time_request", {
                "requested_timezone": timezone_name,
                "request_type": "get_current_time"
            })

            # Get current time
            if timezone_name.upper() == "UTC":
                current_time = datetime.now(timezone.utc)
            else:
                # For simplicity, defaulting to UTC. In production, you'd handle various timezones
                current_time = datetime.now(timezone.utc)
                logger.warning(f"Timezone {timezone_name} not implemented, using UTC")

            result = {
                "current_time": current_time.isoformat(),
                "formatted_time": current_time.strftime("%I:%M:%S %p"),
                "timezone": timezone_name,
                "unix_timestamp": int(current_time.timestamp())
            }

            # Log the response
            await self.log_to_cosmos("time_response", {
                "result": result,
                "success": True
            })

            return result

        except Exception as e:
            # Log the error
            await self.log_to_cosmos("time_error", {
                "error": str(e),
                "requested_timezone": timezone_name
            })
            raise

    async def get_current_date(self) -> Dict[str, Any]:
        """Get the current date information."""
        try:
            # Log the request
            await self.log_to_cosmos("date_request", {
                "request_type": "get_current_date"
            })

            # Get current date
            current_date = datetime.now(timezone.utc)

            result = {
                "current_date": current_date.date().isoformat(),
                "formatted_date": current_date.strftime("%A, %B %d, %Y"),
                "day_of_week": current_date.strftime("%A"),
                "month": current_date.strftime("%B"),
                "year": current_date.year,
                "day": current_date.day
            }

            # Log the response
            await self.log_to_cosmos("date_response", {
                "result": result,
                "success": True
            })

            return result

        except Exception as e:
            # Log the error
            await self.log_to_cosmos("date_error", {
                "error": str(e)
            })
            raise

    async def get_datetime_info(self) -> Dict[str, Any]:
        """Get comprehensive date and time information."""
        try:
            # Log the request
            await self.log_to_cosmos("datetime_request", {
                "request_type": "get_datetime_info"
            })

            # Get current datetime
            current_dt = datetime.now(timezone.utc)

            result = {
                "timestamp": current_dt.isoformat(),
                "date": {
                    "iso": current_dt.date().isoformat(),
                    "formatted": current_dt.strftime("%A, %B %d, %Y"),
                    "day_of_week": current_dt.strftime("%A"),
                    "month": current_dt.strftime("%B"),
                    "year": current_dt.year,
                    "day": current_dt.day
                },
                "time": {
                    "formatted_12h": current_dt.strftime("%I:%M:%S %p"),
                    "formatted_24h": current_dt.strftime("%H:%M:%S"),
                    "hour": current_dt.hour,
                    "minute": current_dt.minute,
                    "second": current_dt.second
                },
                "timezone": "UTC",
                "unix_timestamp": int(current_dt.timestamp())
            }

            # Log the response
            await self.log_to_cosmos("datetime_response", {
                "result": result,
                "success": True
            })

            return result

        except Exception as e:
            # Log the error
            await self.log_to_cosmos("datetime_error", {
                "error": str(e)
            })
            raise

    async def process_query(self, query: str) -> str:
        """Process a natural language query about time/date."""
        try:
            # Log the incoming query
            await self.log_to_cosmos("query_received", {
                "query": query,
                "request_type": "natural_language_query"
            })

            query_lower = query.lower()
            
            # Determine the type of request
            if any(word in query_lower for word in ['time', 'clock', 'hour', 'minute']):
                if 'date' in query_lower or 'day' in query_lower:
                    # Both time and date requested
                    result = await self.get_datetime_info()
                    response = f"Current date and time: {result['date']['formatted']} at {result['time']['formatted_12h']} UTC"
                else:
                    # Just time requested
                    result = await self.get_current_time()
                    response = f"Current time: {result['formatted_time']} UTC"
            elif any(word in query_lower for word in ['date', 'day', 'today', 'calendar']):
                # Date requested
                result = await self.get_current_date()
                response = f"Today's date: {result['formatted_date']}"
            else:
                # Default to full date/time info
                result = await self.get_datetime_info()
                response = f"Current date and time: {result['date']['formatted']} at {result['time']['formatted_12h']} UTC"

            # Log the response
            await self.log_to_cosmos("query_response", {
                "original_query": query,
                "response": response,
                "success": True
            })

            return response

        except Exception as e:
            error_response = f"Sorry, I encountered an error while getting the time/date information: {str(e)}"
            
            # Log the error
            await self.log_to_cosmos("query_error", {
                "original_query": query,
                "error": str(e),
                "response": error_response
            })
            
            return error_response
