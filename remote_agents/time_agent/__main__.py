import logging

import click
import httpx

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotificationConfigStore, BasePushNotificationSender
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent_executor import TimeAgentExecutor
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce Azure SDK logging verbosity
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)
logging.getLogger('azure.ai.agents').setLevel(logging.WARNING)

load_dotenv()


@click.command()
@click.option('--host', default='localhost')
@click.option('--port', default=10003)
def main(host, port):
    """Starts the Time Agent server using A2A with Cosmos DB logging via Azure MCP Server."""
    httpx_client = httpx.AsyncClient()
    push_config_store = InMemoryPushNotificationConfigStore()
    request_handler = DefaultRequestHandler(
        agent_executor=TimeAgentExecutor(),
        task_store=InMemoryTaskStore(),
        push_config_store=push_config_store,
        push_sender=BasePushNotificationSender(httpx_client, push_config_store),
    )

    server = A2AStarletteApplication(
        agent_card=get_agent_card(host, port), http_handler=request_handler
    )
    import uvicorn

    uvicorn.run(server.build(), host=host, port=port)


def get_agent_card(host: str, port: int):
    """Returns the Agent Card for the Time Agent."""

    # Build the agent card
    capabilities = AgentCapabilities(streaming=True)
    skill_time_date = AgentSkill(
        id='time_date_agent',
        name='Time and Date Services',
        description=(
            'Provides current time and date information with comprehensive logging to Cosmos DB. '
            'Handles requests for current time, date, timezone information, and formatted timestamps.'
        ),
        tags=['time', 'date', 'timestamp', 'timezone', 'logging', 'cosmos'],
        examples=[
            'What time is it?',
            'What is the current date?',
            'Show me the current timestamp',
            'What day is today?',
            'Give me the current date and time',
        ],
    )

    agent_card = AgentCard(
        name='TimeAgent',
        description=(
            'This agent provides comprehensive time and date services '
            'with full activity logging to Cosmos DB via Azure MCP Server'
        ),
        url=f'http://{host}:{port}/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=capabilities,
        skills=[skill_time_date],
    )

    return agent_card


if __name__ == '__main__':
    main()
