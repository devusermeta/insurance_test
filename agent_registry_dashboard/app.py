"""
Insurance Claims Processing Agent Registry Dashboard

A modern web dashboard for managing and monitoring insurance claims processing agents.
This dashboard provides a centralized view of all registered insurance agents, 
their capabilities, real-time status monitoring, and agent registration/removal.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentStatus(BaseModel):
    """Agent status information"""
    name: str
    url: str
    status: str  # 'online', 'offline', 'error'
    last_checked: datetime
    response_time: Optional[float] = None
    error_message: Optional[str] = None


class AgentRegistry:
    """Central registry for managing Insurance Claims Processing multi-agent system"""
    
    def __init__(self):
        self.agents: Dict[str, AgentStatus] = {}
        self.agent_cards: Dict[str, Dict] = {}
        
        # Insurance Claims Processing Multi-Agent System configuration
        self.default_agents = [
            {
                "name": "ClaimsAssist Orchestrator",
                "url": "http://localhost:8001",
                "description": "Main orchestrator for insurance claims workflow - plans DAG, routes work, aggregates results"
            },
            {
                "name": "Claims Intake Clarifier",
                "url": "http://localhost:8002",
                "description": "Validates claim submissions for completeness and consistency, flags gaps or mismatches"
            },
            {
                "name": "Document Intelligence",
                "url": "http://localhost:8003", 
                "description": "Processes documents, extracts structured facts with evidence spans for claims"
            },
            {
                "name": "Coverage Rules Engine",
                "url": "http://localhost:8004",
                "description": "Evaluates benefit and policy rules against extracted facts, proposes approve/deny/pend"
            }
        ]
        
        # Initialize with default insurance agents
        for agent_config in self.default_agents:
            self.agents[agent_config["name"]] = AgentStatus(
                name=agent_config["name"],
                url=agent_config["url"],
                status="unknown",
                last_checked=datetime.now()
            )
    
    async def check_agent_health(self, agent_name: str, agent_url: str) -> AgentStatus:
        """Check if an agent is online and get its status"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Special handling for different agent types
                if agent_name == "Host Agent":
                    # Gradio app - check if it's running
                    try:
                        async with session.get(agent_url) as response:
                            response_time = asyncio.get_event_loop().time() - start_time
                            if response.status == 200:
                                return AgentStatus(
                                    name=agent_name,
                                    url=agent_url,
                                    status="online",
                                    last_checked=datetime.now(),
                                    response_time=response_time * 1000
                                )
                    except Exception:
                        pass
                        
                elif agent_name == "MCP SSE Server":
                    # Azure Function MCP server
                    try:
                        async with session.get(f"{agent_url}/api/health") as response:
                            response_time = asyncio.get_event_loop().time() - start_time
                            if response.status == 200:
                                return AgentStatus(
                                    name=agent_name,
                                    url=agent_url,
                                    status="online", 
                                    last_checked=datetime.now(),
                                    response_time=response_time * 1000
                                )
                    except Exception:
                        pass
                        
                else:
                    # A2A agents - try agent-card endpoint first
                    try:
                        async with session.get(f"{agent_url}/.well-known/agent.json") as response:
                            if response.status == 200:
                                agent_card = await response.json()
                                self.agent_cards[agent_name] = agent_card
                                response_time = asyncio.get_event_loop().time() - start_time
                                
                                return AgentStatus(
                                    name=agent_name,
                                    url=agent_url,
                                    status="online",
                                    last_checked=datetime.now(),
                                    response_time=response_time * 1000
                                )
                    except Exception:
                        # Fallback to health endpoint
                        try:
                            async with session.get(f"{agent_url}/health") as response:
                                response_time = asyncio.get_event_loop().time() - start_time
                                if response.status == 200:
                                    return AgentStatus(
                                        name=agent_name,
                                        url=agent_url,
                                        status="online",
                                        last_checked=datetime.now(),
                                        response_time=response_time * 1000
                                    )
                        except Exception:
                            pass
                
                # If all checks fail, mark as offline
                return AgentStatus(
                    name=agent_name,
                    url=agent_url,
                    status="offline",
                    last_checked=datetime.now(),
                    error_message="No response from agent endpoints"
                )
                            
        except Exception as e:
            return AgentStatus(
                name=agent_name,
                url=agent_url,
                status="offline",
                last_checked=datetime.now(),
                error_message=str(e)
            )
    
    async def refresh_all_agents(self):
        """Refresh status for all registered agents"""
        tasks = []
        for agent_name, agent_status in self.agents.items():
            task = self.check_agent_health(agent_status.name, agent_status.url)
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, AgentStatus):
                    agent_name = list(self.agents.keys())[i]
                    self.agents[agent_name] = result
                else:
                    logger.error(f"Error checking agent {list(self.agents.keys())[i]}: {result}")
    
    def enhance_agent_card(self, agent_card: Dict) -> Dict:
        """Enhance agent card with additional fields for future compatibility"""
        enhanced_card = agent_card.copy()
        
        # Add identity mode and authorization token fields if not present
        if 'identity_mode' not in enhanced_card:
            enhanced_card['identity_mode'] = 'Unknown'
        
        if 'authorization_token' not in enhanced_card:
            enhanced_card['authorization_token'] = None  # Will show as 'Unknown' in UI
            
        return enhanced_card

    def add_agent(self, name: str, url: str):
        """Add a new agent to the registry"""
        self.agents[name] = AgentStatus(
            name=name,
            url=url,
            status="unknown",
            last_checked=datetime.now()
        )
    
    def remove_agent(self, name: str):
        """Remove an agent from the registry"""
        if name in self.agents:
            del self.agents[name]
        if name in self.agent_cards:
            del self.agent_cards[name]


