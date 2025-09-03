#!/usr/bin/env python3
"""
Script to query time_agent data from Cosmos DB to verify MCP server functionality
"""

import os
from datetime import datetime, timezone
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Cosmos DB configuration
    cosmos_uri = os.getenv('COSMOS_URI', 'https://ai-avatar.documents.azure.com/')
    cosmos_key = os.getenv('COSMOS_KEY')
    cosmos_database = os.getenv('COSMOS_DATABASE', 'playwright_logs')
    cosmos_container = os.getenv('COSMOS_CONTAINER', 'actions')
    
    if not cosmos_key:
        print("❌ COSMOS_KEY not found in environment variables")
        return
    
    try:
        # Initialize Cosmos client
        print(f"🔗 Connecting to Cosmos DB...")
        print(f"   URI: {cosmos_uri}")
        print(f"   Database: {cosmos_database}")
        print(f"   Container: {cosmos_container}")
        
        client = CosmosClient(cosmos_uri, cosmos_key)
        database = client.get_database_client(cosmos_database)
        container = database.get_container_client(cosmos_container)
        
        # Query for time_agent entries
        print(f"\n📊 Querying time_agent data...")
        
        # Query for recent time_agent entries (last hour)
        query = """
        SELECT * FROM c 
        WHERE c.agent_name = 'TimeAgent' 
        ORDER BY c._ts DESC
        """
        
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        print(f"✅ Found {len(items)} time_agent entries")
        
        if items:
            print(f"\n📋 Recent time_agent activity:")
            for i, item in enumerate(items[:10], 1):  # Show last 10 entries
                timestamp = item.get('timestamp', 'N/A')
                event_type = item.get('event_type', 'N/A')
                print(f"   {i}. {timestamp} - {event_type}")
                
                # Show details for the first few entries
                if i <= 3:
                    print(f"      ID: {item.get('id', 'N/A')}")
                    if 'data' in item:
                        data = item['data']
                        if 'query' in data:
                            print(f"      Query: {data['query']}")
                        if 'response' in data:
                            print(f"      Response: {data['response']}")
                        if 'result' in data and isinstance(data['result'], dict):
                            if 'formatted_time' in data['result']:
                                print(f"      Time: {data['result']['formatted_time']}")
                            if 'formatted_date' in data['result']:
                                print(f"      Date: {data['result']['formatted_date']}")
                    print()
        else:
            print("ℹ️  No time_agent entries found")
            
        # Query for all recent entries to see what's in the container
        print(f"\n🔍 Recent entries in container (any agent):")
        recent_query = """
        SELECT c.id, c.agent_name, c.event_type, c.timestamp 
        FROM c 
        ORDER BY c._ts DESC 
        OFFSET 0 LIMIT 10
        """
        
        recent_items = list(container.query_items(
            query=recent_query,
            enable_cross_partition_query=True
        ))
        
        for i, item in enumerate(recent_items, 1):
            agent = item.get('agent_name', 'Unknown')
            event = item.get('event_type', 'Unknown')
            timestamp = item.get('timestamp', 'N/A')
            print(f"   {i}. {timestamp} - {agent} - {event}")
            
    except Exception as e:
        print(f"❌ Error querying Cosmos DB: {e}")

if __name__ == "__main__":
    main()
