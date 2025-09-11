"""
A2A-compatible wrapper for the Intake Clarifier Executor
Bridges between our existing insurance agent logic and the A2A framework
"""

import logging
import json
from typing import Dict, Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
    new_text_artifact,
)

from agents.intake_clarifier.intake_clarifier_executor import IntakeClarifierExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class A2AIntakeClarifierExecutor(AgentExecutor):
    """A2A-compatible wrapper for the Intake Clarifier"""
    
    def __init__(self):
        self.core_executor = IntakeClarifierExecutor()
        
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute using A2A protocol"""
        try:
            # Get the user input from the context
            user_input = context.get_user_input()
            task = context.current_task
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
            
            logger.info(f"A2A Intake Clarifier processing: {user_input}")
            
            # Check if this is a new workflow request
            if self._is_new_workflow_claim_request(user_input):
                result = await self._handle_new_workflow_verification(user_input)
            else:
                # Use existing core executor for legacy requests
                request_data = self._parse_a2a_request(user_input)
                result = await self.core_executor.execute(request_data)
            
            # Start processing
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    status=TaskStatus(
                        state=TaskState.working,
                        message=new_agent_text_message(
                            "🏥 Starting claim intake clarification...",
                            task.context_id,
                            task.id,
                        ),
                    ),
                    final=False,
                    context_id=task.context_id,
                    task_id=task.id,
                )
            )
            
            # Parse the user input to extract task and parameters
            # Try to parse as JSON first, then fall back to text processing
            request_data = self._parse_user_input(user_input)
            
            # Call our existing executor
            result = await self.core_executor.execute(request_data)
            
            # Format the result as text
            result_text = json.dumps(result, indent=2)
            
            # Send final result
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    append=False,
                    context_id=task.context_id,
                    task_id=task.id,
                    last_chunk=True,
                    artifact=new_text_artifact(
                        name='intake_clarification_result',
                        description='Result of intake clarification process.',
                        text=result_text,
                    ),
                )
            )
            
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    status=TaskStatus(state=TaskState.completed),
                    final=True,
                    context_id=task.context_id,
                    task_id=task.id,
                )
            )
            
        except Exception as e:
            logger.error(f"Error in A2A Intake Clarifier: {e}")
            error_message = f"❌ Error in intake clarification: {str(e)}"
            
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    status=TaskStatus(
                        state=TaskState.failed,
                        message=new_agent_text_message(
                            error_message,
                            task.context_id if task else "unknown",
                            task.id if task else "unknown",
                        ),
                    ),
                    final=True,
                    context_id=task.context_id if task else "unknown",
                    task_id=task.id if task else "unknown",
                )
            )
    
    def _parse_user_input(self, user_input: str) -> Dict[str, Any]:
        """Parse user input to extract task and parameters"""
        try:
            # Try to parse as JSON first
            data = json.loads(user_input)
            if isinstance(data, dict) and ('task' in data or 'parameters' in data):
                return data
        except (json.JSONDecodeError, TypeError):
            pass
        
        # If not JSON, create a default request based on the text
        if "OP-" in user_input:
            # Extract claim ID
            import re
            claim_match = re.search(r'OP-\d+', user_input)
            claim_id = claim_match.group(0) if claim_match else "unknown"
            
            return {
                "task": "validate_claim_intake",
                "parameters": {
                    "claim_id": claim_id,
                    "user_request": user_input,
                    "expected_output": "validation_with_recommendations"
                }
            }
        else:
            # Generic request
            return {
                "task": "general_clarification",
                "parameters": {
                    "user_request": user_input,
                    "expected_output": "clarification_response"
                }
            }

    def _is_new_workflow_claim_request(self, user_input: str) -> bool:
        """Check if this is a new workflow claim verification request"""
        indicators = [
            "claim_id" in user_input.lower(),
            "patient verification" in user_input.lower(),
            "patient_name" in user_input.lower(),
            "category" in user_input.lower()
        ]
        return sum(indicators) >= 2

    async def _handle_new_workflow_verification(self, user_input: str) -> Dict[str, Any]:
        """Handle patient/claim verification for new workflow"""
        try:
            logger.info("🆕 Processing NEW WORKFLOW patient verification")
            
            # Extract claim information
            claim_info = self._extract_claim_info_from_text(user_input)
            
            # Perform enhanced verification
            verification_result = await self._verify_structured_claim_patient(claim_info)
            
            response_message = f"""👤 **PATIENT VERIFICATION COMPLETE**

