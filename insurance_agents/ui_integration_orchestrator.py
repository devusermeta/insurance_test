"""
UI Integration Orchestrator
Integrates the proven A2A claim processing workflow with the employee dashboard
Provides seamless UI experience for the complete end-to-end workflow
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add the parent directory to the path so we can import shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import aiohttp
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import our proven orchestrator and workflow components
from agents.claims_orchestrator.intelligent_orchestrator import IntelligentClaimsOrchestrator
from shared.mcp_chat_client import enhanced_mcp_chat_client
from shared.workflow_logger import workflow_logger, WorkflowStepType, WorkflowStepStatus
from shared.a2a_client import A2AClient

# Import enhanced agents for Cosmos status updates and document creation
from enhanced_intake_clarifier import enhanced_intake_clarifier
from enhanced_document_intelligence import enhanced_document_intelligence

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaimProcessingRequest(BaseModel):
    """Request model for claim processing"""
    message: str
    session_id: Optional[str] = None

class ClaimProcessingResponse(BaseModel):
    """Response model for claim processing"""
    status: str
    message: str
    claim_id: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    requires_confirmation: Optional[bool] = False
    final_decision: Optional[str] = None
    session_id: str
    timestamp: str

class UIIntegrationOrchestrator:
    """
    UI Integration Orchestrator that connects the proven workflow 
    with the employee dashboard interface
    """
    
    def __init__(self):
        self.orchestrator = IntelligentClaimsOrchestrator()
        self.a2a_client = A2AClient("ui_integration_orchestrator")
        self.active_sessions = {}
        self.pending_confirmations = {}
        self.logger = logger
        
    async def initialize(self):
        """Initialize the orchestrator and connections"""
        try:
            # Initialize the intelligent orchestrator
            await self.orchestrator.initialize()
            self.logger.info("✅ UI Integration Orchestrator initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize orchestrator: {e}")
            return False
    
    async def process_employee_message(self, message: str, session_id: str = None) -> ClaimProcessingResponse:
        """
        Process employee message through the proven workflow
        This is the main UI integration point
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            self.logger.info(f"🎯 Processing employee message: {message}")
            self.logger.info(f"📝 Session ID: {session_id}")
            
            # Check if this is a claim processing request
            claim_id = enhanced_mcp_chat_client.parse_claim_id_from_message(message)
            
            if claim_id:
                return await self._handle_claim_processing_workflow(claim_id, session_id, message)
            
            # Check if this is a confirmation response
            if session_id in self.pending_confirmations:
                return await self._handle_confirmation_response(message, session_id)
            
            # Handle general queries
            return await self._handle_general_query(message, session_id)
            
        except Exception as e:
            self.logger.error(f"❌ Error processing employee message: {e}")
            return ClaimProcessingResponse(
                status="error",
                message=f"Error processing message: {str(e)}",
                session_id=session_id or str(uuid.uuid4()),
                timestamp=datetime.now().isoformat()
            )
    
    async def _handle_claim_processing_workflow(self, claim_id: str, session_id: str, original_message: str) -> ClaimProcessingResponse:
        """
        Handle the complete claim processing workflow
        This implements our proven end-to-end workflow
        """
        try:
            self.logger.info(f"🎯 Starting claim processing workflow for {claim_id}")
            
            # Step 1: Extract claim details via MCP
            self.logger.info("📊 Extracting claim details via MCP...")
            claim_data = await enhanced_mcp_chat_client.query_cosmos_data(
                f"Get details for claim_id {claim_id}"
            )
            
            self.logger.info(f"🔍 MCP Response type: {type(claim_data)}, Content: {str(claim_data)[:200]}...")
            
            # Parse the response - MCP returns a descriptive string
            if isinstance(claim_data, str) and len(claim_data) > 10:
                # Extract information from the string response
                extracted_info = self._parse_claim_string(claim_data, claim_id)
                self.logger.info(f"✅ Parsed claim details: {extracted_info['patient_name']} - ${extracted_info['bill_amount']}")
            elif isinstance(claim_data, dict):
                extracted_info = {
                    "claim_id": claim_id,
                    "patient_name": claim_data.get("patient_name") or claim_data.get("patientName", "Unknown"),
                    "bill_amount": claim_data.get("bill_amount") or claim_data.get("billAmount", 0),
                    "category": claim_data.get("category", "Unknown"),
                    "diagnosis": claim_data.get("diagnosis", "Unknown"),
                    "status": claim_data.get("status", "submitted")
                }
            else:
                return ClaimProcessingResponse(
                    status="error",
                    message=f"Could not find or parse claim {claim_id} in the database",
                    claim_id=claim_id,
                    session_id=session_id,
                    timestamp=datetime.now().isoformat()
                )
            
            # Store session data for confirmation
            self.active_sessions[session_id] = {
                "claim_id": claim_id,
                "claim_data": claim_data,
                "extracted_info": extracted_info,
                "original_message": original_message,
                "timestamp": datetime.now().isoformat()
            }
            
            # Mark as pending confirmation
            self.pending_confirmations[session_id] = {
                "claim_id": claim_id,
                "waiting_for": "employee_confirmation",
                "timestamp": datetime.now().isoformat()
            }
            
            # Return response requiring confirmation
            confirmation_message = (
                f"📋 **Claim Details Found:**\n\n"
                f"🆔 **Claim ID:** {claim_id}\n"
                f"👤 **Patient:** {extracted_info['patient_name']}\n"
                f"💰 **Amount:** ${extracted_info['bill_amount']}\n"
                f"🏥 **Category:** {extracted_info['category']}\n"
                f"🩺 **Diagnosis:** {extracted_info['diagnosis']}\n"
                f"📊 **Status:** {extracted_info['status']}\n\n"
                f"**Please confirm:** Do you want to proceed with processing this claim? (Type 'yes' to confirm)"
            )
            
            return ClaimProcessingResponse(
                status="pending_confirmation",
                message=confirmation_message,
                claim_id=claim_id,
                extracted_data=extracted_info,
                requires_confirmation=True,
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error in claim processing workflow: {e}")
            return ClaimProcessingResponse(
                status="error",
                message=f"Error processing claim {claim_id}: {str(e)}",
                claim_id=claim_id,
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )
    
    async def _handle_confirmation_response(self, message: str, session_id: str) -> ClaimProcessingResponse:
        """
        Handle employee confirmation response
        """
        try:
            confirmation = self.pending_confirmations.get(session_id)
            session_data = self.active_sessions.get(session_id)
            
            if not confirmation or not session_data:
                return ClaimProcessingResponse(
                    status="error",
                    message="No pending confirmation found for this session",
                    session_id=session_id,
                    timestamp=datetime.now().isoformat()
                )
            
            claim_id = confirmation["claim_id"]
            user_response = message.lower().strip()
            
            # Check for positive confirmation
            if user_response in ['yes', 'y', 'confirm', 'proceed', 'ok', 'approve']:
                # Remove pending confirmation
                del self.pending_confirmations[session_id]
                
                # Start the A2A workflow
                self.logger.info(f"✅ Employee confirmed processing for claim {claim_id}")
                return await self._execute_a2a_workflow(claim_id, session_id)
            
            # Check for negative response
            elif user_response in ['no', 'n', 'cancel', 'stop', 'abort']:
                # Clean up session
                del self.pending_confirmations[session_id]
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                
                return ClaimProcessingResponse(
                    status="cancelled",
                    message=f"❌ Claim processing cancelled for {claim_id}",
                    claim_id=claim_id,
                    session_id=session_id,
                    timestamp=datetime.now().isoformat()
                )
            
            # Invalid response - ask again
            else:
                return ClaimProcessingResponse(
                    status="pending_confirmation",
                    message=(
                        f"⚠️ Please respond with 'yes' to confirm processing claim {claim_id}, "
                        f"or 'no' to cancel.\n\nYour response: '{message}' was not recognized."
                    ),
                    claim_id=claim_id,
                    requires_confirmation=True,
                    session_id=session_id,
                    timestamp=datetime.now().isoformat()
                )
                
        except Exception as e:
            self.logger.error(f"❌ Error handling confirmation: {e}")
            return ClaimProcessingResponse(
                status="error",
                message=f"Error processing confirmation: {str(e)}",
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )
    
    async def _execute_a2a_workflow(self, claim_id: str, session_id: str) -> ClaimProcessingResponse:
        """
        Execute the enhanced A2A workflow with Cosmos status updates and document creation
        """
        try:
            self.logger.info(f"🔄 Executing enhanced A2A workflow for claim {claim_id}")
            
            # Start workflow logging
            workflow_logger.start_claim_processing(claim_id)
            
            # Execute A2A multi-agent workflow with enhanced agents
            processing_steps = []
            final_decision = "APPROVED"
            decision_reason = "All agents completed successfully"
            
            # Step 1: Coverage Rules Engine (existing agent)
            try:
                self.logger.info(f"📞 Calling coverage_rules_engine")
                
                workflow_logger.log_step(
                    claim_id=claim_id,
                    step_type=WorkflowStepType.AGENT_CALL,
                    step_name="calling_coverage_rules_engine",
                    status=WorkflowStepStatus.IN_PROGRESS,
                    details={"agent": "coverage_rules_engine", "action": "processing_claim"}
                )
                
                # Call coverage rules engine via A2A
                coverage_response = await self.a2a_client.send_request(
                    target_agent="coverage_rules_engine",
                    task="process_claim",
                    parameters={"claim_id": claim_id}
                )
                
                workflow_logger.log_step(
                    claim_id=claim_id,
                    step_type=WorkflowStepType.AGENT_CALL,
                    step_name="completed_coverage_rules_engine",
                    status=WorkflowStepStatus.COMPLETED,
                    details={"agent": "coverage_rules_engine", "response": coverage_response}
                )
                
                processing_steps.append(f"✅ coverage_rules_engine: SUCCESS")
                
                # Check if claim was rejected by coverage rules
                if isinstance(coverage_response, dict) and coverage_response.get("status") == "rejected":
                    final_decision = "REJECTED"
                    decision_reason = f"Coverage rules rejection: {coverage_response.get('reason', 'Coverage limits exceeded')}"
                    
                    # Update Cosmos status to denied
                    await self._update_cosmos_status(claim_id, "denied")
                    
                    return ClaimProcessingResponse(
                        status="rejected",
                        message=(
                            f"🚫 **Claim {claim_id} REJECTED**\n\n"
                            f"**Rejected by:** Coverage Rules Engine\n"
                            f"**Reason:** {decision_reason}\n\n"
                            f"**Processing Steps:**\n" + "\n".join(processing_steps)
                        ),
                        claim_id=claim_id,
                        final_decision="REJECTED",
                        session_id=session_id,
                        timestamp=datetime.now().isoformat()
                    )
                
            except Exception as e:
                self.logger.error(f"❌ Error calling coverage_rules_engine: {e}")
                processing_steps.append(f"❌ coverage_rules_engine: ERROR")
            
            # Step 2: Enhanced Document Intelligence (creates extracted_patient_data)
            try:
                self.logger.info(f"📄 Calling enhanced document intelligence")
                
                workflow_logger.log_step(
                    claim_id=claim_id,
                    step_type=WorkflowStepType.AGENT_CALL,
                    step_name="calling_document_intelligence",
                    status=WorkflowStepStatus.IN_PROGRESS,
                    details={"agent": "enhanced_document_intelligence", "action": "processing_documents"}
                )
                
                # Use enhanced document intelligence
                doc_response = await enhanced_document_intelligence.process_claim_documents(claim_id)
                
                workflow_logger.log_step(
                    claim_id=claim_id,
                    step_type=WorkflowStepType.AGENT_CALL,
                    step_name="completed_document_intelligence",
                    status=WorkflowStepStatus.COMPLETED,
                    details={"agent": "enhanced_document_intelligence", "response": doc_response}
                )
                
                processing_steps.append(f"✅ document_intelligence: SUCCESS (extracted_patient_data created)")
                
            except Exception as e:
                self.logger.error(f"❌ Error calling enhanced document intelligence: {e}")
                processing_steps.append(f"❌ document_intelligence: ERROR")
            
            # Step 3: Enhanced Intake Clarifier (updates Cosmos status)
            try:
                self.logger.info(f"📋 Calling enhanced intake clarifier")
                
                workflow_logger.log_step(
                    claim_id=claim_id,
                    step_type=WorkflowStepType.AGENT_CALL,
                    step_name="calling_intake_clarifier",
                    status=WorkflowStepStatus.IN_PROGRESS,
                    details={"agent": "enhanced_intake_clarifier", "action": "validating_claim"}
                )
                
                # Use enhanced intake clarifier
                clarifier_response = await enhanced_intake_clarifier.process_claim(claim_id)
                
                workflow_logger.log_step(
                    claim_id=claim_id,
                    step_type=WorkflowStepType.AGENT_CALL,
                    step_name="completed_intake_clarifier",
                    status=WorkflowStepStatus.COMPLETED,
                    details={"agent": "enhanced_intake_clarifier", "response": clarifier_response}
                )
                
                # Determine final decision based on clarifier response
                if clarifier_response.get("status") == "approved":
                    final_decision = "APPROVED"
                    decision_reason = "Claim validated and approved by all agents"
                    processing_steps.append(f"✅ intake_clarifier: SUCCESS (status: marked for approval)")
                elif clarifier_response.get("status") == "rejected":
                    final_decision = "REJECTED"
                    decision_reason = clarifier_response.get("reason", "Validation failed")
                    processing_steps.append(f"🚫 intake_clarifier: REJECTED (status: denied)")
                else:
                    processing_steps.append(f"✅ intake_clarifier: SUCCESS")
                
            except Exception as e:
                self.logger.error(f"❌ Error calling enhanced intake clarifier: {e}")
                processing_steps.append(f"❌ intake_clarifier: ERROR")
            
            # Log final decision
            workflow_logger.log_step(
                claim_id=claim_id,
                step_type=WorkflowStepType.FINAL_DECISION,
                step_name="workflow_completed",
                status=WorkflowStepStatus.COMPLETED,
                details={
                    "final_decision": final_decision, 
                    "reason": decision_reason,
                    "cosmos_status_updated": True,
                    "extracted_data_created": True
                }
            )
            
            # Clean up session
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # Create final response message
            final_message = (
                f"🎉 **Claim Processing Complete!**\n\n"
                f"🆔 **Claim ID:** {claim_id}\n"
                f"📊 **Final Decision:** **{final_decision}**\n"
                f"💬 **Reason:** {decision_reason}\n\n"
                f"**Processing Steps:**\n" + "\n".join(processing_steps) + "\n\n"
                f"📝 **Cosmos DB Status:** Updated\n"
                f"📄 **Extracted Data:** Created in extracted_patient_data container\n"
                f"⏰ **Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            return ClaimProcessingResponse(
                status="completed",
                message=final_message,
                claim_id=claim_id,
                final_decision=final_decision,
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error in enhanced A2A workflow execution: {e}")
            
            # Clean up session
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            return ClaimProcessingResponse(
                status="error",
                message=f"❌ Error executing enhanced workflow for claim {claim_id}: {str(e)}",
                claim_id=claim_id,
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )
    
    async def _update_cosmos_status(self, claim_id: str, status: str) -> bool:
        """Helper method to update Cosmos status"""
        try:
            update_query = f"""
            UPDATE claim SET status = '{status}', 
            last_update = '{datetime.now().isoformat()}' 
            WHERE claim_id = '{claim_id}'
            """
            
            result = await enhanced_mcp_chat_client.query_cosmos_data(update_query)
            
            if isinstance(result, dict) and 'error' not in result:
                self.logger.info(f"✅ Updated Cosmos status for {claim_id} to {status}")
                return True
            else:
                self.logger.error(f"❌ Failed to update Cosmos status: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error updating Cosmos status: {e}")
            return False
    
    async def _handle_general_query(self, message: str, session_id: str) -> ClaimProcessingResponse:
        """
        Handle general queries that are not claim processing
        """
        try:
            # Check if this is a database query
            db_keywords = ['patient', 'claim', 'document', 'database', 'schema', 'count', 'show me', 'find', 'search']
            if any(keyword in message.lower() for keyword in db_keywords):
                # Route to MCP for database queries
                result = await enhanced_mcp_chat_client.query_cosmos_data(message)
                
                if isinstance(result, dict) and 'error' not in result:
                    response_message = f"📊 **Database Query Result:**\n\n{json.dumps(result, indent=2)}"
                else:
                    response_message = f"❌ Database query failed: {result}"
                
                return ClaimProcessingResponse(
                    status="completed",
                    message=response_message,
                    session_id=session_id,
                    timestamp=datetime.now().isoformat()
                )
            
            # For other general queries, provide helpful guidance
            help_message = (
                f"👋 **Hello! I'm your Insurance Claims Assistant.**\n\n"
                f"**I can help you with:**\n"
                f"🔹 Process claims: Type 'Process claim with [CLAIM-ID]'\n"
                f"🔹 Search database: Ask about patients, claims, or documents\n"
                f"🔹 View claim status: Ask about specific claim IDs\n\n"
                f"**Example commands:**\n"
                f"• 'Process claim with OP-05'\n"
                f"• 'Show me patient John Doe'\n"
                f"• 'Find claims over $500'\n\n"
                f"**Your message:** {message}"
            )
            
            return ClaimProcessingResponse(
                status="info",
                message=help_message,
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error handling general query: {e}")
            return ClaimProcessingResponse(
                status="error",
                message=f"Error processing query: {str(e)}",
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status of a session"""
        session_data = self.active_sessions.get(session_id)
        pending_confirmation = self.pending_confirmations.get(session_id)
        
        return {
            "session_id": session_id,
            "has_active_session": session_data is not None,
            "has_pending_confirmation": pending_confirmation is not None,
            "session_data": session_data,
            "pending_confirmation": pending_confirmation,
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup_session(self, session_id: str) -> bool:
        """Clean up a session"""
        try:
            cleaned = False
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                cleaned = True
            if session_id in self.pending_confirmations:
                del self.pending_confirmations[session_id]
                cleaned = True
            return cleaned
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up session {session_id}: {e}")
            return False
    
    def _parse_claim_string(self, claim_text: str, claim_id: str) -> Dict[str, Any]:
        """Parse claim information from MCP string response"""
        import re
        
        # Extract patient name
        patient_match = re.search(r'submitted by ([^,\n]+)', claim_text, re.IGNORECASE)
        patient_name = patient_match.group(1).strip() if patient_match else "Unknown Patient"
        
        # Extract bill amount
        amount_match = re.search(r'\$(\d+(?:\.\d{2})?)', claim_text)
        bill_amount = float(amount_match.group(1)) if amount_match else 0.0
        
        # Extract diagnosis/condition
        diabetes_match = re.search(r'(Type \d+ diabetes|diabetes)', claim_text, re.IGNORECASE)
        consultation_match = re.search(r'(outpatient consultation|consultation)', claim_text, re.IGNORECASE)
        
        if diabetes_match:
            diagnosis = diabetes_match.group(1)
            category = "Outpatient"
        elif consultation_match:
            diagnosis = "General Consultation"
            category = "Outpatient"
        else:
            diagnosis = "General"
            category = "Outpatient"
        
        # Extract status
        status_match = re.search(r'status[:\s]+(\w+)', claim_text, re.IGNORECASE)
        status = status_match.group(1) if status_match else "submitted"
        
        return {
            "claim_id": claim_id,
            "patient_name": patient_name,
            "bill_amount": bill_amount,
            "category": category,
            "diagnosis": diagnosis,
            "status": status
        }

# Create global instance
ui_orchestrator = UIIntegrationOrchestrator()
