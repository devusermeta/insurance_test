"""
Enhanced Intake Clarifier Executor with proper MCP Cosmos DB integration
This demonstrates the exact workflow patterns described in your vision
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from shared.mcp_cosmos_client import (
    MCPCosmosClient, 
    read_claims, 
    read_artifacts,
    write_agent_run,
    write_event
)
from shared.mcp_config import A2A_AGENT_PORTS

class EnhancedIntakeClarifierExecutor:
    """
    Enhanced Intake Clarifier Executor with full MCP Cosmos DB integration
    Implements the exact workflow described in your vision
    """
    
    def __init__(self):
        self.agent_name = "intake_clarifier"
        self.agent_description = "Validates and clarifies incoming insurance claims"
        self.port = A2A_AGENT_PORTS["intake_clarifier"]
        self.logger = self._setup_logging()
        
        # Initialize MCP client
        self.cosmos_client = MCPCosmosClient()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup colored logging for the agent"""
        logger = logging.getLogger(f"InsuranceAgent.{self.agent_name}")
        
        # Create colored formatter
        formatter = logging.Formatter(
            f"📋 [{self.agent_name.upper()}] %(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        
        # Setup console handler
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        return logger
    
    async def initialize(self) -> bool:
        """Initialize the executor and MCP client"""
        try:
            success = await self.cosmos_client.initialize()
            if success:
                self.logger.info("✅ Enhanced Intake Clarifier initialized with MCP")
            return success
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False
    
    async def execute_agent_card(self, agent_card: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an A2A Agent Card following the exact workflow from your vision
        
        This implements step 4B from your workflow:
        B) ClaimsIntakeClarifier (Specialized)
        - MCP reads: claims, artifacts
        - Validate minimal completeness, consistency
        - Write results to agent_runs and events
        """
        try:
            task_id = agent_card.get('taskId')
            claim_id = agent_card.get('requiredInputs', {}).get('claimId')
            
            self.logger.info(f"🔄 Executing Agent Card T{task_id} for claim {claim_id}")
            
            # Write initial agent_run record
            await write_agent_run(self.cosmos_client, {
                "taskId": task_id,
                "claimId": claim_id,
                "agent": self.agent_name,
                "status": "started",
                "start": datetime.now().isoformat(),
                "confidence": 0.0,
                "gaps": []
            })
            
            # Write event: card_issued
            await write_event(self.cosmos_client, {
                "ts": datetime.now().isoformat(),
                "claimId": claim_id,
                "actor": self.agent_name,
                "type": "card_issued",
                "details": f"Agent Card T{task_id} issued"
            })
            
            # Step 1: MCP reads claims and artifacts (as specified in workflow)
            claims_data = await read_claims(self.cosmos_client, claim_id)
            artifacts_data = await read_artifacts(self.cosmos_client, claim_id)
            
            if not claims_data:
                return await self._return_failure(task_id, claim_id, ["claim_not_found"])
            
            claim = claims_data[0]
            category = claim.get('category', '')
            
            # Step 2: Validate minimal completeness and consistency
            validation_result = await self._validate_claim_intake(claim, artifacts_data)
            
            if validation_result['status'] == 'pass':
                # Write success result
                await write_agent_run(self.cosmos_client, {
                    "taskId": task_id,
                    "claimId": claim_id,
                    "agent": self.agent_name,
                    "status": "pass",
                    "confidence": validation_result['confidence'],
                    "gaps": [],
                    "end": datetime.now().isoformat()
                })
                
                await write_event(self.cosmos_client, {
                    "ts": datetime.now().isoformat(),
                    "claimId": claim_id,
                    "actor": self.agent_name,
                    "type": "intake_valid",
                    "details": "Intake validation passed"
                })
                
                return {
                    "status": "pass",
                    "taskId": task_id,
                    "confidence": validation_result['confidence'],
                    "gaps": [],
                    "message": "Intake validation completed successfully"
                }
            
            else:
                # Write failure result with gaps
                await write_agent_run(self.cosmos_client, {
                    "taskId": task_id,
                    "claimId": claim_id,
                    "agent": self.agent_name,
                    "status": "fail",
                    "confidence": validation_result['confidence'],
                    "gaps": validation_result['gaps'],
                    "end": datetime.now().isoformat()
                })
                
                await write_event(self.cosmos_client, {
                    "ts": datetime.now().isoformat(),
                    "claimId": claim_id,
                    "actor": self.agent_name,
                    "type": "gap_found",
                    "details": f"Gaps found: {', '.join(validation_result['gaps'])}"
                })
                
                return {
                    "status": "fail",
                    "taskId": task_id,
                    "confidence": validation_result['confidence'],
                    "gaps": validation_result['gaps'],
                    "message": f"Intake validation failed. Missing: {', '.join(validation_result['gaps'])}"
                }
                
        except Exception as e:
            self.logger.error(f"❌ Execution error: {str(e)}")
            return await self._return_error(task_id, claim_id, str(e))
    
    async def _validate_claim_intake(self, claim: Dict[str, Any], artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate claim intake according to the rules from your workflow:
        
        Outpatient rules:
        - Must have memo/report/tests and bill
        
        Inpatient rules:
        - Must include discharge summary with admit/release dates
        """
        gaps = []
        category = claim.get('category', '').lower()
        
        # Check basic required fields
        required_fields = ['claimId', 'memberId', 'category', 'submitDate', 'provider', 'amountBilled']
        for field in required_fields:
            if not claim.get(field):
                gaps.append(f"missing_{field}")
        
        # Create artifact types map
        artifact_types = {artifact.get('type', '').lower() for artifact in artifacts}
        
        if 'outpatient' in category:
            # OP_DOC_REQUIRED rule: OP must have memo/report/tests and bill
            has_bill = any('bill' in atype for atype in artifact_types)
            has_memo_or_report = any(atype in ['memo', 'report', 'tests'] for atype in artifact_types)
            
            if not has_bill:
                gaps.append("missing_bill")
            if not has_memo_or_report:
                gaps.append("missing_memo_or_report")
                
        elif 'inpatient' in category:
            # IP_DISCHARGE_REQUIRED rule: IP must include discharge summary
            has_discharge = any('discharge' in atype for atype in artifact_types)
            
            if not has_discharge:
                gaps.append("missing_discharge_summary")
        
        # Check for date format consistency
        dos_from = claim.get('dosFrom')
        dos_to = claim.get('dosTo')
        if dos_from and dos_to:
            try:
                from_date = datetime.fromisoformat(dos_from.replace('Z', '+00:00'))
                to_date = datetime.fromisoformat(dos_to.replace('Z', '+00:00'))
                if to_date < from_date:
                    gaps.append("invalid_date_range")
            except:
                gaps.append("invalid_date_format")
        
        # Calculate confidence
        confidence = 0.9 if not gaps else max(0.1, 0.9 - (len(gaps) * 0.2))
        
        return {
            "status": "pass" if not gaps else "fail",
            "confidence": confidence,
            "gaps": gaps
        }
    
    async def _return_failure(self, task_id: str, claim_id: str, gaps: List[str]) -> Dict[str, Any]:
        """Return failure response and update databases"""
        await write_agent_run(self.cosmos_client, {
            "taskId": task_id,
            "claimId": claim_id,
            "agent": self.agent_name,
            "status": "fail",
            "confidence": 0.1,
            "gaps": gaps,
            "end": datetime.now().isoformat()
        })
        
        return {
            "status": "fail",
            "taskId": task_id,
            "confidence": 0.1,
            "gaps": gaps,
            "message": f"Validation failed: {', '.join(gaps)}"
        }
    
    async def _return_error(self, task_id: str, claim_id: str, error: str) -> Dict[str, Any]:
        """Return error response and update databases"""
        await write_agent_run(self.cosmos_client, {
            "taskId": task_id,
            "claimId": claim_id,
            "agent": self.agent_name,
            "status": "error",
            "confidence": 0.0,
            "gaps": [],
            "errors": [error],
            "end": datetime.now().isoformat()
        })
        
        return {
            "status": "error",
            "taskId": task_id,
            "error": error,
            "agent": self.agent_name
        }