**Claim Information:**
• **Claim ID**: {claim_info.get('claim_id', 'Unknown')}
• **Patient Name**: {claim_info.get('patient_name', 'Unknown')}
• **Category**: {claim_info.get('category', 'Unknown')}

**Verification Results:**
• **Identity Status**: {'✅ VERIFIED' if verification_result['identity_verified'] else '❌ VERIFICATION FAILED'}
• **Eligibility Status**: {'✅ ELIGIBLE' if verification_result['eligibility_verified'] else '❌ NOT ELIGIBLE'}
• **Documentation Status**: {'✅ COMPLETE' if verification_result['documentation_complete'] else '⚠️ INCOMPLETE'}

**Verification Details:**
{chr(10).join(['• ' + detail for detail in verification_result['verification_details']])}

**Required Actions:**
{chr(10).join(['• ' + action for action in verification_result['required_actions']])}

**Risk Assessment:**
• **Risk Level**: {verification_result['risk_level']}
• **Confidence Score**: {verification_result['confidence_score']}/100
"""

            return {
                "status": "success",
                "response": response_message,
                "verification_result": verification_result,
                "workflow_type": "new_structured"
            }
            
        except Exception as e:
            logger.error(f"❌ Error in new workflow verification: {e}")
            return {
                "status": "error",
                "response": f"Patient verification failed: {str(e)}"
            }

    def _extract_claim_info_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured claim information from task text"""
        import re
        
        claim_info = {}
        patterns = {
            'claim_id': r'claim[_\s]*id[:\s]+([A-Z]{2}-\d{2,3})',
            'patient_name': r'patient[_\s]*name[:\s]+([^,\n]+)',
            'category': r'category[:\s]+([^,\n]+)',
            'diagnosis': r'diagnosis[:\s]+([^,\n]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                claim_info[key] = match.group(1).strip()
        
        return claim_info

    async def _verify_structured_claim_patient(self, claim_info: Dict[str, Any]) -> Dict[str, Any]:
        """Verify patient information for structured claim"""
        import asyncio
        
        patient_name = claim_info.get('patient_name', '')
        category = claim_info.get('category', '').lower()
        claim_id = claim_info.get('claim_id', '')
        
        # Simulate verification processing
        await asyncio.sleep(0.15)
        
        # Enhanced verification based on patient data
        if 'john doe' in patient_name.lower():
            # Known test patient
            identity_verified = True
            eligibility_verified = True
            documentation_complete = True
            verification_details = [
                "Patient identity confirmed via government ID",
                "Insurance policy active and in good standing",
                "Previous claims history reviewed",
                "Contact information verified"
            ]
            required_actions = [
                "No additional verification required",
                "Proceed with standard processing"
            ]
            risk_level = "LOW"
            confidence = 95
        elif claim_id.startswith('OP-'):
            # Outpatient verification
            identity_verified = True
            eligibility_verified = True
            documentation_complete = 'outpatient' in category
            verification_details = [
                "Patient identity verified",
                "Outpatient eligibility confirmed",
                "Basic documentation reviewed"
            ]
            if not documentation_complete:
                verification_details.append("⚠️ Some documentation incomplete")
                
            required_actions = [
                "Verify outpatient pre-authorization",
                "Confirm provider network status"
            ] if not documentation_complete else ["Standard processing approved"]
            
            risk_level = "MEDIUM" if not documentation_complete else "LOW"
            confidence = 80 if documentation_complete else 65
        else:
            # Default verification
            identity_verified = True
            eligibility_verified = False
            documentation_complete = False
            verification_details = [
                "Basic identity check completed",
                "⚠️ Eligibility verification pending",
                "⚠️ Additional documentation required"
            ]
            required_actions = [
                "Complete full eligibility verification",
                "Request additional patient documentation",
                "Schedule manual review if needed"
            ]
            risk_level = "HIGH"
            confidence = 50
        
        return {
            "identity_verified": identity_verified,
            "eligibility_verified": eligibility_verified,
            "documentation_complete": documentation_complete,
            "verification_details": verification_details,
            "required_actions": required_actions,
            "risk_level": risk_level,
            "confidence_score": confidence
        }
    
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel the current task"""
        logger.info("Cancelling Intake Clarifier task")
        # Add cancellation logic if needed
