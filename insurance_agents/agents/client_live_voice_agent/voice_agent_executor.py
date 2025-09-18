"""
Voice Agent Executor - Azure AI Foundry Voice Agent Integration
Implements AgentExecutor for voice-based insurance claims assistance.
Uses Azure AI Foundry Voice Agent for real-time voice interactions.
"""

import asyncio
import json
import logging
import time
import uuid
import os
import httpx
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import TaskArtifactUpdateEvent, TaskState, TaskStatus, TaskStatusUpdateEvent
from a2a.utils import new_agent_text_message, new_task, new_text_artifact

# Azure AI Foundry imports
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Shared utilities
from shared.mcp_chat_client import enhanced_mcp_chat_client

# Import conversation tracker (handle both relative and absolute imports)
try:
    from .conversation_tracker import conversation_tracker
except ImportError:
    from conversation_tracker import conversation_tracker

# Load environment variables
load_dotenv()


class VoiceAgentExecutor(AgentExecutor):
    """
    Voice Agent Executor for insurance claims assistance
    - Uses Azure AI Foundry Voice Agent for voice interactions
    - Integrates with MCP tools for data access
    - Supports real-time voice conversations
    - Maintains conversation state across voice sessions
    """
    
    def __init__(self):
        self.agent_name = "client_live_voice_agent"
        self.agent_description = "Voice-enabled insurance claims assistant with Azure AI Foundry integration"
        self.logger = self._setup_logging()
        
        # Voice session management
        self.active_voice_sessions = {}
        self.voice_conversation_history = {}
        
        # Azure AI Foundry setup for Voice Agent
        self.project_client = None
        self.agents_client = None
        self.azure_voice_agent = None
        self.current_thread = None
        self._setup_azure_ai_client()
        
        # Initialize Azure Voice Agent if client is available
        if self.agents_client:
            self.get_or_create_azure_voice_agent()
        
        # MCP client for data access
        self.mcp_client = enhanced_mcp_chat_client
        
    def _setup_azure_ai_client(self):
        """Setup Azure AI Foundry client for Voice Agent"""
        try:
            # Get Azure AI configuration from environment
            subscription_id = os.environ.get("AZURE_AI_AGENT_SUBSCRIPTION_ID")
            resource_group = os.environ.get("AZURE_AI_AGENT_RESOURCE_GROUP_NAME")
            project_name = os.environ.get("AZURE_AI_AGENT_PROJECT_NAME")
            endpoint = os.environ.get("AZURE_AI_AGENT_ENDPOINT")
            
            if not all([subscription_id, resource_group, project_name, endpoint]):
                missing = []
                if not subscription_id: missing.append("AZURE_AI_AGENT_SUBSCRIPTION_ID")
                if not resource_group: missing.append("AZURE_AI_AGENT_RESOURCE_GROUP_NAME") 
                if not project_name: missing.append("AZURE_AI_AGENT_PROJECT_NAME")
                if not endpoint: missing.append("AZURE_AI_AGENT_ENDPOINT")
                
                self.logger.warning(f"⚠️ Azure AI configuration missing: {', '.join(missing)}")
                self.logger.info("📋 Will use fallback voice processing without Azure AI Foundry")
                return
                
            self.logger.info(f"🔧 Using Azure AI endpoint: {endpoint}")
            self.logger.info(f"🔧 Project: {project_name} in {resource_group}")
            
            # Create project client
            self.project_client = AIProjectClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential(),
                subscription_id=subscription_id,
                resource_group_name=resource_group,
                project_name=project_name
            )
            
            # Use the project client's agents interface
            self.agents_client = self.project_client.agents
            self.logger.info("✅ Azure AI Foundry client initialized for Voice Agent")
            
        except Exception as e:
            self.logger.error(f"❌ Error setting up Azure AI client: {e}")
            self.logger.warning("⚠️ Will continue without Azure AI Foundry - using fallback logic")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup colored logging for the voice agent"""
        logger = logging.getLogger(f"VoiceAgent.{self.agent_name}")
        formatter = logging.Formatter(
            f"🎤 [VOICE-AGENT-EXECUTOR] %(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Suppress verbose Azure client logging
        logging.getLogger("azure").setLevel(logging.WARNING)
        logging.getLogger("azure.core").setLevel(logging.WARNING)
        logging.getLogger("azure.identity").setLevel(logging.WARNING)
        logging.getLogger("azure.ai").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        
        return logger
    
    def get_or_create_azure_voice_agent(self):
        """Get existing Azure AI Voice Agent or create new one for voice interactions"""
        if not self.agents_client:
            self.logger.warning("⚠️ Azure AI client not available - using fallback voice processing")
            return None
            
        try:
            # Check for stored voice agent ID
            stored_agent_id = os.environ.get("AZURE_VOICE_AGENT_ID")
            self.logger.info(f"🔍 Environment check: AZURE_VOICE_AGENT_ID = {stored_agent_id or 'Not Set'}")
            
            if stored_agent_id:
                self.logger.info(f"🔍 Checking for existing voice agent with ID: {stored_agent_id}")
                try:
                    # Try to retrieve the existing voice agent
                    existing_agent = self.agents_client.get_agent(stored_agent_id)
                    if existing_agent:
                        self.logger.info(f"✅ Found existing Azure AI Voice Agent: {existing_agent.name} (ID: {stored_agent_id})")
                        self.azure_voice_agent = existing_agent
                        
                        # Create a new thread for voice sessions
                        self.current_thread = self.agents_client.threads.create()
                        self.logger.info(f"🧵 Created new voice thread: {self.current_thread.id}")
                        
                        return self.azure_voice_agent
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not retrieve stored voice agent {stored_agent_id}: {e}")
                    self.logger.info("🔄 Will create new voice agent")
            
            # Create new Azure AI Voice Agent
            self.logger.info("🎤 Creating new Azure AI Voice Agent...")
            
            # Voice agent configuration with insurance domain expertise
            voice_agent_config = {
                "name": "InsuranceVoiceAssistant",
                "description": "Voice-enabled insurance claims assistant that provides real-time help with claims lookup, document guidance, and insurance explanations",
                "instructions": """You are a helpful voice assistant for insurance claims processing. You can:

