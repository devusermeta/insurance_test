#!/usr/bin/env python3
"""
Cosmos Query Agent - A2A Multi-Agent
Entry point for the Cosmos Query Agent using Azure Cosmos DB MCP Server
"""

import logging
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

import click
import httpx

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotificationConfigStore, BasePushNotificationSender
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent_executor import CosmosQueryAgentExecutor
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
load_dotenv()


@click.command()
@click.option('--host', default='localhost')
@click.option('--port', default=10004)
def main(host, port):
    """Starts the Cosmos Query Agent server using A2A with MCP server integration."""
    httpx_client = httpx.AsyncClient()
    push_config_store = InMemoryPushNotificationConfigStore()
    request_handler = DefaultRequestHandler(
        agent_executor=CosmosQueryAgentExecutor(),
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
    """Returns the Agent Card for the Cosmos Query Agent."""
    
    capabilities = AgentCapabilities(streaming=True)
    skill_cosmos_query = AgentSkill(
        id='cosmos_database_query',
        name='Cosmos Database Query',
        description=(
            'Query Azure Cosmos DB containers and explore database structure using MCP server tools. '
            'Can list containers, describe schemas, count documents, get samples, and run SQL-like queries.'
        ),
        tags=['cosmos', 'database', 'query', 'mcp', 'azure', 'sql'],
        examples=[
            'What is in the actions database?',
            'Show me all containers in the database',
            'Describe the actions container schema',
            'Count documents in the actions container',
            'Show me sample documents from actions',
            'SELECT * FROM c WHERE c.agent_name = "TimeAgent"',
        ],
    )
    
    return AgentCard(
        name="Cosmos Query Agent",
        description="A specialized agent for querying and exploring Azure Cosmos DB data using MCP server tools",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=capabilities,
        skills=[skill_cosmos_query],
    )


if __name__ == "__main__":
    main()
