1. __main__.py - Server Entry Point & A2A Setup
Purpose: This is the main entry point that sets up the A2A server infrastructure.

Key Responsibilities:

Sets up the A2A Starlette Application server
Configures Agent Card with skills and capabilities
Handles logging and server startup
Runs on port 8001 (configurable)



2. claims_orchestrator_executor.py - Core Business Logic
Purpose: This is the brain of the orchestrator - contains ALL the business logic.

Key Responsibilities:

A2A Protocol Implementation - Inherits from AgentExecutor
Dynamic Agent Discovery - Finds and routes to other agents
Workflow Orchestration - Manages the complete claims workflow
Decision Making - Makes final claim decisions
MCP Integration - Communicates with Cosmos DB
Workflow Logging - Tracks every step



3. claims_orchestrator_agent.py - Alternative FastAPI Implementation
Purpose: Provides a FastAPI-based alternative with Azure AI Foundry integration.



4. __init__.py - Python Package Marker