"""
Intelligent Claims Orchestrator
Similar to host_agent architecture but for insurance domain
Uses Azure AI Foundry + Semantic Kernel to dynamically route to appropriate agents based on capabilities
"""

import asyncio
import json
import logging
import uuid
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import TaskArtifactUpdateEvent, TaskState, TaskStatus, TaskStatusUpdateEvent
from a2a.utils import new_agent_text_message, new_task, new_text_artifact

from shared.agent_discovery import AgentDiscoveryService
from shared.a2a_client import A2AClient
from shared.mcp_chat_client import mcp_chat_client
from shared.workflow_logger import workflow_logger

# Azure AI Foundry imports
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class IntelligentClaimsOrchestrator(AgentExecutor):
    """
    Intelligent Claims Orchestrator that works like host_agent
    - Uses Azure AI Foundry for intelligent decision making
    - Dynamically discovers available agents
    - Uses AI to route requests to appropriate agents  
    - Handles both chat conversations and claim processing
    - No hardcoded workflows
    """
    
    def __init__(self):
        self.agent_name = "intelligent_claims_orchestrator"
        self.agent_description = "AI-powered orchestrator for insurance operations with dynamic agent routing"
        self.logger = self._setup_logging()
        
        # Dynamic agent discovery
        self.agent_discovery = AgentDiscoveryService(self.logger)
        self.available_agents = {}
        self.agent_capabilities = {}
        
        # A2A client for agent communication
        self.a2a_client = A2AClient(self.agent_name)
        
        # Session management
        self.active_sessions = {}
        
        # Azure AI Foundry setup (like host_agent)
        self.project_client = None
        self.agents_client = None
        self.azure_agent = None
        self.current_thread = None
        self._setup_azure_ai_client()
        
    def _setup_azure_ai_client(self):
        """Setup Azure AI Foundry client like host_agent"""
        try:
            # Get Azure AI configuration from environment - using correct variable names
            subscription_id = os.environ.get("AZURE_AI_AGENT_SUBSCRIPTION_ID")  # Fixed
            resource_group = os.environ.get("AZURE_AI_AGENT_RESOURCE_GROUP_NAME")  # Fixed
            project_name = os.environ.get("AZURE_AI_AGENT_PROJECT_NAME")  # Fixed
            endpoint = os.environ.get("AZURE_AI_AGENT_ENDPOINT")  # Fixed
            
            if not all([subscription_id, resource_group, project_name, endpoint]):
                missing = []
                if not subscription_id: missing.append("AZURE_AI_AGENT_SUBSCRIPTION_ID")
                if not resource_group: missing.append("AZURE_AI_AGENT_RESOURCE_GROUP_NAME") 
                if not project_name: missing.append("AZURE_AI_AGENT_PROJECT_NAME")
                if not endpoint: missing.append("AZURE_AI_AGENT_ENDPOINT")
                
                self.logger.warning(f"⚠️ Azure AI configuration missing: {', '.join(missing)}")
                return
                
            self.logger.info(f"🔧 Using Azure AI endpoint: {endpoint}")
            self.logger.info(f"🔧 Project: {project_name} in {resource_group}")
            
            # Create project client with correct endpoint
            self.project_client = AIProjectClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential(),
                subscription_id=subscription_id,
                resource_group_name=resource_group,
                project_name=project_name
            )
            
            # Use the project client's agents interface
            self.agents_client = self.project_client.agents
            self.logger.info("✅ Azure AI Foundry client initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Error setting up Azure AI client: {e}")
            self.logger.warning("⚠️ Will continue without Azure AI Foundry - using fallback logic")
        
    def _setup_logging(self) -> logging.Logger:
        """Setup colored logging for the agent"""
        logger = logging.getLogger(f"IntelligentOrchestrator.{self.agent_name}")
        formatter = logging.Formatter(
            f"🧠 [INTELLIGENT-ORCHESTRATOR] %(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def create_azure_agent(self):
        """Create an Azure AI Agent instance like host_agent does"""
        if not self.agents_client:
            self.logger.warning("⚠️ Azure AI client not available - skipping agent creation")
            return None
            
        instructions = self.get_routing_instructions()
        
        try:
            # Get model from environment (using correct variable name)
            model_name = os.environ.get("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-4")
            self.logger.info(f"🤖 Creating Azure AI agent with model: {model_name}")
            
            # Create tool definitions for agent functions
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "route_to_agent",
                        "description": "Routes a request to a specific insurance agent",
                        "parameters": {
                            "type": "object", 
                            "properties": {
                                "agent_name": {
                                    "type": "string",
                                    "description": "The name of the agent to route to (e.g., intake_clarifier, document_intelligence, coverage_rules_engine)"
                                },
                                "task": {
                                    "type": "string", 
                                    "description": "The task description to send to the agent"
                                },
                                "task_type": {
                                    "type": "string",
                                    "description": "The type of task (e.g., claim_intake, document_analysis, coverage_evaluation)"
                                }
                            },
                            "required": ["agent_name", "task"]
                        }
                    }
                },
                {
                    "type": "function", 
                    "function": {
                        "name": "query_insurance_data",
                        "description": "Queries the insurance database using MCP tools",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The natural language query to search the insurance database"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "process_claim_workflow", 
                        "description": "Processes an insurance claim through multiple agents intelligently",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "claim_request": {
                                    "type": "string",
                                    "description": "The claim processing request"
                                },
                                "workflow_type": {
                                    "type": "string", 
                                    "description": "The type of workflow (e.g., auto_claim, property_claim, health_claim)"
                                }
                            },
                            "required": ["claim_request"]
                        }
                    }
                }
            ]
            
            # Create the Azure AI agent
            self.azure_agent = self.agents_client.create_agent(
                model=model_name,
                name="intelligent-claims-orchestrator", 
                instructions=instructions,
                tools=tools
            )
            
            self.logger.info(f"✅ Created Azure AI agent, ID: {self.azure_agent.id}")
            
            # Create a thread for conversation
            self.current_thread = self.agents_client.threads.create()
            self.logger.info(f"✅ Created conversation thread, ID: {self.current_thread.id}")
            
            return self.azure_agent
            
        except Exception as e:
            self.logger.error(f"❌ Error creating Azure AI agent: {e}")
            self.logger.error(f"Model name: {model_name}")
            self.logger.error(f"Instructions length: {len(instructions)} characters")
            raise
        
    async def initialize(self):
        """Initialize the orchestrator by discovering available agents"""
        try:
            self.logger.info("🔍 Discovering available agents...")
            discovered_agents = await self.agent_discovery.discover_all_agents()  # Fixed method name
            
            for agent_name, agent_info in discovered_agents.items():
                if agent_name:
                    self.available_agents[agent_name] = agent_info
                    # Extract capabilities from skills if available
                    skills = agent_info.get('skills', [])
                    capabilities = [skill.get('name', '') for skill in skills if skill.get('name')]
                    self.agent_capabilities[agent_name] = capabilities
            
            self.logger.info(f"✅ Discovered {len(self.available_agents)} agents: {list(self.available_agents.keys())}")
            
        except Exception as e:
            self.logger.error(f"❌ Error discovering agents: {e}")
            
    def get_routing_instructions(self) -> str:
        """Generate AI instructions for intelligent routing"""
        agents_info = []
        for name, info in self.available_agents.items():
            capabilities = ", ".join(self.agent_capabilities.get(name, []))
            agents_info.append(f"- {name}: {info.get('description', 'No description')} | Capabilities: {capabilities}")
        
        agents_list = "\n".join(agents_info) if agents_info else "No agents available"
        
        return f"""You are an Intelligent Insurance Claims Orchestrator.

Your role:
- Analyze employee requests and determine the best agent(s) to handle them
- Route requests to appropriate specialized agents
- Handle natural conversations about insurance operations
- Provide helpful responses by delegating to the right specialists

Available Agents:
{agents_list}

Guidelines:
- For general questions about capabilities, answer directly
- For claim processing, route to intake_clarifier first, then other agents as needed
- For document analysis, use document_intelligence agent
- For coverage questions, use coverage_rules_engine
- For data queries, use MCP tools to query Cosmos DB
- Always explain what agent(s) you're consulting

Be conversational and helpful, like a knowledgeable colleague."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Main execution method - handles both chat and processing requests intelligently
        """
        try:
            # Initialize if not done yet
            if not self.available_agents:
                await self.initialize()
            
            # Extract message from context
            message = context.message
            user_input = context.get_user_input()
            session_id = getattr(message, 'sessionId', str(uuid.uuid4()))
            
            self.logger.info(f"🤖 Processing request from session {session_id}: {user_input[:100]}...")
            
            # Get or create task
            task = context.current_task
            if not task:
                task = new_task(message)
                await event_queue.enqueue_event(task)
            
            # Update task status
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task.id, 
                    status=TaskStatus(state=TaskState.working),
                    contextId=context.context_id if hasattr(context, 'context_id') else session_id,
                    final=False
                )
            )
            
            # Process the request intelligently
            response = await self._process_intelligent_request(user_input, session_id)
            
            # Create response artifact with correct parameters (task_id, content)
            response_text = json.dumps(response, indent=2)
            artifact = new_text_artifact(task.id, response_text)
            
            # Send response
            response_message = new_agent_text_message(response_text)
            await event_queue.enqueue_event(response_message)
            
            # Update task completion based on response status
            if response.get("status") == "error":
                # Mark task as failed if there was an error
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        task_id=task.id, 
                        status=TaskStatus(state=TaskState.failed),
                        contextId=context.context_id if hasattr(context, 'context_id') else session_id,
                        final=True
                    )
                )
            else:
                # Update task completion for successful responses
                await event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        taskId=task.id,
                        artifact=artifact,
                        contextId=context.context_id if hasattr(context, 'context_id') else session_id
                    )
                )
                
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        task_id=task.id, 
                        status=TaskStatus(state=TaskState.completed),
                        contextId=context.context_id if hasattr(context, 'context_id') else session_id,
                        final=True
                    )
                )
            
        except Exception as e:
            self.logger.error(f"❌ Error in execute: {e}")
            # Send error response
            error_response = {
                "status": "error",
                "message": f"Error processing request: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            error_text = json.dumps(error_response)
            error_message = new_agent_text_message(error_text)
            await event_queue.enqueue_event(error_message)
            
            # Mark task as failed, not completed
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task.id if 'task' in locals() and task else str(uuid.uuid4()), 
                    status=TaskStatus(state=TaskState.failed),  # Mark as failed, not completed
                    contextId=context.context_id if hasattr(context, 'context_id') else session_id,
                    final=True
                )
            )
            
    async def _process_intelligent_request(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """
        Process request using Azure AI-powered intelligent routing
        This replaces the hardcoded routing logic with AI decision making
        """
        try:
            # Clean up the input - extract actual user query if it's a chat format
            actual_query = user_input
            if 'Chat Query:' in user_input:
                actual_query = user_input.split('Chat Query:')[1].split('\n')[0].strip()
            elif 'chat conversation' in user_input.lower():
                # Extract the actual question from chat format
                lines = user_input.split('\n')
                for line in lines:
                    if line.strip() and 'context:' not in line.lower() and 'chat query:' not in line.lower():
                        actual_query = line.strip()
                        break
            
            self.logger.info(f"🎯 Processing query with Azure AI: {actual_query}")
            
            # Use Azure AI agent for intelligent routing if available
            if self.azure_agent and self.current_thread:
                return await self._use_azure_ai_routing(actual_query, session_id)
            else:
                # Fallback to simple routing logic
                self.logger.warning("⚠️ Azure AI not available, using fallback routing")
                return await self._fallback_routing(actual_query, session_id)
                
        except Exception as e:
            self.logger.error(f"❌ Error in intelligent processing: {e}")
            return {
                "status": "error",
                "message": f"Error processing request: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _use_azure_ai_routing(self, query: str, session_id: str) -> Dict[str, Any]:
        """Use Azure AI agent for intelligent routing decisions"""
        try:
            self.logger.info("🧠 Using Azure AI for intelligent routing...")
            
            # Create a new thread for this request to avoid state conflicts
            request_thread = self.agents_client.threads.create()
            self.logger.info(f"🧵 Created new thread for request: {request_thread.id}")
            
            # Send message to Azure AI agent
            user_message = f"Employee request: {query}\n\nSession ID: {session_id}\n\nPlease analyze this request and determine the best way to help. Use your available tools if needed."
            
            # Create message using the correct API
            message = self.agents_client.messages.create(
                thread_id=request_thread.id,
                role="user", 
                content=user_message
            )
            
            # Run the agent
            run = self.agents_client.runs.create(
                thread_id=request_thread.id,
                agent_id=self.azure_agent.id
            )
            
            # Poll for completion
            max_attempts = 30  # 30 seconds timeout
            attempt = 0
            while run.status in ["queued", "in_progress", "requires_action"] and attempt < max_attempts:
                await asyncio.sleep(1)
                run = self.agents_client.runs.get(
                    thread_id=request_thread.id,
                    run_id=run.id
                )
                attempt += 1
            
            # Process the response
            if run.status == "completed":
                # Get the assistant's response
                messages = self.agents_client.messages.list(
                    thread_id=request_thread.id,
                    order="desc",
                    limit=1
                )
                
                # Convert ItemPaged to list and get the first message
                messages_list = list(messages)
                if messages_list and messages_list[0].role == "assistant":
                    assistant_response = ""
                    for content in messages_list[0].content:
                        if hasattr(content, 'text'):
                            assistant_response += content.text.value
                    
                    return {
                        "status": "success",
                        "response_type": "azure_ai_response",
                        "message": assistant_response,
                        "ai_powered": True,
                        "original_query": query,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Handle tool calls if any
            elif run.status == "requires_action":
                return await self._handle_azure_tool_calls(run, request_thread, query, session_id)
            
            else:
                self.logger.error(f"❌ Azure AI run failed with status: {run.status}")
                return {
                    "status": "error",
                    "message": f"Azure AI processing failed with status: {run.status}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error using Azure AI routing: {e}")
            return {
                "status": "error", 
                "message": f"Error processing request: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_azure_tool_calls(self, run, request_thread, query: str, session_id: str) -> Dict[str, Any]:
        """Handle tool calls from Azure AI agent"""
        try:
            tool_outputs = []
            
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                self.logger.info(f"🔧 Azure AI requesting tool: {function_name} with args: {function_args}")
                
                # Handle each tool function
                if function_name == "route_to_agent":
                    result = await self._route_to_agent(
                        query, 
                        function_args["agent_name"], 
                        function_args.get("task_type", "general"),
                        session_id
                    )
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result)
                    })
                
                elif function_name == "query_insurance_data":
                    result = await self._handle_mcp_query(function_args["query"])
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result)
                    })
                
                elif function_name == "process_claim_workflow":
                    result = await self._execute_claim_processing_workflow(
                        function_args["claim_request"],
                        session_id, 
                        {"workflow_type": function_args.get("workflow_type", "general_claim")}
                    )
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result)
                    })
            
            # Submit tool outputs and continue the run
            if tool_outputs:
                run = self.agents_client.runs.submit_tool_outputs(
                    thread_id=request_thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
                
                # Get the final response
                if run.status == "completed":
                    messages = self.agents_client.messages.list(
                        thread_id=request_thread.id,
                        order="desc",
                        limit=1
                    )
                    
                    # Convert ItemPaged to list and get the first message
                    messages_list = list(messages)
                    if messages_list and messages_list[0].role == "assistant":
                        assistant_response = ""
                        for content in messages_list[0].content:
                            if hasattr(content, 'text'):
                                assistant_response += content.text.value
                        
                        return {
                            "status": "success",
                            "response_type": "azure_ai_with_tools",
                            "message": assistant_response,
                            "tools_used": [tc.function.name for tc in run.required_action.submit_tool_outputs.tool_calls],
                            "ai_powered": True,
                            "original_query": query,
                            "timestamp": datetime.now().isoformat()
                        }
            
            return await self._fallback_routing(query, session_id)
            
        except Exception as e:
            self.logger.error(f"❌ Error handling tool calls: {e}")
            return await self._fallback_routing(query, session_id)
    
    async def _fallback_routing(self, query: str, session_id: str) -> Dict[str, Any]:
        """Fallback routing when Azure AI is not available"""
        try:
            self.logger.info("⚠️ Using fallback routing logic")
            
            query_lower = query.lower()
            
            # Simple pattern matching for fallback
            if any(word in query_lower for word in ['capabilities', 'what can you do', 'help', 'about']):
                return await self._handle_direct_response(query, {'response_type': 'capabilities'})
            
            elif any(word in query_lower for word in ['claim', 'process claim', 'file claim']):
                return await self._execute_claim_processing_workflow(query, session_id, {})
            
            elif any(word in query_lower for word in ['data', 'query', 'search', 'find']):
                return await self._handle_mcp_query(query)
            
            else:
                return await self._handle_direct_response(query, {'response_type': 'general'})
                
        except Exception as e:
            self.logger.error(f"❌ Error in fallback routing: {e}")
            return {
                "status": "error",
                "message": f"Error processing request: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def cleanup(self):
        """Clean up Azure AI agent resources like host_agent does"""
        try:
            if hasattr(self, 'azure_agent') and self.azure_agent and hasattr(self, 'agents_client') and self.agents_client:
                self.agents_client.delete_agent(self.azure_agent.id)
                self.logger.info(f"🗑️ Deleted Azure AI agent: {self.azure_agent.id}")
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up agent: {e}")
        finally:
            # Close the client to clean up resources
            if hasattr(self, 'agents_client') and self.agents_client:
                try:
                    self.agents_client.close()
                    self.logger.info("🔒 Azure AI client closed")
                except Exception as e:
                    self.logger.error(f"❌ Error closing client: {e}")
            
            if hasattr(self, 'azure_agent'):
                self.azure_agent = None
            if hasattr(self, 'current_thread'):
                self.current_thread = None

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
    
    async def cancel(self, task_id: str) -> None:
        """Cancel a running task - required by AgentExecutor abstract class"""
        self.logger.info(f"🚫 Cancelling task: {task_id}")
        # Implementation for task cancellation
        # In this case, we don't have long-running tasks to cancel
        # but we implement it to satisfy the abstract class requirement
        pass
            
    async def _make_routing_decision(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        AI-powered routing decision making
        This replaces hardcoded if/else routing logic
        """
        query_lower = query.lower()
        
        # Capabilities/general questions - handle directly
        if any(word in query_lower for word in ['capabilities', 'what can you do', 'help', 'about', 'who are you']):
            return {
                'action': 'direct_response',
                'response_type': 'capabilities',
                'reasoning': 'User asking about system capabilities'
            }
        
        # Claim processing workflow
        if any(word in query_lower for word in ['claim', 'process claim', 'file claim', 'submit claim']):
            return {
                'action': 'multi_agent_workflow',
                'workflow_type': 'claim_processing',
                'agents': ['intake_clarifier', 'document_intelligence', 'coverage_rules_engine'],
                'reasoning': 'Claim processing requires multi-agent workflow'
            }
        
        # Document analysis
        if any(word in query_lower for word in ['document', 'pdf', 'image', 'analyze document']):
            return {
                'action': 'route_to_agent',
                'agent': 'document_intelligence',
                'task_type': 'document_analysis',
                'reasoning': 'Document analysis task'
            }
        
        # Coverage questions
        if any(word in query_lower for word in ['coverage', 'policy', 'covered', 'eligible']):
            return {
                'action': 'route_to_agent',
                'agent': 'coverage_rules_engine',
                'task_type': 'coverage_evaluation',
                'reasoning': 'Coverage-related question'
            }
        
        # Data queries
        if any(word in query_lower for word in ['data', 'query', 'search', 'find', 'database', 'records']):
            return {
                'action': 'mcp_query',
                'reasoning': 'Data query request - use MCP tools'
            }
        
        # Default to general conversation
        return {
            'action': 'direct_response',
            'response_type': 'general',
            'reasoning': 'General conversation or unclear intent'
        }
        
    async def _handle_direct_response(self, query: str, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Handle responses that don't require agent routing"""
        if decision.get('response_type') == 'capabilities':
            return {
                "status": "success",
                "response_type": "capabilities",
                "message": f"""I'm the Intelligent Claims Orchestrator for our insurance system. Here are my capabilities:

🧠 **Intelligent Routing**: I analyze your requests and automatically route them to the right specialist agents

📋 **Available Agents I Can Consult**:
{self._format_agent_list()}

💬 **What I Can Help With**:
- Process insurance claims end-to-end
- Analyze documents and images  
- Check coverage eligibility and rules
- Query insurance data and records
- Answer questions about policies and procedures
- Route complex requests to specialized agents

🤖 **How I Work**:
Unlike traditional systems with fixed workflows, I use AI-powered decision making to determine which agents to involve based on your specific needs.

Just ask me anything about insurance operations, and I'll figure out the best way to help you!""",
                "available_agents": list(self.available_agents.keys()),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "success", 
                "response_type": "general",
                "message": f"I understand you're asking about: '{query}'. How can I help you with this? I can process claims, analyze documents, check coverage, or query our database.",
                "suggestions": [
                    "Process a new claim",
                    "Check policy coverage", 
                    "Analyze a document",
                    "Query insurance data"
                ],
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_mcp_query(self, query: str) -> Dict[str, Any]:
        """Handle data queries using MCP tools"""
        try:
            self.logger.info(f"🔍 Processing MCP query: {query}")
            result = await mcp_chat_client.query_cosmos_data(query)
            
            return {
                "status": "success",
                "response_type": "data_query",
                "message": f"Here's what I found in our database:\n\n{result}",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "response_type": "data_query", 
                "message": f"I encountered an issue querying the database: {str(e)}",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
    
    def _format_agent_list(self) -> str:
        """Format available agents for display"""
        if not self.available_agents:
            return "- No agents currently available"
        
        agent_list = []
        for name, info in self.available_agents.items():
            capabilities = self.agent_capabilities.get(name, [])
            caps_str = ", ".join(capabilities) if capabilities else "General purpose"
            agent_list.append(f"- **{name}**: {info.get('description', 'No description')} ({caps_str})")
        
        return "\n".join(agent_list)
    
    async def _route_to_agent(self, query: str, agent_name: str, task_type: str, session_id: str) -> Dict[str, Any]:
        """Route request to a specific agent"""
        try:
            if agent_name not in self.available_agents:
                return {
                    "status": "error",
                    "message": f"Agent '{agent_name}' is not available",
                    "available_agents": list(self.available_agents.keys()),
                    "timestamp": datetime.now().isoformat()
                }
            
            self.logger.info(f"🎯 Routing to {agent_name} for {task_type}")
            
            # Prepare agent-specific payload
            agent_payload = {
                "action": task_type,
                "query": query,
                "session_id": session_id,
                "context": f"Request from intelligent orchestrator: {query}"
            }
            
            # Call the agent using A2A
            agent_response = await self.a2a_client.send_request(
                target_agent=agent_name,
                task=f"{task_type}: {query}",
                parameters=agent_payload
            )
            
            return {
                "status": "success",
                "response_type": "agent_response",
                "message": f"I consulted our {agent_name} specialist and here's what they found:\n\n{agent_response}",
                "agent_used": agent_name,
                "task_type": task_type,
                "original_query": query,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error routing to {agent_name}: {e}")
            return {
                "status": "error",
                "message": f"I had trouble consulting our {agent_name} specialist: {str(e)}",
                "agent_name": agent_name,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _execute_multi_agent_workflow(self, query: str, agents: List[str], workflow_type: str, session_id: str) -> Dict[str, Any]:
        """Execute a workflow involving multiple agents (like claim processing)"""
        try:
            self.logger.info(f"🔄 Executing {workflow_type} workflow with agents: {agents}")
            
            workflow_results = {
                "workflow_type": workflow_type,
                "agents_involved": agents,
                "steps": [],
                "status": "in_progress"
            }
            
            # Dynamic workflow execution based on workflow type
            if workflow_type == "claim_processing":
                return await self._execute_claim_processing_workflow(query, session_id, workflow_results)
            else:
                # Generic multi-agent workflow
                return await self._execute_generic_workflow(query, agents, session_id, workflow_results)
                
        except Exception as e:
            self.logger.error(f"❌ Error in multi-agent workflow: {e}")
            return {
                "status": "error",
                "message": f"Error executing {workflow_type} workflow: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _execute_claim_processing_workflow(self, query: str, session_id: str, workflow_results: Dict = None) -> Dict[str, Any]:
        """Execute intelligent claim processing workflow"""
        try:
            # Initialize workflow_results if not provided
            if workflow_results is None:
                workflow_results = {
                    "workflow_type": "claim_processing",
                    "agents_involved": [],
                    "steps": [],
                    "status": "in_progress"
                }
            
            # Ensure workflow_results has the required structure
            if not isinstance(workflow_results, dict):
                self.logger.error(f"❌ Invalid workflow_results type: {type(workflow_results)}")
                workflow_results = {
                    "workflow_type": "claim_processing",
                    "agents_involved": [],
                    "steps": [],
                    "status": "in_progress"
                }
            
            if "steps" not in workflow_results:
                workflow_results["steps"] = []
            
            self.logger.info(f"🔍 Starting workflow with {len(workflow_results['steps'])} existing steps")
            
            claim_data = {
                "claim_id": f"CLAIM_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "initial_request": query,
                "session_id": session_id
            }
            
            # Step 1: Intake clarification (if needed)
            if 'intake_clarifier' in self.available_agents:
                self.logger.info("📋 Consulting intake clarifier...")
                try:
                    clarification_result = await self._route_to_agent(
                        query, 'intake_clarifier', 'claim_intake', session_id
                    )
                    self.logger.info(f"🔍 Clarification result type: {type(clarification_result)}")
                    self.logger.info(f"🔍 Clarification result keys: {clarification_result.keys() if isinstance(clarification_result, dict) else 'Not a dict'}")
                    
                    workflow_results["steps"].append({
                        "step": "intake_clarification",
                        "agent": "intake_clarifier",
                        "status": clarification_result.get("status", "completed") if isinstance(clarification_result, dict) else "completed",
                        "result": clarification_result
                    })
                except Exception as step_error:
                    self.logger.error(f"❌ Error in intake clarification step: {step_error}")
                    workflow_results["steps"].append({
                        "step": "intake_clarification", 
                        "agent": "intake_clarifier",
                        "status": "failed",
                        "error": str(step_error)
                    })
            
            # Step 2: Document analysis (if documents mentioned or needed)
            if any(word in query.lower() for word in ['document', 'attachment', 'pdf', 'image']):
                if 'document_intelligence' in self.available_agents:
                    self.logger.info("📄 Analyzing documents...")
                    try:
                        doc_result = await self._route_to_agent(
                            query, 'document_intelligence', 'document_analysis', session_id
                        )
                        workflow_results["steps"].append({
                            "step": "document_analysis", 
                            "agent": "document_intelligence",
                            "status": doc_result.get("status", "completed") if isinstance(doc_result, dict) else "completed",
                            "result": doc_result
                        })
                    except Exception as step_error:
                        self.logger.error(f"❌ Error in document analysis step: {step_error}")
                        workflow_results["steps"].append({
                            "step": "document_analysis",
                            "agent": "document_intelligence", 
                            "status": "failed",
                            "error": str(step_error)
                        })
            
            # Step 3: Coverage validation
            if 'coverage_rules_engine' in self.available_agents:
                self.logger.info("🛡️ Validating coverage...")
                try:
                    coverage_result = await self._route_to_agent(
                        query, 'coverage_rules_engine', 'coverage_evaluation', session_id
                    )
                    workflow_results["steps"].append({
                        "step": "coverage_validation",
                        "agent": "coverage_rules_engine", 
                        "status": coverage_result.get("status", "completed") if isinstance(coverage_result, dict) else "completed",
                        "result": coverage_result
                    })
                except Exception as step_error:
                    self.logger.error(f"❌ Error in coverage validation step: {step_error}")
                    workflow_results["steps"].append({
                        "step": "coverage_validation",
                        "agent": "coverage_rules_engine",
                        "status": "failed", 
                        "error": str(step_error)
                    })
            
            workflow_results["status"] = "completed"
            workflow_results["final_decision"] = "Claim processed through intelligent workflow"
            
            # Format final response
            steps_summary = []
            for step in workflow_results["steps"]:
                agent_name = step["agent"].replace('_', ' ').title()
                steps_summary.append(f"✅ **{step['step'].replace('_', ' ').title()}** ({agent_name})")
            
            return {
                "status": "success",
                "response_type": "claim_processing",
                "message": f"""I've processed your claim request through our intelligent workflow:

**Claim ID**: {claim_data['claim_id']}

**Processing Steps Completed**:
{chr(10).join(steps_summary)}

The claim has been successfully processed using our AI-powered routing system. Each specialist agent was consulted based on the specific requirements of your request.""",
                "claim_id": claim_data['claim_id'],
                "workflow_results": workflow_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error in claim processing workflow: {e}")
            return {
                "status": "error",
                "message": f"Error processing claim: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _execute_generic_workflow(self, query: str, agents: List[str], session_id: str, workflow_results: Dict) -> Dict[str, Any]:
        """Execute a generic multi-agent workflow"""
        results = []
        
        for agent_name in agents:
            if agent_name in self.available_agents:
                result = await self._route_to_agent(query, agent_name, "general", session_id)
                results.append({
                    "agent": agent_name,
                    "result": result
                })
                workflow_results["steps"].append({
                    "step": f"consult_{agent_name}",
                    "agent": agent_name,
                    "status": result.get("status", "completed"),
                    "result": result
                })
        
        return {
            "status": "success",
            "response_type": "multi_agent_workflow",
            "message": f"I consulted {len(results)} specialist agents for your request.",
            "agents_consulted": agents,
            "workflow_results": workflow_results,
            "timestamp": datetime.now().isoformat()
        }
