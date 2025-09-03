import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

import httpx
from dotenv import load_dotenv
from direct_cosmos_logger import DirectCosmosLogger


logger = logging.getLogger(__name__)

load_dotenv()


class TimeAgentWithCosmosLogging:
    """Time Agent that provides time/date services and logs everything directly to Azure Cosmos DB."""

    def __init__(self):
        # Direct Cosmos DB logger (bypasses MCP server complexity)
        self.cosmos_logger = DirectCosmosLogger()
        self._cosmos_initialized = False
        
        # Keep old MCP variables for reference
        self.mcp_url = os.getenv('MCP_SERVER_URL', 'http://127.0.0.1:8080/mcp')
        self.cosmos_database = os.getenv('COSMOS_DATABASE', 'playwright_logs') 
        self.cosmos_container = os.getenv('COSMOS_CONTAINER', 'actions')
        self.session_id = None
        self.client = None

    async def initialize(self):
        """Initialize the time agent with direct Azure Cosmos DB logging."""
        try:
            logger.info("Initializing Time Agent with direct Azure Cosmos DB logging")
            
            # Initialize direct Cosmos DB connection
            cosmos_success = await self.cosmos_logger.initialize()
            
            if cosmos_success:
                self._cosmos_initialized = True
                logger.info("✅ Direct Azure Cosmos DB logging initialized successfully")
                
                # Log initialization success
                await self.log_to_cosmos("agent_initialized", {
                    "message": "Time Agent with direct Cosmos DB logging started successfully",
                    "database": self.cosmos_database,
                    "container": self.cosmos_container
                })
                
                return True
            else:
                logger.warning("❌ Direct Cosmos DB logging failed, will use console logging")
                return True  # Still allow agent to work without Cosmos DB
                
        except Exception as e:
            logger.error(f"Failed to initialize Time Agent: {e}")
            return False

    async def log_to_cosmos(self, event_type: str, data: Dict[str, Any]):
        """Log an event to Cosmos DB using direct connection"""
        if self._cosmos_initialized:
            # Use direct Cosmos DB logger
            success = await self.cosmos_logger.log_action(event_type, data)
            if success:
                return True
        
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

    async def get_current_time(self) -> Dict[str, Any]:
        """Get the current time information."""
        try:
            # Log the request
            await self.log_to_cosmos("time_request", {
                "requested_timezone": "UTC",
                "request_type": "get_current_time"
            })

            # Get current time
            current_time = datetime.now(timezone.utc)

            result = {
                "current_time": current_time.isoformat(),
                "formatted_time": current_time.strftime("%I:%M:%S %p"),
                "timezone": "UTC",
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
                "error": str(e)
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
                    "iso": current_dt.time().isoformat(),
                    "formatted_24h": current_dt.strftime("%H:%M:%S"),
                    "formatted_12h": current_dt.strftime("%I:%M:%S %p"),
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

    async def get_logs(self, limit: int = 10) -> list:
        """Get recent logs from Cosmos DB"""
        if self._cosmos_initialized:
            return await self.cosmos_logger.query_logs(limit)
        else:
            return []


# Example usage and testing
async def test_time_agent():
    """Test the time agent functionality"""
    agent = TimeAgentWithCosmosLogging()
    
    # Initialize
    await agent.initialize()
    
    # Test various queries
    queries = [
        "What time is it?",
        "What is the current date?", 
        "Show me the current date and time"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        response = await agent.process_query(query)
        print(f"Response: {response}")
    
    # Get recent logs
    logs = await agent.get_logs(5)
    print(f"\nRecent logs: {len(logs)} entries")
    for log in logs:
        print(f"  - {log.get('event_type', 'unknown')}: {log.get('timestamp', 'no time')}")


if __name__ == "__main__":
    asyncio.run(test_time_agent())
