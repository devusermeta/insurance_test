"""
Script to populate Cosmos DB with test data for insurance claims scenarios
"""

import os
import json
from datetime import datetime, timedelta
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cosmos DB configuration
COSMOS_URI = os.getenv("COSMOS_URI")
COSMOS_KEY = os.getenv("COSMOS_KEY") 
DATABASE_NAME = os.getenv("COSMOS_DATABASE", "insurance_claims")

def get_cosmos_client():
    """Get Cosmos DB client"""
    return CosmosClient(COSMOS_URI, credential=COSMOS_KEY)

def create_containers_if_not_exist(client):
    """Create all required containers if they don't exist"""
    database = client.get_database_client(DATABASE_NAME)
    
    containers = [
        {"name": "claims", "partition_key": "/claimId"},
        {"name": "artifacts", "partition_key": "/claimId"},
        {"name": "extractions", "partition_key": "/claimId"},
        {"name": "rules_eval", "partition_key": "/claimId"},
        {"name": "agent_runs", "partition_key": "/claimId"},
        {"name": "events", "partition_key": "/claimId"},
        {"name": "threads", "partition_key": "/claimId"},
        {"name": "rules_catalog", "partition_key": "/ruleId"}
    ]
    
    for container_config in containers:
        try:
            container = database.create_container(
                id=container_config["name"],
                partition_key={"paths": [container_config["partition_key"]], "kind": "Hash"}
            )
            print(f"✅ Created container: {container_config['name']}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"ℹ️ Container already exists: {container_config['name']}")
            else:
                print(f"❌ Error creating container {container_config['name']}: {e}")

def create_test_scenarios():
    """Create test scenarios as described in your workflow"""
    
    # Test scenario data based on your vision
    scenarios = {
        # OP-1001: Clean OP visit with complete docs → Approve
        "OP-1001": {
            "claim": {
                "id": "OP-1001",
                "claimId": "OP-1001",
                "memberId": "M001",
                "category": "Outpatient",
                "submitDate": "2025-09-04T10:00:00Z",
                "provider": "City General Hospital",
                "dosFrom": "2025-09-03T14:30:00Z",
                "dosTo": "2025-09-03T15:30:00Z",
                "amountBilled": 150.00,
                "region": "US-East",
                "status": "submitted",
                "expectedOutput": "Complete validation and processing"
            },
            "artifacts": [
                {
                    "id": "F-OP-1001-BILL",
                    "claimId": "OP-1001",
                    "fileId": "F-OP-1001-BILL",
                    "type": "bill",
                    "uri": "blob://storage/claims/OP-1001/bill.pdf",
                    "hash": "abc123",
                    "pages": 1,
                    "uploadedBy": "M001"
                },
                {
                    "id": "F-OP-1001-MEMO",
                    "claimId": "OP-1001", 
                    "fileId": "F-OP-1001-MEMO",
                    "type": "memo",
                    "uri": "blob://storage/claims/OP-1001/memo.pdf",
                    "hash": "def456",
                    "pages": 2,
                    "uploadedBy": "M001"
                }
            ]
        },
        
        # OP-1002: Missing memo/report → Pend
        "OP-1002": {
            "claim": {
                "id": "OP-1002",
                "claimId": "OP-1002",
                "memberId": "M002",
                "category": "Outpatient",
                "submitDate": "2025-09-04T11:00:00Z",
                "provider": "Downtown Clinic",
                "dosFrom": "2025-09-02T09:00:00Z",
                "dosTo": "2025-09-02T10:00:00Z",
                "amountBilled": 220.00,
                "region": "US-East",
                "status": "submitted",
                "expectedOutput": "Validation with gap identification"
            },
            "artifacts": [
                {
                    "id": "F-OP-1002-BILL",
                    "claimId": "OP-1002",
                    "fileId": "F-OP-1002-BILL",
                    "type": "bill",
                    "uri": "blob://storage/claims/OP-1002/bill.pdf",
                    "hash": "ghi789",
                    "pages": 1,
                    "uploadedBy": "M002"
                }
                # Note: Missing memo/report - this should trigger pend
            ]
        },
        
        # OP-1003: Dental over cap → Approve with limit
        "OP-1003": {
            "claim": {
                "id": "OP-1003",
                "claimId": "OP-1003",
                "memberId": "M003",
                "category": "Outpatient",
                "submitDate": "2025-09-04T12:00:00Z",
                "provider": "Smile Dental Center",
                "dosFrom": "2025-09-01T10:00:00Z",
                "dosTo": "2025-09-01T11:30:00Z",
                "amountBilled": 1200.00,
                "region": "US-East",
                "status": "submitted",
                "expectedOutput": "Process with cap enforcement"
            },
            "artifacts": [
                {
                    "id": "F-OP-1003-BILL",
                    "claimId": "OP-1003",
                    "fileId": "F-OP-1003-BILL",
                    "type": "bill",
                    "uri": "blob://storage/claims/OP-1003/bill.pdf",
                    "hash": "jkl012",
                    "pages": 1,
                    "uploadedBy": "M003"
                },
                {
                    "id": "F-OP-1003-REPORT",
                    "claimId": "OP-1003",
                    "fileId": "F-OP-1003-REPORT", 
                    "type": "report",
                    "uri": "blob://storage/claims/OP-1003/dental_report.pdf",
                    "hash": "mno345",
                    "pages": 1,
                    "uploadedBy": "M003"
                }
            ]
        },
        
        # IP-2001: Complete inpatient with discharge → Approve
        "IP-2001": {
            "claim": {
                "id": "IP-2001",
                "claimId": "IP-2001",
                "memberId": "M004",
                "category": "Inpatient",
                "submitDate": "2025-09-04T13:00:00Z",
                "provider": "Regional Medical Center",
                "dosFrom": "2025-08-28T08:00:00Z",
                "dosTo": "2025-08-30T16:00:00Z",
                "amountBilled": 8500.00,
                "region": "US-East",
                "status": "submitted",
                "expectedOutput": "Complete inpatient processing"
            },
            "artifacts": [
                {
                    "id": "F-IP-2001-BILL",
                    "claimId": "IP-2001",
                    "fileId": "F-IP-2001-BILL",
                    "type": "bill",
                    "uri": "blob://storage/claims/IP-2001/bill.pdf",
                    "hash": "pqr678",
                    "pages": 3,
                    "uploadedBy": "M004"
                },
                {
                    "id": "F-IP-2001-DISCHARGE",
                    "claimId": "IP-2001",
                    "fileId": "F-IP-2001-DISCHARGE",
                    "type": "discharge_summary",
                    "uri": "blob://storage/claims/IP-2001/discharge.pdf",
                    "hash": "stu901",
                    "pages": 2,
                    "uploadedBy": "M004"
                }
            ]
        },
        
        # IP-2002: Missing discharge summary → Pend
        "IP-2002": {
            "claim": {
                "id": "IP-2002",
                "claimId": "IP-2002",
                "memberId": "M005",
                "category": "Inpatient", 
                "submitDate": "2025-09-04T14:00:00Z",
                "provider": "Metropolitan Hospital",
                "dosFrom": "2025-08-25T12:00:00Z",
                "dosTo": "2025-08-27T10:00:00Z",
                "amountBilled": 6200.00,
                "region": "US-East",
                "status": "submitted",
                "expectedOutput": "Validation with missing discharge identification"
            },
            "artifacts": [
                {
                    "id": "F-IP-2002-BILL",
                    "claimId": "IP-2002",
                    "fileId": "F-IP-2002-BILL",
                    "type": "bill",
                    "uri": "blob://storage/claims/IP-2002/bill.pdf",
                    "hash": "vwx234",
                    "pages": 2,
                    "uploadedBy": "M005"
                }
                # Note: Missing discharge summary - should trigger pend
            ]
        }
    }
    
    # Rules catalog
    rules_catalog = [
        {
            "id": "OP_DOC_REQUIRED",
            "ruleId": "OP_DOC_REQUIRED",
            "description": "OP must have memo/report/tests and bill",
            "category": "Outpatient",
            "type": "documentation",
            "active": True
        },
        {
            "id": "IP_DISCHARGE_REQUIRED", 
            "ruleId": "IP_DISCHARGE_REQUIRED",
            "description": "IP must include discharge summary with admit/release dates",
            "category": "Inpatient",
            "type": "documentation", 
            "active": True
        },
        {
            "id": "CAP_DENTAL_1000",
            "ruleId": "CAP_DENTAL_1000",
            "description": "Dental capped at 1000",
            "category": "Outpatient",
            "type": "coverage_limit",
            "limit": 1000,
            "active": True
        },
        {
            "id": "EXCLUDED_LASIK",
            "ruleId": "EXCLUDED_LASIK", 
            "description": "LASIK excluded",
            "category": "Outpatient",
            "type": "exclusion",
            "active": True
        }
    ]
    
    return scenarios, rules_catalog

def populate_database():
    """Populate database with test scenarios"""
    try:
        print("🔄 Connecting to Cosmos DB...")
        client = get_cosmos_client()
        database = client.get_database_client(DATABASE_NAME)
        
        print("📦 Creating containers...")
        create_containers_if_not_exist(client)
        
        print("📝 Creating test scenarios...")
        scenarios, rules_catalog = create_test_scenarios()
        
        # Populate claims and artifacts
        claims_container = database.get_container_client("claims")
        artifacts_container = database.get_container_client("artifacts")
        rules_container = database.get_container_client("rules_catalog")
        
        # Insert rules catalog
        print("⚖️ Inserting rules catalog...")
        for rule in rules_catalog:
            try:
                rules_container.upsert_item(rule)
                print(f"  ✅ Inserted rule: {rule['ruleId']}")
            except Exception as e:
                print(f"  ❌ Error inserting rule {rule['ruleId']}: {e}")
        
        # Insert scenarios
        print("🏥 Inserting test scenarios...")
        for scenario_id, scenario_data in scenarios.items():
            try:
                # Insert claim
                claims_container.upsert_item(scenario_data["claim"])
                print(f"  ✅ Inserted claim: {scenario_id}")
                
                # Insert artifacts
                for artifact in scenario_data["artifacts"]:
                    artifacts_container.upsert_item(artifact)
                    print(f"    ✅ Inserted artifact: {artifact['fileId']}")
                    
            except Exception as e:
                print(f"  ❌ Error inserting scenario {scenario_id}: {e}")
        
        print("\n🎉 Test data population completed!")
        print("\n📊 Summary:")
        print(f"  - {len(scenarios)} test claims created")
        print(f"  - {sum(len(s['artifacts']) for s in scenarios.values())} artifacts created")
        print(f"  - {len(rules_catalog)} rules created")
        
        print("\n🧪 Test scenarios available:")
        print("  - OP-1001: Clean outpatient → Should approve")
        print("  - OP-1002: Missing memo → Should pend")
        print("  - OP-1003: Dental over cap → Should approve with limit")
        print("  - IP-2001: Complete inpatient → Should approve") 
        print("  - IP-2002: Missing discharge → Should pend")
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")

if __name__ == "__main__":
    populate_database()
