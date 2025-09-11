#!/usr/bin/env python3
"""
Debug script to test Coverage Rules Engine directly
"""

import asyncio
import json
from agents.coverage_rules_engine.coverage_rules_executor_fixed import CoverageRulesExecutorFixed

# Create test case for OP-03
test_request = """
Analyze this claim for coverage determination using LLM classification:

Claim ID: OP-03
Patient: John Smith
Category: Outpatient
Diagnosis: Knee pain
Bill Amount: $100.0

Complete Document Data (including attachments):
Results:
--------------------------------------------------

Document 1:
  id: OP-03
  claimId: OP-03
  status: submitted
  category: Outpatient
  billAmount: 100
  billDate: 2025-08-24
  submittedAt: 2025-08-24T09:00:00Z
  lastUpdatedAt: 2025-09-08T14:00:00Z
  assignedEmployeeName: Emily Chen
  assignedEmployeeID: EMP-7001
  patientName: John Smith
  memberId: M-001
  region: US
  diagnosis: Knee pain
  serviceType: consultation
  memoAttachment: https://captainpstorage1120d503b.blob.core.windows.net/outpatients/OP-03/OP-03_Memo.pdf
  billAttachment: https://captainpstorage1120d503b.blob.core.windows.net/outpatients/OP-03/OP-03_Medical_Bill.pdf
  _rid: R8FHAJ1aACIIAAAAAAAAAA==
  _self: dbs/R8FHAA==/colls/R8FHAJ1aACI=/docs/R8FHAJ1aACIIAAAAAAAAAA==/
  _etag: "0500ea23-0000-0200-0000-68c2a9940000"
  _attachments: attachments/
  _ts: 1757587860

LLM Classification Required:
- Use LLM to classify claim type based on diagnosis (Eye/Dental/General)
- Apply business rules: Eye ≤ $500, Dental ≤ $1000, General ≤ $200000

Document Requirements:
- Outpatient: Must have bills + memo
- Inpatient: Must have bills + memo + discharge summary
"""

async def test_coverage_rules():
    print("🧪 Testing Coverage Rules Engine directly...")
    
    executor = CoverageRulesExecutorFixed()
    
    # Test the claim info extraction
    print("\n🔍 Step 1: Extracting claim info...")
    claim_info = executor._extract_claim_info_from_text(test_request)
    print('Extracted claim info:')
    print(json.dumps(claim_info, indent=2))
    
    # Test the classification
    print("\n🏷️ Step 2: Classifying claim type...")
    diagnosis = claim_info.get('diagnosis', 'Knee pain')
    claim_type = executor._classify_claim_type(diagnosis)
    print(f'Claim classification: {claim_type}')
    
    # Test the document check
    print("\n📄 Step 3: Checking document requirements...")
    doc_check = executor._check_document_requirements(claim_info)
    print(f'Document check result: {doc_check}')
    
    # Test the full evaluation
    print("\n⚖️ Step 4: Full evaluation...")
    evaluation = await executor._evaluate_structured_claim(claim_info)
    print('Full evaluation result:')
    print(json.dumps(evaluation, indent=2))
    
    print(f"\n🎯 FINAL RESULT: {'✅ APPROVED' if evaluation.get('eligible', False) else '❌ DENIED'}")
    if not evaluation.get('eligible', False):
        print(f"   Rejection reason: {evaluation.get('rejection_reason', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(test_coverage_rules())
