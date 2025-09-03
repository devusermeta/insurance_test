"""
Insurance Claims Processing Dashboard

A professional web dashboard for insurance claim processing employees to manage
and monitor the multi-agent claims processing workflow. Features real-time status
updates, claim processing controls, and agent orchestration visibility.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging with terminal colors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TerminalLogger:
    """Terminal logging for the dashboard"""
    
    COLORS = {
        'reset': '\033[0m', 'bold': '\033[1m', 'red': '\033[91m',
        'green': '\033[92m', 'yellow': '\033[93m', 'blue': '\033[94m',
        'magenta': '\033[95m', 'cyan': '\033[96m'
    }
    
    @classmethod
    def log(cls, level: str, component: str, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        emoji_map = {
            'INFO': '📋', 'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌',
            'DASHBOARD': '🖥️', 'CLAIM': '🏥', 'AGENT': '🤖'
        }
        color_map = {
            'INFO': cls.COLORS['blue'], 'SUCCESS': cls.COLORS['green'],
            'WARNING': cls.COLORS['yellow'], 'ERROR': cls.COLORS['red'],
            'DASHBOARD': cls.COLORS['cyan'], 'CLAIM': cls.COLORS['magenta'],
            'AGENT': cls.COLORS['green']
        }
        
        emoji = emoji_map.get(level, '📋')
        color = color_map.get(level, cls.COLORS['blue'])
        print(f"{color}[{timestamp}] {emoji} {component.upper()}: {message}{cls.COLORS['reset']}")

# Data Models
class ClaimStatus(BaseModel):
    """Claim processing status"""
    claimId: str
    status: str  # submitted, processing, approved, pended, denied
    category: str  # Outpatient, Inpatient
    amountBilled: float
    submitDate: str
    lastUpdate: str
    assignedEmployee: Optional[str] = None

class AgentInfo(BaseModel):
    """Insurance agent information"""
    agentId: str
    name: str
    type: str  # orchestrator, specialist
    status: str  # online, offline, busy, error
    capabilities: List[str]
    lastActivity: str
    currentClaims: List[str]

class ProcessingRequest(BaseModel):
    """Claim processing request"""
    claimId: str
    expectedOutput: str
    priority: str = "normal"
    employeeId: str

# Initialize FastAPI app
app = FastAPI(
    title="Insurance Claims Processing Dashboard",
    description="Professional dashboard for insurance claim processing employees",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, this would be in a database)
active_claims: Dict[str, ClaimStatus] = {}
registered_agents: Dict[str, AgentInfo] = {}
processing_logs: List[Dict] = []

terminal_logger = TerminalLogger()

@app.on_event("startup")
async def startup_event():
    """Initialize dashboard on startup"""
    terminal_logger.log("DASHBOARD", "STARTUP", "Insurance Claims Processing Dashboard starting...")
    
    # Initialize demo agents
    await initialize_demo_agents()
    
    # Load sample claims
    await load_sample_claims()
    
    terminal_logger.log("SUCCESS", "DASHBOARD", "Dashboard initialized successfully on http://localhost:3000")

async def initialize_demo_agents():
    """Initialize demo insurance agents"""
    demo_agents = [
        {
            "agentId": "claims_assist_001",
            "name": "ClaimsAssist Orchestrator", 
            "type": "orchestrator",
            "status": "online",
            "capabilities": ["workflow_orchestration", "agent_routing", "decision_aggregation"],
            "lastActivity": datetime.now().isoformat(),
            "currentClaims": []
        },
        {
            "agentId": "intake_clarifier_001",
            "name": "Claims Intake Clarifier",
            "type": "specialist", 
            "status": "online",
            "capabilities": ["intake_validation", "completeness_check", "gap_analysis"],
            "lastActivity": datetime.now().isoformat(),
            "currentClaims": []
        },
        {
            "agentId": "doc_intelligence_001", 
            "name": "Document Intelligence",
            "type": "specialist",
            "status": "online", 
            "capabilities": ["document_processing", "text_extraction", "evidence_tagging"],
            "lastActivity": datetime.now().isoformat(),
            "currentClaims": []
        },
        {
            "agentId": "coverage_rules_001",
            "name": "Coverage Rules Engine", 
            "type": "specialist",
            "status": "online",
            "capabilities": ["policy_evaluation", "rules_matching", "decision_recommendation"],
            "lastActivity": datetime.now().isoformat(),
            "currentClaims": []
        }
    ]
    
    for agent_data in demo_agents:
        agent = AgentInfo(**agent_data)
        registered_agents[agent.agentId] = agent
        terminal_logger.log("AGENT", "REGISTER", f"Registered agent: {agent.name}")

async def load_sample_claims():
    """Load sample claims for demonstration"""
    sample_claims = [
        {
            "claimId": "OP-1001",
            "status": "submitted",
            "category": "Outpatient", 
            "amountBilled": 180.0,
            "submitDate": "2025-08-21",
            "lastUpdate": datetime.now().isoformat(),
            "assignedEmployee": None
        },
        {
            "claimId": "OP-1002", 
            "status": "processing",
            "category": "Outpatient",
            "amountBilled": 220.0,
            "submitDate": "2025-08-19", 
            "lastUpdate": datetime.now().isoformat(),
            "assignedEmployee": "emp_001"
        },
        {
            "claimId": "IP-2001",
            "status": "approved", 
            "category": "Inpatient",
            "amountBilled": 14000.0,
            "submitDate": "2025-08-10",
            "lastUpdate": datetime.now().isoformat(),
            "assignedEmployee": "emp_002"
        }
    ]
    
    for claim_data in sample_claims:
        claim = ClaimStatus(**claim_data)
        active_claims[claim.claimId] = claim
        terminal_logger.log("CLAIM", "LOAD", f"Loaded claim: {claim.claimId} - ${claim.amountBilled}")

# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard HTML"""
    html_file = Path(__file__).parent / "static" / "insurance_dashboard.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding='utf-8'), status_code=200)
    else:
        return HTMLResponse(content="<h1>Insurance Dashboard - HTML file not found</h1>", status_code=404)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/claims")