1. **Claims Lookup**: Help customers check claim status, find claim details, and track progress
2. **Insurance Definitions**: Explain insurance terms like deductible, premium, coverage types
3. **Document Guidance**: Help with document upload requirements and claim submission

Key behaviors:
- Speak naturally and clearly for voice interactions
- Be empathetic when discussing claims and accidents
- Provide specific, actionable guidance
- Use MCP tools to look up real claim data when available
- Keep responses concise but helpful for voice conversations
- Always confirm important details before taking actions

You have access to MCP tools for database queries and document processing.
""",
                "model": "gpt-4o",  # Use latest model for voice
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "lookup_claim_status",
                            "description": "Look up insurance claim status and details",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "claim_number": {
                                        "type": "string",
                                        "description": "The claim number to look up"
                                    }
                                },
                                "required": ["claim_number"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "explain_insurance_term",
                            "description": "Provide clear explanation of insurance terms",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "term": {
                                        "type": "string",
                                        "description": "The insurance term to explain"
                                    }
                                },
                                "required": ["term"]
                            }
                        }
                    }
                ]
            }
            
            # Create the voice agent
            self.azure_voice_agent = self.agents_client.create_agent(
                model=voice_agent_config["model"],
                name=voice_agent_config["name"],
                description=voice_agent_config["description"],
                instructions=voice_agent_config["instructions"],
                tools=voice_agent_config["tools"]
            )
            
            self.logger.info(f"✅ Created new Azure AI Voice Agent: {self.azure_voice_agent.name}")
            self.logger.info(f"🆔 Voice Agent ID: {self.azure_voice_agent.id}")
            self.logger.info("💡 Consider setting AZURE_VOICE_AGENT_ID={} in .env for persistence".format(self.azure_voice_agent.id))
            
            # Create a thread for voice conversations
            self.current_thread = self.agents_client.threads.create()
            self.logger.info(f"🧵 Created voice conversation thread: {self.current_thread.id}")
            
            return self.azure_voice_agent
            
        except Exception as e:
            self.logger.error(f"❌ Error creating/retrieving Azure AI Voice Agent: {e}")
            self.logger.warning("⚠️ Will use fallback voice processing")
            import traceback
            traceback.print_exc()
            return None
    
    async def initialize(self):
        """Initialize the voice agent"""
        self.logger.info("🎤 Voice Agent Executor initialized with Azure AI Foundry")
        self.logger.info("📋 Ready for voice interactions and MCP tool integration")
        
        if self.azure_voice_agent:
            self.logger.info(f"✅ Azure AI Voice Agent ready: {self.azure_voice_agent.name}")
        else:
            self.logger.info("📱 Using fallback voice processing (Azure AI not available)")
    
    async def execute(self, request_context: RequestContext) -> AsyncGenerator[Any, None]:
        """Execute voice agent request with conversation tracking"""
        self.logger.info("🔄 Voice Agent execute called - Processing voice interaction")
        
        try:
            # Extract request details
            task = request_context.task
            user_message = task.prompt if hasattr(task, 'prompt') else str(task)
            session_id = getattr(request_context, 'session_id', str(uuid.uuid4())[:8])
            
            self.logger.info(f"🎙️ Processing voice request for session {session_id}")
            
            # Start conversation tracking session if not active
            if not conversation_tracker.current_session_id:
                conversation_tracker.start_session({
                    "agent_type": "client_live_voice_agent",
                    "session_source": "a2a_request",
                    "user_session_id": session_id
                })
            
            # Log the incoming user message
            conversation_tracker.log_voice_interaction(
                transcript=user_message,
                audio_metadata={
                    "session_id": session_id,
                    "request_time": datetime.now().isoformat(),
                    "agent": "client_live_voice_agent"
                }
            )
            
            # Create response task
            response_task = new_task("Voice interaction response")
            response_task.status = TaskStatus(state=TaskState.working)
            
            # Process with Azure AI Voice Agent if available
            if self.azure_voice_agent and self.current_thread:
                response_text = await self._process_with_azure_voice_agent(user_message, session_id)
            else:
                # Fallback processing
                response_text = await self._fallback_voice_processing(user_message, session_id)
            
            # Log the agent response
            conversation_tracker.log_agent_response(
                response=response_text,
                response_metadata={
                    "session_id": session_id,
                    "response_time": datetime.now().isoformat(),
                    "agent": "client_live_voice_agent",
                    "azure_ai_used": bool(self.azure_voice_agent and self.current_thread)
                }
            )
            
            # Create response artifact
            response_artifact = new_text_artifact(
                content=response_text,
                title="Voice Response"
            )
            
            # Update task with response
            response_task.status = TaskStatus(state=TaskState.completed)
            response_task.artifacts = [response_artifact]
            
            # Yield response events
            yield TaskStatusUpdateEvent(
                task_id=response_task.task_id,
                status=TaskStatus(state=TaskState.completed)
            )
            
            yield TaskArtifactUpdateEvent(
                task_id=response_task.task_id,
                artifact=response_artifact
            )
            
            self.logger.info(f"✅ Voice interaction completed for session {session_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error in voice agent execution: {e}")
            import traceback
            traceback.print_exc()
            
            # Log the error event
            conversation_tracker.log_system_event(
                event=f"Error in voice agent execution: {str(e)}",
                event_metadata={
                    "error_type": type(e).__name__,
                    "session_id": session_id if 'session_id' in locals() else "unknown",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Yield error response
            error_task = new_task("Voice error response")
            error_task.status = TaskStatus(state=TaskState.failed)
            
            yield TaskStatusUpdateEvent(
                task_id=error_task.task_id,
                status=TaskStatus(state=TaskState.failed)
            )
    
    async def _process_with_azure_voice_agent(self, user_message: str, session_id: str) -> str:
        """Process user message with Azure AI Voice Agent"""
        try:
            self.logger.info(f"🤖 Processing with Azure AI Voice Agent: {user_message[:50]}...")
            
            # Add message to thread
            message = self.agents_client.threads.messages.create(
                thread_id=self.current_thread.id,
                role="user",
                content=user_message
            )
            
            # Run the voice agent
            run = self.agents_client.threads.runs.create(
                thread_id=self.current_thread.id,
                agent_id=self.azure_voice_agent.id
            )
            
            # Wait for completion
            while run.status not in ["completed", "failed", "cancelled"]:
                await asyncio.sleep(0.5)
                run = self.agents_client.threads.runs.retrieve(
                    thread_id=self.current_thread.id,
                    run_id=run.id
                )
            
            if run.status == "completed":
                # Get the response
                messages = self.agents_client.threads.messages.list(
                    thread_id=self.current_thread.id,
                    order="desc",
                    limit=1
                )
                
                if messages.data:
                    response_message = messages.data[0]
                    if response_message.content:
                        response_text = response_message.content[0].text.value
                        self.logger.info(f"✅ Azure AI Voice Agent response generated")
                        return response_text
            
            self.logger.warning("⚠️ Azure AI Voice Agent did not generate response, using fallback")
            return await self._fallback_voice_processing(user_message, session_id)
            
        except Exception as e:
            self.logger.error(f"❌ Error processing with Azure AI Voice Agent: {e}")
            return await self._fallback_voice_processing(user_message, session_id)
    
    async def _fallback_voice_processing(self, user_message: str, session_id: str) -> str:
        """Fallback voice processing when Azure AI is not available"""
        self.logger.info("📱 Using fallback voice processing")
        
        # Simple pattern matching for common insurance requests
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['claim', 'status', 'number']):
            return "I can help you check your claim status. To look up your claim, I'll need your claim number. Can you provide that?"
        
        elif any(word in message_lower for word in ['deductible', 'premium', 'coverage']):
            return "I'd be happy to explain insurance terms. Which specific term would you like me to explain?"
        
        elif any(word in message_lower for word in ['document', 'upload', 'file']):
            return "I can guide you through document submission. What type of documents do you need to submit for your claim?"
        
        elif any(word in message_lower for word in ['help', 'what', 'how']):
            return "I'm here to help with your insurance needs. I can assist with claim lookups, explain insurance terms, and guide you through document submission. What would you like help with?"
        
        else:
            return "I'm your voice assistant for insurance help. I can check claim status, explain insurance terms, and help with documents. How can I assist you today?"

    async def cancel(self, task_id: str) -> None:
        """Cancel a running task - required by AgentExecutor abstract class"""
        self.logger.info(f"🚫 Cancelling voice task: {task_id}")
        
        # Log cancellation event
        conversation_tracker.log_system_event(
            event=f"Task cancelled: {task_id}",
            event_metadata={
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "action": "cancel"
            }
        )
        
        # Implementation for task cancellation
        # For voice agents, we might need to stop audio streams or ongoing Azure AI operations
        # For now, implement as placeholder to satisfy abstract class requirement
        pass

    def cleanup(self):
        """Clean up resources when shutting down"""
        self.logger.info("🧹 Cleaning up Voice Agent Executor resources...")
        
        # End current conversation session
        if conversation_tracker.current_session_id:
            conversation_tracker.log_system_event(
                event="Voice agent shutting down",
                event_metadata={
                    "timestamp": datetime.now().isoformat(),
                    "action": "cleanup"
                }
            )
            conversation_tracker.end_session()
        
        # Add cleanup logic for Azure connections, audio resources, etc.
        pass