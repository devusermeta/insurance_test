"""
Insurance Claims Test Data Population Script
Populates Azure Cosmos DB with realistic test claims data for multi-agent system testing
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaimsDataGenerator:
    """Generate realistic insurance claims test data"""
    
    def __init__(self):
        self.claim_types = ["automotive", "property", "health", "life", "travel"]
        self.statuses = ["submitted", "under_review", "approved", "denied", "pending_documents"]
        self.priorities = ["low", "normal", "high", "urgent"]
        
        self.automotive_scenarios = [
            "Rear-end collision on Highway 101",
            "Vehicle vandalism in parking lot", 
            "Hit and run accident downtown",
            "Weather-related damage (hail)",
            "Theft of vehicle and contents",
            "Single vehicle accident on wet roads",
            "Multi-vehicle pile-up on interstate",
            "Parking lot collision at shopping center"
        ]
        
        self.property_scenarios = [
            "Water damage from burst pipe",
            "Fire damage to kitchen area",
            "Storm damage to roof and windows",
            "Burglary with stolen electronics",
            "Basement flooding during heavy rain",
            "Tree fell on house during windstorm",
            "Smoke damage from neighbor's fire",
            "Vandalism to exterior property"
        ]
        
        self.customer_names = [
            "John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis",
            "James Wilson", "Jennifer Miller", "David Garcia", "Lisa Anderson",
            "Robert Martinez", "Maria Rodriguez", "William Taylor", "Anna Lee"
        ]
        
        self.locations = [
            "San Francisco, CA", "Los Angeles, CA", "Seattle, WA", "Portland, OR",
            "Phoenix, AZ", "Denver, CO", "Austin, TX", "Chicago, IL",
            "New York, NY", "Miami, FL", "Atlanta, GA", "Boston, MA"
        ]

    def generate_claim_id(self) -> str:
        """Generate a unique claim ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = random.randint(1000, 9999)
        return f"CLM_{timestamp}_{random_suffix}"

    def generate_policy_number(self, claim_type: str) -> str:
        """Generate a policy number based on claim type"""
        type_codes = {
            "automotive": "AUTO",
            "property": "PROP", 
            "health": "HLTH",
            "life": "LIFE",
            "travel": "TRVL"
        }
        code = type_codes.get(claim_type, "GEN")
        number = random.randint(100000, 999999)
        return f"POL_{code}_{number}"

    def generate_customer_id(self) -> str:
        """Generate a customer ID"""
        return f"CUST_{random.randint(10000, 99999)}"

    def generate_claim(self, claim_type: str = None) -> Dict[str, Any]:
        """Generate a single realistic claim"""
        if not claim_type:
            claim_type = random.choice(self.claim_types)
            
        # Base claim data
        claim = {
            "id": self.generate_claim_id(),
            "claim_id": self.generate_claim_id(),
            "customer_id": self.generate_customer_id(),
            "customer_name": random.choice(self.customer_names),
            "policy_number": self.generate_policy_number(claim_type),
            "claim_type": claim_type,
            "status": random.choice(self.statuses),
            "priority": random.choice(self.priorities),
            "incident_date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "reported_date": (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat(),
            "location": random.choice(self.locations),
            "created_date": datetime.now().isoformat(),
            "updated_date": datetime.now().isoformat()
        }
        
        # Type-specific data
        if claim_type == "automotive":
            claim.update({
                "description": random.choice(self.automotive_scenarios),
                "estimated_amount": round(random.uniform(1000, 50000), 2),
                "vehicle_year": random.randint(2010, 2024),
                "vehicle_make": random.choice(["Toyota", "Honda", "Ford", "BMW", "Mercedes"]),
                "vehicle_model": random.choice(["Camry", "Accord", "F-150", "X3", "C-Class"]),
                "documents": [
                    {"type": "police_report", "status": random.choice(["uploaded", "pending"])},
                    {"type": "photos", "status": "uploaded"},
                    {"type": "repair_estimate", "status": random.choice(["uploaded", "pending"])}
                ]
            })
        elif claim_type == "property":
            claim.update({
                "description": random.choice(self.property_scenarios),
                "estimated_amount": round(random.uniform(2000, 100000), 2),
                "property_type": random.choice(["single_family", "condo", "apartment", "townhouse"]),
                "property_value": round(random.uniform(200000, 800000), 2),
                "documents": [
                    {"type": "photos", "status": "uploaded"},
                    {"type": "contractor_estimate", "status": random.choice(["uploaded", "pending"])},
                    {"type": "receipts", "status": random.choice(["uploaded", "pending"])}
                ]
            })
        elif claim_type == "health":
            claim.update({
                "description": "Medical treatment and related expenses",
                "estimated_amount": round(random.uniform(500, 25000), 2),
                "treatment_type": random.choice(["emergency", "surgery", "specialist", "therapy"]),
                "provider_name": random.choice(["General Hospital", "Medical Center", "Clinic Plus"]),
                "documents": [
                    {"type": "medical_bills", "status": "uploaded"},
                    {"type": "treatment_records", "status": random.choice(["uploaded", "pending"])},
                    {"type": "receipts", "status": "uploaded"}
                ]
            })
        
        # Add fraud risk indicators
        claim["fraud_risk_score"] = round(random.uniform(0.0, 1.0), 3)
        claim["fraud_indicators"] = []
        
        if claim["fraud_risk_score"] > 0.7:
            claim["fraud_indicators"] = random.sample([
                "high_claim_amount", "recent_policy_change", "multiple_claims", 
                "suspicious_timing", "inconsistent_details"
            ], random.randint(1, 3))
            
        return claim

    def generate_claims_batch(self, count: int = 50) -> List[Dict[str, Any]]:
        """Generate a batch of test claims"""
        claims = []
        
        # Generate claims with realistic distribution
        type_distribution = {
            "automotive": 0.4,  # 40%
            "property": 0.3,    # 30%
            "health": 0.2,      # 20%
            "life": 0.05,       # 5%
            "travel": 0.05      # 5%
        }
        
        for _ in range(count):
            # Choose claim type based on distribution
            rand = random.random()
            cumulative = 0
            claim_type = "automotive"  # default
            
            for ctype, prob in type_distribution.items():
                cumulative += prob
                if rand <= cumulative:
                    claim_type = ctype
                    break
                    
            claims.append(self.generate_claim(claim_type))
            
        return claims

