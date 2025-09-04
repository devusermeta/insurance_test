"""
Unified Insurance Management Dashboard

A comprehensive web dashboard that provides both claims processing and agent registry
management on a single service. Features seamless navigation between employee claims
dashboard and admin agent registry dashboard.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

# Add the parent directory to the path so we can import shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import shared modules
try:
    from shared.workflow_logger import workflow_logger
except ImportError:
    # Create a mock workflow logger if import fails
    class MockWorkflowLogger:
        def get_workflow_steps(self, claim_id):
            return []
        def get_all_recent_steps(self, limit):
            return []
    workflow_logger = MockWorkflowLogger()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class TerminalLogger:
    """Terminal logging for the dashboard"""
    
    def log(self, category: str, action: str, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        emoji_map = {
            "AGENT": "🤖",
            "CALL": "📞", 
            "CLAIM": "📋",
            "API": "🔌",
            "WORKFLOW": "🔄",
            "STATUS": "📊",
            "REFRESH": "🖥️"
        }
        emoji = emoji_map.get(category.upper(), "📝")
        print(f"[{timestamp}] {emoji} {action.upper()}: {message}")

terminal_logger = TerminalLogger()

# Pydantic models
class ClaimData(BaseModel):
    """Claim processing status"""
    claim_id: str
    type: str
    amount: float
    status: str
    assignedEmployee: Optional[str] = None
    category: Optional[str] = None

class AgentInfo(BaseModel):
    """Insurance agent information"""
    name: str
    url: str
    status: str
    skills: List[str] = []

class ProcessingRequest(BaseModel):
    """Claim processing request"""
    action: str = "process_claim"

# Initialize FastAPI
app = FastAPI(title="Insurance Management Dashboard", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# Global variables
active_claims: Dict[str, ClaimData] = {}
processing_logs: List[Dict] = []

# Sample claims data
default_claims = [
    ClaimData(
        claim_id="OP-1001",
        type="outpatient", 
        amount=180.0,
        status="submitted",
        assignedEmployee="Sarah Johnson",
        category="outpatient"
    ),
    ClaimData(
        claim_id="AC-2001", 
        type="auto",
        amount=2500.0,
        status="submitted",
        assignedEmployee="Mike Chen", 
        category="auto"
    ),
    ClaimData(
        claim_id="HM-3001",
        type="home",
        amount=1200.0, 
        status="submitted",
        assignedEmployee="Jessica Wong",
        category="home"
    )
]

# Initialize claims
for claim in default_claims:
    active_claims[claim.claim_id] = claim

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard"""
    try:
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        dashboard_path = os.path.join(static_dir, "claims_dashboard.html")
        
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(f.read())
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        return HTMLResponse("<h1>Dashboard Error</h1><p>Could not load dashboard</p>", status_code=500)

@app.get("/api/claims")
async def get_claims():
    """Get all active claims"""
    terminal_logger.log("API", "CALL", f"Retrieved {len(active_claims)} claims")
    return {"claims": list(active_claims.values())}

@app.get("/api/processing-steps/{claim_id}")
async def get_processing_steps(claim_id: str):
    """Get processing steps for a specific claim"""
    steps = workflow_logger.get_workflow_steps(claim_id)
    return {"claim_id": claim_id, "steps": steps}

@app.get("/api/processing-steps") 
async def get_all_processing_steps():
    """Get recent processing steps across all claims"""
    steps = workflow_logger.get_all_recent_steps(20)
    return {"steps": steps}

@app.get("/api/agents")
async def get_agents():
    """Get agent registry status"""
    terminal_logger.log("API", "REFRESH", "Refreshing agent status...")
    
    agent_ports = {
        "claims_orchestrator": 8001,
        "intake_clarifier": 8002, 
        "document_intelligence": 8003,
        "coverage_rules_engine": 8004
    }
    
    agents = []
    for agent_id, port in agent_ports.items():
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
                agent_card_url = f"http://localhost:{port}/.well-known/agent.json"
                async with session.get(agent_card_url) as response:
                    if response.status == 200:
                        agent_data = await response.json()
                        agents.append(AgentInfo(
                            name=agent_data.get('name', agent_id),
                            url=f"http://localhost:{port}",
                            status="online",
                            skills=agent_data.get('skills', [])
                        ))
                        terminal_logger.log("AGENT_CARD", "SUCCESS", f"Fetched agent card for {agent_data.get('name', agent_id)}")
                    else:
                        agents.append(AgentInfo(name=agent_id, url=f"http://localhost:{port}", status="offline"))
        except Exception as e:
            agents.append(AgentInfo(name=agent_id, url=f"http://localhost:{port}", status="offline"))
            terminal_logger.log("AGENT", "ERROR", f"Failed to reach {agent_id}: {str(e)[:50]}")
    
    for agent in agents:
        status_emoji = "✅" if agent.status == "online" else "❌"
        terminal_logger.log("STATUS_CHECK", "AGENT", f"Agent {agent.name}: {agent.status}")
    
    return {"agents": agents}

@app.post("/api/claims/{claim_id}/process")
async def process_claim(claim_id: str, request: ProcessingRequest, background_tasks: BackgroundTasks):
    """Process a claim using the real orchestrator"""
    if claim_id not in active_claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim_data = active_claims[claim_id]
    terminal_logger.log("CLAIM", "PROCESS", f"Processing claim {claim_id}")
    
    try:
        # Get the actual claim data
        claim_info = {
            "claim_id": claim_id,
            "type": getattr(claim_data, 'category', 'general'),
            "amount": float(getattr(claim_data, 'amount', 0)),
            "description": f"Insurance claim processing for {claim_id}",
            "customer_id": getattr(claim_data, 'assignedEmployee', 'UNKNOWN') or "UNKNOWN",
            "policy_number": f"POL_{claim_id}",
            "incident_date": "2024-01-15",
            "location": "Dashboard Processing",
            "documents": ["claim_form.pdf", "supporting_documents.pdf"],
            "customer_statement": f"Processing {getattr(claim_data, 'category', 'general')} claim through dashboard interface"
        }
        
        # Send to real orchestrator using A2A protocol
        a2a_payload = {
            "jsonrpc": "2.0",
            "id": f"dashboard-{claim_id}-{datetime.now().strftime('%H%M%S')}",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": f"msg-{claim_id}-{datetime.now().strftime('%H%M%S')}",
                    "role": "user",
                    "parts": [
                        {
                            "kind": "text",
                            "text": json.dumps({
                                "action": "process_claim",
                                "claim_id": claim_id,
                                "claim_data": claim_info
                            })
                        }
                    ]
                }
            }
        }
        
        terminal_logger.log("AGENT", "CALL", f"Sending claim {claim_id} to real orchestrator...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001",  # orchestrator URL
                json=a2a_payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=60)  # Allow more time for real processing
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    # Update claim status
                    claim_data.status = "approved"
                    active_claims[claim_id] = claim_data
                    
                    terminal_logger.log("CLAIM", "SUCCESS", f"Claim {claim_id} processed successfully")
                    return {
                        "status": "success",
                        "message": f"Claim {claim_id} processed successfully",
                        "result": result
                    }
                else:
                    terminal_logger.log("CLAIM", "ERROR", f"Orchestrator returned {response.status}")
                    return {
                        "status": "error", 
                        "message": f"Processing failed with status {response.status}",
                        "result": result
                    }
                    
    except Exception as e:
        terminal_logger.log("CLAIM", "ERROR", f"Processing failed: {str(e)}")
        return {
            "status": "error",
            "message": f"Processing failed: {str(e)}"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")
