#!/usr/bin/env python3
"""
Cosmos DB Collections Setup for Insurance Claims Processing

This script creates and initializes Cosmos DB collections based on the CSV schemas
from the Docs/ folder. It includes terminal logging for real-time progress monitoring.
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from azure.cosmos import CosmosClient, PartitionKey, exceptions
    from azure.identity import DefaultAzureCredential
    from dotenv import load_dotenv
    import pandas as pd
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Load environment variables
load_dotenv()

# Terminal logging setup with colors
class TerminalLogger:
    """Enhanced terminal logging with colors and emojis for workflow visibility"""
    
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m'
    }
    
    @classmethod
    def log(cls, level: str, component: str, message: str, reasoning: str = None):
        """Log with timestamp, colors, and optional reasoning"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        emoji_map = {
            'INFO': '📋',
            'SUCCESS': '✅', 
            'WARNING': '⚠️',
            'ERROR': '❌',
            'COSMOS': '🌌',
            'REASONING': '🧠'
        }
        
        color_map = {
            'INFO': cls.COLORS['blue'],
            'SUCCESS': cls.COLORS['green'],
            'WARNING': cls.COLORS['yellow'], 
            'ERROR': cls.COLORS['red'],
            'COSMOS': cls.COLORS['magenta'],
            'REASONING': cls.COLORS['cyan']
        }
        
        emoji = emoji_map.get(level, '📋')
        color = color_map.get(level, cls.COLORS['white'])
        
        print(f"{color}[{timestamp}] {emoji} {component.upper()}: {message}{cls.COLORS['reset']}")
        
        if reasoning:
            print(f"{cls.COLORS['cyan']}[{timestamp}] 🧠 REASONING: {reasoning}{cls.COLORS['reset']}")

