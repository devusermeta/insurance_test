"""
Claims Orchestrator Agent - A2A Protocol Implementation
Main orchestration agent that coordinates the entire claims processing workflow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
import click
import httpx
from typing import Dict, Any
from datetime import datetime

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotificationConfigStore, BasePushNotificationSender
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv

from shared.mcp_config import A2A_AGENT_PORTS
from agents.claims_orchestrator.claims_orchestrator_executor import ClaimsOrchestratorExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce Azure SDK logging verbosity
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)

load_dotenv()

@click.command()
@click.option('--host', default='localhost')
@click.option('--port', default=A2A_AGENT_PORTS["claims_orchestrator"])
def main(host, port):
    """Starts the Claims Orchestrator Agent server using A2A."""
    httpx_client = httpx.AsyncClient()
    push_config_store = InMemoryPushNotificationConfigStore()
    request_handler = DefaultRequestHandler(
        agent_executor=ClaimsOrchestratorExecutor(),
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
    """Returns the Agent Card for the Claims Orchestrator Agent."""

    # Build the agent card
    capabilities = AgentCapabilities(streaming=True)
    
    skill_claims_orchestration = AgentSkill(
        id='claims_orchestration',
        name='Claims Processing Orchestration',
        description=(
            'Coordinates the complete insurance claims processing workflow, '
            'managing interactions between intake clarification, document analysis, '
            'and coverage evaluation agents to ensure efficient claim processing.'
        ),
        tags=['insurance', 'claims', 'orchestration', 'workflow', 'coordination'],
        examples=[
            'Process a new auto insurance claim with documents',
            'Coordinate claim workflow between multiple agents',
            'Check status of claim processing pipeline',
            'Route claim through validation and approval process'
        ],
    )

    skill_workflow_management = AgentSkill(
        id='workflow_management',
        name='Insurance Workflow Management',
        description=(
            'Manages complex insurance workflows including claim intake, '
            'validation, document processing, fraud detection, and coverage evaluation.'
        ),
        tags=['workflow', 'insurance', 'automation', 'process-management'],
        examples=[
            'Start claim processing workflow for customer',
            'Monitor claim processing status across agents',
            'Handle workflow exceptions and escalations',
            'Generate workflow completion reports'
        ],
    )

    agent_card = AgentCard(
        name='ClaimsOrchestratorAgent',
        description=(
            'Main orchestration agent for insurance claims processing. '
            'Coordinates the entire claims workflow from intake through approval, '
            'managing interactions with specialized agents for validation, '
            'document analysis, and coverage evaluation.'
        ),
        url=f'http://{host}:{port}/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=capabilities,
        skills=[skill_claims_orchestration, skill_workflow_management],
    )

    return agent_card

if __name__ == '__main__':
    main()
