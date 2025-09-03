"""
Coverage Rules Engine Agent - A2A Protocol Implementation
Specialized agent for evaluating coverage rules and policy decisions
"""

import asyncio
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

from .coverage_rules_executor import CoverageRulesExecutor
from shared.mcp_config import A2A_AGENT_PORTS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

@click.command()
@click.option('--host', default='localhost')
@click.option('--port', default=A2A_AGENT_PORTS["coverage_rules_engine"])
def main(host, port):
    """Starts the Coverage Rules Engine Agent server using A2A."""
    httpx_client = httpx.AsyncClient()
    push_config_store = InMemoryPushNotificationConfigStore()
    request_handler = DefaultRequestHandler(
        agent_executor=CoverageRulesExecutor(),
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
    """Returns the Agent Card for the Coverage Rules Engine Agent."""

    # Build the agent card
    capabilities = AgentCapabilities(streaming=True)
    
    # Define agent skills
    skills = [
        AgentSkill(
            id="coverage_evaluation",
            name="Coverage Evaluation",
            description="Evaluate insurance coverage for claims and determine eligibility",
            tags=["coverage", "evaluation", "eligibility"]
        ),
        AgentSkill(
            id="policy_analysis", 
            name="Policy Analysis",
            description="Analyze policy terms, conditions, and coverage limits",
            tags=["policy", "analysis", "terms"]
        ),
        AgentSkill(
            id="rules_execution",
            name="Rules Execution",
            description="Execute specific business rules and return decisions",
            tags=["rules", "execution", "business"]
        ),
        AgentSkill(
            id="decision_engine",
            name="Decision Engine",
            description="Make automated decisions based on rules and policies",
            tags=["decision", "automation", "policies"]
        )
    ]
    
    agent_card = AgentCard(
        name="Coverage Rules Engine Agent",
        description="Specialized agent for evaluating insurance coverage, executing business rules, and making automated policy decisions",
        version="1.0.0",
        url=f"http://{host}:{port}",
        skills=skills,
        capabilities=capabilities,
        default_input_modes=["text"],
        default_output_modes=["text"]
    )
    
    logger.info("⚖️ Coverage Rules Engine Agent initialized")
    logger.info(f"🔧 Agent skills: {[skill.name for skill in agent_card.skills]}")
    
    return agent_card

if __name__ == "__main__":
    main()
