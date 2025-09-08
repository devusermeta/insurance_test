#!/usr/bin/env python3
"""
Cosmos DB Setup Script for Insurance System
Creates database, container, and populates with patient records
"""

import asyncio
import json
import os
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey, exceptions

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class CosmosDBSetup:
    def __init__(self):
        self.endpoint = os.getenv('COSMOS_ENDPOINT')
        self.key = os.getenv('COSMOS_KEY')
        self.database_name = "insurance"
        self.container_name = "patient_details"
        
        if not self.endpoint or not self.key:
            raise ValueError("❌ Please set COSMOS_ENDPOINT and COSMOS_KEY in your .env file")
        
        self.client = CosmosClient(self.endpoint, self.key)
        print(f"✅ Connected to Cosmos DB: {self.endpoint}")
    
    async def setup_database(self):
        """Create database and container"""
        try:
            # Create database
            print(f"🔧 Creating database: {self.database_name}")
            database = self.client.create_database_if_not_exists(id=self.database_name)
            print(f"✅ Database '{self.database_name}' ready")
            
            # Create container with partition key
            print(f"🔧 Creating container: {self.container_name}")
            container = database.create_container_if_not_exists(
                id=self.container_name,
                partition_key=PartitionKey(path="/claimId"),
                offer_throughput=400  # Minimum throughput
            )
            print(f"✅ Container '{self.container_name}' ready")
            
            return database, container
            
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error setting up database: {e}")
            raise
    
    def get_patient_records(self):
        """Get the 8 sample patient records"""
        return [
            {
                "id": "pat_001",
                "claimId": "OP-1001",
                "status": "submitted",
                "category": "Outpatient",
                "amountBilled": 180.0,
                "submitDate": "2025-08-21",
                "lastUpdate": "2025-09-08T14:00:00Z",
                "assignedEmployee": None,
                "patientName": "John Smith",
                "provider": "CLN-ALPHA",
                "memberId": "M-001",
                "region": "US",
                "diagnosis": "Routine checkup",
                "serviceType": "consultation"
            },
            {
                "id": "pat_002",
                "claimId": "OP-1002", 
                "status": "processing",
                "category": "Outpatient",
                "amountBilled": 320.0,
                "submitDate": "2025-08-19",
                "lastUpdate": "2025-09-08T13:30:00Z",
                "assignedEmployee": "emp_001",
                "patientName": "Jane Doe",
                "provider": "CLN-BETA",
                "memberId": "M-002",
                "region": "US",
                "diagnosis": "Blood test and lab work",
                "serviceType": "laboratory"
            },
            {
                "id": "pat_003",
                "claimId": "IP-2001",
                "status": "approved", 
                "category": "Inpatient",
                "amountBilled": 14000.0,
                "submitDate": "2025-08-10",
                "lastUpdate": "2025-09-08T12:00:00Z",
                "assignedEmployee": "emp_002",
                "patientName": "Robert Johnson",
                "provider": "HSP-GAMMA",
                "memberId": "M-004",
                "region": "US",
                "diagnosis": "Knee replacement surgery",
                "serviceType": "surgical"
            },
            {
                "id": "pat_004",
                "claimId": "OP-1003",
                "status": "submitted",
                "category": "Outpatient", 
                "amountBilled": 1200.0,
                "submitDate": "2025-08-15",
                "lastUpdate": "2025-09-08T11:30:00Z",
                "assignedEmployee": None,
                "patientName": "Maria Garcia",
                "provider": "CLN-DENTAL",
                "memberId": "M-003",
                "region": "US",
                "diagnosis": "Root canal treatment",
                "serviceType": "dental"
            },
            {
                "id": "pat_005",
                "claimId": "IP-2002",
                "status": "pending",
                "category": "Inpatient",
                "amountBilled": 8500.0,
                "submitDate": "2025-08-22",
                "lastUpdate": "2025-09-08T10:15:00Z",
                "assignedEmployee": "emp_003", 
                "patientName": "David Wilson",
                "provider": "HSP-DELTA",
                "memberId": "M-005",
                "region": "US",
                "diagnosis": "Cardiac monitoring and treatment",
                "serviceType": "cardiac"
            },
            {
                "id": "pat_006",
                "claimId": "OP-1004",
                "status": "denied",
                "category": "Outpatient",
                "amountBilled": 450.0,
                "submitDate": "2025-08-18",
                "lastUpdate": "2025-09-08T09:45:00Z",
                "assignedEmployee": "emp_001",
                "patientName": "Sarah Brown",
                "provider": "CLN-URGENT", 
                "memberId": "M-006",
                "region": "US",
                "diagnosis": "Emergency room visit - non-covered",
                "serviceType": "emergency"
            },
            {
                "id": "pat_007",
                "claimId": "IP-2003", 
                "status": "approved",
                "category": "Inpatient",
                "amountBilled": 5000.0,
                "submitDate": "2025-08-12",
                "lastUpdate": "2025-09-08T08:30:00Z",
                "assignedEmployee": "emp_002",
                "patientName": "Michael Chen",
                "provider": "HSP-OMEGA",
                "memberId": "M-007",
                "region": "US",
                "diagnosis": "Appendectomy",
                "serviceType": "surgical"
            },
            {
                "id": "pat_008",
                "claimId": "OP-1005",
                "status": "processing",
                "category": "Outpatient",
                "amountBilled": 890.0,
                "submitDate": "2025-08-25",
                "lastUpdate": "2025-09-08T07:20:00Z",
                "assignedEmployee": "emp_003",
                "patientName": "Lisa Anderson", 
                "provider": "CLN-VISION",
                "memberId": "M-008",
                "region": "US",
                "diagnosis": "Eye surgery consultation",
                "serviceType": "ophthalmology"
            }
        ]
    
    async def populate_container(self, container):
        """Insert patient records into container"""
        patient_records = self.get_patient_records()
        
        print(f"📝 Inserting {len(patient_records)} patient records...")
        
        for record in patient_records:
            try:
                # Insert record
                container.create_item(body=record)
                print(f"✅ Inserted patient: {record['patientName']} (Claim: {record['claimId']})")
                
            except exceptions.CosmosResourceExistsError:
                print(f"⚠️ Patient record already exists: {record['claimId']}")
                
            except exceptions.CosmosHttpResponseError as e:
                print(f"❌ Error inserting {record['claimId']}: {e}")
        
        print(f"✅ Finished inserting patient records")
    
    async def verify_data(self, container):
        """Verify the inserted data"""
        print("🔍 Verifying inserted data...")
        
        # Query all items
        query = "SELECT * FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        print(f"📊 Found {len(items)} patient records in database:")
        for item in items:
            print(f"   • {item['patientName']} - {item['claimId']} - ${item['amountBilled']} ({item['status']})")
        
        return items
    
    async def run_setup(self):
        """Run the complete setup process"""
        try:
            print("🏥 Starting Cosmos DB setup for Insurance System...")
            print("=" * 60)
            
            # Step 1: Create database and container
            database, container = await self.setup_database()
            
            # Step 2: Populate with patient records  
            await self.populate_container(container)
            
            # Step 3: Verify data
            items = await self.verify_data(container)
            
            print("=" * 60)
            print("🎉 Cosmos DB setup completed successfully!")
            print(f"📊 Database: {self.database_name}")
            print(f"📊 Container: {self.container_name}")
            print(f"📊 Records: {len(items)} patient records")
            print("\n🔧 Next steps:")
            print("1. Start the MCP server: python azure-cosmos-mcp-server-samples/python/cosmos_server.py")
            print("2. Update MCP server config to use 'insurance' database and 'patient_details' container")
            print("3. Restart your insurance agents - they'll now use real data!")
            
        except Exception as e:
            print(f"❌ Setup failed: {str(e)}")
            raise

async def main():
    """Main entry point"""
    setup = CosmosDBSetup()
    await setup.run_setup()

if __name__ == "__main__":
    asyncio.run(main())
