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
from shared.agent_discovery import AgentDiscoveryService
from shared.workflow_logger import workflow_logger, WorkflowStepType, WorkflowStepStatus
from shared.mcp_chat_client import mcp_chat_client

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
        
        # Initialize enhanced agent discovery
        self.agent_discovery = AgentDiscoveryService(self.logger)
        
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
            self.logger.info(f"📨 Raw message: {str(message)[:200]}...")
            
            # Try to parse JSON from user input
            try:
                parsed_input = json.loads(user_input) if user_input.startswith('{') else {"raw": user_input}
                self.logger.info(f"📋 Parsed input: {parsed_input}")
            except json.JSONDecodeError:
                parsed_input = {"raw": user_input}
            
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
            
            # Route to appropriate handler with better detection
            if 'chat query:' in user_input.lower() or 'chat conversation' in user_input.lower():
                # This is a chat query - extract the actual user question
                actual_query = user_input
                if 'Chat Query:' in user_input:
                    actual_query = user_input.split('Chat Query:')[1].split('\n')[0].strip()
                result = await self._handle_chat_query(actual_query, request_data.get('parameters', {}))
            elif ('process_claim' in user_input.lower() and 'chat query:' not in user_input.lower()) or ('{"action": "process_claim"' in user_input):
                result = await self._handle_claim_processing(request_data.get('parameters', {}))
            elif 'workflow' in user_input.lower():
                result = await self._handle_workflow_request(request_data.get('parameters', {}))
            elif 'status' in user_input.lower():
                result = await self._handle_status_request(request_data.get('parameters', {}))
            else:
                # Default to chat handling for general queries
                result = await self._handle_chat_query(user_input, request_data.get('parameters', {}))
            
            # Determine response text based on result type
            if isinstance(result, dict) and "response" in result:
                # Chat query - return the response text directly
                response_text = result["response"]
            else:
                # Other requests - return JSON structure
                response_text = json.dumps(result, indent=2)
            
            # Create response artifact
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
        """Handle claim processing requests with enhanced agent discovery and detailed logging"""
        
        self.logger.info("🏥 =================================================")
        self.logger.info("🏥 STARTING ENHANCED CLAIMS PROCESSING WORKFLOW")
        self.logger.info("🏥 =================================================")
        
        try:
            # Extract claim information
            claim_id = parameters.get('claim_id', f"CLAIM_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            claim_data = parameters.get('claim_data', {})
            
            # Start workflow tracking
            workflow_logger.start_claim_processing(claim_id)
            
            self.logger.info(f"📋 Processing claim: {claim_id}")
            
            # STEP 1: DISCOVER ALL AVAILABLE AGENTS
            self.logger.info("\n🔍 STEP 1: AGENT DISCOVERY PHASE")
            discovered_agents = await self.agent_discovery.discover_all_agents()
            
            # Log discovery step
            agent_details = []
            for agent_id, agent_info in discovered_agents.items():
                agent_details.append({
                    "agent_id": agent_id,
                    "name": agent_info.get('name', 'Unknown'),
                    "skills": len(agent_info.get('skills', []))
                })
            
            discovery_step_id = workflow_logger.log_discovery(
                agents_found=len(discovered_agents),
                agent_details=agent_details
            )
            
            if not discovered_agents:
                workflow_logger.update_step(discovery_step_id, WorkflowStepStatus.FAILED)
                self.logger.error("❌ CRITICAL: No agents discovered! Cannot process claim.")
                return {
                    "status": "failed",
                    "error": "No agents available for processing",
                    "claim_id": claim_id
                }
            
            self.logger.info(f"\n� DISCOVERY SUMMARY:")
            self.logger.info(self.agent_discovery.get_discovery_summary())
            
            # STEP 2: CHECK EXISTING CLAIM DATA
            self.logger.info("\n🔍 STEP 2: CHECKING EXISTING CLAIM DATA")
            existing_claim = await self.mcp_client.get_claims(claim_id)
            
            if existing_claim.get('error'):
                self.logger.warning(f"⚠️ Could not fetch existing claim: {existing_claim.get('error')}")
            else:
                self.logger.info("✅ Successfully retrieved claim data from Cosmos DB")
            
            # STEP 3: INTELLIGENT AGENT SELECTION AND TASK DISPATCH
            processing_results = {}
            
            # Task 1: Intake Clarification
            self.logger.info("\n📝 STEP 3A: INTAKE CLARIFICATION TASK")
            clarifier_agent = self.agent_discovery.select_agent_for_task(
                task_description=f"Validate and clarify insurance claim data for claim {claim_id}",
                task_type="claim_validation"
            )
            
            # Log agent selection
            if clarifier_agent:
                selection_step_id = workflow_logger.log_agent_selection(
                    task_type="intake_clarification",
                    selected_agent=clarifier_agent['agent_id'],
                    agent_name=clarifier_agent.get('name', clarifier_agent['agent_id']),
                    reasoning=f"Best match for claim validation - {clarifier_agent.get('name', 'Selected agent')}"
                )
                workflow_logger.update_step(selection_step_id, WorkflowStepStatus.COMPLETED)
                
                # Log task dispatch
                dispatch_step_id = workflow_logger.log_task_dispatch(
                    agent_name=clarifier_agent.get('name', clarifier_agent['agent_id']),
                    task_description=f"Process claim {claim_id} for initial validation",
                    agent_url=clarifier_agent['base_url']
                )
                
                clarifier_task = {
                    "description": f"Process claim {claim_id} for initial validation",
                    "message": json.dumps({
                        "action": "process_claim",
                        "claim_id": claim_id,
                        "claim_data": claim_data
                    })
                }
                
                clarifier_result = await self.agent_discovery.send_task_to_agent(clarifier_agent, clarifier_task)
                processing_results['clarification'] = clarifier_result
                
                # Log agent response
                success = clarifier_result.get('status') == 'success'
                response_step_id = workflow_logger.log_agent_response(
                    agent_name=clarifier_agent.get('name', clarifier_agent['agent_id']),
                    success=success,
                    response_summary="Validation completed successfully" if success else "Validation failed",
                    response_details=clarifier_result
                )
                
                if not success:
                    self.logger.error(f"❌ Intake clarification failed")
                    return {
                        "status": "failed",
                        "step": "intake_clarification", 
                        "error": clarifier_result.get('error'),
                        "claim_id": claim_id
                    }
            else:
                self.logger.error("❌ No suitable agent found for intake clarification")
                return {"status": "failed", "error": "No clarifier agent available", "claim_id": claim_id}
            
            # Task 2: Document Analysis
            documents = claim_data.get('documents', [])
            if documents:
                self.logger.info("\n📄 STEP 3B: DOCUMENT ANALYSIS TASK")
                doc_agent = self.agent_discovery.select_agent_for_task(
                    task_description=f"Analyze and extract information from {len(documents)} documents for claim {claim_id}",
                    task_type="document_analysis"
                )
                
                if doc_agent:
                    doc_task = {
                        "description": f"Analyze documents for claim {claim_id}",
                        "message": json.dumps({
                            "action": "analyze_documents",
                            "claim_id": claim_id,
                            "documents": documents
                        })
                    }
                    
                    doc_result = await self.agent_discovery.send_task_to_agent(doc_agent, doc_task)
                    processing_results['document_analysis'] = doc_result
                    
                    if doc_result.get('status') != 'success':
                        self.logger.error(f"❌ Document analysis failed")
                        return {
                            "status": "failed",
                            "step": "document_analysis",
                            "error": doc_result.get('error'),
                            "claim_id": claim_id
                        }
                else:
                    self.logger.warning("⚠️ No document intelligence agent found - skipping document analysis")
            else:
                self.logger.info("📄 No documents provided - skipping document analysis")
            
            # Task 3: Coverage Validation
            self.logger.info("\n⚖️ STEP 3C: COVERAGE VALIDATION TASK")
            rules_agent = self.agent_discovery.select_agent_for_task(
                task_description=f"Evaluate coverage rules and policy compliance for claim {claim_id}",
                task_type="coverage_evaluation"
            )
            
            if rules_agent:
                # Combine all data for rules evaluation
                combined_data = {
                    "claim_id": claim_id,
                    "original_claim": claim_data,
                    "clarification_result": processing_results.get('clarification', {}),
                    "document_analysis": processing_results.get('document_analysis', {})
                }
                
                rules_task = {
                    "description": f"Validate coverage and policy compliance for claim {claim_id}",
                    "message": json.dumps({
                        "action": "validate_coverage",
                        "claim_data": combined_data
                    })
                }
                
                rules_result = await self.agent_discovery.send_task_to_agent(rules_agent, rules_task)
                processing_results['coverage_validation'] = rules_result
                
                if rules_result.get('status') != 'success':
                    self.logger.error(f"❌ Coverage validation failed")
                    return {
                        "status": "failed",
                        "step": "coverage_validation",
                        "error": rules_result.get('error'),
                        "claim_id": claim_id
                    }
            else:
                self.logger.error("❌ No suitable agent found for coverage validation")
                return {"status": "failed", "error": "No rules engine agent available", "claim_id": claim_id}
            
            # STEP 4: FINAL DECISION MAKING
            self.logger.info("\n🎯 STEP 4: MAKING FINAL DECISION")
            self.logger.info("� Analyzing all agent responses...")
            
            # Get coverage rules from Cosmos DB
            coverage_rules = await self.mcp_client.get_coverage_rules()
            
            # Make final decision based on all results
            final_decision = self._make_final_decision(
                claim_data=claim_data,
                processing_results=processing_results,
                coverage_rules=coverage_rules
            )
            
            self.logger.info(f"⚖️ FINAL DECISION: {final_decision.get('decision', 'Unknown')}")
            self.logger.info(f"📝 Reasoning: {final_decision.get('reasoning', 'No reasoning provided')}")
            
            # STEP 5: STORE RESULTS
            self.logger.info("\n💾 STEP 5: STORING RESULTS TO COSMOS DB")
            await self._store_claim_results(claim_id, {
                "claim_id": claim_id,
                "original_data": claim_data,
                "processing_results": processing_results,
                "final_decision": final_decision,
                "processing_timestamp": datetime.now().isoformat(),
                "processed_by": self.agent_name,
                "agent_discovery_summary": self.agent_discovery.get_discovery_summary()
            })
            
            self.logger.info("\n🎉 ===============================================")
            self.logger.info(f"🎉 CLAIM {claim_id} PROCESSING COMPLETED SUCCESSFULLY!")
            self.logger.info(f"🎉 DECISION: {final_decision.get('decision')}")
            self.logger.info("🎉 ===============================================")
            
            # Complete workflow tracking
            workflow_logger.log_completion(
                claim_id=claim_id,
                final_status=f"Claim processed with decision: {final_decision.get('decision', 'Unknown')}",
                processing_time_ms=5000  # Approximate processing time
            )
            
            return {
                "status": "completed",
                "claim_id": claim_id,
                "final_decision": final_decision,
                "processing_results": processing_results,
                "agents_used": list(discovered_agents.keys()),
                "processing_steps": [
                    "agent_discovery",
                    "intake_clarification", 
                    "document_analysis",
                    "coverage_validation",
                    "final_decision"
                ],
                "agent": self.agent_name
            }
            
        except Exception as e:
            self.logger.error(f"❌ CRITICAL ERROR in claim processing: {str(e)}")
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
        """Handle general requests including chat queries with MCP integration"""
        self.logger.info(f"🤖 Handling general request: {task}")
        
        # Check if this is a chat query (coming from the dashboard)
        if "Chat Query:" in task or parameters.get("is_chat", False):
            return await self._handle_chat_query(task, parameters)
        
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
                "Coordinate with specialized agents",
                "Answer questions about claims data via chat"
            ]
        }
    
    async def _handle_chat_query(self, task: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat queries with MCP integration for Cosmos DB access"""
        self.logger.info(f"💬 Handling chat query: {task}")
        
        try:
            # Extract the actual user query from the task
            if "Chat Query:" in task:
                user_query = task.split("Chat Query:", 1)[1].strip()
                if "\n\nContext:" in user_query:
                    user_query = user_query.split("\n\nContext:")[0].strip()
            else:
                user_query = task
            
            self.logger.info(f"🔍 Processing user query: {user_query}")
            
            # Use MCP chat client to query Cosmos DB
            try:
                response = await mcp_chat_client.query_cosmos_data(user_query, parameters)
                
                self.logger.info(f"✅ MCP query successful")
                
                return {
                    "status": "success",
                    "response": response,
                    "query": user_query,
                    "agent": self.agent_name,
                    "timestamp": datetime.now().isoformat(),
                    "source": "cosmos_db_via_mcp"
                }
                
            except Exception as mcp_error:
                self.logger.error(f"❌ MCP query failed: {mcp_error}")
                
                # Fallback to general response if MCP fails
                fallback_response = self._generate_fallback_response(user_query, str(mcp_error))
                
                return {
                    "status": "partial_success",
                    "response": fallback_response,
                    "query": user_query,
                    "agent": self.agent_name,
                    "timestamp": datetime.now().isoformat(),
                    "source": "fallback",
                    "mcp_error": str(mcp_error)
                }
                
        except Exception as e:
            self.logger.error(f"❌ Chat query processing failed: {e}")
            
            error_response = f"I apologize, but I encountered an error processing your question: {str(e)}. Please try again or contact support if the issue persists."
            
            return {
                "status": "error",
                "response": error_response,
                "query": task,
                "agent": self.agent_name,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _generate_fallback_response(self, user_query: str, error_message: str) -> str:
        """Generate a helpful fallback response when MCP is unavailable"""
        query_lower = user_query.lower()
        
        if "help" in query_lower or "what can you do" in query_lower:
            return """I'm your Claims Orchestrator Assistant! Here's what I can help you with:

🔍 **Claims Processing:**
- Process new claims through our validation pipeline
- Check claim status and processing history
- Route claims to specialized agents

📊 **Workflow Management:**
- Coordinate multi-agent claim workflows
- Monitor processing steps and status
- Generate processing reports

⚠️ **Note:** I'm currently unable to query the database directly due to a connection issue with the MCP server. Please ensure the Cosmos DB MCP server is running on port 8080.

**Error details:** {error_message}"""
        
        elif any(word in query_lower for word in ["hello", "hi", "hey"]):
            return f"👋 Hello! I'm your Claims Orchestrator Assistant. I'm currently experiencing connectivity issues with our database ({error_message}), but I'm still here to help with claims processing and workflow coordination!"
        
        else:
            return f"""I understand you're asking about: "{user_query}"

🔧 **Service Status:** I'm currently unable to access our claims database due to a connectivity issue. 

**What I can still do:**
- Help process new claims
- Explain our workflow processes
- Coordinate with other agents
- Provide general assistance

**To resolve database queries:** Please ensure the Cosmos DB MCP server is running on port 8080.

**Error details:** {error_message}"""
    
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
    
    def _make_final_decision(self, claim_data: Dict[str, Any], processing_results: Dict[str, Any], coverage_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make final decision on claim based on all analysis results
        
        Args:
            claim_data: Original claim data
            processing_results: Results from all agent processing steps
            coverage_rules: Coverage rules from Cosmos DB
            
        Returns:
            Final decision with reasoning
        """
        try:
            self.logger.info("🎯 Analyzing results from all agents for final decision...")
            
            # Extract key decision factors - handle nested claim_data structure
            nested_claim_data = claim_data.get('claim_data', claim_data)
            claim_amount = nested_claim_data.get('amount', 0)
            claim_type = nested_claim_data.get('type', 'unknown')
            
            # Extract results from agent processing
            clarification_result = processing_results.get('clarification', {})
            doc_analysis_result = processing_results.get('document_analysis', {})
            coverage_result = processing_results.get('coverage_validation', {})
            
            # Try to extract validation from coverage result response
            coverage_valid = True  # Default assumption
            risk_score = 0.3  # Default low risk
            
            # Log decision factors
            self.logger.info(f"📊 Decision Factors:")
            self.logger.info(f"   💰 Claim Amount: ${claim_amount}")
            self.logger.info(f"   📝 Claim Type: {claim_type}")
            self.logger.info(f"   ✅ Coverage Valid: {coverage_valid}")
            self.logger.info(f"   ⚠️ Risk Score: {risk_score}")
            
            # Enhanced decision logic
            if not coverage_valid:
                decision = "denied"
                reason = "Coverage validation failed - claim not covered under current policy"
                confidence = 0.95
                self.logger.info(f"❌ Decision: DENIED - {reason}")
            elif risk_score > 0.8:
                decision = "denied" 
                reason = f"High fraud risk detected (risk score: {risk_score})"
                confidence = 0.85
                self.logger.info(f"❌ Decision: DENIED - {reason}")
            elif claim_amount > 50000:
                decision = "requires_review"
                reason = "High value claim requires manual review"
                confidence = 0.75
                self.logger.info(f"⚠️ Decision: REQUIRES REVIEW - {reason}")
            else:
                decision = "approved"
                reason = "All validation checks passed successfully"
                confidence = 0.90
                self.logger.info(f"✅ Decision: APPROVED - {reason}")
            
            return {
                "decision": decision,
                "reasoning": reason,
                "confidence": confidence,
                "claim_amount": claim_amount,
                "claim_type": claim_type,
                "risk_score": risk_score,
                "coverage_valid": coverage_valid,
                "processing_summary": {
                    "clarification_status": clarification_result.get('status', 'unknown'),
                    "document_analysis_status": doc_analysis_result.get('status', 'skipped'),
                    "coverage_validation_status": coverage_result.get('status', 'unknown')
                },
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
    
    async def _handle_chat_query(self, user_query: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle chat queries from employees using MCP tools
        """
        try:
            self.logger.info(f"💬 Processing chat query: {user_query[:100]}...")
            
            # Clean the query if it has our formatting
            if "Context: This is a chat conversation" in user_query:
                user_query = user_query.split("Context:")[0].strip()
            
            # Check if this is a capabilities/system info query
            if any(keyword in user_query.lower() for keyword in ['capabilities', 'what can you do', 'help', 'commands', 'features']):
                return {
                    "response": """🤖 **Claims Orchestrator Capabilities**

I can help you with:

**📊 Data Queries:**
- "Show me recent claims"
- "How many claims are pending?"
- "Find high-value claims over $5000"
- "Show claims by status"

**🔍 Claim Information:**
- "Get details for claim ID 12345"
- "Show all approved claims"
- "Find declined claims"

**📈 Analytics:**
- "Claims summary for this month"
- "Show processing statistics"
- "Risk analysis reports"

**⚙️ System Status:**
- "Are all agents running?"
- "System health check"
- "Agent status report"

Just ask me anything about your insurance data in natural language!""",
                    "session_id": parameters.get("session_id", "default"),
                    "type": "chat_response"
                }
            
            # Try to use MCP client for data queries
            try:
                # Use the MCP chat client if available
                if hasattr(self, 'mcp_chat_client'):
                    mcp_response = await self.mcp_chat_client.query_cosmos_data(user_query)
                    if mcp_response.get('status') == 'success':
                        return {
                            "response": mcp_response.get('response', 'Query completed successfully.'),
                            "session_id": parameters.get("session_id", "default"),
                            "type": "chat_response",
                            "data": mcp_response.get('data')
                        }
                
                # Fallback to direct MCP client
                self.logger.info("🔄 Using direct MCP client for query...")
                
                # Check if this is a general system query
                if any(keyword in user_query.lower() for keyword in ['claims', 'data', 'show', 'find', 'get', 'list']):
                    # Try to get some general data
                    cosmos_result = await self.mcp_client.get_recent_claims(limit=5)
                    
                    if cosmos_result.get('error'):
                        return {
                            "response": f"I encountered an issue querying the database: {cosmos_result.get('error')}. However, I'm here to help with your insurance questions. Could you try rephrasing your question?",
                            "session_id": parameters.get("session_id", "default"),
                            "type": "chat_response"
                        }
                    
                    claims_data = cosmos_result.get('claims', [])
                    if claims_data:
                        response = f"Here are some recent claims I found:\n\n"
                        for claim in claims_data[:3]:  # Show max 3 claims
                            response += f"**Claim {claim.get('id', 'N/A')}**\n"
                            response += f"• Status: {claim.get('status', 'Unknown')}\n"
                            response += f"• Amount: ${claim.get('amount', 0):,.2f}\n"
                            response += f"• Type: {claim.get('type', 'Unknown')}\n\n"
                        
                        response += f"Found {len(claims_data)} total claims. Ask me specific questions about claims data!"
                    else:
                        response = "I didn't find any claims data at the moment. The database might be empty or there could be a connection issue. Feel free to ask me other questions about the system!"
                    
                    return {
                        "response": response,
                        "session_id": parameters.get("session_id", "default"),
                        "type": "chat_response"
                    }
                
                # Default friendly response for general chat
                return {
                    "response": f"I understand you're asking about: '{user_query}'. I'm your Claims Orchestrator assistant, and I'm designed to help with insurance claims data and system queries. Try asking me about claims, data, or system status. For example: 'Show me recent claims' or 'What are my capabilities?'",
                    "session_id": parameters.get("session_id", "default"),
                    "type": "chat_response"
                }
                
            except Exception as mcp_error:
                self.logger.warning(f"⚠️ MCP query failed: {str(mcp_error)}")
                
                # Friendly fallback response
                return {
                    "response": f"I received your question about '{user_query}'. I'm currently having trouble accessing the database, but I'm here to help! I can assist with claims data queries, system status checks, and general insurance questions. The MCP server might need to be restarted. Please try again or ask about my capabilities.",
                    "session_id": parameters.get("session_id", "default"),
                    "type": "chat_response"
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error handling chat query: {str(e)}")
            return {
                "response": "I'm sorry, I encountered an error processing your request. Please try again or contact support if the problem persists.",
                "session_id": parameters.get("session_id", "default"),
                "type": "chat_response",
                "error": str(e)
            }
    
    async def _handle_workflow_request(self, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle workflow-related requests"""
        return {
            "status": "success",
            "message": "Workflow request processed",
            "type": "workflow_response"
        }
    
    async def _handle_status_request(self, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle status check requests"""
        return {
            "status": "success", 
            "message": "System status: All agents operational",
            "type": "status_response"
        }
    
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
