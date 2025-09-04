"""
Direct test of insurance agent logic bypassing A2A framework
"""

import asyncio
import json
import sys
import os

# Add the insurance_agents directory to path
sys.path.append('insurance_agents')

from agents.intake_clarifier.intake_clarifier_executor import IntakeClarifierExecutor
from agents.document_intelligence.document_intelligence_executor import DocumentIntelligenceExecutor
from agents.coverage_rules_engine.coverage_rules_executor import CoverageRulesExecutor
from agents.claims_orchestrator.claims_orchestrator_executor import ClaimsOrchestratorExecutor

async def test_direct_agent_calls():
    """Test agents directly without A2A framework"""
    print("🚀 Testing Insurance Agents Directly")
    print("=" * 50)
    
    # Test claims from your existing data
    test_claims = ["OP-1001", "OP-1002", "OP-1003"]
    
    # Test Intake Clarifier
    print("\n🏥 TESTING INTAKE CLARIFIER (DIRECT)")
    print("-" * 40)
    
    intake_clarifier = IntakeClarifierExecutor()
    
    for claim_id in test_claims:
        request = {
            "task": "validate_claim_intake",
            "parameters": {
                "claim_id": claim_id,
                "expected_output": "validation_with_recommendations"
            }
        }
        
        try:
            result = await intake_clarifier.execute(request)
            print(f"✅ {claim_id}: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"❌ {claim_id}: Error - {e}")
    
    # Test Document Intelligence
    print("\n📄 TESTING DOCUMENT INTELLIGENCE (DIRECT)")
    print("-" * 40)
    
    doc_intelligence = DocumentIntelligenceExecutor()
    
    for claim_id in test_claims:
        request = {
            "task": "extract_document_data",
            "parameters": {
                "claim_id": claim_id,
                "expected_output": "structured_extractions_with_evidence"
            }
        }
        
        try:
            result = await doc_intelligence.execute(request)
            print(f"✅ {claim_id}: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"❌ {claim_id}: Error - {e}")
    
    # Test Coverage Rules Engine
    print("\n⚖️ TESTING COVERAGE RULES ENGINE (DIRECT)")
    print("-" * 40)
    
    coverage_rules = CoverageRulesExecutor()
    
    for claim_id in test_claims:
        request = {
            "task": "evaluate_coverage_rules",
            "parameters": {
                "claim_id": claim_id,
                "expected_output": "rules_evaluation_with_decision"
            }
        }
        
        try:
            result = await coverage_rules.execute(request)
            print(f"✅ {claim_id}: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"❌ {claim_id}: Error - {e}")
    
    # Test Claims Orchestrator
    print("\n🎯 TESTING CLAIMS ORCHESTRATOR (DIRECT)")
    print("-" * 40)
    
    claims_orchestrator = ClaimsOrchestratorExecutor()
    
    request = {
        "task": "process_claim_end_to_end",
        "parameters": {
            "claimId": "OP-1001",
            "expectedOutput": "Complete claim processing with decision"
        }
    }
    
    try:
        result = await claims_orchestrator.execute(request)
        print(f"✅ Full workflow: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Full workflow: Error - {e}")

if __name__ == "__main__":
    asyncio.run(test_direct_agent_calls())
