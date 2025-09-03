"""
Claims Orchestrator Agent
Main orchestration agent that coordinates the entire claims processing workflow
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

class ClaimRequest(BaseModel):
    """Pydantic model for claim processing requests"""
    claim_id: str
    claim_type: str
    customer_id: str
    description: str
    documents: List[str] = []
    priority: str = "normal"

class ClaimsOrchestratorAgent(BaseInsuranceAgent):
    """
    Claims Orchestrator Agent - Coordinates the entire claims processing workflow
    
    Responsibilities:
    - Receive new claims and route them through the proper workflow
    - Coordinate with other agents (Intake Clarifier, Document Intelligence, Rules Engine)
    - Monitor claim processing status and escalate when needed
    - Provide status updates to the claims dashboard
    """
    
    def __init__(self):
        super().__init__(
            agent_name="claims_orchestrator",
            agent_description="Main orchestration agent for insurance claims processing",
            port=A2A_AGENT_PORTS["claims_orchestrator"]
        )
        self.app = FastAPI(title="Claims Orchestrator Agent", version="1.0.0")
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes for the agent"""
        
        @self.app.post("/api/process_claim")
        async def process_claim(claim_request: ClaimRequest):
            """Main endpoint to process a new insurance claim"""
            try:
                self.logger.info(f"🏥 Starting claim processing for claim ID: {claim_request.claim_id}")
                
                # Step 1: Log claim received
                await self.log_event(
                    "claim_received",
                    f"New claim received: {claim_request.claim_id}",
                    {
                        "claim_id": claim_request.claim_id,
                        "claim_type": claim_request.claim_type,
                        "customer_id": claim_request.customer_id,
                        "priority": claim_request.priority
                    }
                )
                
                # Step 2: Store claim in Cosmos DB
                claim_data = {
                    "id": claim_request.claim_id,
                    "claim_type": claim_request.claim_type,
                    "customer_id": claim_request.customer_id,
                    "description": claim_request.description,
                    "documents": claim_request.documents,
                    "priority": claim_request.priority,
                    "status": "processing",
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
                
                await self.query_cosmos_via_mcp("claims", {"insert": claim_data})
                
                # Step 3: Start orchestrated workflow
                workflow_result = await self._orchestrate_claim_workflow(claim_request)
                
                return {
                    "status": "success",
                    "claim_id": claim_request.claim_id,
                    "message": "Claim processing initiated",
                    "workflow_status": workflow_result,
                    "agent": self.agent_name
                }
                
            except Exception as e:
                self.logger.error(f"❌ Error processing claim {claim_request.claim_id}: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/status")
        async def get_status():
            """Get agent status"""
            return self.get_status()
        
        @self.app.post("/api/message")
        async def receive_message(message: Dict[str, Any]):
            """Receive A2A messages from other agents"""
            return await self.process_request(message)
        
        @self.app.get("/api/claims/{claim_id}/status")
        async def get_claim_status(claim_id: str):
            """Get status of a specific claim"""
            try:
                # Query claim from Cosmos DB
                claims = await self.query_cosmos_via_mcp("claims", {"id": claim_id})
                
                if not claims:
                    raise HTTPException(status_code=404, detail="Claim not found")
                
                return {
                    "claim_id": claim_id,
                    "status": claims[0].get("status", "unknown"),
                    "last_updated": claims[0].get("last_updated"),
                    "agent": self.agent_name
                }
                
            except Exception as e:
                self.logger.error(f"❌ Error getting claim status for {claim_id}: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _orchestrate_claim_workflow(self, claim_request: ClaimRequest) -> Dict[str, Any]:
        """Orchestrate the complete claim processing workflow"""
        self.logger.info(f"🔄 Orchestrating workflow for claim {claim_request.claim_id}")
        
        workflow_steps = []
        
        try:
            # Step 1: Send to Intake Clarifier for initial processing
            self.logger.info("📋 Step 1: Sending to Intake Clarifier")
            intake_message = {
                "type": "clarify_claim",
                "claim_id": claim_request.claim_id,
                "claim_data": claim_request.dict(),
                "source": "orchestrator"
            }
            
            intake_result = await self.communicate_with_agent("intake_clarifier", intake_message)
            workflow_steps.append({
                "step": "intake_clarification",
                "status": "completed" if not intake_result.get("error") else "failed",
                "result": intake_result
            })
            
            # Step 2: Send documents to Document Intelligence (if documents exist)
            if claim_request.documents:
                self.logger.info("📄 Step 2: Sending to Document Intelligence")
                doc_message = {
                    "type": "analyze_documents",
                    "claim_id": claim_request.claim_id,
                    "documents": claim_request.documents,
                    "source": "orchestrator"
                }
                
                doc_result = await self.communicate_with_agent("document_intelligence", doc_message)
                workflow_steps.append({
                    "step": "document_analysis",
                    "status": "completed" if not doc_result.get("error") else "failed",
                    "result": doc_result
                })
            
            # Step 3: Apply coverage rules via Rules Engine
            self.logger.info("⚖️ Step 3: Applying Coverage Rules")
            rules_message = {
                "type": "evaluate_coverage",
                "claim_id": claim_request.claim_id,
                "claim_type": claim_request.claim_type,
                "customer_id": claim_request.customer_id,
                "source": "orchestrator"
            }
            
            rules_result = await self.communicate_with_agent("coverage_rules_engine", rules_message)
            workflow_steps.append({
                "step": "rules_evaluation",
                "status": "completed" if not rules_result.get("error") else "failed",
                "result": rules_result
            })
            
            # Step 4: Update claim status based on workflow results
            await self._update_claim_status(claim_request.claim_id, workflow_steps)
            
            # Log workflow completion
            await self.log_event(
                "workflow_completed",
                f"Claim workflow completed for {claim_request.claim_id}",
                {"claim_id": claim_request.claim_id, "workflow_steps": len(workflow_steps)}
            )
            
            return {
                "status": "completed",
                "steps": workflow_steps,
                "total_steps": len(workflow_steps),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Workflow orchestration failed for {claim_request.claim_id}: {str(e)}")
            
            await self.log_event(
                "workflow_failed",
                f"Claim workflow failed for {claim_request.claim_id}: {str(e)}",
                {"claim_id": claim_request.claim_id, "error": str(e)}
            )
            
            return {
                "status": "failed",
                "error": str(e),
                "completed_steps": workflow_steps,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _update_claim_status(self, claim_id: str, workflow_steps: List[Dict[str, Any]]):
        """Update claim status based on workflow results"""
        # Determine overall status
        failed_steps = [step for step in workflow_steps if step["status"] == "failed"]
        
        if failed_steps:
            new_status = "requires_review"
            self.logger.warning(f"⚠️ Claim {claim_id} requires review due to failed steps")
        else:
            new_status = "approved"
            self.logger.info(f"✅ Claim {claim_id} approved automatically")
        
        # Update claim in Cosmos DB
        update_data = {
            "status": new_status,
            "last_updated": datetime.now().isoformat(),
            "workflow_summary": {
                "total_steps": len(workflow_steps),
                "failed_steps": len(failed_steps),
                "completed_at": datetime.now().isoformat()
            }
        }
        
        await self.query_cosmos_via_mcp("claims", {"update": {"id": claim_id, "data": update_data}})

# FastAPI app instance
agent = ClaimsOrchestratorAgent()
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
        "claims_orchestrator_agent:app",
        host="0.0.0.0",
        port=A2A_AGENT_PORTS["claims_orchestrator"],
        reload=True,
        log_level="info"
    )
