"""
Updated Insurance Registry Dashboard with Azure AI Foundry Integration
Dynamically discovers and routes to Azure AI Foundry agents
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from azure_ai_foundry_router import AzureAIFoundryAgentRouter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessingRequest(BaseModel):
    """Claim processing request"""
    claimId: str
    request: str
    priority: str = "normal"
    employeeId: str

class AgentRoutingRequest(BaseModel):
    """Agent routing request"""
    request: str
    context: Optional[Dict] = None

# Initialize Azure AI Foundry router
project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "https://your-project.cognitiveservices.azure.com")
agent_router = AzureAIFoundryAgentRouter(project_endpoint)

# FastAPI app
app = FastAPI(
    title="Insurance Agents Registry Dashboard", 
    description="Dynamic agent registry with Azure AI Foundry integration"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global state
active_threads: Dict[str, str] = {}  # claim_id -> thread_id mapping
routing_history: List[Dict] = []

@app.on_event("startup")
async def startup_event():
    """Discover Azure AI Foundry agents on startup"""
    logger.info("🚀 Starting Insurance Registry Dashboard with Azure AI Foundry")
    try:
        await agent_router.discover_agents()
        logger.info("✅ Agent discovery completed")
    except Exception as e:
        logger.error(f"❌ Failed to discover agents: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page"""
    with open("static/index.html") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/api/agents")
async def get_agents():
    """Get all discovered Azure AI Foundry agents"""
    try:
        registry_data = agent_router.get_agent_registry_data()
        agents_list = list(registry_data.values())
        
        return {
            "status": "success",
            "agents": agents_list,
            "total": len(agents_list),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/discover")
async def rediscover_agents():
    """Rediscover Azure AI Foundry agents"""
    try:
        discovered = await agent_router.discover_agents()
        return {
            "status": "success", 
            "message": f"Discovered {len(discovered)} agents",
            "agents": list(discovered.keys())
        }
    except Exception as e:
        logger.error(f"Failed to rediscover agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/route-request")
async def route_request(request: AgentRoutingRequest):
    """Route user request to best Azure AI Foundry agent"""
    try:
        # Get routing decision
        decision = await agent_router.route_request(request.request, request.context)
        
        if not decision.selected_agent:
            return {
                "status": "error",
                "message": "No suitable agent found",
                "decision": decision.__dict__
            }
        
        # Get agent info
        registry_data = agent_router.get_agent_registry_data()
        selected_agent_info = registry_data.get(decision.selected_agent, {})
        
        return {
            "status": "success",
            "decision": {
                "selected_agent": decision.selected_agent,
                "agent_name": selected_agent_info.get("name", "Unknown"),
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "fallback_agents": decision.fallback_agents
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to route request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-claim")
async def process_claim(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """Process claim using dynamic agent routing"""
    try:
        claim_id = request.claimId
        user_request = request.request
        
        logger.info(f"🏥 Processing claim {claim_id}: {user_request}")
        
        # Get routing decision
        context = {
            "claim_id": claim_id,
            "priority": request.priority,
            "employee_id": request.employeeId
        }
        
        decision = await agent_router.route_request(user_request, context)
        
        if not decision.selected_agent:
            raise HTTPException(status_code=400, detail="No suitable agent found for this request")
        
        # Get or create thread for this claim
        thread_id = active_threads.get(claim_id)
        
        # Execute with selected agent
        result = await agent_router.execute_with_agent(
            agent_id=decision.selected_agent,
            request=user_request,
            thread_id=thread_id
        )
        
        if result["status"] == "success":
            # Store thread ID for future interactions
            active_threads[claim_id] = result["thread_id"]
            
            # Record routing history
            routing_record = {
                "timestamp": datetime.now().isoformat(),
                "claim_id": claim_id,
                "request": user_request,
                "selected_agent": decision.selected_agent,
                "confidence": decision.confidence,
                "result": "success"
            }
            routing_history.append(routing_record)
            
            return {
                "status": "success",
                "claim_id": claim_id,
                "agent_used": result["agent"],
                "response": result["response"],
                "thread_id": result["thread_id"],
                "routing_decision": decision.__dict__
            }
        else:
            raise HTTPException(status_code=500, detail=f"Agent execution failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Failed to process claim: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/routing-history")
async def get_routing_history():
    """Get routing history for analytics"""
    return {
        "status": "success",
        "history": routing_history[-50:],  # Last 50 routing decisions
        "total_routes": len(routing_history)
    }

@app.get("/api/agent-performance")
async def get_agent_performance():
    """Get agent performance analytics"""
    try:
        registry_data = agent_router.get_agent_registry_data()
        
        performance_data = {}
        for agent_id, agent_info in registry_data.items():
            performance = agent_info.get("performance", {})
            performance_data[agent_id] = {
                "name": agent_info["name"],
                "total_requests": performance.get("total_requests", 0),
                "successful_requests": performance.get("successful_requests", 0),
                "success_rate": performance.get("success_rate", 0.0),
                "capabilities": agent_info["capabilities"]
            }
        
        return {
            "status": "success",
            "performance": performance_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/capabilities")
async def get_capability_index():
    """Get capability index for understanding agent skills"""
    try:
        capability_data = {}
        
        # Build capability index from discovered agents
        registry_data = agent_router.get_agent_registry_data()
        
        for agent_id, agent_info in registry_data.items():
            for capability in agent_info["capabilities"]:
                if capability not in capability_data:
                    capability_data[capability] = []
                capability_data[capability].append({
                    "agent_id": agent_id,
                    "agent_name": agent_info["name"]
                })
        
        return {
            "status": "success",
            "capabilities": capability_data,
            "total_capabilities": len(capability_data)
        }
        
    except Exception as e:
        logger.error(f"Failed to get capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/live-updates")
async def websocket_endpoint(websocket):
    """WebSocket for live dashboard updates"""
    await websocket.accept()
    try:
        while True:
            # Send live agent status updates
            registry_data = agent_router.get_agent_registry_data()
            await websocket.send_json({
                "type": "agent_status",
                "data": registry_data,
                "timestamp": datetime.now().isoformat()
            })
            await asyncio.sleep(5)  # Update every 5 seconds
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

if __name__ == "__main__":
    logger.info("🖥️ Starting Insurance Registry Dashboard with Dynamic Azure AI Foundry Routing...")
    uvicorn.run(
        "updated_registry_app:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        log_level="info"
    )
