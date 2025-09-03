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
from agent import CosmosQueryAgent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CosmosQueryAgentExecutor(AgentExecutor):
    """Cosmos Query Agent Executor using Azure Cosmos DB MCP Server"""

    def __init__(self):
        self.agent = CosmosQueryAgent()
        self._initialized = False

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Execute a task using the Cosmos Query Agent.

        This follows the same RequestContext pattern as other sample agents:
        - Read user input from context.get_user_input()
        - Use context.current_task or create a new task from context.message
        - Emit TaskStatus/Artifact events via enqueue_event
        """
        try:
            # Initialize agent if needed
            if not self._initialized:
                logger.info("Initializing Cosmos Query Agent...")
                success = await self.agent.initialize()
                if not success:
                    await self._send_error(
                        context, event_queue, "Failed to initialize Cosmos Query Agent"
                    )
                    return
                self._initialized = True
                logger.info("Cosmos Query Agent initialized successfully")

            # Derive query and task from context
            query = context.get_user_input()
            task = context.current_task
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)

            # Update task status to working
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    status=TaskStatus(state=TaskState.working),
                    final=False,
                    context_id=task.context_id,
                    task_id=task.id,
                )
            )

            logger.info(f"Cosmos Query Agent executing task: {task.id}")
            logger.info(f"User query: {query}")

            # Process the query using the Cosmos Query Agent (via MCP tools)
            response = await self.agent.process_query(query)

            # Create an artifact from the response
            artifact = new_text_artifact(
                name="cosmos_query_result",
                text=response,
                description="Cosmos DB query result",
            )

            # Send artifact update
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    append=False,
                    context_id=task.context_id,
                    task_id=task.id,
                    last_chunk=True,
                    artifact=artifact,
                )
            )

            # Also send the response as a message for chat UIs
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

            logger.info("Cosmos Query Agent task completed successfully")

        except Exception as e:
            logger.error(f"Error in Cosmos Query Agent execution: {e}", exc_info=True)
            await self._send_error(
                context,
                event_queue,
                f"Error executing Cosmos Query Agent task: {str(e)}",
            )

    async def _send_error(
        self, context: RequestContext, event_queue: EventQueue, error_message: str
    ):
        """Send error status, error artifact, and error message."""
        task = context.current_task or new_task(context.message)
        if not context.current_task:
            await event_queue.enqueue_event(task)

        # Error message and artifact
        display_text = (
            f"Sorry, I encountered an error while querying the Cosmos DB: {error_message}"
        )
        message = new_agent_text_message(display_text, task.context_id, task.id)
        await event_queue.enqueue_event(message)

        error_artifact = new_text_artifact(
            name="error",
            text=display_text,
            description="Cosmos Query Agent error",
        )

        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                append=False,
                context_id=task.context_id,
                task_id=task.id,
                last_chunk=True,
                artifact=error_artifact,
            )
        )

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                status=TaskStatus(state=TaskState.failed),
                final=True,
                context_id=task.context_id,
                task_id=task.id,
            )
        )

    async def cancel(
        self, request_context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel the current task execution."""
        logger.info("Cosmos Query Agent task cancelled")
        raise Exception('Cosmos Query Agent task was cancelled')
