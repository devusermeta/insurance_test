"""
A2A Communication Client for Insurance Agents
Handles agent-to-agent communication using the A2A protocol
"""

import asyncio
import json
import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from shared.mcp_config import A2A_AGENT_PORTS

class A2AClient:
    """
    Client for A2A (Agent-to-Agent) communication
    Enables agents to communicate with each other using the A2A protocol
    """
    
    def __init__(self, source_agent: str):
        self.source_agent = source_agent
        self.logger = logging.getLogger(f"A2AClient.{source_agent}")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _get_agent_url(self, agent_name: str) -> str:
        """Get the URL for a specific agent"""
        port = A2A_AGENT_PORTS.get(agent_name)
        if not port:
            raise ValueError(f"Unknown agent: {agent_name}")
        return f"http://localhost:{port}"
    
    async def send_request(self, target_agent: str, task: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send an A2A request to another agent
        
        Args:
            target_agent: Name of the target agent
            task: Task description or command
            parameters: Task parameters
            
        Returns:
            Response from the target agent
        """
        try:
            if parameters is None:
                parameters = {}
                
            agent_url = self._get_agent_url(target_agent)
            self.logger.info(f"📤 Sending A2A request to {target_agent}: {task}")
            
            # Prepare A2A request payload
            payload = {
                "task": task,
                "parameters": parameters,
                "source_agent": self.source_agent,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send request to target agent
            response = await self.client.post(
                f"{agent_url}/execute",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"✅ A2A request to {target_agent} completed successfully")
                return result
            else:
                error_msg = f"A2A request failed: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return {"error": error_msg, "status": "failed"}
                
        except Exception as e:
            error_msg = f"Error sending A2A request to {target_agent}: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "status": "failed"}
    
    async def process_claim_with_clarifier(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send claim to Intake Clarifier agent for initial processing
        
        Args:
            claim_data: Claim information to process
            
        Returns:
            Clarified claim data
        """
        return await self.send_request(
            "intake_clarifier",
            "clarify_claim_intake",
            {"claim_data": claim_data}
        )
    
    async def analyze_documents_with_intelligence(self, claim_id: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send documents to Document Intelligence agent for analysis
        
        Args:
            claim_id: The claim ID
            documents: List of documents to analyze
            
        Returns:
            Document analysis results
        """
        return await self.send_request(
            "document_intelligence",
            "analyze_claim_documents",
            {"claim_id": claim_id, "documents": documents}
        )
    
    async def validate_coverage_with_rules_engine(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send claim to Coverage Rules Engine for policy validation
        
        Args:
            claim_data: Claim data to validate
            
        Returns:
            Coverage validation results
        """
        return await self.send_request(
            "coverage_rules_engine",
            "validate_claim_coverage",
            {"claim_data": claim_data}
        )
    
    async def orchestrate_claim_processing(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send claim to Claims Orchestrator for complete processing workflow
        
        Args:
            claim_data: Claim data to process
            
        Returns:
            Complete processing results
        """
        return await self.send_request(
            "claims_orchestrator",
            "process_claim_workflow",
            {"claim_data": claim_data}
        )
    
    async def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """
        Get the status of another agent
        
        Args:
            agent_name: Name of the agent to check
            
        Returns:
            Agent status information
        """
        try:
            agent_url = self._get_agent_url(agent_name)
            response = await self.client.get(f"{agent_url}/.well-known/agent.json")
            
            if response.status_code == 200:
                return {"status": "online", "info": response.json()}
            else:
                return {"status": "offline", "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"status": "offline", "error": str(e)}
    
    async def broadcast_message(self, message: str, parameters: Dict[str, Any] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Broadcast a message to all other agents
        
        Args:
            message: Message to broadcast
            parameters: Message parameters
            
        Returns:
            Responses from all agents
        """
        results = []
        
        for agent_name in A2A_AGENT_PORTS.keys():
            if agent_name != self.source_agent:
                result = await self.send_request(agent_name, message, parameters)
                results.append({
                    "agent": agent_name,
                    "response": result
                })
        
        return {"broadcast_results": results}
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
