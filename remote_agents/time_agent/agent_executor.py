import logging

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
from agent import TimeAgentWithCosmosLogging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeAgentExecutor(AgentExecutor):
    """Time Agent Executor with Cosmos DB logging via Azure MCP Server"""

    def __init__(self):
        self.agent = TimeAgentWithCosmosLogging()
        self._initialized = False

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        # Initialize the agent if not already done
        if not self._initialized:
            await self.agent.initialize()
            self._initialized = True
            logger.info("Time Agent with Cosmos DB logging initialized successfully")
        
        query = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        # Log the execution start
        await self.agent.log_to_cosmos("execution_start", {
            "task_id": task.id,
            "session_id": getattr(context.message, 'sessionId', 'unknown'),
            "user_query": query,
            "context_id": task.context_id
        })

        try:
            # Update task status to working
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    status=TaskStatus(state=TaskState.working),
                    final=False,
                    context_id=task.context_id,
                    task_id=task.id,
                )
            )

            # Process the query and get response
            response = await self.agent.process_query(query)

            # Create text artifact with the response
            artifact = new_text_artifact(
                name='time_response',
                text=response,
                description='Time/date information response'
            )
            
            # Add artifact to task using event
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    append=False,
                    context_id=task.context_id,
                    task_id=task.id,
                    last_chunk=True,
                    artifact=artifact,
                )
            )

            # Send the response as a message
            message = new_agent_text_message(response, task.context_id, task.id)
            await event_queue.enqueue_event(message)

            # Mark task as completed
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    status=TaskStatus(state=TaskState.completed),
                    final=True,
                    context_id=task.context_id,
                    task_id=task.id,
                )
            )

            # Log the successful completion
            await self.agent.log_to_cosmos("execution_completed", {
                "task_id": task.id,
                "session_id": getattr(context.message, 'sessionId', 'unknown'),
                "user_query": query,
                "response": response,
                "context_id": task.context_id,
                "success": True
            })

            logger.info(f"Time Agent successfully processed query: {query}")

        except Exception as e:
            logger.error(f"Error in Time Agent execution: {e}", exc_info=True)

            # Log the error
            await self.agent.log_to_cosmos("execution_error", {
                "task_id": task.id,
                "session_id": getattr(context.message, 'sessionId', 'unknown'),
                "user_query": query,
                "error": str(e),
                "context_id": task.context_id,
                "success": False
            })

            # Send error message
            error_message = f"I encountered an error while processing your request: {str(e)}"
            message = new_agent_text_message(error_message, task.context_id, task.id)
            await event_queue.enqueue_event(message)

            # Create error artifact
            artifact = new_text_artifact(
                name='error_response',
                text=error_message,
                description='Error message from time agent'
            )

            # Add error artifact using event
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    append=False,
                    context_id=task.context_id,
                    task_id=task.id,
                    last_chunk=True,
                    artifact=artifact,
                )
            )

            # Mark task as failed
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    status=TaskStatus(state=TaskState.failed),
                    final=True,
                    context_id=task.context_id,
                    task_id=task.id,
                )
            )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        # Log the cancellation
        if hasattr(self, 'agent'):
            await self.agent.log_to_cosmos("execution_cancelled", {
                "session_id": getattr(context.message, 'sessionId', 'unknown'),
                "reason": "Task was cancelled by user or system"
            })
        
        logger.info("Time Agent task cancelled")
        raise Exception('Time Agent task was cancelled')
