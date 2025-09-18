#!/usr/bin/env python3
"""
Client Live Voice Agent - Main Entry Point

Starts the voice agent server following A2A protocol standards.
Runs on port 8007 and provides voice interaction capabilities.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotificationConfigStore, BasePushNotificationSender
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from voice_agent_executor import VoiceAgentExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='🎤 [VOICE-AGENT] %(asctime)s - %(levelname)s - %(message)s',
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point for the Voice Agent."""
    try:
        logger.info("🚀 Starting Client Live Voice Agent...")
        logger.info("🔧 Port: 8007")
        logger.info("🎯 Mode: Independent Voice Agent with A2A Protocol")
        
        # Create the voice agent executor
        voice_executor = VoiceAgentExecutor()
        
        # Initialize the agent
        await voice_executor.initialize()
        
        # Create agent capabilities
        agent_capabilities = AgentCapabilities(
            audio=True,
            vision=False,
            toolUse=True,
            contextState=True,
            streaming=True
        )
        
        # Create agent card
        agent_card = AgentCard(
            name="ClientLiveVoiceAgent",
            description="Voice-enabled insurance claims assistant with real-time interaction and Azure AI Foundry integration",
            url="http://localhost:8007/",
            version="1.0.0",
            id="client_live_voice_agent",
            defaultInputModes=['audio', 'text'],
            defaultOutputModes=['audio', 'text'],
            instructions="Provides voice-based insurance claims assistance with Azure AI Foundry integration",
            capabilities=agent_capabilities,
            skills=[
                AgentSkill(
                    id="voice_claims_lookup",
                    name="Voice Claims Lookup",
                    description="Voice-based insurance claims lookup and status checking with real-time interaction",
                    tags=['voice', 'claims', 'lookup', 'real-time', 'azure'],
                    examples=[
                        'Check the status of my claim',
                        'Look up claim number 12345',
                        'What is the status of my insurance claim?',
                        'Find details about my recent claim'
                    ]
                ),
                AgentSkill(
                    id="voice_definitions",
                    name="Voice Insurance Definitions",
                    description="Voice-based insurance term definitions and explanations",
                    tags=['voice', 'definitions', 'explanations', 'insurance', 'terms'],
                    examples=[
                        'What is a deductible?',
                        'Explain what comprehensive coverage means',
                        'Define collision coverage',
                        'What does liability insurance cover?'
                    ]
                ),
                AgentSkill(
                    id="voice_document_upload",
                    name="Voice Document Upload Assistant",
                    description="Voice-guided document upload assistance for claims processing",
                    tags=['voice', 'documents', 'upload', 'guidance', 'claims'],
                    examples=[
                        'Help me upload photos of my accident',
                        'Guide me through document submission',
                        'What documents do I need for my claim?',
                        'How do I submit my repair estimates?'
                    ]
                )
            ]
        )
        
        # Create task store and push notification components
        import httpx
        httpx_client = httpx.AsyncClient()
        task_store = InMemoryTaskStore()
        push_config_store = InMemoryPushNotificationConfigStore()
        
        # Create request handler with required parameters
        request_handler = DefaultRequestHandler(
            agent_executor=voice_executor,
            task_store=task_store,
            push_config_store=push_config_store,
            push_sender=BasePushNotificationSender(httpx_client, push_config_store)
        )
        
        # Create A2A application
        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler
        )
        
        logger.info("✅ Voice Agent initialized successfully")
        logger.info("🎤 Ready to accept voice interactions on http://localhost:8007")
        
        # Build the server app
        app = server.build()
        
        # Add CORS middleware to allow frontend connections
        from starlette.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins for development
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        return app
        
    except KeyboardInterrupt:
        logger.info("🛑 Voice Agent stopped by user")
    except Exception as e:
        logger.error(f"❌ Error starting Voice Agent: {e}")
        import traceback
        traceback.print_exc()
        raise

def start_server():
    """Start the voice agent server"""
    import uvicorn
    
    # Get the app by running the async main function
    app = asyncio.run(main())
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8007)

if __name__ == "__main__":
    start_server()