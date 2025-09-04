"""
Fixed Dashboard with Real Cosmos Integration
Connects to your actual MCP server and A2A agents instead of using fake data
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import uuid

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
            'DASHBOARD': '🖥️', 'CLAIM': '🏥', 'AGENT': '🤖', 'COSMOS': '🌌'
        }
        color_map = {
            'INFO': cls.COLORS['blue'], 'SUCCESS': cls.COLORS['green'],
            'WARNING': cls.COLORS['yellow'], 'ERROR': cls.COLORS['red'],
            'DASHBOARD': cls.COLORS['cyan'], 'CLAIM': cls.COLORS['magenta'],
            'AGENT': cls.COLORS['green'], 'COSMOS': cls.COLORS['blue']
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
    # Real fields from Cosmos
    memberId: Optional[str] = None
    provider: Optional[str] = None
    region: Optional[str] = None
    dosFrom: Optional[str] = None
    dosTo: Optional[str] = None

class ProcessingRequest(BaseModel):
    """Request to process a claim"""
    employeeId: str
    priority: str = "normal"

class CosmosDataLoader:
    """Loads real data from Cosmos DB via MCP server"""
    
    def __init__(self, mcp_url: str = "http://localhost:8080"):
        self.mcp_url = mcp_url
        
    async def load_real_claims(self) -> List[ClaimStatus]:
        """Load real claims from Cosmos DB"""
        try:
            async with aiohttp.ClientSession() as session:
                # Call MCP server to get claims
                mcp_payload = {
                    "jsonrpc": "2.0",
                    "id": str(uuid.uuid4()),
                    "method": "tools/call",
                    "params": {
                        "name": "query_cosmos",
                        "arguments": {
                            "collection": "claims",
                            "query": "SELECT * FROM c",
                            "max_items": 50
                        }
                    }
                }
                
                async with session.post(
                    f"{self.mcp_url}/mcp", 
                    json=mcp_payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        terminal_logger.log("COSMOS", "SUCCESS", f"Loaded real claims data from Cosmos")
                        
                        # Parse Cosmos response
                        claims = []
                        if "result" in data and "content" in data["result"]:
                            items = data["result"]["content"]
                            if isinstance(items, list):
                                for item in items:
                                    claim = ClaimStatus(
                                        claimId=item.get("claimId", "Unknown"),
                                        status=item.get("status", "submitted"),
                                        category=item.get("category", "Unknown"),
                                        amountBilled=float(item.get("amountBilled", 0)),
                                        submitDate=item.get("submitDate", ""),
                                        lastUpdate=datetime.now().isoformat(),
                                        memberId=item.get("memberId"),
                                        provider=item.get("provider"),
                                        region=item.get("region"),
                                        dosFrom=item.get("dosFrom"),
                                        dosTo=item.get("dosTo")
                                    )
                                    claims.append(claim)
                                    terminal_logger.log("COSMOS", "LOAD", f"Loaded claim: {claim.claimId} - ${claim.amountBilled}")
                        
                        return claims
                    else:
                        terminal_logger.log("ERROR", "COSMOS", f"MCP server returned {response.status}")
                        return []
        
        except Exception as e:
            terminal_logger.log("ERROR", "COSMOS", f"Failed to load real claims: {str(e)}")
            return []

class RealAgentProcessor:
    """Processes claims using real A2A agents"""
    
    def __init__(self):
        self.orchestrator_url = "http://localhost:8001"
        
    async def process_claim_with_real_agents(self, claim_id: str) -> Dict[str, Any]:
        """Send claim to real orchestrator for processing"""
        try:
            terminal_logger.log("AGENT", "START", f"Sending claim {claim_id} to real orchestrator")
            
            # Create A2A message for orchestrator
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
                                "text": f"""
Please process insurance claim {claim_id} using the complete workflow:

1. Use the intake clarifier to validate claim completeness
2. Use document intelligence to extract information from claim documents  
3. Use coverage rules engine to evaluate coverage and make a decision
4. Provide the final recommendation: approve, pend, or deny with rationale

