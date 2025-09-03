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


class TimeAgentWithDirectCosmosLogging:
    """Time Agent that provides time/date services and logs directly to Azure Cosmos DB."""

    def __init__(self):
        # Cosmos DB configuration from environment
        self.cosmos_uri = os.getenv('COSMOS_URI', 'https://ai-avatar.documents.azure.com:443/')
        self.cosmos_key = os.getenv('COSMOS_KEY')
        self.cosmos_database = os.getenv('COSMOS_DATABASE', 'playwright_logs')
        self.cosmos_container = os.getenv('COSMOS_CONTAINER', 'actions')
        
        # Initialize Cosmos client
        self.cosmos_client = None
        self.cosmos_container_client = None

    async def initialize(self):
        """Initialize the Time Agent with direct Cosmos DB connection."""
        try:
            logger.info("Initializing Time Agent with direct Azure Cosmos DB logging")
            logger.info(f"Target Cosmos DB: {self.cosmos_database}/{self.cosmos_container}")
            
            # Initialize Cosmos DB client if key is available
            if self.cosmos_key:
                try:
                    from azure.cosmos import CosmosClient
                    
                    self.cosmos_client = CosmosClient(self.cosmos_uri, self.cosmos_key)
                    database_client = self.cosmos_client.get_database_client(self.cosmos_database)
                    self.cosmos_container_client = database_client.get_container_client(self.cosmos_container)
                    
                    # Test connection by reading container properties
                    properties = self.cosmos_container_client.read()
                    logger.info(f"✅ Successfully connected to Cosmos DB container: {properties['id']}")
                    
                except ImportError:
                    logger.warning("azure-cosmos package not available, logging to console only")
                except Exception as e:
                    logger.error(f"Failed to connect to Cosmos DB: {e}")
                    logger.info("Will fall back to console logging")
            else:
                logger.warning("No Cosmos DB key found, logging to console only")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Time Agent: {e}")
            return False

    async def log_to_cosmos(self, event_type: str, data: Dict[str, Any]):
        """Log an event directly to Cosmos DB."""
        # Create log entry with proper structure for Cosmos DB
        log_entry = {
            "id": f"time_agent_{datetime.now(timezone.utc).isoformat().replace(':', '_').replace('.', '_')}_{event_type}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": "TimeAgent",
            "event_type": event_type,
            "data": data,
            "partition_key": "time_agent",
            "_ts": int(datetime.now(timezone.utc).timestamp())
        }
        
        # Always log to console for immediate visibility
        logger.info(f"[COSMOS_LOG] {json.dumps(log_entry, indent=2)}")
        
        # Try to write to Cosmos DB if available
        if self.cosmos_container_client:
            try:
                result = self.cosmos_container_client.create_item(body=log_entry)
                logger.info(f"✅ Successfully logged to Cosmos DB: {event_type}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to write to Cosmos DB: {e}")
                logger.info(f"[COSMOS_FALLBACK] Logged to console only")
                return True  # Don't fail the main operation
        else:
            logger.info(f"[CONSOLE_ONLY] No Cosmos DB connection available")
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


# Export the class for backwards compatibility
TimeAgentWithCosmosLogging = TimeAgentWithDirectCosmosLogging
