# Time Agent

A specialized A2A agent that provides comprehensive time and date services with full activity logging to Cosmos DB via Azure MCP Server.

## Overview

The Time Agent responds to queries about current time, date, and timestamp information while logging all interactions to Azure Cosmos DB through the Azure MCP Server. This demonstrates the integration of:

- **A2A Protocol** for agent communication
- **Azure MCP Server** for Cosmos DB operations
- **Comprehensive logging** for agent activity monitoring

## Features

- **Time Services**: Current time with timezone support
- **Date Services**: Current date with various formatting options
- **Combined DateTime**: Comprehensive date and time information
- **Natural Language Processing**: Understands various time/date queries
- **Cosmos DB Logging**: All requests, responses, and errors logged via Azure MCP Server
- **A2A Integration**: Full compliance with A2A protocol standards

## Agent Capabilities

### Supported Queries
- "What time is it?"
- "What is the current date?"
- "Show me the current timestamp"
- "What day is today?"
- "Give me the current date and time"

### Response Formats
- **Time**: Formatted in 12-hour and 24-hour formats
- **Date**: Various formats including day of week, month name, etc.
- **Timestamps**: ISO format and Unix timestamps
- **Combined**: Full date/time information

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Azure AI Foundry Configuration
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME = "your-gpt-4-deployment-name"
AZURE_AI_AGENT_ENDPOINT = "https://your-project.eastus2.inference.ai.azure.com/"
AZURE_AI_AGENT_SUBSCRIPTION_ID = "your-azure-subscription-id"
AZURE_AI_AGENT_RESOURCE_GROUP_NAME = "your-resource-group-name"
AZURE_AI_AGENT_PROJECT_NAME = "your-project-name"

# Azure MCP Server Configuration for Cosmos DB logging
AZURE_MCP_SERVER_URL = "https://your-azure-mcp-server.azurewebsites.net"
COSMOS_DB_SUBSCRIPTION_ID = "your-azure-subscription-id"
COSMOS_DB_ACCOUNT_NAME = "your-cosmos-db-account-name"
COSMOS_DB_DATABASE_NAME = "agent_logs"
COSMOS_DB_CONTAINER_NAME = "time_agent_logs"
```

## Installation and Setup

1. **Navigate to the time_agent directory**:
   ```powershell
   cd "samples\python\agents\azureaifoundry_sdk\multi_agent\remote_agents\time_agent"
   ```

2. **Install dependencies**:
   ```powershell
   uv sync
   ```

3. **Configure environment**:
   ```powershell
   copy .env.example .env
   # Edit .env with your Azure and Cosmos DB configuration
   ```

## Running the Agent

### Start the Time Agent Server
```powershell
cd "samples\python\agents\azureaifoundry_sdk\multi_agent\remote_agents\time_agent"
.venv\Scripts\activate
python .
```

The agent will start on `http://localhost:10003` by default.

### Register with Host Agent

Add the time agent URL to the host agent's configuration in `host_agent\.env`:
```bash
TIME_AGENT_URL=http://localhost:10003
```

## Cosmos DB Logging

All agent activities are logged to Cosmos DB via the Azure MCP Server:

### Log Entry Structure
```json
{
  "id": "time_agent_2025-08-19T10:30:00.000Z_query_received",
  "timestamp": "2025-08-19T10:30:00.000Z",
  "agent_name": "TimeAgent",
  "event_type": "query_received",
  "data": {
    "query": "What time is it?",
    "request_type": "natural_language_query"
  },
  "partition_key": "time_agent"
}
```

### Logged Events
- `query_received`: User queries received
- `time_request`: Time-specific requests
- `date_request`: Date-specific requests
- `datetime_request`: Combined date/time requests
- `query_response`: Successful responses
- `execution_start`: Task execution begins
- `execution_completed`: Task completed successfully
- `execution_error`: Task execution errors
- `query_error`: Query processing errors

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Host Agent    │───▶│   Time Agent    │───▶│ Azure MCP Server│
│                 │ A2A│ (Port 10003)    │ MCP│ (Cosmos Tools)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Agent Registry  │    │ • Get Time/Date │    │   Cosmos DB     │
│ (Existing)      │    │ • Log via MCP   │    │   Logging       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Integration with Multi-Agent System

The Time Agent integrates seamlessly with the existing multi-agent infrastructure:

1. **Discovery**: Uses the same agent registry mechanism as other remote agents
2. **Communication**: Standard A2A protocol for all interactions
3. **Logging**: Enhanced with Cosmos DB logging via Azure MCP Server
4. **Deployment**: Can be deployed to Azure AI Foundry like other agents

## Testing

Test the agent directly using A2A client calls or through the host agent's web interface.

Example A2A request:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "message/send",
  "params": {
    "id": "time-query-001",
    "sessionId": "user-session-123",
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "What time is it?"
        }
      ]
    }
  }
}
```

## Next Steps

1. **Configure Azure MCP Server**: Set up the Azure MCP Server for Cosmos DB access
2. **Implement Real MCP Connection**: Replace placeholder logging with actual MCP calls
3. **Add Timezone Support**: Implement comprehensive timezone handling
4. **Deploy to Azure**: Deploy the agent to Azure AI Foundry
5. **Monitor Logs**: Use Cosmos DB queries to monitor agent performance and usage