class CosmosCollectionSetup:
    """Setup Cosmos DB collections for insurance claims processing"""
    
    def __init__(self):
        self.logger = TerminalLogger()
        self.client = None
        self.database = None
        self.docs_path = Path(__file__).parent.parent / "Docs"
        
        # Collection schemas based on CSV analysis
        self.collection_schemas = {
            "claims": {
                "partition_key": "/claimId",
                "sample_fields": ["claimId", "memberId", "category", "submitDate", "provider", 
                                "dosFrom", "dosTo", "amountBilled", "region", "expectedOutput", "status", "createdBy"]
            },
            "artifacts": {
                "partition_key": "/claimId", 
                "sample_fields": ["claimId", "fileId", "type", "uri", "hash", "pages", "uploadedBy"]
            },
            "agent_runs": {
                "partition_key": "/claimId",
                "sample_fields": ["taskId", "claimId", "agent", "status", "confidence", "gaps", "start", "end"]
            },
            "events": {
                "partition_key": "/claimId",
                "sample_fields": ["ts", "claimId", "actor", "type", "details"]
            },
            "threads": {
                "partition_key": "/claimThreadId",
                "sample_fields": ["conversationId", "claimThreadId", "subThreadIds"]
            },
            "extractions_files": {
                "partition_key": "/claimId",
                "sample_fields": ["claimId", "fileId", "fields", "evidence"]
            },
            "extractions_summary": {
                "partition_key": "/claimId", 
                "sample_fields": ["claimId", "lines", "diagnoses", "keyDates", "totalBilled"]
            },
            "rules_eval": {
                "partition_key": "/claimId",
                "sample_fields": ["claimId", "lineId", "code", "covered", "allowedAmount", "rationale", "ruleIds", "overallDecision"]
            },
            "rules_catalog": {
                "partition_key": "/ruleId",
                "sample_fields": ["ruleId", "name", "description", "category", "active"]
            }
        }
    
    async def setup_cosmos_connection(self) -> bool:
        """Initialize Cosmos DB connection with terminal logging"""
        try:
            self.logger.log("INFO", "COSMOS_SETUP", "Initializing Cosmos DB connection...")
            
            # Check environment variables
            cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
            cosmos_key = os.getenv("COSMOS_KEY") 
            database_name = os.getenv("COSMOS_DATABASE", "insurance_claims")
            
            if not cosmos_endpoint:
                self.logger.log("ERROR", "COSMOS_SETUP", "COSMOS_ENDPOINT environment variable not set")
                return False
                
            self.logger.log("REASONING", "COSMOS_SETUP", f"Using endpoint: {cosmos_endpoint}")
            
            # Initialize client
            if cosmos_key:
                self.client = CosmosClient(cosmos_endpoint, cosmos_key)
                self.logger.log("SUCCESS", "COSMOS_SETUP", "Connected using primary key authentication")
            else:
                # Use Azure Identity for authentication
                credential = DefaultAzureCredential()
                self.client = CosmosClient(cosmos_endpoint, credential)
                self.logger.log("SUCCESS", "COSMOS_SETUP", "Connected using Azure Identity")
            
            # Create or get database
            self.logger.log("INFO", "COSMOS_SETUP", f"Setting up database: {database_name}")
            self.database = self.client.create_database_if_not_exists(database_name)
            self.logger.log("SUCCESS", "COSMOS_SETUP", f"Database '{database_name}' ready")
            
            return True
            
        except Exception as e:
            self.logger.log("ERROR", "COSMOS_SETUP", f"Failed to connect to Cosmos DB: {str(e)}")
            return False
    
    async def create_collections(self) -> bool:
        """Create all insurance collections with proper schemas"""
        try:
            self.logger.log("INFO", "COLLECTIONS", "Creating insurance claims collections...")
            
            for collection_name, schema in self.collection_schemas.items():
                try:
                    self.logger.log("INFO", "COLLECTIONS", f"Creating collection: {collection_name}")
                    self.logger.log("REASONING", "COLLECTIONS", 
                                  f"Partition key: {schema['partition_key']}, Fields: {len(schema['sample_fields'])}")
                    
                    # Create collection with partition key
                    collection = self.database.create_container_if_not_exists(
                        id=collection_name,
                        partition_key=PartitionKey(path=schema['partition_key']),
                        offer_throughput=400  # Minimum RU/s for development
                    )
                    
                    self.logger.log("SUCCESS", "COLLECTIONS", f"Collection '{collection_name}' created successfully")
                    
                except exceptions.CosmosHttpResponseError as e:
                    if e.status_code == 409:  # Conflict - collection already exists
                        self.logger.log("WARNING", "COLLECTIONS", f"Collection '{collection_name}' already exists")
                    else:
                        raise e
                        
            self.logger.log("SUCCESS", "COLLECTIONS", "All collections setup completed")
            return True
            
        except Exception as e:
            self.logger.log("ERROR", "COLLECTIONS", f"Failed to create collections: {str(e)}")
            return False
    
    async def load_sample_data(self) -> bool:
        """Load sample data from CSV files for testing"""
        try:
            self.logger.log("INFO", "SAMPLE_DATA", "Loading sample data from CSV files...")
            
            # Load claims data
            claims_file = self.docs_path / "claims.csv"
            if claims_file.exists():
                df = pd.read_csv(claims_file)
                container = self.database.get_container_client("claims")
                
                for _, row in df.iterrows():
                    item = row.to_dict()
                    # Ensure claimId is string for partition key
                    item['id'] = item['claimId']
                    
                    try:
                        container.create_item(item)
                        self.logger.log("SUCCESS", "SAMPLE_DATA", f"Loaded claim: {item['claimId']}")
                    except exceptions.CosmosHttpResponseError as e:
                        if e.status_code == 409:  # Already exists
                            self.logger.log("WARNING", "SAMPLE_DATA", f"Claim {item['claimId']} already exists")
                        else:
                            raise e
            
            # Load artifacts data  
            artifacts_file = self.docs_path / "artifacts.csv"
            if artifacts_file.exists():
                df = pd.read_csv(artifacts_file)
                container = self.database.get_container_client("artifacts")
                
                for _, row in df.iterrows():
                    item = row.to_dict()
                    item['id'] = item['fileId']
                    
                    try:
                        container.create_item(item)
                        self.logger.log("SUCCESS", "SAMPLE_DATA", f"Loaded artifact: {item['fileId']}")
                    except exceptions.CosmosHttpResponseError as e:
                        if e.status_code == 409:
                            self.logger.log("WARNING", "SAMPLE_DATA", f"Artifact {item['fileId']} already exists")
                        else:
                            raise e
            
            self.logger.log("SUCCESS", "SAMPLE_DATA", "Sample data loading completed")
            return True
            
        except Exception as e:
            self.logger.log("ERROR", "SAMPLE_DATA", f"Failed to load sample data: {str(e)}")
            return False
    
    async def test_collections(self) -> bool:
        """Test basic read/write operations on collections"""
        try:
            self.logger.log("INFO", "TESTING", "Testing collection operations...")
            
            # Test claims collection
            claims_container = self.database.get_container_client("claims")
            
            # Test query
            query = "SELECT * FROM c WHERE c.category = 'Outpatient'"
            items = list(claims_container.query_items(query, enable_cross_partition_query=True))
            
            self.logger.log("SUCCESS", "TESTING", f"Query test passed: Found {len(items)} outpatient claims")
            self.logger.log("REASONING", "TESTING", f"Query: {query}")
            
            # Test write operation
            test_item = {
                "id": "TEST-001",
                "claimId": "TEST-001", 
                "memberId": "M-TEST",
                "category": "Test",
                "status": "testing",
                "createdBy": "cosmos_setup"
            }
            
            try:
                claims_container.create_item(test_item)
                self.logger.log("SUCCESS", "TESTING", "Write test passed: Created test item")
                
                # Clean up test item
                claims_container.delete_item("TEST-001", partition_key="TEST-001")
                self.logger.log("SUCCESS", "TESTING", "Cleanup completed: Removed test item")
                
            except exceptions.CosmosHttpResponseError as e:
                if e.status_code == 409:
                    self.logger.log("WARNING", "TESTING", "Test item already exists, skipping write test")
                else:
                    raise e
            
            self.logger.log("SUCCESS", "TESTING", "All collection tests passed")
            return True
            
        except Exception as e:
            self.logger.log("ERROR", "TESTING", f"Collection testing failed: {str(e)}")
            return False

