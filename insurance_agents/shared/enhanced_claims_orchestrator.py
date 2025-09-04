"""
Enhanced Claims Orchestrator - Full Workflow Implementation
This implements the complete DAG workflow from your vision
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import httpx

from shared.mcp_cosmos_client import (
    MCPCosmosClient,
    read_claims,
    read_artifacts, 
    read_agent_runs,
    read_rules_eval,
    read_extractions,
    write_agent_run,
    write_event,
    write_claim
)
from shared.mcp_config import A2A_AGENT_PORTS

class EnhancedClaimsOrchestrator:
    """
    Enhanced Claims Orchestrator implementing the complete workflow from your vision
    
    Implements the full DAG:
    IntakeClarifier → DocIntelligence (parallel) → CoverageRules → Decision
    """
    
    def __init__(self):
        self.agent_name = "claims_orchestrator"
        self.agent_description = "Main orchestration agent for insurance claims processing"
        self.port = A2A_AGENT_PORTS["claims_orchestrator"] 
        self.logger = self._setup_logging()
        
        # A2A Registry URL (for discovering other agents)
        self.a2a_registry_url = "http://localhost:8000/registry"
        
        # Agent ports for direct communication
        self.agent_ports = {
            "intake_clarifier": A2A_AGENT_PORTS["intake_clarifier"],
            "document_intelligence": A2A_AGENT_PORTS["document_intelligence"], 
            "coverage_rules_engine": A2A_AGENT_PORTS["coverage_rules_engine"]
        }
        
        # Initialize MCP client
        self.cosmos_client = MCPCosmosClient()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup colored logging for the agent"""
        logger = logging.getLogger(f"InsuranceAgent.{self.agent_name}")
        
        formatter = logging.Formatter(
            f"🏥 [{self.agent_name.upper()}] %(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        return logger
    
    async def initialize(self) -> bool:
        """Initialize orchestrator and MCP client"""
        try:
            success = await self.cosmos_client.initialize()
            if success:
                self.logger.info("✅ Enhanced Claims Orchestrator initialized")
            return success
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False
    
    async def execute_claims_processing(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete claims processing workflow from your vision
        
        This implements steps 3-11 from your workflow:
        3. ClaimsAssist triggers agent processing via A2A
        4-11. Execute DAG and return decision
        """
        try:
            claim_id = request.get('claimId')
            expected_output = request.get('expectedOutput', 'Complete claim processing')
            
            self.logger.info(f"🔄 Starting claims processing for {claim_id}")
            
            # Write initial processing event
            await write_event(self.cosmos_client, {
                "ts": datetime.now().isoformat(),
                "claimId": claim_id,
                "actor": self.agent_name,
                "type": "processing_started",
                "details": f"Started processing with expected output: {expected_output}"
            })
            
            # Step 1: Execute IntakeClarifier (T1)
            intake_result = await self._execute_intake_clarifier(claim_id)
            
            if intake_result['status'] == 'fail':
                # Return gaps to employee for resolution
                return {
                    "status": "pend",
                    "claimId": claim_id,
                    "decision": "pend",
                    "gaps": intake_result['gaps'],
                    "message": f"Missing required items: {', '.join(intake_result['gaps'])}",
                    "nextAction": "Please provide the missing documents"
                }
            
            # Step 2: Execute DocIntelligence in parallel (T2) 
            doc_intel_result = await self._execute_document_intelligence(claim_id)
            
            # Step 3: Execute CoverageRules (T3) - needs both intake and doc intel
            if doc_intel_result['status'] in ['pass', 'partial']:
                coverage_result = await self._execute_coverage_rules(claim_id)
            else:
                coverage_result = {
                    "status": "fail",
                    "message": "Document intelligence failed"
                }
            
            # Step 4: Aggregate results and make decision
            final_decision = await self._aggregate_and_decide(
                claim_id, intake_result, doc_intel_result, coverage_result
            )
            
            # Write final decision
            await self._write_final_decision(claim_id, final_decision)
            
            return final_decision
            
        except Exception as e:
            self.logger.error(f"❌ Claims processing error: {str(e)}")
            return {
                "status": "error", 
                "claimId": claim_id,
                "error": str(e)
            }
    
    async def _execute_intake_clarifier(self, claim_id: str) -> Dict[str, Any]:
        """Execute IntakeClarifier agent (T1)"""
        try:
            task_id = f"T1_{claim_id}_{datetime.now().strftime('%H%M%S')}"
            
            self.logger.info(f"📋 Issuing Agent Card T1 for IntakeClarifier")
            
            # Create Agent Card for IntakeClarifier
            agent_card = {
                "taskId": task_id,
                "capability": "intake.validate",
                "requiredInputs": {
                    "claimId": claim_id,
                    "submitDate": datetime.now().isoformat(),
                    "category": "auto-detect",
                    "artifacts": "auto-load"
                },
                "expectedOutputs": ["gap_list", "validation_status", "confidence"],
                "allowedTools": ["cosmos.read", "cosmos.write"],
                "budgets": {"timeSLA": 30},
                "dataScope": ["claims", "artifacts", "agent_runs", "events"],
                "qualityGates": {"minConfidence": 0.7}
            }
            
            # Write agent card issued event
            await write_event(self.cosmos_client, {
                "ts": datetime.now().isoformat(),
                "claimId": claim_id,
                "actor": self.agent_name,
                "type": "card_issued",
                "details": f"Agent Card T1 issued to IntakeClarifier"
            })
            
            # Call IntakeClarifier via A2A
            result = await self._call_agent_via_a2a(
                "intake_clarifier", 
                agent_card
            )
            
            self.logger.info(f"📋 IntakeClarifier T1 completed: {result.get('status')}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing IntakeClarifier: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _execute_document_intelligence(self, claim_id: str) -> Dict[str, Any]:
        """Execute DocIntelligence agent (T2)"""
        try:
            task_id = f"T2_{claim_id}_{datetime.now().strftime('%H%M%S')}"
            
            self.logger.info(f"📄 Issuing Agent Card T2 for DocIntelligence")
            
            # Create Agent Card for DocIntelligence
            agent_card = {
                "taskId": task_id,
                "capability": "doc.extract",
                "requiredInputs": {
                    "claimId": claim_id,
                    "artifacts": "auto-load"
                },
                "expectedOutputs": ["extractions_summary", "evidence_spans", "confidence"],
                "allowedTools": ["cosmos.read", "cosmos.write"],
                "budgets": {"timeSLA": 60},
                "dataScope": ["artifacts", "extractions", "agent_runs", "events"],
                "qualityGates": {"minConfidence": 0.6, "evidenceSpansRequired": True}
            }
            
            # Write agent card issued event
            await write_event(self.cosmos_client, {
                "ts": datetime.now().isoformat(),
                "claimId": claim_id,
                "actor": self.agent_name,
                "type": "card_issued",
                "details": f"Agent Card T2 issued to DocIntelligence"
            })
            
            # Call DocIntelligence via A2A
            result = await self._call_agent_via_a2a(
                "document_intelligence",
                agent_card
            )
            
            self.logger.info(f"📄 DocIntelligence T2 completed: {result.get('status')}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing DocIntelligence: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _execute_coverage_rules(self, claim_id: str) -> Dict[str, Any]:
        """Execute CoverageRules agent (T3)"""
        try:
            task_id = f"T3_{claim_id}_{datetime.now().strftime('%H%M%S')}"
            
            self.logger.info(f"⚖️ Issuing Agent Card T3 for CoverageRules")
            
            # Create Agent Card for CoverageRules
            agent_card = {
                "taskId": task_id,
                "capability": "rules.evaluate", 
                "requiredInputs": {
                    "claimId": claim_id,
                    "extractionsSummary": "auto-load",
                    "rulesReference": "auto-load"
                },
                "expectedOutputs": ["rules_evaluation", "per_line_decisions", "overall_decision"],
                "allowedTools": ["cosmos.read", "cosmos.write"],
                "budgets": {"timeSLA": 45},
                "dataScope": ["claims", "extractions", "rules_eval", "agent_runs", "events"],
                "qualityGates": {"minConfidence": 0.8, "ruleIdsRequired": True}
            }
            
            # Write agent card issued event
            await write_event(self.cosmos_client, {
                "ts": datetime.now().isoformat(),
                "claimId": claim_id,
                "actor": self.agent_name,
                "type": "card_issued",
                "details": f"Agent Card T3 issued to CoverageRules"
            })
            
            # Call CoverageRules via A2A
            result = await self._call_agent_via_a2a(
                "coverage_rules_engine",
                agent_card
            )
            
            self.logger.info(f"⚖️ CoverageRules T3 completed: {result.get('status')}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing CoverageRules: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _aggregate_and_decide(
        self, 
        claim_id: str,
        intake_result: Dict[str, Any],
        doc_intel_result: Dict[str, Any], 
        coverage_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregate results from all agents and make final decision
        
        Implements decision logic from your workflow:
        - Auto-approve when all gates pass
        - Pend when gaps exist
        - Deny when explicit rule violation
        """
        try:
            self.logger.info(f"🔍 Aggregating results for final decision")
            
            # Read all agent runs for this claim
            agent_runs = await read_agent_runs(self.cosmos_client)
            claim_runs = [run for run in agent_runs if run.get('claimId') == claim_id]
            
            # Read rules evaluation
            rules_data = await read_rules_eval(self.cosmos_client, claim_id)
            
            # Read extractions summary
            extractions_data = await read_extractions(self.cosmos_client, claim_id)
            
            # Decision logic
            if coverage_result.get('status') == 'pass' and intake_result.get('status') == 'pass':
                # Check if rules evaluation suggests approval
                overall_decision = None
                confidence = 0.0
                
                if rules_data:
                    overall_rules = [r for r in rules_data if r.get('overallDecision')]
                    if overall_rules:
                        overall_decision = overall_rules[0].get('overallDecision')
                        confidence = overall_rules[0].get('confidence', 0.0)
                
                if overall_decision == 'approve' and confidence >= 0.8:
                    decision = {
                        "status": "success",
                        "claimId": claim_id,
                        "decision": "approve",
                        "confidence": confidence,
                        "message": "Approved - all validation gates passed",
                        "nextAction": "Proceed to pay",
                        "rationale": ["Intake validation passed", "Document extraction successful", "Coverage rules satisfied"],
                        "evidenceLinks": self._build_evidence_links(extractions_data, rules_data)
                    }
                elif overall_decision == 'deny':
                    decision = {
                        "status": "success",
                        "claimId": claim_id,
                        "decision": "deny",
                        "confidence": confidence,
                        "message": "Denied - rule violation detected",
                        "nextAction": "Inform member of denial",
                        "rationale": self._extract_denial_reasons(rules_data),
                        "evidenceLinks": self._build_evidence_links(extractions_data, rules_data)
                    }
                else:
                    decision = {
                        "status": "success",
                        "claimId": claim_id,
                        "decision": "pend",
                        "confidence": confidence,
                        "message": "Pending review - manual intervention required",
                        "nextAction": "Review required",
                        "rationale": ["Low confidence score", "Manual review needed"],
                        "evidenceLinks": self._build_evidence_links(extractions_data, rules_data)
                    }
            else:
                # Some agent failed - pend for missing items
                all_gaps = []
                if intake_result.get('gaps'):
                    all_gaps.extend(intake_result['gaps'])
                if doc_intel_result.get('gaps'):
                    all_gaps.extend(doc_intel_result['gaps'])
                
                decision = {
                    "status": "success",
                    "claimId": claim_id,
                    "decision": "pend",
                    "confidence": 0.3,
                    "gaps": all_gaps,
                    "message": f"Pending - missing items: {', '.join(all_gaps)}",
                    "nextAction": "Provide missing documents",
                    "rationale": ["Validation gaps detected"],
                    "evidenceLinks": []
                }
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error in aggregation: {e}")
            return {
                "status": "error",
                "claimId": claim_id,
                "error": str(e)
            }
    
    async def _write_final_decision(self, claim_id: str, decision: Dict[str, Any]):
        """Write final decision to database"""
        try:
            # Update claim status
            claims_data = await read_claims(self.cosmos_client, claim_id)
            if claims_data:
                claim = claims_data[0]
                claim['status'] = decision.get('decision')
                claim['confidence'] = decision.get('confidence')
                claim['lastUpdated'] = datetime.now().isoformat()
                await write_claim(self.cosmos_client, claim)
            
            # Write decision proposed event
            await write_event(self.cosmos_client, {
                "ts": datetime.now().isoformat(),
                "claimId": claim_id,
                "actor": self.agent_name,
                "type": "decision_proposed",
                "details": f"Decision: {decision.get('decision')} (confidence: {decision.get('confidence', 0):.2f})"
            })
            
            self.logger.info(f"✅ Final decision written: {decision.get('decision')}")
            
        except Exception as e:
            self.logger.error(f"Error writing final decision: {e}")
    
    async def _call_agent_via_a2a(self, agent_name: str, agent_card: Dict[str, Any]) -> Dict[str, Any]:
        """Call another agent via A2A protocol"""
        try:
            port = self.agent_ports.get(agent_name)
            if not port:
                raise ValueError(f"Unknown agent: {agent_name}")
            
            url = f"http://localhost:{port}/execute"
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(url, json=agent_card)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "status": "error", 
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            self.logger.error(f"Error calling {agent_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def _build_evidence_links(self, extractions_data: List[Dict], rules_data: List[Dict]) -> List[Dict[str, str]]:
        """Build evidence links from extraction and rules data"""
        links = []
        
        # Add extraction evidence
        for extraction in extractions_data:
            if extraction.get('evidence'):
                for evidence in extraction['evidence']:
                    links.append({
                        "type": "extraction",
                        "fileId": extraction.get('fileId'),
                        "page": evidence.get('page'),
                        "text": evidence.get('text', '')[:100] + "..."
                    })
        
        # Add rules evidence
        for rule in rules_data:
            if rule.get('ruleIds'):
                for rule_id in rule['ruleIds']:
                    links.append({
                        "type": "rule",
                        "ruleId": rule_id,
                        "rationale": rule.get('rationale', '')
                    })
        
        return links[:5]  # Limit to 5 evidence links
    
    def _extract_denial_reasons(self, rules_data: List[Dict]) -> List[str]:
        """Extract denial reasons from rules evaluation"""
        reasons = []
        
        for rule in rules_data:
            if rule.get('overallDecision') == 'deny':
                if rule.get('reasons'):
                    reasons.extend(rule['reasons'])
                elif rule.get('rationale'):
                    reasons.append(rule['rationale'])
        
        return reasons or ["Rule violation detected"]