async def get_claims():
    """Get all active claims"""
    terminal_logger.log("INFO", "API", f"Retrieved {len(active_claims)} claims")
    return {"claims": list(active_claims.values())}

@app.get("/api/claims/{claim_id}")
async def get_claim(claim_id: str):
    """Get specific claim details"""
    if claim_id not in active_claims:
        terminal_logger.log("WARNING", "API", f"Claim not found: {claim_id}")
        raise HTTPException(status_code=404, detail="Claim not found")
    
    terminal_logger.log("INFO", "API", f"Retrieved claim details: {claim_id}")
    return {"claim": active_claims[claim_id]}

@app.get("/api/agents")
async def get_agents():
    """Get all registered agents"""
    terminal_logger.log("INFO", "API", f"Retrieved {len(registered_agents)} agents")
    return {"agents": list(registered_agents.values())}

@app.post("/api/claims/{claim_id}/process")
async def process_claim(claim_id: str, request: ProcessingRequest, background_tasks: BackgroundTasks):
    """Start claim processing"""
    if claim_id not in active_claims:
        terminal_logger.log("ERROR", "API", f"Cannot process - claim not found: {claim_id}")
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Update claim status
    active_claims[claim_id].status = "processing"
    active_claims[claim_id].assignedEmployee = request.employeeId
    active_claims[claim_id].lastUpdate = datetime.now().isoformat()
    
    terminal_logger.log("CLAIM", "PROCESS", f"Started processing claim: {claim_id} by employee: {request.employeeId}")
    
    # Start background processing simulation
    background_tasks.add_task(simulate_claim_processing, claim_id)
    
    return {"message": f"Processing started for claim {claim_id}", "status": "processing"}

@app.get("/api/logs")
async def get_processing_logs():
    """Get recent processing logs"""
    return {"logs": processing_logs[-50:]}  # Return last 50 logs

async def simulate_claim_processing(claim_id: str):
    """Simulate the multi-agent claim processing workflow"""
    try:
        terminal_logger.log("CLAIM", "WORKFLOW", f"Starting multi-agent processing for {claim_id}")
        
        # Simulate agent workflow stages
        stages = [
            ("claims_assist_001", "Orchestrating workflow", 2),
            ("intake_clarifier_001", "Validating claim intake", 3),
            ("doc_intelligence_001", "Processing documents", 4),
            ("coverage_rules_001", "Evaluating coverage rules", 3),
            ("claims_assist_001", "Aggregating results", 2)
        ]
        
        for agent_id, activity, duration in stages:
            # Update agent status
            if agent_id in registered_agents:
                registered_agents[agent_id].currentClaims.append(claim_id)
                registered_agents[agent_id].lastActivity = datetime.now().isoformat()
            
            # Log activity
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "claimId": claim_id,
                "agentId": agent_id,
                "activity": activity,
                "status": "in_progress"
            }
            processing_logs.append(log_entry)
            terminal_logger.log("AGENT", "ACTIVITY", f"{agent_id}: {activity} for {claim_id}")
            
            # Simulate processing time
            await asyncio.sleep(duration)
            
            # Remove claim from agent's current claims
            if agent_id in registered_agents and claim_id in registered_agents[agent_id].currentClaims:
                registered_agents[agent_id].currentClaims.remove(claim_id)
        
        # Complete processing
        active_claims[claim_id].status = "approved"  # Simplified - always approve for demo
        active_claims[claim_id].lastUpdate = datetime.now().isoformat()
        
        final_log = {
            "timestamp": datetime.now().isoformat(),
            "claimId": claim_id,
            "agentId": "claims_assist_001",
            "activity": "Processing completed - APPROVED",
            "status": "completed"
        }
        processing_logs.append(final_log)
        terminal_logger.log("SUCCESS", "WORKFLOW", f"Completed processing for {claim_id} - APPROVED")
        
    except Exception as e:
        terminal_logger.log("ERROR", "WORKFLOW", f"Processing failed for {claim_id}: {str(e)}")
        active_claims[claim_id].status = "error"
        active_claims[claim_id].lastUpdate = datetime.now().isoformat()

if __name__ == "__main__":
    terminal_logger.log("DASHBOARD", "START", "Starting Insurance Claims Processing Dashboard...")
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=3000, 
        reload=True,
        log_level="info"
    )