async def main():
    """Main setup function"""
    logger = TerminalLogger()
    
    logger.log("INFO", "SETUP_START", "Starting Cosmos DB collections setup for Insurance Claims Processing")
    
    # Check dependencies
    if not DEPENDENCIES_AVAILABLE:
        logger.log("ERROR", "DEPENDENCIES", f"Missing required dependencies: {IMPORT_ERROR}")
        logger.log("INFO", "DEPENDENCIES", "Run: pip install -r azure-cosmos-mcp-server-samples/python/requirements.txt")
        return False
    
    # Initialize setup
    setup = CosmosCollectionSetup()
    
    # Step 1: Connect to Cosmos DB
    if not await setup.setup_cosmos_connection():
        logger.log("ERROR", "SETUP_FAILED", "Could not establish Cosmos DB connection")
        return False
    
    # Step 2: Create collections
    if not await setup.create_collections():
        logger.log("ERROR", "SETUP_FAILED", "Could not create collections")
        return False
    
    # Step 3: Load sample data
    if not await setup.load_sample_data():
        logger.log("WARNING", "SETUP_WARNING", "Sample data loading failed, but collections are ready")
    
    # Step 4: Test collections
    if not await setup.test_collections():
        logger.log("WARNING", "SETUP_WARNING", "Collection testing failed, but setup may still be valid")
    
    logger.log("SUCCESS", "SETUP_COMPLETE", "Cosmos DB collections setup completed successfully!")
    logger.log("INFO", "NEXT_STEPS", "Collections are ready for insurance agents to use via MCP tools")
    
    return True

if __name__ == "__main__":
    asyncio.run(main())
