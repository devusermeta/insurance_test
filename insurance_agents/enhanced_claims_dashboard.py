"""
Enhanced Insurance Claims Dashboard with Integrated A2A Workflow
Combines the existing dashboard with our proven orchestrator workflow
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

# Add the parent directory to the path so we can import shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Import the UI integration orchestrator
from ui_integration_orchestrator import ui_orchestrator, ClaimProcessingRequest, ClaimProcessingResponse

# Import existing dashboard components
from shared.workflow_logger import workflow_logger, WorkflowStepType, WorkflowStepStatus

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Enhanced Insurance Claims Dashboard",
    description="Complete insurance claims processing with integrated A2A workflow",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models for API requests/responses
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    status: str
    requires_confirmation: Optional[bool] = False
    claim_id: Optional[str] = None
    timestamp: str

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.session_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.session_connections[session_id] = websocket
        logger.info(f"🔌 WebSocket connected for session {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if session_id in self.session_connections:
            del self.session_connections[session_id]
        logger.info(f"🔌 WebSocket disconnected for session {session_id}")

    async def send_personal_message(self, message: str, session_id: str):
        websocket = self.session_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_text(message)
                return True
            except Exception as e:
                logger.error(f"❌ Error sending message to {session_id}: {e}")
                return False
        return False

    async def broadcast(self, message: str):
        for connection in self.active_connections[:]:  # Create a copy to avoid modification during iteration
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"❌ Error broadcasting message: {e}")
                # Remove disconnected connection
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

manager = ConnectionManager()

# Initialize the UI orchestrator on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the UI orchestrator"""
    logger.info("🚀 Starting Enhanced Insurance Claims Dashboard...")
    success = await ui_orchestrator.initialize()
    if success:
        logger.info("✅ Dashboard initialized successfully")
    else:
        logger.error("❌ Failed to initialize dashboard")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Main dashboard route
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the enhanced claims dashboard"""
    try:
        with open("static/enhanced_claims_dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # Fallback to basic dashboard
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Enhanced Insurance Claims Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: linear-gradient(135deg, #2a5298, #1e3c72); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
                .chat-section { background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }
                #chatMessages { height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; background: white; margin: 10px 0; }
                .message { margin: 10px 0; padding: 10px; border-radius: 8px; }
                .user-message { background: #e3f2fd; text-align: right; }
                .assistant-message { background: #f1f8e9; }
                .system-message { background: #fff3e0; font-style: italic; }
                .error-message { background: #ffebee; color: #c62828; }
                .input-group { display: flex; gap: 10px; margin: 10px 0; }
                input[type="text"] { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
                button { background: #2a5298; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
                button:hover { background: #1e3c72; }
                .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
                .status.success { background: #e8f5e8; color: #2e7d32; }
                .status.pending { background: #fff8e1; color: #f57c00; }
                .status.error { background: #ffebee; color: #c62828; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏥 Enhanced Insurance Claims Dashboard</h1>
                    <p>Complete claims processing with integrated A2A workflow</p>
                </div>
                
                <div class="chat-section">
                    <h2>🤖 Claims Assistant</h2>
                    <div id="chatMessages"></div>
                    <div class="input-group">
                        <input type="text" id="messageInput" placeholder="Type your message here (e.g., 'Process claim with OP-05')...">
                        <button onclick="sendMessage()">Send</button>
                    </div>
                    <div id="statusDisplay"></div>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3>💡 Quick Commands</h3>
                    <ul>
                        <li><strong>Process claim:</strong> "Process claim with [CLAIM-ID]" (e.g., "Process claim with OP-05")</li>
                        <li><strong>Search database:</strong> "Show me patient John Doe" or "Find claims over $500"</li>
                        <li><strong>View status:</strong> "What is the status of claim IP-01"</li>
                    </ul>
                </div>
            </div>
            
            <script>
                let currentSessionId = generateSessionId();
                let ws = null;
                
                function generateSessionId() {
                    return 'session_' + Math.random().toString(36).substr(2, 9);
                }
                
                function connectWebSocket() {
                    ws = new WebSocket(`ws://localhost:8001/ws/${currentSessionId}`);
                    
                    ws.onopen = function(event) {
                        console.log('WebSocket connected');
                        addMessage('system', '🔌 Connected to claims assistant');
                    };
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        addMessage('assistant', data.message);
                        updateStatus(data.status, data.requires_confirmation);
                    };
                    
                    ws.onclose = function(event) {
                        console.log('WebSocket disconnected');
                        addMessage('system', '🔌 Disconnected from claims assistant');
                    };
                    
                    ws.onerror = function(error) {
                        console.error('WebSocket error:', error);
                        addMessage('error', '❌ Connection error');
                    };
                }
                
                function addMessage(type, content) {
                    const messagesDiv = document.getElementById('chatMessages');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${type}-message`;
                    messageDiv.innerHTML = content.replace(/\\n/g, '<br>').replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
                    messagesDiv.appendChild(messageDiv);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }
                
                function updateStatus(status, requiresConfirmation) {
                    const statusDiv = document.getElementById('statusDisplay');
                    let statusClass = 'status ';
                    let statusText = '';
                    
                    switch(status) {
                        case 'pending_confirmation':
                            statusClass += 'pending';
                            statusText = '⏳ Waiting for confirmation...';
                            break;
                        case 'processing':
                            statusClass += 'pending';
                            statusText = '🔄 Processing claim...';
                            break;
                        case 'completed':
                            statusClass += 'success';
                            statusText = '✅ Processing completed';
                            break;
                        case 'error':
                            statusClass += 'error';
                            statusText = '❌ Error occurred';
                            break;
                        default:
                            statusClass += 'success';
                            statusText = '💬 Ready for new message';
                    }
                    
                    statusDiv.innerHTML = `<div class="${statusClass}">${statusText}</div>`;
                }
                
                async function sendMessage() {
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    
                    if (!message) return;
                    
                    // Add user message to chat
                    addMessage('user', message);
                    input.value = '';
                    
                    // Send via REST API
                    try {
                        const response = await fetch('/api/chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                message: message,
                                session_id: currentSessionId
                            })
                        });
                        
                        const data = await response.json();
                        addMessage('assistant', data.response);
                        updateStatus(data.status, data.requires_confirmation);
                        
                    } catch (error) {
                        console.error('Error sending message:', error);
                        addMessage('error', '❌ Failed to send message');
                    }
                }
                
                // Handle Enter key in input
                document.getElementById('messageInput').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        sendMessage();
                    }
                });
                
                // Initialize WebSocket connection
                connectWebSocket();
                
                // Welcome message
                addMessage('assistant', '👋 Welcome to the Enhanced Insurance Claims Dashboard!\\n\\nI can help you process claims, search the database, and answer questions.\\n\\nTry: "Process claim with OP-05"');
            </script>
        </body>
        </html>
        """)

