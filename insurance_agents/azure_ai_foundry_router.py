"""
Azure AI Foundry Agent Router
Dynamic agent selection and routing based on agent cards and capabilities
Similar to host_agent but for cloud-hosted Azure AI Foundry agents
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from dataclasses import dataclass
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

@dataclass
class AgentCapability:
    """Represents an agent capability parsed from agent card"""
    skill_id: str
    name: str
    description: str
    tags: List[str]
    agent_id: str
    agent_endpoint: str

@dataclass
class RoutingDecision:
    """Represents a routing decision"""
    selected_agent: str
    confidence: float
    reasoning: str
    fallback_agents: List[str]

class AzureAIFoundryAgentRouter:
    """
    Dynamic agent router for Azure AI Foundry agents
    Discovers agents via agent cards and routes requests based on capabilities
    """
    
    def __init__(self, project_endpoint: str):
        self.project_endpoint = project_endpoint
        self.client = AIProjectClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential()
        )
        
        # Dynamic agent registry
        self.discovered_agents: Dict[str, Dict] = {}
        self.agent_capabilities: Dict[str, List[AgentCapability]] = {}
        self.capability_index: Dict[str, List[AgentCapability]] = {}
        
        # Routing intelligence
        self.routing_history: List[Dict] = []
        self.agent_performance: Dict[str, Dict] = {}
        
    async def discover_agents(self) -> Dict[str, Dict]:
        """
        Discover all Azure AI Foundry agents and their capabilities
        Similar to how host_agent discovers remote_agents
        """
        logger.info("🔍 Discovering Azure AI Foundry agents...")
        
        try:
            # Get all agents from Azure AI Foundry project
            agents = self.client.agents.list_agents()
            
            for agent in agents:
                await self._process_agent_card(agent)
                
            logger.info(f"✅ Discovered {len(self.discovered_agents)} agents")
            return self.discovered_agents
            
        except Exception as e:
            logger.error(f"❌ Failed to discover agents: {str(e)}")
            return {}
    
    async def _process_agent_card(self, agent) -> None:
        """Process an individual agent and build capability index"""
        try:
            agent_id = agent.id
            agent_name = agent.name or f"Agent-{agent_id[:8]}"
            
            # Get agent details and capabilities
            agent_details = self.client.agents.get_agent(agent_id)
            
            # Parse agent card/capabilities
            agent_info = {
                "id": agent_id,
                "name": agent_name,
                "description": agent_details.description or "",
                "model": agent_details.model,
                "instructions": agent_details.instructions[:200] + "..." if len(agent_details.instructions) > 200 else agent_details.instructions,
                "tools": agent_details.tools or [],
                "endpoint": f"{self.project_endpoint}/agents/{agent_id}",
                "status": "online",
                "capabilities": []
            }
            
            # Extract capabilities from instructions and tools
            capabilities = self._extract_capabilities(agent_details)
            agent_info["capabilities"] = capabilities
            
            # Store in registry
            self.discovered_agents[agent_id] = agent_info
            self.agent_capabilities[agent_id] = capabilities
            
            # Build capability index for routing
            for capability in capabilities:
                for tag in capability.tags:
                    if tag not in self.capability_index:
                        self.capability_index[tag] = []
                    self.capability_index[tag].append(capability)
            
            logger.info(f"📋 Processed agent: {agent_name} with {len(capabilities)} capabilities")
            
        except Exception as e:
            logger.error(f"❌ Failed to process agent {agent.id}: {str(e)}")
    
    def _extract_capabilities(self, agent_details) -> List[AgentCapability]:
        """Extract capabilities from agent instructions and tools"""
        capabilities = []
        
        # Analyze instructions for capabilities
        instructions = agent_details.instructions.lower()
        
        # Map instruction keywords to capabilities
        capability_mapping = {
            "orchestrat": {"skill": "workflow_orchestration", "tags": ["orchestration", "workflow", "coordination"]},
            "clarif": {"skill": "claim_clarification", "tags": ["clarification", "validation", "intake"]},
            "document": {"skill": "document_analysis", "tags": ["document", "analysis", "ocr", "extraction"]},
            "coverage": {"skill": "coverage_evaluation", "tags": ["coverage", "rules", "policy", "evaluation"]},
            "fraud": {"skill": "fraud_detection", "tags": ["fraud", "detection", "risk", "assessment"]},
            "damage": {"skill": "damage_assessment", "tags": ["damage", "assessment", "images", "inspection"]},
            "form": {"skill": "form_recognition", "tags": ["form", "recognition", "fields", "extraction"]},
            "rules": {"skill": "rules_execution", "tags": ["rules", "execution", "business", "decision"]},
            "policy": {"skill": "policy_analysis", "tags": ["policy", "analysis", "terms", "conditions"]}
        }
        
        for keyword, capability_info in capability_mapping.items():
            if keyword in instructions:
                capability = AgentCapability(
                    skill_id=capability_info["skill"],
                    name=capability_info["skill"].replace("_", " ").title(),
                    description=f"Agent capability for {capability_info['skill']}",
                    tags=capability_info["tags"],
                    agent_id=agent_details.id,
                    agent_endpoint=f"{self.project_endpoint}/agents/{agent_details.id}"
                )
                capabilities.append(capability)
        
        # Add tool-based capabilities
        for tool in agent_details.tools or []:
            if tool.get("type") == "function":
                func_name = tool.get("function", {}).get("name", "")
                capability = AgentCapability(
                    skill_id=f"tool_{func_name}",
                    name=func_name.replace("_", " ").title(),
                    description=tool.get("function", {}).get("description", ""),
                    tags=[func_name, "tool", "function"],
                    agent_id=agent_details.id,
                    agent_endpoint=f"{self.project_endpoint}/agents/{agent_details.id}"
                )
                capabilities.append(capability)
        
        return capabilities
    
    async def route_request(self, user_request: str, context: Dict = None) -> RoutingDecision:
        """
        Dynamically route user request to best agent based on capabilities
        Similar to host_agent's routing logic
        """
        logger.info(f"🎯 Routing request: {user_request[:100]}...")
        
        # Analyze request to determine required capabilities
        required_capabilities = self._analyze_request_capabilities(user_request)
        
        # Score agents based on capability match
        agent_scores = self._score_agents(required_capabilities, context)
        
        # Select best agent
        if agent_scores:
            best_agent = max(agent_scores.items(), key=lambda x: x[1]["score"])
            agent_id, score_info = best_agent
            
            decision = RoutingDecision(
                selected_agent=agent_id,
                confidence=score_info["score"],
                reasoning=score_info["reasoning"],
                fallback_agents=[aid for aid, _ in sorted(agent_scores.items(), key=lambda x: x[1]["score"], reverse=True)[1:3]]
            )
            
            # Record routing decision
            self.routing_history.append({
                "timestamp": datetime.now().isoformat(),
                "request": user_request,
                "decision": decision.__dict__,
                "all_scores": agent_scores
            })
            
            logger.info(f"✅ Selected agent: {self.discovered_agents[agent_id]['name']} (confidence: {decision.confidence:.2f})")
            return decision
        
        else:
            logger.warning("⚠️ No suitable agent found for request")
            return RoutingDecision(
                selected_agent="",
                confidence=0.0,
                reasoning="No agent capabilities matched the request",
                fallback_agents=[]
            )
    
    def _analyze_request_capabilities(self, request: str) -> List[str]:
        """Analyze user request to determine required capabilities"""
        request_lower = request.lower()
        
        # Capability keywords mapping
        capability_keywords = {
            "workflow": ["process", "workflow", "orchestrate", "coordinate", "manage"],
            "clarification": ["clarify", "validate", "check", "verify", "confirm"],
            "document": ["document", "file", "pdf", "image", "scan", "text", "extract"],
            "coverage": ["coverage", "policy", "eligible", "covered", "benefits"],
            "fraud": ["fraud", "suspicious", "risk", "anomaly", "unusual"],
            "damage": ["damage", "inspect", "assess", "photo", "image", "repair"],
            "form": ["form", "field", "data", "fill", "complete"],
            "rules": ["rule", "condition", "evaluate", "decide", "determine"],
            "analysis": ["analyze", "review", "examine", "study", "investigate"]
        }
        
        required_capabilities = []
        for capability, keywords in capability_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                required_capabilities.append(capability)
        
        return required_capabilities
    
    def _score_agents(self, required_capabilities: List[str], context: Dict = None) -> Dict[str, Dict]:
        """Score agents based on capability match and performance history"""
        agent_scores = {}
        
        for agent_id, capabilities in self.agent_capabilities.items():
            score = 0.0
            reasoning_parts = []
            
            # Base capability matching
            agent_tags = []
            for cap in capabilities:
                agent_tags.extend(cap.tags)
            
            for required_cap in required_capabilities:
                if required_cap in agent_tags:
                    score += 1.0
                    reasoning_parts.append(f"matches {required_cap}")
                elif any(required_cap in tag for tag in agent_tags):
                    score += 0.5
                    reasoning_parts.append(f"partially matches {required_cap}")
            
            # Performance history adjustment
            if agent_id in self.agent_performance:
                perf = self.agent_performance[agent_id]
                success_rate = perf.get("success_rate", 0.5)
                score *= (0.5 + success_rate)
                reasoning_parts.append(f"success rate: {success_rate:.1%}")
            
            # Context-based adjustments
            if context:
                if context.get("priority") == "high" and "orchestration" in agent_tags:
                    score += 0.5
                    reasoning_parts.append("high priority orchestration")
                
                if context.get("claim_type") == "complex" and "analysis" in agent_tags:
                    score += 0.3
                    reasoning_parts.append("complex analysis needed")
            
            if score > 0:
                agent_scores[agent_id] = {
                    "score": score,
                    "reasoning": "; ".join(reasoning_parts)
                }
        
        return agent_scores
    
    async def execute_with_agent(self, agent_id: str, request: str, thread_id: str = None) -> Dict:
        """
        Execute request with selected Azure AI Foundry agent
        """
        try:
            agent_info = self.discovered_agents.get(agent_id)
            if not agent_info:
                raise ValueError(f"Agent {agent_id} not found")
            
            logger.info(f"🚀 Executing with agent: {agent_info['name']}")
            
            # Create or use existing thread
            if not thread_id:
                thread = self.client.agents.create_thread()
                thread_id = thread.id
            
            # Send message to agent
            message = self.client.agents.create_message(
                thread_id=thread_id,
                role="user",
                content=request
            )
            
            # Run the agent
            run = self.client.agents.create_run(
                thread_id=thread_id,
                assistant_id=agent_id
            )
            
            # Wait for completion
            completed_run = self.client.agents.get_run(thread_id=thread_id, run_id=run.id)
            while completed_run.status in ["queued", "in_progress", "requires_action"]:
                await asyncio.sleep(1)
                completed_run = self.client.agents.get_run(thread_id=thread_id, run_id=run.id)
            
            # Get response
            messages = self.client.agents.list_messages(thread_id=thread_id)
            latest_message = messages.data[0] if messages.data else None
            
            result = {
                "status": "success",
                "agent": agent_info['name'],
                "agent_id": agent_id,
                "thread_id": thread_id,
                "response": latest_message.content[0].text.value if latest_message else "No response",
                "run_id": run.id
            }
            
            # Update performance tracking
            self._update_agent_performance(agent_id, True)
            
            logger.info(f"✅ Agent execution completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Agent execution failed: {str(e)}")
            self._update_agent_performance(agent_id, False)
            return {
                "status": "error",
                "error": str(e),
                "agent_id": agent_id
            }
    
    def _update_agent_performance(self, agent_id: str, success: bool):
        """Update agent performance tracking"""
        if agent_id not in self.agent_performance:
            self.agent_performance[agent_id] = {
                "total_requests": 0,
                "successful_requests": 0,
                "success_rate": 0.0
            }
        
        perf = self.agent_performance[agent_id]
        perf["total_requests"] += 1
        if success:
            perf["successful_requests"] += 1
        perf["success_rate"] = perf["successful_requests"] / perf["total_requests"]
    
    def get_agent_registry_data(self) -> Dict:
        """Get agent registry data for dashboard"""
        registry_data = {}
        
        for agent_id, agent_info in self.discovered_agents.items():
            capabilities = [cap.skill_id for cap in self.agent_capabilities.get(agent_id, [])]
            performance = self.agent_performance.get(agent_id, {})
            
            registry_data[agent_id] = {
                "agentId": agent_id,
                "name": agent_info["name"],
                "type": "azure_ai_foundry",
                "status": agent_info["status"],
                "capabilities": capabilities,
                "endpoint": agent_info["endpoint"],
                "performance": performance,
                "lastActivity": datetime.now().isoformat()
            }
        
        return registry_data
