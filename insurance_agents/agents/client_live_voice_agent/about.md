# Client Live Voice Agent

## Overview
The Client Live Voice Agent is a sophisticated voice-enabled insurance claims assistant that combines Azure AI Foundry Voice Agent capabilities with real-time voice interaction.

## Key Features
- **Real-time Voice Processing**: Direct integration with Azure Voice Live API
- **Azure AI Foundry Integration**: Intelligent voice agent with persistent conversation capabilities
- **Claims Database Access**: Direct access to insurance claims via MCP tools
- **A2A Protocol Compliance**: Follows Agent-to-Agent communication standards
- **Session Management**: Tracks voice conversations with session-based logging

## Architecture
- **Voice Interface**: Direct browser WebSocket connection to Azure Voice Live API
- **Azure AI Foundry Voice Agent**: Intelligent conversation handling with tool integration
- **MCP Tools**: Database access through Model Context Protocol
- **Conversation Logging**: Persistent conversation tracking in voice_chat.json

## Capabilities
1. **Voice Claims Lookup**: "What's the status of claim OP-02?"
2. **Insurance Definitions**: "What is a deductible?"
3. **Document Upload**: Request secure upload links
4. **Real-time Interaction**: Natural voice conversations with interruption handling

## Technical Stack
- Azure AI Foundry Voice Agent
- Azure Voice Live API (WebSocket)
- Cosmos DB (via MCP)
- A2A Framework
- FastAPI Server

## Port Configuration
- Agent Server: 8007
- MCP Cosmos Server: 8080

## Environment Variables
- `AZURE_VOICE_AGENT_ID`: Persistent voice agent identifier
- `AZURE_AI_AGENT_*`: Azure AI Foundry configuration
- Voice Live API credentials in config.js

## Usage
The agent provides a complete voice interface for insurance claims operations, maintaining conversation context and providing intelligent responses through Azure AI Foundry integration.