"""
Coverage Rules Engine Agent
Specialized agent for evaluating insurance coverage and applying business rules
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from shared.base_agent import BaseInsuranceAgent
from shared.mcp_config import A2A_AGENT_PORTS

class CoverageEvaluationRequest(BaseModel):
    """Pydantic model for coverage evaluation requests"""
    claim_id: str
    customer_id: str
    claim_type: str
    claim_amount: float = 0.0
    incident_date: str = None

class CoverageRulesEngineAgent(BaseInsuranceAgent):
    """
    Coverage Rules Engine Agent - Evaluates coverage and applies business rules
    
    Responsibilities:
    - Evaluate policy coverage for claims
    - Apply deductibles and coverage limits
    - Check policy status and validity
    - Apply business rules and exclusions
    - Calculate claim approval amounts
    - Determine coverage decisions (approve/deny/partial)
    """
    
    def __init__(self):
        super().__init__(
            agent_name="coverage_rules_engine",
            agent_description="Evaluates insurance coverage and applies business rules",
            port=A2A_AGENT_PORTS["coverage_rules_engine"]
        )
        self.app = FastAPI(title="Coverage Rules Engine Agent", version="1.0.0")
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes for the agent"""
        
        @self.app.post("/api/evaluate_coverage")
        async def evaluate_coverage(request: CoverageEvaluationRequest):
            """Main endpoint to evaluate coverage for a claim"""
            try:
                self.logger.info(f"⚖️ Starting coverage evaluation for claim: {request.claim_id}")
                
                # Perform coverage evaluation
                evaluation_result = await self._evaluate_coverage(request)
                
                # Log the evaluation event
                await self.log_event(
                    "coverage_evaluated",
                    f"Completed coverage evaluation for claim {request.claim_id}",
                    {
                        "claim_id": request.claim_id,
                        "customer_id": request.customer_id,
                        "claim_type": request.claim_type,
                        "decision": evaluation_result.get("decision"),
                        "approved_amount": evaluation_result.get("approved_amount")
                    }
                )
                
                return {
                    "status": "success",
                    "claim_id": request.claim_id,
                    "evaluation_result": evaluation_result,
                    "agent": self.agent_name
                }
                
            except Exception as e:
                self.logger.error(f"❌ Error evaluating coverage: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/status")
        async def get_status():
            """Get agent status"""
            return self.get_status()
        
        @self.app.post("/api/message")
        async def receive_message(message: Dict[str, Any]):
            """Receive A2A messages from other agents"""
            message_type = message.get("type")
            
            if message_type == "evaluate_coverage":
                claim_id = message.get("claim_id")
                customer_id = message.get("customer_id")
                claim_type = message.get("claim_type")
                claim_amount = message.get("claim_amount", 0.0)
                incident_date = message.get("incident_date")
                
                request = CoverageEvaluationRequest(
                    claim_id=claim_id,
                    customer_id=customer_id,
                    claim_type=claim_type,
                    claim_amount=claim_amount,
                    incident_date=incident_date
                )
                
                return await self._evaluate_coverage(request)
            else:
                return await self.process_request(message)
        
        @self.app.post("/api/check_policy")
        async def check_policy(request: Dict[str, Any]):
            """Check policy status and details"""
            try:
                customer_id = request.get("customer_id")
                policy_type = request.get("policy_type", "auto")
                
                self.logger.info(f"📋 Checking policy for customer: {customer_id}")
                
                policy_info = await self._check_policy_status(customer_id, policy_type)
                
                return {
                    "status": "success",
                    "customer_id": customer_id,
                    "policy_info": policy_info,
                    "agent": self.agent_name
                }
                
            except Exception as e:
                self.logger.error(f"❌ Error checking policy: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/apply_rules")
        async def apply_rules(request: Dict[str, Any]):
            """Apply specific business rules to a claim"""
            try:
                claim_data = request.get("claim_data", {})
                rule_set = request.get("rule_set", "standard")
                
                self.logger.info(f"📏 Applying {rule_set} rules to claim")
                
                rule_results = await self._apply_business_rules(claim_data, rule_set)
                
                return {
                    "status": "success",
                    "rule_results": rule_results,
                    "agent": self.agent_name
                }
                
            except Exception as e:
                self.logger.error(f"❌ Error applying rules: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _evaluate_coverage(self, request: CoverageEvaluationRequest) -> Dict[str, Any]:
        """Perform comprehensive coverage evaluation"""
        claim_id = request.claim_id
        customer_id = request.customer_id
        claim_type = request.claim_type
        
        self.logger.info(f"🔍 Evaluating coverage for {claim_type} claim {claim_id}")
        
        evaluation_result = {
            "claim_id": claim_id,
            "customer_id": customer_id,
            "claim_type": claim_type,
            "decision": "pending",
            "approved_amount": 0.0,
            "deductible": 0.0,
            "coverage_limit": 0.0,
            "policy_status": "unknown",
            "exclusions_applied": [],
            "rules_applied": [],
            "reasoning": [],
            "confidence_score": 0
        }
        
        try:
            # Step 1: Check policy status
            self.logger.info("📋 Step 1: Checking policy status")
            policy_info = await self._check_policy_status(customer_id, claim_type)
            evaluation_result["policy_status"] = policy_info["status"]
            evaluation_result["coverage_limit"] = policy_info["coverage_limit"]
            evaluation_result["deductible"] = policy_info["deductible"]
            
            if policy_info["status"] != "active":
                evaluation_result["decision"] = "denied"
                evaluation_result["reasoning"].append(f"Policy status: {policy_info['status']}")
                evaluation_result["confidence_score"] = 100
                return evaluation_result
            
            # Step 2: Apply business rules
            self.logger.info("📏 Step 2: Applying business rules")
            rule_results = await self._apply_business_rules({
                "claim_id": claim_id,
                "customer_id": customer_id,
                "claim_type": claim_type,
                "claim_amount": request.claim_amount,
                "incident_date": request.incident_date
            })
            
            evaluation_result["rules_applied"] = rule_results["applied_rules"]
            evaluation_result["exclusions_applied"] = rule_results["exclusions"]
            
            # Step 3: Check exclusions
            self.logger.info("🚫 Step 3: Checking policy exclusions")
            exclusions = await self._check_exclusions(request)
            evaluation_result["exclusions_applied"].extend(exclusions)
            
            if exclusions:
                evaluation_result["decision"] = "denied"
                evaluation_result["reasoning"].append("Claim falls under policy exclusions")
                evaluation_result["confidence_score"] = 95
                return evaluation_result
            
            # Step 4: Calculate approved amount
            self.logger.info("💰 Step 4: Calculating approved amount")
            approved_amount = await self._calculate_approved_amount(
                request.claim_amount,
                evaluation_result["deductible"],
                evaluation_result["coverage_limit"],
                rule_results
            )
            
            evaluation_result["approved_amount"] = approved_amount
            
            # Step 5: Make final decision
            if approved_amount > 0:
                if approved_amount == request.claim_amount - evaluation_result["deductible"]:
                    evaluation_result["decision"] = "approved"
                    evaluation_result["reasoning"].append("Full coverage approved after deductible")
                else:
                    evaluation_result["decision"] = "partial_approval"
                    evaluation_result["reasoning"].append("Partial coverage due to limits or adjustments")
                evaluation_result["confidence_score"] = 90
            else:
                evaluation_result["decision"] = "denied"
                evaluation_result["reasoning"].append("No coverage amount calculated")
                evaluation_result["confidence_score"] = 85
            
            # Step 6: Store evaluation results
            await self._store_evaluation_results(evaluation_result)
            
            self.logger.info(f"✅ Coverage evaluation completed: {evaluation_result['decision']}")
            
            return evaluation_result
            
        except Exception as e:
            self.logger.error(f"❌ Coverage evaluation failed: {str(e)}")
            evaluation_result["decision"] = "error"
            evaluation_result["reasoning"].append(f"Evaluation error: {str(e)}")
            return evaluation_result
    
    async def _check_policy_status(self, customer_id: str, policy_type: str = "auto") -> Dict[str, Any]:
        """Check customer policy status and details"""
        # Mock policy lookup - in real implementation, query policy database
        policy_info = {
            "customer_id": customer_id,
            "policy_type": policy_type,
            "status": "active",
            "effective_date": "2024-01-01",
            "expiration_date": "2025-12-31",
            "coverage_limit": 50000.0,
            "deductible": 500.0,
            "premium_status": "current"
        }
        
        # Simulate some business logic
        if customer_id == "CUST_EXPIRED":
            policy_info["status"] = "expired"
            policy_info["expiration_date"] = "2024-12-31"
        elif customer_id == "CUST_SUSPENDED":
            policy_info["status"] = "suspended"
            policy_info["premium_status"] = "overdue"
        
        # Adjust coverage based on policy type
        if policy_type == "health":
            policy_info["coverage_limit"] = 100000.0
            policy_info["deductible"] = 1000.0
        elif policy_type == "property":
            policy_info["coverage_limit"] = 200000.0
            policy_info["deductible"] = 1000.0
        
        return policy_info
    
    async def _apply_business_rules(self, claim_data: Dict[str, Any], rule_set: str = "standard") -> Dict[str, Any]:
        """Apply business rules to claim data"""
        rule_results = {
            "applied_rules": [],
            "exclusions": [],
            "adjustments": [],
            "flags": []
        }
        
        claim_type = claim_data.get("claim_type", "")
        claim_amount = claim_data.get("claim_amount", 0.0)
        customer_id = claim_data.get("customer_id", "")
        incident_date = claim_data.get("incident_date")
        
        # Rule 1: Maximum claim amount limits
        if claim_amount > 25000:
            rule_results["applied_rules"].append({
                "rule": "high_value_claim_review",
                "description": "Claims over $25,000 require additional review",
                "action": "flag_for_review"
            })
            rule_results["flags"].append("requires_manual_review")
        
        # Rule 2: Recent claim history check
        # Mock: Check if customer has had recent claims
        recent_claims = await self._check_recent_claims(customer_id)
        if len(recent_claims) > 2:
            rule_results["applied_rules"].append({
                "rule": "frequent_claimant",
                "description": "Customer has multiple recent claims",
                "action": "increased_scrutiny"
            })
            rule_results["flags"].append("frequent_claimant")
        
        # Rule 3: Incident date validation
        if incident_date:
            try:
                incident_dt = datetime.fromisoformat(incident_date.replace('Z', '+00:00'))
                days_since_incident = (datetime.now() - incident_dt).days
                
                if days_since_incident > 30:
                    rule_results["applied_rules"].append({
                        "rule": "late_reporting",
                        "description": f"Claim reported {days_since_incident} days after incident",
                        "action": "apply_late_reporting_penalty"
                    })
                    rule_results["adjustments"].append({
                        "type": "late_reporting_penalty",
                        "percentage": 10,
                        "amount": claim_amount * 0.1
                    })
            except:
                pass
        
        # Rule 4: Claim type specific rules
        if claim_type == "auto":
            rule_results["applied_rules"].append({
                "rule": "auto_claim_standard",
                "description": "Standard auto claim processing rules applied",
                "action": "standard_processing"
            })
        elif claim_type == "health":
            rule_results["applied_rules"].append({
                "rule": "health_claim_verification",
                "description": "Health claims require medical provider verification",
                "action": "verify_medical_provider"
            })
            rule_results["flags"].append("requires_medical_verification")
        
        return rule_results
    
    async def _check_exclusions(self, request: CoverageEvaluationRequest) -> List[Dict[str, Any]]:
        """Check if claim falls under policy exclusions"""
        exclusions = []
        
        claim_type = request.claim_type
        incident_date = request.incident_date
        
        # Mock exclusion checks
        if claim_type == "auto":
            # Check for racing exclusion (mock)
            if "racing" in str(request.claim_id).lower():
                exclusions.append({
                    "exclusion": "racing_activities",
                    "description": "Damages from racing activities are excluded",
                    "severity": "full_exclusion"
                })
            
            # Check for commercial use exclusion
            if "commercial" in str(request.claim_id).lower():
                exclusions.append({
                    "exclusion": "commercial_use",
                    "description": "Personal policy does not cover commercial vehicle use",
                    "severity": "full_exclusion"
                })
        
        elif claim_type == "health":
            # Check for pre-existing condition exclusion
            if "pre_existing" in str(request.claim_id).lower():
                exclusions.append({
                    "exclusion": "pre_existing_condition",
                    "description": "Pre-existing conditions excluded from coverage",
                    "severity": "partial_exclusion"
                })
        
        return exclusions
    
    async def _check_recent_claims(self, customer_id: str) -> List[Dict[str, Any]]:
        """Check customer's recent claim history"""
        # Mock recent claims check
        recent_claims = []
        
        # Simulate recent claims for certain customers
        if customer_id == "CUST_FREQUENT":
            recent_claims = [
                {"claim_id": "CLAIM_001", "date": "2025-08-15", "amount": 2500},
                {"claim_id": "CLAIM_002", "date": "2025-07-20", "amount": 1800},
                {"claim_id": "CLAIM_003", "date": "2025-06-10", "amount": 3200}
            ]
        elif customer_id in ["CUST_001", "CUST_002"]:
            recent_claims = [
                {"claim_id": "CLAIM_OLD", "date": "2025-05-01", "amount": 1500}
            ]
        
        return recent_claims
    
    async def _calculate_approved_amount(
        self, 
        claim_amount: float, 
        deductible: float, 
        coverage_limit: float,
        rule_results: Dict[str, Any]
    ) -> float:
        """Calculate the approved claim amount after deductibles, limits, and adjustments"""
        
        # Start with the claim amount
        approved_amount = claim_amount
        
        # Apply deductible
        approved_amount = max(0, approved_amount - deductible)
        
        # Apply coverage limit
        approved_amount = min(approved_amount, coverage_limit)
        
        # Apply rule-based adjustments
        for adjustment in rule_results.get("adjustments", []):
            if adjustment["type"] == "late_reporting_penalty":
                penalty = adjustment["amount"]
                approved_amount = max(0, approved_amount - penalty)
                self.logger.info(f"💰 Applied late reporting penalty: ${penalty}")
        
        # Check for exclusions that would reduce amount
        if rule_results.get("exclusions"):
            for exclusion in rule_results["exclusions"]:
                if exclusion.get("severity") == "full_exclusion":
                    approved_amount = 0
                    break
                elif exclusion.get("severity") == "partial_exclusion":
                    approved_amount *= 0.5  # 50% reduction for partial exclusions
        
        return round(approved_amount, 2)
    
    async def _store_evaluation_results(self, evaluation_result: Dict[str, Any]):
        """Store coverage evaluation results in Cosmos DB"""
        # Store in rules_eval collection
        rules_eval_data = {
            "id": f"coverage_eval_{evaluation_result['claim_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "claim_id": evaluation_result["claim_id"],
            "customer_id": evaluation_result["customer_id"],
            "evaluation_type": "coverage_evaluation",
            "decision": evaluation_result["decision"],
            "approved_amount": evaluation_result["approved_amount"],
            "rules_applied": evaluation_result["rules_applied"],
            "exclusions": evaluation_result["exclusions_applied"],
            "created_by": self.agent_name,
            "created_at": datetime.now().isoformat(),
            "full_evaluation": evaluation_result
        }
        
        await self.query_cosmos_via_mcp("rules_eval", {"insert": rules_eval_data})
        
        # Also store as artifact
        artifact_data = {
            "id": f"coverage_artifact_{evaluation_result['claim_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "claim_id": evaluation_result["claim_id"],
            "artifact_type": "coverage_evaluation",
            "content": evaluation_result,
            "created_by": self.agent_name,
            "created_at": datetime.now().isoformat()
        }
        
        await self.query_cosmos_via_mcp("artifacts", {"insert": artifact_data})

# FastAPI app instance
agent = CoverageRulesEngineAgent()
app = agent.app

@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    await agent.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await agent.shutdown()

if __name__ == "__main__":
    # Run the agent server
    uvicorn.run(
        "coverage_rules_agent:app",
        host="0.0.0.0",
        port=A2A_AGENT_PORTS["coverage_rules_engine"],
        reload=True,
        log_level="info"
    )