# Initialize the registry
registry = AgentRegistry()

# Create FastAPI app
app = FastAPI(
    title="Insurance Claims Processing Agent Registry",
    description="Central dashboard for monitoring and managing insurance claims processing agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard HTML"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/agents")
async def get_agents():
    """Get all registered agents with their current status"""
    await registry.refresh_all_agents()
    return {
        "agents": [agent.dict() for agent in registry.agents.values()],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/agents/{agent_name}")
async def get_agent_details(agent_name: str):
    """Get detailed information about a specific agent"""
    if agent_name not in registry.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Refresh this specific agent
    agent_status = registry.agents[agent_name]
    updated_status = await registry.check_agent_health(agent_name, agent_status.url)
    registry.agents[agent_name] = updated_status
    
    # Get agent card if available and enhance it
    agent_card = registry.agent_cards.get(agent_name, {})
    if agent_card:
        agent_card = registry.enhance_agent_card(agent_card)
    
    return {
        "status": updated_status.dict(),
        "agent_card": agent_card,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/agents")
async def add_agent(request: Request):
    """Add a new agent to the registry"""
    form_data = await request.form()
    name = form_data.get("name")
    url = form_data.get("url")
    
    if not name or not url:
        raise HTTPException(status_code=422, detail="Name and URL are required")
    
    registry.add_agent(name, url)
    return {"message": f"Agent {name} added successfully"}


@app.delete("/api/agents/{agent_name}")
async def remove_agent(agent_name: str):
    """Remove an agent from the registry"""
    if agent_name not in registry.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    registry.remove_agent(agent_name)
    return {"message": f"Agent {agent_name} removed successfully"}


@app.get("/api/health")
async def health_check():
    """Dashboard health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


async def periodic_health_check():
    """Background task to periodically check agent health"""
    while True:
        try:
            await registry.refresh_all_agents()
            logger.info("Completed periodic health check for all agents")
        except Exception as e:
            logger.error(f"Error during periodic health check: {e}")
        
        # Wait 30 seconds before next check
        await asyncio.sleep(30)


@app.on_event("startup")
async def startup_event():
    """Start background tasks when the app starts"""
    # Start periodic health check
    asyncio.create_task(periodic_health_check())
    
    # Initial health check
    await registry.refresh_all_agents()
    logger.info("Azure AI Foundry Multi-Agent Registry Dashboard started successfully")


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
