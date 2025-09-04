"""
Claims Orchestrator Agent
Main orchestration agent that coordinates the entire claims processing workflow
Enhanced with Azure AI Foundry agent routing capabilities
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from shared.base_agent import BaseInsuranceAgent
from shared.mcp_config import A2A_AGENT_PORTS

# Azure AI Foundry imports (optional - will gracefully degrade if not available)
try:
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    from dotenv import load_dotenv
    load_dotenv()
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

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
    Enhanced with Azure AI Foundry agent routing capabilities
    
    Responsibilities:
    - Receive new claims and route them through the proper workflow
    - Coordinate with local A2A agents (Intake Clarifier, Document Intelligence, Rules Engine)
    - Route intelligent tasks to Azure AI Foundry specialist agents when available
    - Monitor claim processing status and escalate when needed
    - Provide status updates to the claims dashboard
    - Dynamically choose between local A2A agents and Azure AI Foundry agents
    """
    
    def __init__(self):
        super().__init__(
            agent_name="claims_orchestrator",
            agent_description="Main orchestration agent for insurance claims processing with Azure AI Foundry integration",
            port=A2A_AGENT_PORTS["claims_orchestrator"]
        )
        self.app = FastAPI(title="Claims Orchestrator Agent", version="2.0.0")
        
        # Initialize Azure AI Foundry connection if available
        self.azure_client = None
        self.azure_agents = {}
        self._init_azure_integration()
        
        self.setup_routes()
    
    def _init_azure_integration(self):
        """Initialize Azure AI Foundry integration if credentials are available"""
        if not AZURE_AVAILABLE:
            self.logger.warning("🔶 Azure AI Foundry SDK not available - will use local A2A agents only")
            return
        
        try:
            # Azure AI Foundry configuration
            subscription_id = os.getenv('AZURE_AI_AGENT_SUBSCRIPTION_ID')
            resource_group = os.getenv('AZURE_AI_AGENT_RESOURCE_GROUP_NAME')
            project_name = os.getenv('AZURE_AI_AGENT_PROJECT_NAME')
            
            if all([subscription_id, resource_group, project_name]):
                conn_str = f"https://eastus.api.azureml.ms/agents/v1.0/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.MachineLearningServices/workspaces/{project_name}"
                
                self.azure_client = AIProjectClient.from_connection_string(
                    conn_str=conn_str,
                    credential=DefaultAzureCredential()
                )
                
                # Load Azure agent IDs
                self.azure_agents = {
                    'claims_orchestrator': os.getenv('CLAIMS_ORCHESTRATOR_AGENT_ID'),
                    'intake_clarifier': os.getenv('INTAKE_CLARIFIER_AGENT_ID'),
                    'document_intelligence': os.getenv('DOCUMENT_INTELLIGENCE_AGENT_ID'),
                    'coverage_rules_engine': os.getenv('COVERAGE_RULES_ENGINE_AGENT_ID')
                }
                
                active_agents = {k: v for k, v in self.azure_agents.items() if v}
                self.logger.info(f"✅ Azure AI Foundry integration enabled - {len(active_agents)} agents available")
                
            else:
                self.logger.warning("🔶 Azure AI Foundry configuration incomplete - using local agents only")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Azure AI Foundry: {str(e)}")
            self.azure_client = None
    
    def setup_routes(self):
        """Setup FastAPI routes for the agent"""
        
        @self.app.post("/api/intelligent_routing")
        async def intelligent_routing(request: Dict[str, Any]):
            """
            NEW: Intelligent routing endpoint that can route to Azure AI Foundry or local A2A agents
            Analyzes the request and chooses the best agent type for the task
            """
            try:
                user_message = request.get("message", "")
                preferred_mode = request.get("mode", "auto")  # auto, azure, local
                
                self.logger.info(f"🧠 Intelligent routing request: {user_message}")
                
                # Analyze request and determine routing
                routing_decision = await self._analyze_intelligent_routing(user_message, preferred_mode)
                
                if routing_decision["use_azure"] and self.azure_client:
                    # Route to Azure AI Foundry agent
                    result = await self._route_to_azure_agent(
                        routing_decision["target_agent"],
                        user_message,
                        request.get("context", {})
                    )
                else:
                    # Route to local A2A agent
                    result = await self._route_to_local_agent(
                        routing_decision["target_agent"],
                        user_message,
                        request.get("context", {})
                    )
                
                return {
                    "status": "success",
                    "routing_decision": routing_decision,
                    "result": result,
                    "agent": self.agent_name
                }
                
            except Exception as e:
                self.logger.error(f"❌ Intelligent routing failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
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
        
        
        @self.app.get("/api/routing_demo")
        async def routing_demo():
            """
            NEW: Demonstration of intelligent routing capabilities
            Shows how the orchestrator chooses between Azure AI Foundry and local A2A agents
            """
            
            demo_scenarios = [
                {
                    "message": "I want to file a new auto insurance claim",
                    "expected": "Simple intake - local A2A agent"
                },
                {
                    "message": "Can you analyze this complex damage photo and explain what you see?",
                    "expected": "Complex analysis - Azure AI Foundry agent"
                },
                {
                    "message": "What does my policy cover for this type of damage?",
                    "expected": "Rules lookup - local A2A agent"
                },
                {
                    "message": "Please intelligently assess this claim for potential fraud indicators",
                    "expected": "Intelligent analysis - Azure AI Foundry agent"
                }
            ]
            
            results = []
            for scenario in demo_scenarios:
                routing = await self._analyze_intelligent_routing(scenario["message"], "auto")
                
                results.append({
                    "scenario": scenario["message"],
                    "expected": scenario["expected"],
                    "routing_decision": routing,
                    "will_use": "Azure AI Foundry" if routing["use_azure"] else "Local A2A",
                    "target_agent": routing["target_agent"],
                    "rationale": routing["rationale"]
                })
            
            return {
                "demo_name": "Intelligent Agent Routing",
                "azure_available": bool(self.azure_client),
                "total_scenarios": len(results),
                "scenarios": results,
                "agent": self.agent_name
            }

        @self.app.get("/api/status")
        async def get_status():
            """Get agent status including Azure AI Foundry integration status"""
            base_status = self.get_status()
            
            # Add Azure integration status
            azure_status = {
                "azure_integration": {
                    "available": bool(self.azure_client),
                    "agents_configured": len([v for v in self.azure_agents.values() if v]) if self.azure_client else 0,
                    "total_agents": len(self.azure_agents) if self.azure_client else 0,
                    "routing_modes": ["local_a2a", "azure_ai_foundry", "intelligent_auto"]
                }
            }
            
            return {**base_status, **azure_status}
        
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
    
    async def _analyze_intelligent_routing(self, user_message: str, preferred_mode: str) -> Dict[str, Any]:
        """
        Analyze user message and determine optimal routing strategy
        Returns routing decision with rationale
        """
        
        user_message_lower = user_message.lower()
        
        # Define capability keywords for each agent type
        agent_capabilities = {
            'intake_clarifier': {
                'keywords': ['file claim', 'new claim', 'submit claim', 'validate', 'fraud', 'intake'],
                'azure_better_for': ['complex validation', 'fraud analysis', 'intelligent extraction'],
                'local_better_for': ['simple validation', 'structured data entry', 'workflow routing']
            },
            'document_intelligence': {
                'keywords': ['photo', 'document', 'analyze', 'extract', 'damage', 'medical', 'image'],
                'azure_better_for': ['image analysis', 'complex extraction', 'AI interpretation'],
                'local_better_for': ['document storage', 'simple text extraction', 'file management']
            },
            'coverage_rules_engine': {
                'keywords': ['coverage', 'policy', 'rules', 'eligible', 'deductible', 'benefits'],
                'azure_better_for': ['complex policy interpretation', 'contextual analysis', 'edge cases'],
                'local_better_for': ['rule application', 'calculations', 'structured decisions']
            }
        }
        
        # Score agents based on keyword matches
        agent_scores = {}
        for agent_type, info in agent_capabilities.items():
            score = sum(1 for keyword in info['keywords'] if keyword in user_message_lower)
            agent_scores[agent_type] = score
        
        # Find best matching agent
        best_agent = max(agent_scores, key=agent_scores.get) if any(agent_scores.values()) else 'claims_orchestrator'
        
        # Determine if Azure or local is better
        use_azure = False
        rationale = []
        
        if preferred_mode == "azure":
            use_azure = True
            rationale.append("User preference: Azure AI Foundry")
        elif preferred_mode == "local":
            use_azure = False
            rationale.append("User preference: Local A2A agents")
        else:  # auto mode
            # Check if Azure is available
            if not self.azure_client or not self.azure_agents.get(best_agent):
                use_azure = False
                rationale.append("Azure AI Foundry not available")
            else:
                # Intelligent decision based on task complexity
                complexity_indicators = [
                    'analyze', 'intelligent', 'complex', 'understand', 'interpret', 
                    'explain', 'summarize', 'recommend', 'assess'
                ]
                
                has_complexity = any(indicator in user_message_lower for indicator in complexity_indicators)
                
                if has_complexity:
                    use_azure = True
                    rationale.append("Complex task detected - Azure AI better suited")
                else:
                    use_azure = False
                    rationale.append("Simple task - local A2A agent sufficient")
        
        return {
            "target_agent": best_agent,
            "use_azure": use_azure,
            "confidence": agent_scores.get(best_agent, 0),
            "rationale": "; ".join(rationale),
            "agent_scores": agent_scores,
            "azure_available": bool(self.azure_client and self.azure_agents.get(best_agent))
        }
    
    async def _route_to_azure_agent(self, agent_type: str, message: str, context: Dict = None) -> Dict[str, Any]:
        """Route task to Azure AI Foundry agent"""
        
        agent_id = self.azure_agents.get(agent_type)
        if not agent_id:
            raise Exception(f"Azure agent {agent_type} not available")
        
        try:
            self.logger.info(f"🎯 Routing to Azure AI Foundry agent: {agent_type} (ID: {agent_id})")
            
            # Create thread and send message
            thread = self.azure_client.agents.create_thread()
            
            enhanced_message = message
            if context:
                enhanced_message = f"Context: {context}\n\nRequest: {message}"
            
            # Add message to thread
            self.azure_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=enhanced_message
            )
            
            # Create run
            run = self.azure_client.agents.create_run(
                thread_id=thread.id,
                agent_id=agent_id
            )
            
            return {
                "success": True,
                "agent_type": f"azure_{agent_type}",
                "thread_id": thread.id,
                "run_id": run.id,
                "message": f"Task routed to Azure AI Foundry {agent_type}",
                "routing_mode": "azure"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Azure routing failed for {agent_type}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "agent_type": agent_type,
                "routing_mode": "azure"
            }
    
    async def _route_to_local_agent(self, agent_type: str, message: str, context: Dict = None) -> Dict[str, Any]:
        """Route task to local A2A agent"""
        
        try:
            self.logger.info(f"🎯 Routing to local A2A agent: {agent_type}")
            
            # Create A2A message
            a2a_message = {
                "type": "process_request",
                "message": message,
                "context": context or {},
                "source": "claims_orchestrator",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to local agent
            result = await self.communicate_with_agent(agent_type, a2a_message)
            
            return {
                "success": True,
                "agent_type": f"local_{agent_type}",
                "result": result,
                "message": f"Task routed to local A2A {agent_type}",
                "routing_mode": "local"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Local routing failed for {agent_type}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "agent_type": agent_type,
                "routing_mode": "local"
            }

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