async def populate_cosmos_db():
    """Populate Cosmos DB with test claims data"""
    logger.info("🚀 Starting Cosmos DB population with test claims data...")
    
    # Initialize data generator
    generator = ClaimsDataGenerator()
    
    try:
        # Import MCP client for Cosmos operations
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        
        from shared.mcp_client import MCPClient
        
        mcp_client = MCPClient()
        logger.info("✅ MCP Client initialized")
        
        # Generate test claims
        logger.info("📊 Generating test claims data...")
        claims = generator.generate_claims_batch(100)  # Generate 100 test claims
        
        # Insert claims into Cosmos DB
        logger.info(f"💾 Inserting {len(claims)} claims into Cosmos DB...")
        
        success_count = 0
        for i, claim in enumerate(claims):
            try:
                # Use MCP to insert claim
                result = await mcp_client.execute_tool(
                    "create_item",
                    {
                        "container": "claims",
                        "item": claim
                    }
                )
                
                if result.get("success"):
                    success_count += 1
                    if (i + 1) % 10 == 0:
                        logger.info(f"   📝 Inserted {i + 1}/{len(claims)} claims...")
                else:
                    logger.warning(f"   ⚠️ Failed to insert claim {claim['claim_id']}: {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error inserting claim {claim['claim_id']}: {str(e)}")
        
        logger.info(f"✅ Successfully inserted {success_count}/{len(claims)} claims")
        
        # Verify data insertion
        logger.info("🔍 Verifying data insertion...")
        all_claims = await mcp_client.get_claims()
        logger.info(f"📊 Total claims in database: {len(all_claims)}")
        
        # Show some sample data
        if all_claims:
            logger.info("📋 Sample claims:")
            for claim in all_claims[:3]:
                logger.info(f"   • {claim.get('claim_id')} - {claim.get('claim_type')} - ${claim.get('estimated_amount', 0):,.2f}")
        
        await mcp_client.close()
        logger.info("🎉 Cosmos DB population completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to populate Cosmos DB: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(populate_cosmos_db())
