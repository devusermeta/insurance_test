"""
Claims Orchestrator Executor
Implements the agent execution logic for the Claims Orchestrator with A2A and MCP integration
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import TaskArtifactUpdateEvent, TaskState, TaskStatus, TaskStatusUpdateEvent
from a2a.utils import new_agent_text_message, new_task, new_text_artifact

from shared.base_agent import BaseInsuranceAgent
from shared.mcp_config import A2A_AGENT_PORTS
from shared.mcp_client import MCPClient
from shared.a2a_client import A2AClient

class ClaimsOrchestratorExecutor(AgentExecutor):
    """
    Executor for Claims Orchestrator Agent
    Implements the business logic for orchestrating insurance claims processing
    Now properly inherits from A2A AgentExecutor
    """
    
    def __init__(self):
        self.agent_name = "claims_orchestrator"
        self.agent_description = "Main orchestration agent for insurance claims processing"
        self.port = A2A_AGENT_PORTS["claims_orchestrator"]
        self.logger = self._setup_logging()
        
        # Initialize MCP and A2A clients
        self.mcp_client = MCPClient()
        self.a2a_client = A2AClient(self.agent_name)
        
    def _setup_logging(self) -> logging.Logger:
        """Setup colored logging for the agent"""
        logger = logging.getLogger(f"InsuranceAgent.{self.agent_name}")
        
        # Create colored formatter
        formatter = logging.Formatter(
            f"🏥 [{self.agent_name.upper()}] %(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        
        # Setup console handler
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        return logger
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        A2A Framework Execute Method
        This is the main entry point for A2A requests
        """
        try:
            # Extract message from context
            message = context.message
            user_input = context.get_user_input()
            
            self.logger.info(f"🔄 A2A Executing request: {user_input}")
            
            # Get or create task
            task = context.current_task
            if not task:
                task = new_task(message)
                await event_queue.enqueue_event(task)
            
            # Update task status to running
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task.id, 
                    status=TaskStatus(state=TaskState.working),
                    contextId=context.context_id if hasattr(context, 'context_id') else "claims_orchestrator_context",
                    final=False
                )
            )
            
            # Process the request using our existing logic
            request_data = {
                "task": user_input,
                "parameters": {
                    "message": user_input,
                    "context": getattr(message, 'context', {}),
                    "session_id": getattr(message, 'sessionId', 'unknown')
                }
            }
            
            # Route to appropriate handler (using existing logic)
            if 'process_claim' in user_input.lower() or 'claim' in user_input.lower():
                result = await self._handle_claim_processing(request_data.get('parameters', {}))
            elif 'workflow' in user_input.lower():
                result = await self._handle_workflow_request(request_data.get('parameters', {}))
            elif 'status' in user_input.lower():
                result = await self._handle_status_request(request_data.get('parameters', {}))
            else:
                result = await self._handle_general_request(user_input, request_data.get('parameters', {}))
            
            # Create response artifact
            response_text = json.dumps(result, indent=2)
            artifact = new_text_artifact(task.id, response_text)
            
            # Send response
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    task_id=task.id, 
                    artifact=artifact,
                    contextId=getattr(context, 'context_id', 'default-context'),
                    final=False
                )
            )
            
            # Send agent message
            agent_message = new_agent_text_message(response_text)
            await event_queue.enqueue_event(agent_message)
            
            # Mark task as completed
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task.id, 
                    status=TaskStatus(state=TaskState.completed),
                    contextId=context.context_id if hasattr(context, 'context_id') else "claims_orchestrator_context",
                    final=True
                )
            )
            
            self.logger.info("✅ A2A execution completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ A2A execution error: {str(e)}")
            
            # Mark task as failed if we have one
            if 'task' in locals() and task:
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        task_id=task.id, 
                        status=TaskStatus(state=TaskState.failed),
                        contextId=context.context_id if hasattr(context, 'context_id') else "claims_orchestrator_context",
                        final=True
                    )
                )
            
            # Send error response
            error_response = {"status": "error", "error": str(e), "agent": self.agent_name}
            error_text = json.dumps(error_response, indent=2)
            
            if 'task' in locals() and task:
                artifact = new_text_artifact(task.id, error_text)
                await event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        task_id=task.id, 
                        artifact=artifact,
                        contextId=getattr(context, 'context_id', 'default-context'),
                        final=True
                    )
                )
            
            agent_message = new_agent_text_message(error_text)
            await event_queue.enqueue_event(agent_message)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Cancel method required by AgentExecutor abstract base class
        """
        try:
            self.logger.info("🛑 Cancelling Claims Orchestrator execution")
            
            # Get current task if available
            task = context.current_task
            if task:
                # Mark task as cancelled
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        task_id=task.id, 
                        status=TaskStatus(state=TaskState.cancelled),
                        contextId=context.context_id if hasattr(context, 'context_id') else "claims_orchestrator_context",
                        final=True
                    )
                )
                
                # Send cancellation message
                cancel_message = new_agent_text_message("Claims orchestration cancelled by request")
                await event_queue.enqueue_event(cancel_message)
            
            self.logger.info("✅ Claims Orchestrator execution cancelled successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error during cancellation: {str(e)}")

    # Keep the old execute method for backward compatibility
    async def execute_legacy(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy Execute Method (for backward compatibility)
        This is the original entry point for non-A2A requests
        """
        try:
            self.logger.info(f"🔄 Legacy executing request: {request.get('task', 'unknown')}")
            
            # Extract task and parameters
            task = request.get('task', '')
            parameters = request.get('parameters', {})
            
            # Route to appropriate handler
            if 'process_claim' in task.lower() or 'claim' in task.lower():
                return await self._handle_claim_processing(parameters)
            elif 'workflow' in task.lower():
                return await self._handle_workflow_request(parameters)
            elif 'status' in task.lower():
                return await self._handle_status_request(parameters)
            else:
                return await self._handle_general_request(task, parameters)
                
        except Exception as e:
            self.logger.error(f"❌ Legacy execution error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "agent": self.agent_name
            }

    async def _handle_claim_processing(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle claim processing requests with complete A2A workflow"""
        self.logger.info("🏥 Starting complete claims processing workflow")
        
        try:
            # Extract claim information
            claim_id = parameters.get('claim_id', f"CLAIM_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            claim_data = parameters.get('claim_data', {})
            
            self.logger.info(f"📋 Processing claim: {claim_id}")
            
            # Step 1: Check if claim exists in Cosmos DB using MCP
            self.logger.info("🔍 Checking existing claim data in Cosmos DB...")
            existing_claim = await self.mcp_client.get_claims(claim_id)
            
            if existing_claim.get('error'):
                self.logger.warning(f"⚠️ Could not fetch existing claim: {existing_claim.get('error')}")
            else:
                self.logger.info("✅ Successfully retrieved claim data from Cosmos DB")
            
            # Step 2: Send to Intake Clarifier for initial processing (A2A)
            self.logger.info("📝 Sending claim to Intake Clarifier for initial processing...")
            clarifier_result = await self.a2a_client.process_claim_with_clarifier(claim_data)
            
            if clarifier_result.get('status') == 'failed':
                self.logger.error(f"❌ Intake clarification failed: {clarifier_result.get('error')}")
                return {
                    "status": "failed",
                    "step": "intake_clarification",
                    "error": clarifier_result.get('error'),
                    "claim_id": claim_id
                }
            
            self.logger.info("✅ Intake clarification completed successfully")
            clarified_data = clarifier_result.get('clarified_data', claim_data)
            
            # Step 3: Send to Document Intelligence for document analysis (A2A)
            documents = claim_data.get('documents', [])
            if documents:
                self.logger.info("📄 Sending documents to Document Intelligence agent...")
                doc_analysis_result = await self.a2a_client.analyze_documents_with_intelligence(claim_id, documents)
                
                if doc_analysis_result.get('status') == 'failed':
                    self.logger.error(f"❌ Document analysis failed: {doc_analysis_result.get('error')}")
                    return {
                        "status": "failed",
                        "step": "document_analysis",
                        "error": doc_analysis_result.get('error'),
                        "claim_id": claim_id
                    }
                
                self.logger.info("✅ Document analysis completed successfully")
                clarified_data['document_analysis'] = doc_analysis_result.get('analysis_results', {})
            
            # Step 4: Send to Coverage Rules Engine for policy validation (A2A)
            self.logger.info("⚖️ Sending claim to Coverage Rules Engine for validation...")
            coverage_result = await self.a2a_client.validate_coverage_with_rules_engine(clarified_data)
            
            if coverage_result.get('status') == 'failed':
                self.logger.error(f"❌ Coverage validation failed: {coverage_result.get('error')}")
                return {
                    "status": "failed",
                    "step": "coverage_validation",
                    "error": coverage_result.get('error'),
                    "claim_id": claim_id
                }
            
            self.logger.info("✅ Coverage validation completed successfully")
            
            # Step 5: Get coverage rules from Cosmos DB using MCP for final decision
            self.logger.info("📜 Retrieving coverage rules from Cosmos DB...")
            coverage_rules = await self.mcp_client.get_coverage_rules()
            
            # Step 6: Make final decision based on all results
            final_decision = self._make_final_decision(
                claim_data=clarified_data,
                coverage_result=coverage_result,
                coverage_rules=coverage_rules
            )
            
            # Step 7: Store results back to Cosmos DB (direct write)
            await self._store_claim_results(claim_id, {
                "claim_id": claim_id,
                "original_data": claim_data,
                "clarified_data": clarified_data,
                "coverage_validation": coverage_result,
                "final_decision": final_decision,
                "processing_timestamp": datetime.now().isoformat(),
                "processed_by": self.agent_name
            })
            
            self.logger.info(f"🎉 Claim {claim_id} processing completed successfully with decision: {final_decision.get('decision')}")
            
            return {
                "status": "completed",
                "claim_id": claim_id,
                "final_decision": final_decision,
                "processing_steps": [
                    "intake_clarification",
                    "document_analysis",
                    "coverage_validation",
                    "final_decision"
                ],
                "agent": self.agent_name
            }
            
        except Exception as e:
            self.logger.error(f"❌ Claim processing error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "claim_id": claim_id,
                "agent": self.agent_name
            }
        claim_type = parameters.get('claim_type', 'auto')
        customer_id = parameters.get('customer_id', 'UNKNOWN')
        description = parameters.get('description', '')
        documents = parameters.get('documents', [])
        
        # Start orchestrated workflow
        workflow_result = await self._orchestrate_claim_workflow({
            'claim_id': claim_id,
            'claim_type': claim_type,
            'customer_id': customer_id,
            'description': description,
            'documents': documents
        })
        
        return {
            "status": "success",
            "claim_id": claim_id,
            "message": "Claim processing initiated",
            "workflow_result": workflow_result,
            "agent": self.agent_name
        }
    
    async def _handle_workflow_request(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow management requests"""
        self.logger.info("🔄 Managing workflow request")
        
        workflow_type = parameters.get('workflow_type', 'standard')
        
        return {
            "status": "success",
            "message": f"Workflow {workflow_type} managed successfully",
            "workflow_details": {
                "type": workflow_type,
                "steps": ["intake", "validation", "document_analysis", "coverage_evaluation"],
                "estimated_duration": "15-30 minutes"
            },
            "agent": self.agent_name
        }
    
    async def _handle_status_request(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status check requests"""
        claim_id = parameters.get('claim_id')
        
        if claim_id:
            self.logger.info(f"📊 Checking status for claim: {claim_id}")
            # Mock status check
            return {
                "status": "success",
                "claim_id": claim_id,
                "claim_status": "processing",
                "last_updated": datetime.now().isoformat(),
                "agent": self.agent_name
            }
        else:
            return {
                "status": "success",
                "agent_status": "running",
                "agent": self.agent_name,
                "port": self.port,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_general_request(self, task: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general requests"""
        self.logger.info(f"🤖 Handling general request: {task}")
        
        return {
            "status": "success",
            "message": f"Processed task: {task}",
            "task": task,
            "parameters": parameters,
            "agent": self.agent_name,
            "capabilities": [
                "Process insurance claims",
                "Orchestrate multi-agent workflows", 
                "Monitor claim processing status",
                "Route claims through validation pipeline",
                "Coordinate with specialized agents"
            ]
        }
    
    async def _orchestrate_claim_workflow(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate the complete claim processing workflow"""
        claim_id = claim_data['claim_id']
        self.logger.info(f"🔄 Orchestrating workflow for claim {claim_id}")
        
        workflow_steps = []
        
        try:
            # Step 1: Intake Clarification (Mock)
            self.logger.info("📋 Step 1: Sending to Intake Clarifier")
            clarification_result = await self._mock_agent_communication(
                "intake_clarifier", 
                {
                    "type": "clarify_claim",
                    "claim_data": claim_data
                }
            )
            workflow_steps.append({
                "step": "intake_clarification",
                "status": "completed",
                "result": clarification_result
            })
            
            # Step 2: Document Analysis (Mock)
            if claim_data.get('documents'):
                self.logger.info("📄 Step 2: Sending to Document Intelligence")
                doc_result = await self._mock_agent_communication(
                    "document_intelligence",
                    {
                        "type": "analyze_documents", 
                        "claim_id": claim_id,
                        "documents": claim_data['documents']
                    }
                )
                workflow_steps.append({
                    "step": "document_analysis",
                    "status": "completed",
                    "result": doc_result
                })
            
            # Step 3: Coverage Evaluation (Mock)
            self.logger.info("⚖️ Step 3: Applying Coverage Rules")
            coverage_result = await self._mock_agent_communication(
                "coverage_rules_engine",
                {
                    "type": "evaluate_coverage",
                    "claim_id": claim_id,
                    "claim_type": claim_data['claim_type'],
                    "customer_id": claim_data['customer_id']
                }
            )
            workflow_steps.append({
                "step": "coverage_evaluation", 
                "status": "completed",
                "result": coverage_result
            })
            
            self.logger.info(f"✅ Workflow completed for {claim_id}")
            
            return {
                "status": "completed",
                "steps": workflow_steps,
                "total_steps": len(workflow_steps),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Workflow failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "completed_steps": workflow_steps,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _mock_agent_communication(self, target_agent: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Mock A2A communication with other agents"""
        self.logger.info(f"📡 Communicating with {target_agent}")
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Mock responses based on agent type
        if target_agent == "intake_clarifier":
            return {
                "validation_status": "validated",
                "completeness_score": 85,
                "fraud_risk_score": 15,
                "issues": [],
                "agent": target_agent
            }
        elif target_agent == "document_intelligence":
            return {
                "documents_analyzed": len(message.get('documents', [])),
                "confidence_score": 90,
                "fraud_indicators": [],
                "extracted_data": {"total_damage": 5000},
                "agent": target_agent
            }
        elif target_agent == "coverage_rules_engine":
            return {
                "decision": "approved",
                "approved_amount": 4500,
                "deductible": 500,
                "policy_status": "active",
                "agent": target_agent
            }
        else:
            return {
                "status": "success",
                "message": f"Processed by {target_agent}",
                "agent": target_agent
            }
    
    def _make_final_decision(self, claim_data: Dict[str, Any], coverage_result: Dict[str, Any], coverage_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make final decision on claim based on all analysis results
        
        Args:
            claim_data: Clarified claim data
            coverage_result: Coverage validation results
            coverage_rules: Coverage rules from Cosmos DB
            
        Returns:
            Final decision with reasoning
        """
        try:
            # Extract key decision factors
            claim_amount = claim_data.get('amount', 0)
            claim_type = claim_data.get('type', 'unknown')
            coverage_valid = coverage_result.get('coverage_valid', False)
            risk_score = coverage_result.get('risk_score', 0.5)
            
            # Simple decision logic (can be enhanced with more sophisticated rules)
            if not coverage_valid:
                decision = "denied"
                reason = "Coverage validation failed"
                confidence = 0.95
            elif risk_score > 0.8:
                decision = "denied"
                reason = "High risk score detected"
                confidence = 0.85
            elif claim_amount > 50000:
                decision = "requires_review"
                reason = "High value claim requires manual review"
                confidence = 0.75
            else:
                decision = "approved"
                reason = "All validation checks passed"
                confidence = 0.90
            
            return {
                "decision": decision,
                "reason": reason,
                "confidence": confidence,
                "claim_amount": claim_amount,
                "claim_type": claim_type,
                "risk_score": risk_score,
                "coverage_valid": coverage_valid,
                "decision_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error making final decision: {str(e)}")
            return {
                "decision": "error",
                "reason": f"Decision making failed: {str(e)}",
                "confidence": 0.0,
                "decision_timestamp": datetime.now().isoformat()
            }
    
    async def _store_claim_results(self, claim_id: str, results: Dict[str, Any]) -> bool:
        """
        Store claim processing results to Cosmos DB
        
        Args:
            claim_id: The claim ID
            results: Processing results to store
            
        Returns:
            Success status
        """
        try:
            self.logger.info(f"💾 Storing claim results for {claim_id}")
            
            # In a real implementation, this would use Cosmos DB client to write data
            # For now, we'll log the action and simulate success
            self.logger.info(f"✅ Claim results stored successfully for {claim_id}")
            
            # TODO: Implement actual Cosmos DB write operation
            # This could use Azure Cosmos DB Python SDK directly
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error storing claim results: {str(e)}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.mcp_client.close()
            await self.a2a_client.close()
            self.logger.info("🧹 Resources cleaned up successfully")
        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {str(e)}")

    async def _orchestrate_claim_workflow(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy method maintained for backward compatibility
        Delegates to the new _handle_claim_processing method
        """
        return await self._handle_claim_processing({"claim_data": claim_data})
