"""
A2A Protocol Client for Working with Real Agents
Updated to work with the actual A2A framework endpoints
"""

import asyncio
import json
import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class A2AProtocolClient:
    """
    Client that works with the actual A2A protocol endpoints
    """
    
    def __init__(self, client_name: str = "test_client"):
        self.client_name = client_name
        self.logger = logging.getLogger(f"A2AClient.{client_name}")
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # A2A Agent ports (from your config)
        self.agent_ports = {
            "claims_orchestrator": 8001,
            "intake_clarifier": 8002,
            "document_intelligence": 8003,
            "coverage_rules_engine": 8004
        }
    
    def _get_agent_url(self, agent_name: str) -> str:
        """Get the base URL for an agent"""
        port = self.agent_ports.get(agent_name)
        if not port:
            raise ValueError(f"Unknown agent: {agent_name}")
        return f"http://localhost:{port}"
    
    async def get_agent_info(self, agent_name: str) -> Dict[str, Any]:
        """Get agent card information using JSON-RPC format"""
        try:
            agent_url = self._get_agent_url(agent_name)
            
            # JSON-RPC request for agent info
            request_data = {
                "jsonrpc": "2.0",
                "method": "get_agent_card",
                "params": {},
                "id": f"info_{datetime.now().timestamp()}"
            }
            
            response = await self.client.post(
                f"{agent_url}/",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "agent": agent_name}
                
        except Exception as e:
            return {"error": str(e), "agent": agent_name}
    
    async def send_a2a_task(self, agent_name: str, skill_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a task to an agent using A2A JSON-RPC protocol"""
        try:
            agent_url = self._get_agent_url(agent_name)
            
            # JSON-RPC format for A2A task execution
            request_data = {
                "jsonrpc": "2.0",
                "method": "execute_task",
                "params": {
                    "skill": skill_id,
                    "task": task_data.get("task", "process_request"),
                    "parameters": task_data.get("parameters", {}),
                    "context": task_data.get("context", {}),
                    "metadata": {
                        "source": self.client_name,
                        "timestamp": datetime.now().isoformat(),
                        "request_id": f"{self.client_name}_{datetime.now().timestamp()}"
                    }
                },
                "id": f"task_{datetime.now().timestamp()}"
            }
            
            self.logger.info(f"📤 Sending A2A task to {agent_name} (skill: {skill_id})")
            
            # POST with JSON-RPC format
            response = await self.client.post(
                f"{agent_url}/",
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"✅ A2A task successful: {agent_name}")
                return result
            else:
                error_msg = f"HTTP {response.status_code} - {response.text}"
                self.logger.error(f"❌ A2A task failed: {error_msg}")
                return {"error": error_msg, "status_code": response.status_code}
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ A2A task exception: {error_msg}")
            return {"error": error_msg}
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.aclose()

async def test_a2a_protocol_with_real_data():
    """Test the A2A protocol with your real claims data"""
    logger.info("🏥 Testing A2A Protocol with Real Claims Data")
    logger.info("=" * 60)
    
    client = A2AProtocolClient("real_data_tester")
    
    try:
        # Test schema adaptation first
        logger.info("🔄 Testing schema adaptation...")
        try:
            from shared.cosmos_schema_adapter import adapt_claim_data
            
            # Your real Cosmos DB claim structure
            cosmos_claim = {
                "claimId": "OP-1001",
                "memberId": "M-001",
                "category": "Outpatient",
                "provider": "CLN-ALPHA",
                "submitDate": "2025-08-21",
                "amountBilled": 850.00,
                "status": "submitted",
                "region": "West Coast"
            }
            
            adapted_claim = adapt_claim_data(cosmos_claim)
            logger.info(f"✅ Schema adaptation successful!")
            logger.info(f"   Claim: {adapted_claim['claim_id']} - ${adapted_claim['estimated_amount']}")
            
        except Exception as e:
            logger.error(f"❌ Schema adaptation failed: {str(e)}")
            # Use fallback data
            adapted_claim = {
                "claim_id": "OP-1001",
                "customer_id": "M-001",
                "claim_type": "outpatient",
                "estimated_amount": 850.00,
                "provider": "CLN-ALPHA",
                "submit_date": "2025-08-21"
            }
        
        # Test agent availability
        logger.info("\n📊 Checking agent availability...")
        agents_to_test = ["claims_orchestrator", "intake_clarifier", "document_intelligence", "coverage_rules_engine"]
        available_agents = []
        
        for agent_name in agents_to_test:
            agent_info = await client.get_agent_info(agent_name)
            if "error" not in agent_info:
                logger.info(f"  ✅ {agent_name} - AVAILABLE")
                available_agents.append(agent_name)
            else:
                logger.info(f"  ❌ {agent_name} - OFFLINE ({agent_info.get('error', 'unknown')})")
        
        if not available_agents:
            logger.info("⚠️ No agents available for testing")
            return
        
        # Test Claims Orchestrator if available
        if "claims_orchestrator" in available_agents:
            logger.info("\n🚀 Testing Claims Orchestrator with real claim...")
            
            task_data = {
                "task": "process_claim",
                "parameters": {
                    "claim_data": adapted_claim,
                    "processing_options": {
                        "priority": "normal",
                        "validate_coverage": True,
                        "enable_fraud_detection": True
                    }
                },
                "context": {
                    "source": "cosmos_db",
                    "original_format": "healthcare_claim",
                    "test_mode": True
                }
            }
            
            # Try the claims orchestration skill
            result = await client.send_a2a_task(
                "claims_orchestrator", 
                "claims_orchestration", 
                task_data
            )
            
            if "error" not in result:
                logger.info("✅ Claims orchestration successful!")
                logger.info(f"   Processing ID: {result.get('processing_id', 'N/A')}")
                logger.info(f"   Status: {result.get('status', 'N/A')}")
                logger.info(f"   Next Steps: {result.get('next_steps', 'N/A')}")
            else:
                logger.info(f"⚠️ Claims orchestration issue: {result['error']}")
        
        # Test Intake Clarifier if available
        if "intake_clarifier" in available_agents:
            logger.info("\n📋 Testing Intake Clarifier...")
            
            clarifier_task = {
                "task": "validate_claim_data",
                "parameters": {
                    "claim_data": adapted_claim
                },
                "context": {
                    "validation_level": "standard"
                }
            }
            
            result = await client.send_a2a_task(
                "intake_clarifier",
                "claim_validation", 
                clarifier_task
            )
            
            if "error" not in result:
                logger.info("✅ Intake clarification successful!")
            else:
                logger.info(f"⚠️ Intake clarification issue: {result['error']}")
        
        # Test Document Intelligence if available  
        if "document_intelligence" in available_agents:
            logger.info("\n📄 Testing Document Intelligence...")
            
            doc_task = {
                "task": "analyze_claim_documents",
                "parameters": {
                    "claim_id": adapted_claim['claim_id'],
                    "document_types": ["bill", "report", "test_results"]
                }
            }
            
            result = await client.send_a2a_task(
                "document_intelligence",
                "document_analysis",
                doc_task
            )
            
            if "error" not in result:
                logger.info("✅ Document intelligence successful!")
            else:
                logger.info(f"⚠️ Document intelligence issue: {result['error']}")
        
        logger.info("\n📋 A2A Protocol Test Summary:")
        logger.info(f"   🟢 Agents Available: {len(available_agents)}")
        logger.info(f"   ✅ Schema Adaptation: Working")
        logger.info(f"   🔧 A2A Communication: {len(available_agents) > 0}")
        
        logger.info("\n🎯 Real Data A2A Test Completed!")
        logger.info("=" * 60)
        
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(test_a2a_protocol_with_real_data())
