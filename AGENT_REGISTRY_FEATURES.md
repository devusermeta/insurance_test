# Agent Registry - Add/Remove Custom Agents Feature

## Overview
The Insurance Agent Registry Dashboard now supports adding and removing custom agents dynamically through the web interface. Custom agents are automatically discovered via the A2A protocol standard and displayed alongside built-in agents.

## Features Implemented

### ✅ Add Custom Agents
- **Access**: Click the "Add Agent" button in the agent registry dashboard
- **Functionality**: 
  - Enter any agent URL that implements the A2A protocol
  - System automatically fetches agent information from `/.well-known/agent.json`
  - Real-time validation and testing of agent URLs
  - Duplicate detection (prevents adding existing agents)
  - Automatic status monitoring

### ✅ Remove Custom Agents  
- **Access**: Click the "Remove Agent" button in the agent registry dashboard
- **Functionality**:
  - Shows dropdown with only custom agents (built-in agents are protected)
  - Preview agent information before removal
  - Confirmation workflow
  - Immediate removal from registry

### ✅ Persistent Storage
- Custom agents are stored in `custom_agents.json` file
- Agents persist across dashboard restarts
- Automatic backup and recovery

### ✅ Real-time Integration
- Custom agents appear as cards alongside built-in agents
- Automatic health monitoring every 7 seconds
- Status updates (online/offline)
- Full agent card details available

## Usage Instructions

### Adding a Custom Agent

1. **Open Agent Registry**: Navigate to the agent registry dashboard
2. **Click "Add Agent"**: Button is in the top-right header
3. **Enter URL**: Paste the agent's base URL (e.g., `https://my-custom-agent.com`)
4. **Test (Optional)**: Click "Test" to validate the agent before adding
5. **Add Agent**: Click "Add Agent" to register it

**Requirements for Custom Agents:**
- Must implement A2A protocol with `/.well-known/agent.json` endpoint
- Agent card must include: `name`, `description`, `version`
- URL must be accessible via HTTP/HTTPS

### Removing a Custom Agent

1. **Click "Remove Agent"**: Button is in the top-right header  
2. **Select Agent**: Choose from dropdown (only shows custom agents)
3. **Review Information**: Preview shows agent details
4. **Confirm Removal**: Click "Remove Agent" to delete

### Agent Card Format

Custom agents should serve a JSON response at `/.well-known/agent.json`:

```json
{
  "name": "My Custom Agent",
  "description": "Description of what this agent does",
  "version": "1.0.0",
  "skills": [
    {
      "id": "skill_id",
      "name": "Skill Name", 
      "description": "What this skill does",
      "tags": ["tag1", "tag2"]
    }
  ],
  "capabilities": {
    "streaming": true
  },
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"]
}
```

## Technical Implementation

### Backend API Endpoints
- `POST /api/agents` - Add custom agent
- `DELETE /api/agents/{agent_id}` - Remove custom agent  
- `GET /api/agents` - List all agents (built-in + custom)
- `GET /api/agent-card/{agent_id}` - Get detailed agent information

### Storage
- **File**: `insurance_agents/insurance_agents_registry_dashboard/custom_agents.json`
- **Format**: JSON with agent metadata and cached agent cards
- **Backup**: Automatic file-based persistence

### Error Handling
- Invalid URLs (non-HTTP/HTTPS)
- Network timeouts and connection failures
- Malformed agent.json responses
- Duplicate agent detection
- Protection of built-in agents

## Example Custom Agent URLs

For testing, you can try adding:
- `http://localhost:8005` (if you have another agent running)
- `https://your-custom-agent-url.com`

## Files Modified

1. **Backend**: `insurance_agents/insurance_agents_registry_dashboard/app.py`
   - Added custom agent storage functions
   - Added API endpoints for add/remove
   - Enhanced agent discovery to include custom agents

2. **Frontend**: `insurance_agents/insurance_agents_registry_dashboard/static/agent_registry.html`
   - Added modal dialogs for add/remove functionality
   - Added JavaScript functions for agent management
   - Enhanced UI with form validation and error handling

## Security Considerations

- Only agents with valid A2A protocol implementation can be added
- Built-in system agents cannot be removed
- URL validation prevents injection attacks
- Network timeouts prevent hanging requests
- CORS policies maintained for security

## Future Enhancements

- Agent authentication/authorization
- Bulk agent import/export
- Agent health history tracking
- Custom agent grouping/categorization
- Agent performance metrics