# API Routes

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatMessage):
    """
    Main chat endpoint for processing employee messages
    """
    try:
        logger.info(f"📝 Chat request: {request.message}")
        
        # Process message through UI orchestrator
        response = await ui_orchestrator.process_employee_message(
            message=request.message,
            session_id=request.session_id
        )
        
        # Convert to chat response format
        chat_response = ChatResponse(
            response=response.message,
            session_id=response.session_id,
            status=response.status,
            requires_confirmation=response.requires_confirmation or False,
            claim_id=response.claim_id,
            timestamp=response.timestamp
        )
        
        logger.info(f"✅ Chat response: {response.status}")
        return chat_response
        
    except Exception as e:
        logger.error(f"❌ Error in chat endpoint: {e}")
        return ChatResponse(
            response=f"❌ Error processing message: {str(e)}",
            session_id=request.session_id or str(uuid.uuid4()),
            status="error",
            timestamp=datetime.now().isoformat()
        )

@app.get("/api/session/{session_id}")
async def get_session_status(session_id: str):
    """Get the status of a specific session"""
    try:
        status = await ui_orchestrator.get_session_status(session_id)
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"❌ Error getting session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/session/{session_id}")
async def cleanup_session(session_id: str):
    """Clean up a session"""
    try:
        success = await ui_orchestrator.cleanup_session(session_id)
        return JSONResponse(content={"success": success, "session_id": session_id})
    except Exception as e:
        logger.error(f"❌ Error cleaning up session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/claims/{claim_id}/steps")
async def get_claim_processing_steps(claim_id: str):
    """Get the processing steps for a specific claim"""
    try:
        steps = workflow_logger.get_workflow_steps(claim_id)
        return JSONResponse(content={"claim_id": claim_id, "steps": steps})
    except Exception as e:
        logger.error(f"❌ Error getting claim steps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Enhanced Insurance Claims Dashboard",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

# WebSocket endpoint for real-time communication
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                message = message_data.get("message", "")
                
                if message:
                    # Process message through UI orchestrator
                    response = await ui_orchestrator.process_employee_message(
                        message=message,
                        session_id=session_id
                    )
                    
                    # Send response back
                    await websocket.send_text(json.dumps({
                        "message": response.message,
                        "status": response.status,
                        "requires_confirmation": response.requires_confirmation or False,
                        "claim_id": response.claim_id,
                        "timestamp": response.timestamp
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "message": "❌ Invalid message format",
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        logger.info(f"🔌 Client {session_id} disconnected")

if __name__ == "__main__":
    # Run the enhanced dashboard
    logger.info("🚀 Starting Enhanced Insurance Claims Dashboard on http://localhost:8001")
    uvicorn.run(
        "enhanced_claims_dashboard:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
