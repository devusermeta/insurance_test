"""
Schema Adapter for Existing Cosmos DB Data
Adapts our insurance agents to work with the existing healthcare claims schema
"""

# Existing Schema Mapping
COSMOS_SCHEMA_MAPPING = {
    "claims": {
        "id_field": "claimId",
        "fields": {
            "claimId": "claim_id",
            "memberId": "customer_id", 
            "category": "claim_type",
            "provider": "provider_name",
            "submitDate": "incident_date",
            "amountBilled": "estimated_amount",
            "status": "status",
            "region": "location"
        }
    },
    "artifacts": {
        "id_field": "fileId",
        "fields": {
            "claimId": "claim_id",
            "fileId": "document_id",
            "type": "document_type", 
            "uri": "document_uri",
            "hash": "document_hash"
        }
    },
    "rules_catalog": {
        "id_field": "ruleId",
        "fields": {
            "ruleId": "rule_id",
            "description": "rule_description",
            "category": "category",
            "type": "rule_type",
            "coverage_percentage": "coverage_percentage",
            "annual_limit": "annual_limit"
        }
    }
}

# Sample existing claims we can test with
EXISTING_TEST_CLAIMS = [
    "OP-1001",  # Outpatient claim with CLN-ALPHA
    "OP-1002",  # Outpatient claim with CLN-BETA  
    "OP-1003"   # Outpatient claim with CLN-DENTAL
]

def adapt_claim_data(cosmos_claim):
    """Convert Cosmos DB claim to our agent format"""
    return {
        "claim_id": cosmos_claim.get("claimId"),
        "customer_id": cosmos_claim.get("memberId"),
        "claim_type": cosmos_claim.get("category", "").lower(),
        "provider_name": cosmos_claim.get("provider"),
        "incident_date": cosmos_claim.get("submitDate"),
        "estimated_amount": cosmos_claim.get("amountBilled", 0),
        "status": cosmos_claim.get("status", "submitted"),
        "location": cosmos_claim.get("region", ""),
        "dos_from": cosmos_claim.get("dosFrom"),
        "dos_to": cosmos_claim.get("dosTo"),
        "created_by": cosmos_claim.get("createdBy"),
        
        # Additional fields for our workflow
        "priority": "normal",
        "documents": []  # Will be populated from artifacts
    }

def adapt_artifacts_data(cosmos_artifacts):
    """Convert Cosmos DB artifacts to our document format"""
    documents = []
    for artifact in cosmos_artifacts:
        documents.append({
            "type": artifact.get("type"),
            "document_id": artifact.get("fileId"),
            "uri": artifact.get("uri"),
            "hash": artifact.get("hash"),
            "status": "uploaded",
            "pages": artifact.get("pages", 1)
        })
    return documents

def adapt_rules_data(cosmos_rules):
    """Convert Cosmos DB rules to our coverage format"""
    rules = []
    for rule in cosmos_rules:
        rules.append({
            "rule_id": rule.get("ruleId"),
            "description": rule.get("description"),
            "category": rule.get("category"),
            "rule_type": rule.get("type"),
            "coverage_percentage": rule.get("coverage_percentage", 100),
            "annual_limit": rule.get("annual_limit"),
            "required_documents": rule.get("required_documents", []),
            "active": rule.get("active", True)
        })
    return rules
