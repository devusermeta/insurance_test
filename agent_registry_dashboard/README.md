# Azure AI Foundry Multi-Agent Registry Dashboard

A beautiful, professional web dashboard for managing and monitoring your Azure AI Foundry multi-agent system. This dashboard provides a centralized view of all registered agents, their real-time status, capabilities, and detailed information.

## 🌟 Features

### **Beautiful Azure-Themed UI**
- Azure blue gradient backgrounds with glassmorphism effects
- Responsive design optimized for all devices
- Smooth animations and hover effects
- Professional typography using Inter font
- Microsoft Azure branding elements

### **📊 Real-time Monitoring**
- Live agent status indicators (online/offline/error)
- Response time monitoring with millisecond precision
- Automatic health checks every 30 seconds
- Visual status indicators with pulse animations
- Azure AI Foundry integration status

### **🔍 Detailed Agent Information**
- Comprehensive agent cards with A2A protocol information
- Skills and capabilities display with categorized tags
- Connection details and error diagnostics
- Agent-specific configuration viewing
- Azure AI Foundry routing information

### **⚡ Easy Management**
- Add new agents dynamically through UI
- Remove agents from registry
- Manual refresh capability
- Individual agent connectivity testing
- Real-time status updates

## 🏗️ Architecture

The dashboard is specifically designed for the Azure AI Foundry multi-agent system:

1. **Backend API (FastAPI)**
   - RESTful API for agent management
   - Periodic health monitoring with smart endpoint detection
   - A2A agent card discovery
   - Real-time status updates with Azure-specific handling

2. **Frontend (Modern Web Interface)**
   - Azure-themed responsive design
   - Real-time updates without page refresh
   - Modal dialogs for detailed agent views
   - Interactive agent cards with type-specific styling

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Your Azure AI Foundry multi-agent system running:
  - Host Agent (Gradio interface)
  - Playwright Agent 
  - Tool Agent
  - MCP SSE Server

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the dashboard:**
   ```bash
   python app.py
   ```

3. **Access the dashboard:**
   Open your browser and navigate to: `http://localhost:8080`

## 🎯 Pre-configured Agents

The dashboard comes pre-configured for your Azure AI Foundry multi-agent system:

| Agent Name        | Default URL              | Description                              | Technology Stack            |
|-------------------|--------------------------|------------------------------------------|-----------------------------|
| Host Agent        | http://localhost:8083    | Central routing with Azure AI Foundry   | Gradio + Azure AI + A2A     |
| Playwright Agent  | http://localhost:10001   | Web automation and screenshot tools     | A2A + MCP + Playwright      |
| Tool Agent        | http://localhost:10002   | Development tools and Git operations    | A2A + MCP + Dev Tools       |
| MCP SSE Server    | http://localhost:7071    | Model Context Protocol with SSE         | Azure Functions + MCP + SSE |

## 📡 API Endpoints

The dashboard exposes these REST API endpoints:

- `GET /` - Serve the main dashboard interface
- `GET /api/agents` - Get all registered agents with status
- `GET /api/agents/{agent_name}` - Get detailed agent information
- `POST /api/agents` - Add a new agent to registry
- `DELETE /api/agents/{agent_name}` - Remove agent from registry
- `GET /api/health` - Dashboard health check

## 🎨 Agent-Specific Features

### **Host Agent (Azure AI Foundry)**
- Azure blue gradient styling
- Azure AI Foundry integration indicators
- Semantic Kernel capabilities display
- Task routing visualization

### **Playwright Agent**
- Teal gradient styling for web automation theme
- Web automation capabilities highlighting
- Screenshot and browser interaction skills
- MCP tool integration status

### **Tool Agent**
- Purple gradient styling for development tools
- Git operations and VSCode integration display
- Development workflow capabilities
- MCP-based tool execution status

### **MCP SSE Server**
- Orange gradient styling for server functions
- Azure Functions integration status
- Server-Sent Events (SSE) capability display
- MCP protocol compliance indicators

