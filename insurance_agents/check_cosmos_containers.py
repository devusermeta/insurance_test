#!/usr/bin/env python3
"""
Check and create required Cosmos DB containers for the insurance workflow
"""

import os
from dotenv import load_dotenv
from azure.cosmos import CosmosClient, PartitionKey

# Load environment variables
load_dotenv()

def check_and_create_containers():
    """Check if required containers exist and create them if needed"""
    
    # Get Cosmos DB credentials
    endpoint = os.getenv("COSMOS_ENDPOINT")
    key = os.getenv("COSMOS_KEY") 
    database_name = os.getenv("COSMOS_DATABASE_NAME", "insurance")
    
    if not endpoint or not key:
        print("❌ Missing Cosmos DB credentials in .env file")
        return False
    
    try:
        # Initialize Cosmos client
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        
        print(f"✅ Connected to Cosmos DB database: {database_name}")
        
        # List existing containers
        containers = list(database.list_containers())
        existing_container_names = [c['id'] for c in containers]
        
        print(f"📋 Existing containers: {existing_container_names}")
        
        # Required containers for the workflow
        required_containers = [
            {"id": "extracted_patient_data", "partition_key": "/claimId"},
            {"id": "claims", "partition_key": "/id"},
            {"id": "policies", "partition_key": "/id"},
            {"id": "claims_status", "partition_key": "/claimId"}
        ]
        
        # Check and create missing containers
        for container_spec in required_containers:
            container_id = container_spec["id"]
            
            if container_id in existing_container_names:
                print(f"✅ Container '{container_id}' already exists")
            else:
                print(f"🔄 Creating container '{container_id}'...")
                try:
                    database.create_container(
                        id=container_id,
                        partition_key=PartitionKey(path=container_spec["partition_key"])
                    )
                    print(f"✅ Created container '{container_id}'")
                except Exception as e:
                    print(f"❌ Failed to create container '{container_id}': {e}")
        
        print("\n🎯 Container check completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error checking Cosmos DB containers: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking Cosmos DB containers for insurance workflow...")
    print("=" * 60)
    check_and_create_containers()
