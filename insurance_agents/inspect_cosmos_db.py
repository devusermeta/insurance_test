"""
Cosmos DB Inspector
Inspects current contents of Azure Cosmos DB insurance_claims database
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def inspect_cosmos_db():
    """Inspect current Cosmos DB contents"""
    logger.info("🔍 Inspecting Cosmos DB Contents...")
    logger.info("=" * 60)
    
    try:
        # Import MCP client for Cosmos operations
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        
        from shared.mcp_client import MCPClient
        
        mcp_client = MCPClient()
        logger.info("✅ MCP Client connected to Cosmos DB")
        
        # Check what containers exist
        logger.info("\n📊 Checking available containers...")
        try:
            containers_result = await mcp_client.execute_tool("list_collections", {})
            if containers_result.get("success"):
                containers = containers_result.get("collections", [])
                logger.info(f"📁 Found {len(containers)} containers:")
                for container in containers:
                    logger.info(f"   • {container}")
            else:
                logger.warning("⚠️ Could not retrieve container list")
        except Exception as e:
            logger.error(f"❌ Error listing containers: {str(e)}")
        
        # Check claims container specifically
        logger.info("\n🏥 Inspecting 'claims' container...")
        try:
            claims_result = await mcp_client.get_claims()
            
            # Handle MCP result format
            if isinstance(claims_result, dict):
                if claims_result.get("success"):
                    all_claims = claims_result.get("items", [])
                elif "items" in claims_result:
                    all_claims = claims_result["items"]
                elif "error" in claims_result:
                    logger.error(f"❌ Error getting claims: {claims_result['error']}")
                    all_claims = []
                else:
                    # Fallback - might be the data directly
                    all_claims = []
                    logger.warning("⚠️ Unexpected claims result format")
            elif isinstance(claims_result, list):
                all_claims = claims_result
            else:
                logger.warning("⚠️ Unexpected claims result type")
                all_claims = []
            
            logger.info(f"📋 Found {len(all_claims)} existing claims")
            
            if all_claims:
                logger.info("\n📊 Claims Summary:")
                
                # Analyze claim types
                claim_types = {}
                statuses = {}
                total_amount = 0
                date_range = {"earliest": None, "latest": None}
                
                for claim in all_claims:
                    # Count claim types
                    claim_type = claim.get("claim_type", "unknown")
                    claim_types[claim_type] = claim_types.get(claim_type, 0) + 1
                    
                    # Count statuses
                    status = claim.get("status", "unknown")
                    statuses[status] = statuses.get(status, 0) + 1
                    
                    # Sum amounts
                    amount = claim.get("estimated_amount", 0)
                    if isinstance(amount, (int, float)):
                        total_amount += amount
                    
                    # Track date range
                    created_date = claim.get("created_date") or claim.get("incident_date")
                    if created_date:
                        if not date_range["earliest"] or created_date < date_range["earliest"]:
                            date_range["earliest"] = created_date
                        if not date_range["latest"] or created_date > date_range["latest"]:
                            date_range["latest"] = created_date
                
                # Display analysis
                logger.info(f"   💰 Total estimated amount: ${total_amount:,.2f}")
                
                logger.info("   📈 Claim Types:")
                for claim_type, count in sorted(claim_types.items()):
                    percentage = (count / len(all_claims)) * 100
                    logger.info(f"      • {claim_type}: {count} ({percentage:.1f}%)")
                
                logger.info("   📊 Claim Statuses:")
                for status, count in sorted(statuses.items()):
                    percentage = (count / len(all_claims)) * 100
                    logger.info(f"      • {status}: {count} ({percentage:.1f}%)")
                
                if date_range["earliest"] and date_range["latest"]:
                    logger.info(f"   📅 Date Range: {date_range['earliest'][:10]} to {date_range['latest'][:10]}")
                
                # Show sample claims
                logger.info("\n📋 Sample Claims (first 5):")
                for i, claim in enumerate(all_claims[:5]):
                    claim_id = claim.get("claim_id", claim.get("id", "unknown"))
                    claim_type = claim.get("claim_type", "unknown")
                    amount = claim.get("estimated_amount", 0)
                    status = claim.get("status", "unknown")
                    customer = claim.get("customer_name", claim.get("customer_id", "unknown"))
                    
                    logger.info(f"   {i+1}. {claim_id}")
                    logger.info(f"      Type: {claim_type} | Amount: ${amount:,.2f} | Status: {status}")
                    logger.info(f"      Customer: {customer}")
                    logger.info("")
                
            else:
                logger.info("📭 No claims found in database - it's empty!")
                
        except Exception as e:
            logger.error(f"❌ Error inspecting claims: {str(e)}")
        
        # Check other containers if they exist
        containers_to_check = ["artifacts", "events", "rules", "customers", "policies"]
        
        for container_name in containers_to_check:
            logger.info(f"\n📁 Checking '{container_name}' container...")
            try:
                result = await mcp_client.execute_tool(
                    "query_cosmos",
                    {
                        "container": container_name,
                        "query": "SELECT COUNT(1) as count FROM c"
                    }
                )
                
                if result.get("success"):
                    items = result.get("items", [])
                    if items:
                        count = items[0].get("count", 0)
                        logger.info(f"   📊 Found {count} items in '{container_name}'")
                        
                        if count > 0 and count <= 10:
                            # Show sample items for small containers
                            sample_result = await mcp_client.execute_tool(
                                "query_cosmos",
                                {
                                    "container": container_name,
                                    "query": "SELECT * FROM c OFFSET 0 LIMIT 3"
                                }
                            )
                            
                            if sample_result.get("success"):
                                sample_items = sample_result.get("items", [])
                                logger.info(f"   📋 Sample items:")
                                for item in sample_items:
                                    item_id = item.get("id", "unknown")
                                    item_type = type(item).__name__
                                    logger.info(f"      • {item_id} ({len(str(item))} chars)")
                    else:
                        logger.info(f"   📭 Container '{container_name}' is empty")
                else:
                    logger.info(f"   ❓ Container '{container_name}' might not exist or is inaccessible")
                    
            except Exception as e:
                logger.info(f"   ❓ Could not access container '{container_name}': {str(e)}")
        
        await mcp_client.close()
        
        logger.info("\n🏁 Cosmos DB inspection completed!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Failed to inspect Cosmos DB: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(inspect_cosmos_db())
