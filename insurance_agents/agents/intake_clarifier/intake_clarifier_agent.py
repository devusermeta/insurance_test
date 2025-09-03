"""
Intake Clarifier Agent  
Specialized agent for clarifying and validating incoming claims
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from shared.base_agent import BaseInsuranceAgent
from shared.mcp_config import A2A_AGENT_PORTS

class ClaimClarification(BaseModel):
    """Pydantic model for claim clarification requests"""
    claim_id: str
    clarification_type: str
    questions: List[str] = []
    validation_status: str = "pending"

class IntakeClarifierAgent(BaseInsuranceAgent):
    """
    Intake Clarifier Agent - Validates and clarifies incoming claims
    
    Responsibilities:
    - Validate claim information completeness and accuracy
    - Identify missing information or inconsistencies
    - Generate clarification questions for incomplete claims
    - Perform initial fraud detection screening
    - Categorize claims by complexity and priority
    """
    
    def __init__(self):
        super().__init__(
            agent_name="intake_clarifier",
            agent_description="Validates and clarifies incoming insurance claims",
            port=A2A_AGENT_PORTS["intake_clarifier"]
        )
        self.app = FastAPI(title="Intake Clarifier Agent", version="1.0.0")
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes for the agent"""
        
        @self.app.post("/api/clarify_claim")
        async def clarify_claim(claim_data: Dict[str, Any]):
            """Main endpoint to clarify and validate a claim"""
            try:
                claim_id = claim_data.get("claim_id")
                self.logger.info(f"📋 Starting claim clarification for: {claim_id}")
                
                # Perform claim validation and clarification
                clarification_result = await self._perform_claim_clarification(claim_data)
                
                # Log the clarification event
                await self.log_event(
                    "claim_clarified",
                    f"Completed clarification for claim {claim_id}",
                    {
                        "claim_id": claim_id,
                        "validation_status": clarification_result.get("validation_status"),
                        "issues_found": len(clarification_result.get("issues", []))
                    }
                )
                
                return {
                    "status": "success",
                    "claim_id": claim_id,
                    "clarification_result": clarification_result,
                    "agent": self.agent_name
                }
                
            except Exception as e:
                self.logger.error(f"❌ Error clarifying claim: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/status")
        async def get_status():
            """Get agent status"""
            return self.get_status()
        
        @self.app.post("/api/message") 
        async def receive_message(message: Dict[str, Any]):
            """Receive A2A messages from other agents"""
            message_type = message.get("type")
            
            if message_type == "clarify_claim":
                claim_data = message.get("claim_data", {})
                return await self._perform_claim_clarification(claim_data)
            else:
                return await self.process_request(message)
        
        @self.app.post("/api/validate_customer")
        async def validate_customer(customer_data: Dict[str, Any]):
            """Validate customer information"""
            try:
                customer_id = customer_data.get("customer_id")
                self.logger.info(f"👤 Validating customer: {customer_id}")
                
                validation_result = await self._validate_customer_info(customer_data)
                
                return {
                    "status": "success",
                    "customer_id": customer_id,
                    "validation_result": validation_result,
                    "agent": self.agent_name
                }
                
            except Exception as e:
                self.logger.error(f"❌ Error validating customer: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _perform_claim_clarification(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive claim clarification and validation"""
        claim_id = claim_data.get("claim_id")
        self.logger.info(f"🔍 Analyzing claim for clarification: {claim_id}")
        
        clarification_result = {
            "claim_id": claim_id,
            "validation_status": "unknown",
            "issues": [],
            "questions": [],
            "recommendations": [],
            "fraud_risk_score": 0,
            "completeness_score": 0,
            "priority_level": "normal"
        }
        
        try:
            # Step 1: Validate required fields
            self.logger.info("📝 Step 1: Validating required fields")
            required_fields = ["claim_id", "claim_type", "customer_id", "description"]
            missing_fields = []
            
            for field in required_fields:
                if not claim_data.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                clarification_result["issues"].append({
                    "type": "missing_required_fields",
                    "fields": missing_fields,
                    "severity": "high"
                })
                clarification_result["questions"].extend([
                    f"Please provide the missing {field}" for field in missing_fields
                ])
            
            # Step 2: Validate claim description quality
            self.logger.info("📋 Step 2: Analyzing claim description")
            description = claim_data.get("description", "")
            if len(description) < 20:
                clarification_result["issues"].append({
                    "type": "insufficient_description",
                    "severity": "medium",
                    "message": "Claim description is too brief"
                })
                clarification_result["questions"].append(
                    "Can you provide more detailed description of the incident?"
                )
            
            # Step 3: Check for inconsistencies
            self.logger.info("🔍 Step 3: Checking for inconsistencies")
            inconsistencies = await self._detect_inconsistencies(claim_data)
            if inconsistencies:
                clarification_result["issues"].extend(inconsistencies)
                clarification_result["questions"].extend([
                    f"Please clarify: {issue['message']}" for issue in inconsistencies
                ])
            
            # Step 4: Fraud risk assessment
            self.logger.info("🚨 Step 4: Assessing fraud risk")
            fraud_score = await self._assess_fraud_risk(claim_data)
            clarification_result["fraud_risk_score"] = fraud_score
            
            if fraud_score > 70:
                clarification_result["issues"].append({
                    "type": "high_fraud_risk",
                    "severity": "critical",
                    "score": fraud_score,
                    "message": "Claim flagged for potential fraud"
                })
                clarification_result["recommendations"].append("Escalate for manual fraud review")
                clarification_result["priority_level"] = "urgent"
            
            # Step 5: Calculate completeness score
            completeness_score = await self._calculate_completeness_score(claim_data)
            clarification_result["completeness_score"] = completeness_score
            
            # Step 6: Determine validation status
            if missing_fields or fraud_score > 70:
                clarification_result["validation_status"] = "requires_clarification"
            elif completeness_score < 60:
                clarification_result["validation_status"] = "incomplete"
            else:
                clarification_result["validation_status"] = "validated"
                clarification_result["recommendations"].append("Proceed to document analysis")
            
            # Step 7: Set priority level
            if clarification_result["validation_status"] == "requires_clarification":
                clarification_result["priority_level"] = "high"
            elif completeness_score < 40:
                clarification_result["priority_level"] = "high"
            
            # Store clarification results in Cosmos DB
            await self._store_clarification_results(clarification_result)
            
            self.logger.info(f"✅ Clarification completed for {claim_id}: {clarification_result['validation_status']}")
            
            return clarification_result
            
        except Exception as e:
            self.logger.error(f"❌ Error during claim clarification: {str(e)}")
            clarification_result["validation_status"] = "error"
            clarification_result["issues"].append({
                "type": "processing_error",
                "severity": "critical",
                "message": str(e)
            })
            return clarification_result
    
    async def _detect_inconsistencies(self, claim_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect inconsistencies in claim data"""
        inconsistencies = []
        
        # Example: Check date consistency
        claim_type = claim_data.get("claim_type", "").lower()
        description = claim_data.get("description", "").lower()
        
        # Simple rule-based inconsistency detection
        if "auto" in claim_type and "vehicle" not in description and "car" not in description:
            inconsistencies.append({
                "type": "type_description_mismatch",
                "severity": "medium",
                "message": "Claim type indicates auto claim but description doesn't mention vehicle"
            })
        
        if "health" in claim_type and "medical" not in description and "doctor" not in description:
            inconsistencies.append({
                "type": "type_description_mismatch",
                "severity": "medium", 
                "message": "Claim type indicates health claim but description doesn't mention medical details"
            })
        
        return inconsistencies
    
    async def _assess_fraud_risk(self, claim_data: Dict[str, Any]) -> int:
        """Assess fraud risk score (0-100)"""
        risk_score = 0
        
        # Simple fraud risk factors
        description = claim_data.get("description", "").lower()
        
        # High-risk keywords
        high_risk_keywords = ["total loss", "complete damage", "stolen", "fire", "flood"]
        risk_keywords_found = sum(1 for keyword in high_risk_keywords if keyword in description)
        risk_score += risk_keywords_found * 15
        
        # Very brief descriptions are suspicious
        if len(description) < 10:
            risk_score += 20
        
        # Weekend claims (mock logic)
        risk_score += 10  # Mock weekend detection
        
        # Customer history check (mock)
        customer_id = claim_data.get("customer_id")
        if customer_id:
            # Mock previous claims check
            previous_claims = await self.query_cosmos_via_mcp("claims", {"customer_id": customer_id})
            if len(previous_claims) > 3:  # Mock: Multiple recent claims
                risk_score += 25
        
        return min(risk_score, 100)  # Cap at 100
    
    async def _calculate_completeness_score(self, claim_data: Dict[str, Any]) -> int:
        """Calculate claim completeness score (0-100)"""
        score = 0
        total_points = 100
        
        # Required fields (40 points)
        required_fields = ["claim_id", "claim_type", "customer_id", "description"]
        provided_required = sum(1 for field in required_fields if claim_data.get(field))
        score += (provided_required / len(required_fields)) * 40
        
        # Optional but valuable fields (30 points)
        optional_fields = ["documents", "incident_date", "location", "amount"]
        provided_optional = sum(1 for field in optional_fields if claim_data.get(field))
        score += (provided_optional / len(optional_fields)) * 30
        
        # Description quality (20 points)
        description = claim_data.get("description", "")
        if len(description) > 50:
            score += 20
        elif len(description) > 20:
            score += 10
        
        # Documents provided (10 points)
        documents = claim_data.get("documents", [])
        if documents:
            score += min(len(documents) * 5, 10)
        
        return int(score)
    
    async def _validate_customer_info(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate customer information"""
        customer_id = customer_data.get("customer_id")
        
        # Mock customer validation
        validation_result = {
            "customer_id": customer_id,
            "is_valid": True,
            "policy_active": True,
            "verification_status": "verified",
            "issues": []
        }
        
        # Simple validation rules
        if not customer_id:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Missing customer ID")
        
        return validation_result
    
    async def _store_clarification_results(self, clarification_result: Dict[str, Any]):
        """Store clarification results in Cosmos DB"""
        # Add to artifacts collection
        artifact_data = {
            "id": f"clarification_{clarification_result['claim_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "claim_id": clarification_result["claim_id"],
            "artifact_type": "clarification_report",
            "content": clarification_result,
            "created_by": self.agent_name,
            "created_at": datetime.now().isoformat()
        }
        
        await self.query_cosmos_via_mcp("artifacts", {"insert": artifact_data})

# FastAPI app instance
agent = IntakeClarifierAgent()
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
        "intake_clarifier_agent:app",
        host="0.0.0.0",
        port=A2A_AGENT_PORTS["intake_clarifier"],
        reload=True,
        log_level="info"
    )
