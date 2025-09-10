# Claims Orchestrator Agent Persistence Fix

## Problem Fixed

Previously, the Claims Orchestrator was creating a **new Azure AI agent** every time it started up. This was:
- ❌ Inefficient (unnecessary resource usage)
- ❌ Costly (agent creation has costs)  
- ❌ Cluttering Azure AI Foundry with duplicate agents
- ❌ Losing agent context and configuration between sessions

## Solution Implemented  

Now the Claims Orchestrator follows the **proper agent persistence pattern**:

### ✅ Agent Persistence
- **One agent** is created and reused across all sessions
- Agent ID is stored and retrieved from environment variables
- System searches for existing agents before creating new ones
- Automatic cleanup utilities for duplicate agents

### ✅ Thread Management
- **New threads** are created for each conversation/session
- Threads are ephemeral and session-specific
- Proper session thread mapping for conversation continuity

## How It Works

### 1. Agent Lookup Strategy
The system now follows this hierarchy:

1. **Check Environment**: Look for stored `AZURE_AI_AGENT_ID`
2. **Search by Name**: Find existing "intelligent-claims-orchestrator" agent  
3. **Create New**: Only if none found, create a new agent
4. **Store ID**: Save the agent ID for future use

### 2. Thread Strategy
- **Persistent Threads**: Chat conversations reuse threads per session
- **Isolated Threads**: Claim processing gets dedicated threads
- **Clean Lifecycle**: Threads are properly cleaned up when done

## Configuration

### Environment Variables
Add this to your `.env` file to enable persistence:

```bash
# Azure AI Agent Persistence
AZURE_AI_AGENT_ID=your_agent_id_here
```

### Getting Your Agent ID
1. Run the orchestrator once - it will create an agent and log the ID
2. Use the management utility: `python manage_agents.py`
3. Copy the ID from logs and add to `.env`

## Management Tools

### Agent Management Utility
Use the included `manage_agents.py` script:

```bash
cd /path/to/claims_orchestrator
python manage_agents.py
```

Features:
- 📊 Show agent status and recommendations
- 📋 List all agents in Azure AI Foundry
- 🔄 Get or create agent with persistence
- 🧹 Clean up duplicate agents  
- 💾 Update .env file automatically

### Cleanup Old Agents
If you have duplicate agents from before this fix:

```python
# In Python
orchestrator = IntelligentClaimsOrchestrator()
orchestrator.cleanup_old_agents()
```

Or use the management utility menu option.

## Benefits

### 🚀 Performance
- Faster startup (no agent creation delay)
- Reduced API calls to Azure AI Foundry
- Better resource utilization

### 💰 Cost Optimization  
- No redundant agent creation costs
- Fewer unnecessary API operations
- Efficient resource usage

### 🧹 Clean Architecture
- Proper separation: Agent (persistent) vs Threads (ephemeral)
- Better error handling and fallbacks
- Cleaner Azure AI Foundry workspace

### 📈 Scalability
- Support for multiple concurrent sessions
- Proper session isolation
- Better memory management

## Code Changes Summary

### Key Files Modified
1. **`intelligent_orchestrator.py`**:
   - `create_azure_agent()` → `get_or_create_azure_agent()`
   - Added agent persistence logic
   - Added cleanup utilities
   - Added status reporting

2. **`__main__.py`**:
   - Updated initialization to use new method
   - Better logging and error handling

3. **New Files**:
   - `manage_agents.py`: Agent management utility
   - This README documentation

### Backwards Compatibility
- ✅ Existing functionality unchanged
- ✅ Fallback mode still works without Azure AI
- ✅ No breaking changes to the API
- ✅ Works with or without stored agent ID

## Next Steps

1. **Add Agent ID**: Add `AZURE_AI_AGENT_ID` to your `.env` file
2. **Clean Up**: Use the management utility to remove duplicate agents  
3. **Monitor**: Check logs for persistence confirmations
4. **Optimize**: Consider adding agent ID to configuration management system

## Troubleshooting

### If Agent Not Found
The system will automatically create a new agent and provide the ID to store.

### If Multiple Agents Exist  
Use the cleanup utility to remove duplicates and keep the most recent one.

### If Environment Variable Missing
The system will search by name as fallback, then create new if needed.

## Future Enhancements

Possible improvements for the future:
- Database storage for agent IDs (instead of environment variables)
- Agent version management and updates
- Automated agent health monitoring
- Cross-environment agent sharing strategies
