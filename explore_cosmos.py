"""
Script to explore existing Cosmos DB data structure
"""

import os
import sys
import json
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load environment variables from the cosmos server directory
cosmos_env_path = os.path.join(os.path.dirname(__file__), "azure-cosmos-mcp-server-samples", "python", ".env")
load_dotenv(cosmos_env_path)

def explore_cosmos_db():
    """Explore the existing Cosmos DB structure"""
    
    try:
        # Get connection info
        uri = os.getenv("COSMOS_URI")
        key = os.getenv("COSMOS_KEY")
        database_name = os.getenv("COSMOS_DATABASE", "insurance_claims")
        
        print(f"🔍 Exploring Cosmos DB: {database_name}")
        print(f"📍 URI: {uri}")
        
        # Connect to Cosmos DB
        client = CosmosClient(uri, credential=key)
        database = client.get_database_client(database_name)
        
        # List all containers
        print("\n📦 Available containers:")
        containers = list(database.list_containers())
        
        if not containers:
            print("  ❌ No containers found!")
            return
        
        for container_info in containers:
            container_name = container_info['id']
            print(f"  📁 {container_name}")
            
            # Get container and sample some data
            container = database.get_container_client(container_name)
            
            try:
                # Count documents
                count_query = "SELECT VALUE COUNT(1) FROM c"
                count_result = list(container.query_items(
                    query=count_query,
                    enable_cross_partition_query=True
                ))
                doc_count = count_result[0] if count_result else 0
                
                print(f"    📊 Documents: {doc_count}")
                
                if doc_count > 0:
                    # Get sample documents
                    sample_query = "SELECT * FROM c OFFSET 0 LIMIT 3"
                    samples = list(container.query_items(
                        query=sample_query,
                        enable_cross_partition_query=True
                    ))
                    
                    print(f"    📋 Sample documents:")
                    for i, doc in enumerate(samples, 1):
                        # Show first few fields of each document
                        doc_preview = {}
                        for key, value in list(doc.items())[:5]:
                            if isinstance(value, (str, int, float, bool)):
                                doc_preview[key] = value
                            else:
                                doc_preview[key] = f"<{type(value).__name__}>"
                        print(f"      {i}. {json.dumps(doc_preview, indent=8)}")
                        
                    # Show unique field names across all documents
                    fields_query = "SELECT * FROM c OFFSET 0 LIMIT 10"
                    field_samples = list(container.query_items(
                        query=fields_query,
                        enable_cross_partition_query=True
                    ))
                    
                    all_fields = set()
                    for doc in field_samples:
                        all_fields.update(doc.keys())
                    
                    print(f"    🔑 Fields found: {sorted(list(all_fields))}")
                
            except Exception as e:
                print(f"    ❌ Error querying container: {e}")
            
            print()
        
        return containers
        
    except Exception as e:
        print(f"❌ Error exploring Cosmos DB: {e}")
        return []

def suggest_test_scenarios(containers):
    """Suggest test scenarios based on existing data"""
    print("\n🧪 Test Scenario Suggestions:")
    
    container_names = [c['id'] for c in containers]
    
    if 'claims' in container_names:
        print("✅ Found 'claims' container - can test claims processing workflow")
    else:
        print("❓ No 'claims' container found - you may need to create claims data")
    
    if 'artifacts' in container_names:
        print("✅ Found 'artifacts' container - can test document processing")
    else:
        print("❓ No 'artifacts' container found - you may need to create artifact data")
    
    # Check for other workflow containers
    workflow_containers = ['extractions', 'rules_eval', 'agent_runs', 'events', 'threads']
    missing_containers = [c for c in workflow_containers if c not in container_names]
    
    if missing_containers:
        print(f"📝 Missing workflow containers: {missing_containers}")
        print("   These will be created automatically when agents run")
    
    print("\n🎯 Next Steps:")
    print("1. Review the existing data structure above")
    print("2. We can modify agents to work with your existing containers")
    print("3. Test agents by calling them with existing claim IDs")
    print("4. Or create specific test claims if needed")

if __name__ == "__main__":
    containers = explore_cosmos_db()
    if containers:
        suggest_test_scenarios(containers)
