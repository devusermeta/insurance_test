import asyncio
import json
import os
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey

async def upload_claims_data():
    """Upload claims data to Cosmos DB"""
    # Get connection details from environment
    endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
    key = os.getenv("AZURE_COSMOS_KEY")
    database_name = "insurance"
    container_name = "claims"  # Use claims container instead of claim_details
    
    if not endpoint or not key:
        print("❌ Missing AZURE_COSMOS_ENDPOINT or AZURE_COSMOS_KEY environment variables")
        return
    
    print(f"🔗 Connecting to Cosmos DB...")
    print(f"   URI: {endpoint}")
    print(f"   Database: {database_name}")
    print(f"   Container: {container_name}")
    
    async with CosmosClient(endpoint, key) as client:
        # Get database
        database = client.get_database_client(database_name)
        
        # Create container if it doesn't exist
        try:
            container = await database.create_container(
                id=container_name,
                partition_key=PartitionKey(path="/claimId"),
                offer_throughput=400
            )
            print(f"✅ Created new container: {container_name}")
        except Exception:
            container = database.get_container_client(container_name)
            print(f"✅ Using existing container: {container_name}")
        
        # Load claims data
        script_dir = os.path.dirname(os.path.abspath(__file__))
        claims_file = os.path.join(script_dir, "dataset", "claims.json")
        
        with open(claims_file, 'r') as f:
            claims = json.load(f)
        
        print(f"📊 Uploading {len(claims)} claims...")
        
        # Upload each claim
        for claim in claims:
            try:
                await container.create_item(body=claim)
                print(f"   ✅ Uploaded claim: {claim['claimId']} - {claim['patientName']}")
            except Exception as e:
                print(f"   ⚠️  Error uploading {claim['claimId']}: {e}")
                # Try to update if it already exists
                try:
                    await container.replace_item(item=claim['id'], body=claim)
                    print(f"   ✅ Updated claim: {claim['claimId']} - {claim['patientName']}")
                except Exception as e2:
                    print(f"   ❌ Failed to update {claim['claimId']}: {e2}")
        
        print("✅ Claims upload completed!")

if __name__ == "__main__":
    asyncio.run(upload_claims_data())
