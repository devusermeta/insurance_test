"""
Populate rules catalog in Cosmos DB for testing
"""

import os
import sys
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load environment variables from the cosmos server directory
cosmos_env_path = os.path.join(os.path.dirname(__file__), "azure-cosmos-mcp-server-samples", "python", ".env")
load_dotenv(cosmos_env_path)

def populate_rules_catalog():
    """Populate the rules catalog with basic insurance rules"""
    
    try:
        # Get connection info
        uri = os.getenv("COSMOS_URI")
        key = os.getenv("COSMOS_KEY")
        database_name = os.getenv("COSMOS_DATABASE", "insurance_claims")
        
        # Connect to Cosmos DB
        client = CosmosClient(uri, credential=key)
        database = client.get_database_client(database_name)
        rules_container = database.get_container_client("rules_catalog")
        
        # Basic insurance rules for testing
        rules = [
            {
                "id": "OP_DOC_REQUIRED",
                "ruleId": "OP_DOC_REQUIRED", 
                "description": "Outpatient claims must have memo/report/tests and bill",
                "category": "Outpatient",
                "type": "documentation",
                "required_documents": ["bill", "memo", "report"],
                "active": True
            },
            {
                "id": "IP_DISCHARGE_REQUIRED",
                "ruleId": "IP_DISCHARGE_REQUIRED",
                "description": "Inpatient claims must include discharge summary",
                "category": "Inpatient", 
                "type": "documentation",
                "required_documents": ["bill", "discharge_summary"],
                "active": True
            },
            {
                "id": "CAP_DENTAL_1000",
                "ruleId": "CAP_DENTAL_1000",
                "description": "Dental procedures capped at $1000 annually",
                "category": "Outpatient",
                "type": "coverage_limit",
                "provider_pattern": "DENTAL",
                "annual_limit": 1000,
                "active": True
            },
            {
                "id": "BASIC_COVERAGE",
                "ruleId": "BASIC_COVERAGE",
                "description": "Basic coverage for standard procedures",
                "category": "All",
                "type": "coverage",
                "coverage_percentage": 80,
                "active": True
            }
        ]
        
        print("📝 Populating rules catalog...")
        
        for rule in rules:
            try:
                rules_container.upsert_item(rule)
                print(f"  ✅ Added rule: {rule['ruleId']}")
            except Exception as e:
                print(f"  ❌ Error adding rule {rule['ruleId']}: {e}")
        
        print(f"\n🎉 Successfully populated {len(rules)} rules!")
        
        # Verify by counting
        count_query = "SELECT VALUE COUNT(1) FROM c"
        count_result = list(rules_container.query_items(
            query=count_query,
            enable_cross_partition_query=True
        ))
        total_rules = count_result[0] if count_result else 0
        print(f"📊 Total rules in catalog: {total_rules}")
        
    except Exception as e:
        print(f"❌ Error populating rules catalog: {e}")

if __name__ == "__main__":
    populate_rules_catalog()
