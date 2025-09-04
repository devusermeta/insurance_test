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
    
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel the current task"""
        logger.info("Cancelling Intake Clarifier task")
        # Add cancellation logic if needed
