"""
Direct Azure Cosmos DB Logger for Time Agent
Bypasses MCP server and logs directly to Cosmos DB
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class DirectCosmosLogger:
    """Direct Azure Cosmos DB logger without MCP"""
    
    def __init__(self):
        self.cosmos_uri = os.getenv('COSMOS_URI', 'https://ai-avatar.documents.azure.com:443/')
        self.cosmos_key = os.getenv('COSMOS_KEY')
        self.database_name = os.getenv('COSMOS_DATABASE', 'playwright_logs') 
        self.container_name = os.getenv('COSMOS_CONTAINER', 'actions')
        
        self.client = None
        self.database = None
        self.container = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize direct Cosmos DB connection"""
        try:
            if not self.cosmos_key:
                logger.error("COSMOS_KEY environment variable not set")
                return False
                
            logger.info(f"Initializing direct Cosmos DB connection to {self.cosmos_uri}")
            logger.info(f"Database: {self.database_name}, Container: {self.container_name}")
            
            # Create Cosmos client
            self.client = CosmosClient(self.cosmos_uri, self.cosmos_key)
            
            # Get database and container
            self.database = self.client.get_database_client(self.database_name)
            self.container = self.database.get_container_client(self.container_name)
            
            # Test connection with a simple query
            test_query = "SELECT VALUE COUNT(1) FROM c"
            list(self.container.query_items(query=test_query, enable_cross_partition_query=True))
            
            logger.info("✅ Successfully connected to Azure Cosmos DB directly")
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize direct Cosmos DB connection: {e}")
            return False
    
    async def log_action(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Log an action directly to Cosmos DB"""
        if not self._initialized:
            logger.warning("Direct Cosmos DB logger not initialized")
            return False
            
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
            
            # Insert into Cosmos DB
            result = self.container.create_item(body=log_entry)
            
            logger.info(f"✅ Successfully logged to Azure Cosmos DB: {event_type}")
            logger.info(f"   Document ID: {result['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log to Azure Cosmos DB: {e}")
            return False
    
    async def query_logs(self, limit: int = 10) -> list:
        """Query recent logs from Cosmos DB"""
        if not self._initialized:
            return []
            
        try:
            query = f"SELECT TOP {limit} * FROM c WHERE c.agent_name = 'TimeAgent' ORDER BY c.timestamp DESC"
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            logger.error(f"Failed to query logs: {e}")
            return []