This is a real claim from our Cosmos database. Please coordinate with all specialist agents and return the final decision.
"""
                            }
                        ]
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.orchestrator_url,
                    json=a2a_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    response_text = await response.text()
                    terminal_logger.log("AGENT", "RESPONSE", f"Orchestrator response: {response.status}")
                    
                    if response.status < 400:
                        terminal_logger.log("SUCCESS", "AGENT", f"Successfully sent claim {claim_id} to orchestrator")
                        return {
                            "status": "processing",
                            "message": "Claim sent to real agents",
                            "orchestrator_response": response_text
                        }
                    else:
                        terminal_logger.log("ERROR", "AGENT", f"Orchestrator error: {response.status} - {response_text}")
                        return {
                            "status": "error", 
                            "message": f"Orchestrator error: {response.status}",
                            "error": response_text
                        }
                        
        except Exception as e:
            terminal_logger.log("ERROR", "AGENT", f"Failed to process claim {claim_id}: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

# Global objects
app = FastAPI(title="Real Insurance Claims Dashboard", version="2.0.0")
terminal_logger = TerminalLogger()
cosmos_loader = CosmosDataLoader()
agent_processor = RealAgentProcessor()

# In-memory storage (replace with database in production)
active_claims: Dict[str, ClaimStatus] = {}
processing_logs: List[Dict[str, Any]] = []

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize the dashboard with real data"""
    terminal_logger.log("DASHBOARD", "STARTUP", "Real Insurance Claims Dashboard starting...")
    
    # Load real claims from Cosmos
    real_claims = await cosmos_loader.load_real_claims()
    
    if real_claims:
        for claim in real_claims:
            active_claims[claim.claimId] = claim
        terminal_logger.log("SUCCESS", "STARTUP", f"Loaded {len(real_claims)} real claims from Cosmos DB")
    else:
        terminal_logger.log("WARNING", "STARTUP", "No claims loaded - check Cosmos MCP server connection")

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the claims dashboard"""
    html_file = Path(__file__).parent / "static" / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding='utf-8'), status_code=200)
    else:
        # Return a simple HTML page if static file doesn't exist
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Real Insurance Claims Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .claim { border: 1px solid #ddd; padding: 20px; margin: 10px 0; }
                .btn { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
            </style>
        </head>
        <body>
            <h1>🏥 Real Insurance Claims Dashboard</h1>
            <p>✅ Connected to real Cosmos DB data and A2A agents</p>
            <div id="claims"></div>
            <script>
                async function loadClaims() {
                    const response = await fetch('/api/claims');
                    const claims = await response.json();
                    const container = document.getElementById('claims');
                    container.innerHTML = claims.map(claim => `
                        <div class="claim">
                            <h3>${claim.claimId} - $${claim.amountBilled}</h3>
                            <p>Status: ${claim.status} | Category: ${claim.category}</p>
                            <p>Provider: ${claim.provider || 'N/A'} | Member: ${claim.memberId || 'N/A'}</p>
                            <button class="btn" onclick="processClaim('${claim.claimId}')">Process with Real Agents</button>
                        </div>
                    `).join('');
                }
                
                async function processClaim(claimId) {
                    console.log('Processing claim:', claimId);
                    const response = await fetch(`/api/claims/${claimId}/process`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ employeeId: 'emp_dashboard' })
                    });
                    const result = await response.json();
                    alert(`Claim ${claimId}: ${result.message}`);
                }
                
                loadClaims();
                setInterval(loadClaims, 5000); // Refresh every 5 seconds
            </script>
        </body>
        </html>
        """, status_code=200)

@app.get("/api/claims")
async def get_claims():
    """Get all claims from real Cosmos data"""
    terminal_logger.log("API", "REQUEST", f"Retrieved {len(active_claims)} real claims")
    return list(active_claims.values())

@app.post("/api/claims/{claim_id}/process")
async def process_claim(claim_id: str, request: ProcessingRequest, background_tasks: BackgroundTasks):
    """Process claim using real A2A agents"""
    if claim_id not in active_claims:
        terminal_logger.log("ERROR", "API", f"Cannot process - claim not found: {claim_id}")
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Update claim status
    active_claims[claim_id].status = "processing"
    active_claims[claim_id].assignedEmployee = request.employeeId
    active_claims[claim_id].lastUpdate = datetime.now().isoformat()
    
    terminal_logger.log("CLAIM", "PROCESS", f"Started REAL processing for claim: {claim_id} by employee: {request.employeeId}")
    
    # Process with real agents in background
    background_tasks.add_task(process_with_real_agents, claim_id)
    
    return {"message": f"Claim {claim_id} sent to real A2A agents for processing", "status": "processing"}

async def process_with_real_agents(claim_id: str):
    """Process claim with actual A2A agents"""
    try:
        terminal_logger.log("CLAIM", "WORKFLOW", f"Starting REAL agent processing for {claim_id}")
        
        # Send to real orchestrator
        result = await agent_processor.process_claim_with_real_agents(claim_id)
        
        if result["status"] == "processing":
            terminal_logger.log("SUCCESS", "WORKFLOW", f"Claim {claim_id} successfully sent to real agents")
            # Note: The actual processing happens in the agents - status will be updated by them
        else:
            active_claims[claim_id].status = "error"
            active_claims[claim_id].lastUpdate = datetime.now().isoformat()
            terminal_logger.log("ERROR", "WORKFLOW", f"Failed to process claim {claim_id}: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        active_claims[claim_id].status = "error"
        active_claims[claim_id].lastUpdate = datetime.now().isoformat()
        terminal_logger.log("ERROR", "WORKFLOW", f"Exception processing claim {claim_id}: {str(e)}")

@app.get("/api/logs")
async def get_processing_logs():
    """Get processing logs"""
    return processing_logs[-50:]  # Last 50 entries

if __name__ == "__main__":
    terminal_logger.log("DASHBOARD", "START", "Starting Real Insurance Claims Dashboard...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3001,  # Use different port from old dashboard
        log_level="info"
    )
