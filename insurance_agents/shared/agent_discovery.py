"""
Enhanced Agent Discovery Module
Adds detailed agent discovery, capability matching, and routing decisions
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import json


class AgentDiscoveryService:
    """
    Enhanced agent discovery with detailed logging and intelligent routing
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.discovered_agents = {}
        self.last_discovery = None
        
        # Known agent endpoints
        self.agent_endpoints = {
            "intake_clarifier": "http://localhost:8002",
            "document_intelligence": "http://localhost:8003", 
            "coverage_rules_engine": "http://localhost:8004",
            "communication_agent": "http://localhost:8005"
        }
    
    async def discover_all_agents(self) -> Dict[str, Any]:
        """
        Discover all available agents and their capabilities
        """
        self.logger.info("🔍 AGENT DISCOVERY: Starting agent discovery process...")
        
        discovered = {}
        
        for agent_id, base_url in self.agent_endpoints.items():
            self.logger.info(f"   🤖 Discovering {agent_id} at {base_url}")
            
            try:
                agent_info = await self._discover_single_agent(agent_id, base_url)
                if agent_info:
                    discovered[agent_id] = agent_info
                    self.logger.info(f"   ✅ {agent_id}: ONLINE with {len(agent_info.get('skills', []))} skills")
                    
                    # Log capabilities
                    for skill in agent_info.get('skills', []):
                        skill_name = skill.get('name', 'Unknown')
                        self.logger.info(f"      • Skill: {skill_name}")
                else:
                    self.logger.warning(f"   ❌ {agent_id}: OFFLINE or no agent card")
                    
            except Exception as e:
                self.logger.error(f"   ❌ {agent_id}: Discovery failed - {str(e)}")
        
        self.discovered_agents = discovered
        self.last_discovery = datetime.now()
        
        self.logger.info(f"🎯 DISCOVERY COMPLETE: Found {len(discovered)} agents online")
        
        return discovered
    
    async def _discover_single_agent(self, agent_id: str, base_url: str) -> Optional[Dict[str, Any]]:
        """Discover a single agent's capabilities"""
        
        try:
            async with aiohttp.ClientSession() as session:
                # Try agent card endpoint
                agent_card_url = f"{base_url}/.well-known/agent.json"
                
                async with session.get(agent_card_url, timeout=5) as response:
                    if response.status == 200:
                        agent_card = await response.json()
                        
                        return {
                            "agent_id": agent_id,
                            "name": agent_card.get("name", "Unknown Agent"),
                            "base_url": base_url,
                            "skills": agent_card.get("skills", []),
                            "capabilities": agent_card.get("capabilities", {}),
                            "description": agent_card.get("description", ""),
                            "status": "online",
                            "discovered_at": datetime.now().isoformat()
                        }
        
        except Exception as e:
            self.logger.debug(f"Failed to discover {agent_id}: {str(e)}")
            
        return None
    
    def select_agent_for_task(self, task_description: str, task_type: str) -> Optional[Dict[str, Any]]:
        """
        Intelligently select the best agent for a given task
        """
        self.logger.info(f"🎯 AGENT SELECTION: Selecting agent for task type '{task_type}'")
        self.logger.info(f"   📋 Task description: {task_description[:100]}...")
        
        if not self.discovered_agents:
            self.logger.warning("⚠️ No agents discovered yet - run discovery first")
            return None
        
        # Task-to-agent mapping logic
        task_mappings = {
            "intake_validation": ["intake_clarifier"],
            "claim_validation": ["intake_clarifier"],
            "fraud_detection": ["intake_clarifier"],
            "document_analysis": ["document_intelligence"],
            "document_processing": ["document_intelligence"], 
            "text_extraction": ["document_intelligence"],
            "coverage_evaluation": ["coverage_rules_engine"],
            "rules_evaluation": ["coverage_rules_engine"],
            "policy_analysis": ["coverage_rules_engine"]
        }
        
        # Find matching agents
        candidate_agents = []
        
        # Direct mapping
        if task_type in task_mappings:
            for agent_id in task_mappings[task_type]:
                if agent_id in self.discovered_agents:
                    candidate_agents.append(self.discovered_agents[agent_id])
                    self.logger.info(f"   ✅ Direct match: {agent_id} handles {task_type}")
        
        # Skill-based matching
        task_keywords = task_description.lower().split()
        for agent_id, agent_info in self.discovered_agents.items():
            for skill in agent_info.get("skills", []):
                skill_text = (skill.get("name", "") + " " + skill.get("description", "")).lower()
                
                # Check if task keywords match skill
                matches = sum(1 for keyword in task_keywords if keyword in skill_text)
                if matches > 0:
                    if agent_info not in candidate_agents:
                        candidate_agents.append(agent_info)
                        self.logger.info(f"   🎯 Skill match: {agent_id} - '{skill.get('name')}' matches task")
        
        if not candidate_agents:
            self.logger.warning(f"⚠️ No suitable agents found for task type: {task_type}")
            return None
        
        # Select best agent (for now, just take the first match)
        selected_agent = candidate_agents[0]
        
        self.logger.info(f"🎯 SELECTION RESULT: Chose {selected_agent['agent_id']} - {selected_agent['name']}")
        self.logger.info(f"   📊 Reason: Best match for {task_type}")
        self.logger.info(f"   🌐 Will send to: {selected_agent['base_url']}")
        
        return selected_agent
    
    async def send_task_to_agent(self, agent_info: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a task to a specific agent using A2A protocol
        """
        agent_id = agent_info["agent_id"]
        base_url = agent_info["base_url"]
        
        self.logger.info(f"📤 TASK DISPATCH: Sending task to {agent_id}")
        self.logger.info(f"   🎯 Agent: {agent_info['name']}")
        self.logger.info(f"   📋 Task: {task.get('description', 'No description')}")
        
        try:
            # Create A2A message
            a2a_payload = {
                "jsonrpc": "2.0",
                "id": f"task-{agent_id}-{datetime.now().strftime('%H%M%S')}",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": f"msg-{agent_id}-{datetime.now().strftime('%H%M%S')}",
                        "role": "user",
                        "parts": [
                            {
                                "kind": "text",
                                "text": task.get("message", "Process this task")
                            }
                        ]
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    base_url,
                    json=a2a_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                ) as response:
                    
                    response_text = await response.text()
                    
                    if response.status < 400:
                        self.logger.info(f"✅ TASK SUCCESS: {agent_id} processed task successfully")
                        return {
                            "status": "success",
                            "agent": agent_id,
                            "response": response_text,
                            "response_code": response.status
                        }
                    else:
                        self.logger.error(f"❌ TASK FAILED: {agent_id} returned {response.status}")
                        return {
                            "status": "failed",
                            "agent": agent_id,
                            "error": response_text,
                            "response_code": response.status
                        }
        
        except Exception as e:
            self.logger.error(f"❌ TASK ERROR: Failed to send task to {agent_id}: {str(e)}")
            return {
                "status": "error",
                "agent": agent_id,
                "error": str(e)
            }
    
    def get_discovery_summary(self) -> str:
        """Get a summary of discovered agents"""
        if not self.discovered_agents:
            return "No agents discovered yet"
        
        summary = f"Discovered {len(self.discovered_agents)} agents:\n"
        for agent_id, agent_info in self.discovered_agents.items():
            skills_count = len(agent_info.get("skills", []))
            summary += f"• {agent_info['name']} ({agent_id}): {skills_count} skills\n"
        
        return summary