## 🔧 Customization

### Adding New Agents

1. **Through the UI:** Click the "Add Agent" button
2. **Modify default configuration** in `app.py`:
   ```python
   self.default_agents = [
       {
           "name": "Your New Agent",
           "url": "http://localhost:9000",
           "description": "Your agent description"
       },
       # ... existing agents
   ]
   ```
3. **Via API call:**
   ```bash
   curl -X POST "http://localhost:8080/api/agents?name=MyAgent&url=http://localhost:9000"
   ```

### Styling Customization

The dashboard uses CSS custom properties for easy theming. Key Azure colors:
- Primary: `#0078d4` (Azure Blue)
- Secondary: `#00bcf2` (Azure Light Blue) 
- Accent: `#005a9e` (Azure Dark Blue)

### Health Check Configuration

Modify the monitoring interval in `app.py`:
```python
# Change refresh interval (in seconds)
await asyncio.sleep(30)  # Currently 30 seconds
```

## 🔍 Agent Integration

For optimal dashboard integration, ensure your agents expose:

1. **A2A Agents** (Playwright & Tool Agents):
   - `/.well-known/agent.json` - A2A agent card
   - `/health` - Health check endpoint

2. **Host Agent** (Gradio):
   - Root endpoint `/` responding with 200 status

3. **MCP SSE Server**:
   - `/api/health` - Azure Functions health endpoint

### Example A2A Agent Card:
```json
{
  "name": "Playwright Agent",
  "description": "Web automation agent using Playwright",
  "version": "1.0.0",
  "capabilities": {
    "inputModes": ["text"],
    "outputModes": ["text", "image"],
    "streaming": true
  },
  "skills": [
    {
      "id": "playwright_tools",
      "name": "Web Automation",
      "description": "Browser automation and screenshot capabilities",
      "examples": ["Take a screenshot of google.com"]
    }
  ]
}
```

## 🚀 Deployment

### Development
```bash
python app.py
```

### Production
Use a proper ASGI server for production:
```bash
uvicorn app:app --host 0.0.0.0 --port 8080 --workers 4
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

## 🛠️ Troubleshooting

### Common Issues

1. **Agents not appearing**
   - Verify agent URLs and ports are correct
   - Check if agents are running and accessible
   - Review dashboard logs for connection errors

2. **Host Agent shows offline**
   - Ensure Gradio app is running on port 7860
   - Check if the Gradio interface is accessible
   - Verify no firewall blocking the connection

3. **A2A Agents not responding**
   - Confirm agents expose `/.well-known/agent.json`
   - Check A2A protocol implementation
   - Verify agent startup and configuration

4. **MCP Server connectivity issues**
   - Ensure Azure Functions are deployed and running
   - Check `/api/health` endpoint accessibility
   - Verify MCP server configuration

### Debug Mode
Enable detailed logging by modifying `app.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🌟 Azure AI Foundry Integration

This dashboard is specifically optimized for Azure AI Foundry workflows:

- **Intelligent Routing**: Visual indication of Azure AI-powered task delegation
- **Semantic Kernel Integration**: Display of SK-based agent capabilities  
- **A2A Protocol Support**: Native support for Agent-to-Agent communication
- **MCP Compatibility**: Full Model Context Protocol integration
- **Azure Functions**: Specialized handling for Azure Function-based agents

## 📈 Future Enhancements

Planned features:
- 📊 Historical performance metrics and charts
- 🔔 Alert system for agent failures and performance issues
- 📝 Agent interaction logs and conversation history
- 🔧 Advanced configuration management interface
- 🔐 Azure AD authentication integration
- 📊 Performance analytics with Azure Monitor integration
- 🌐 Multi-environment support (dev/staging/prod)

## 🤝 Contributing

Feel free to submit issues and pull requests to improve the dashboard! This project follows the same license as the parent A2A samples repository.

## 📄 License

This project is licensed under the same terms as the Azure AI Foundry multi-agent samples.
