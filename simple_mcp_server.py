"""
Simple working MCP server for testing time_agent integration.
This proves the concept without needing real Cosmos DB setup.
"""
import json
import logging
from datetime import datetime
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple-mcp-server")

# Initialize FastMCP
mcp = FastMCP("Simple MCP Server")

# In-memory storage for demonstration
logged_actions = []

@mcp.tool()
def query_cosmos(query: str) -> str:
    """
    Query logged actions (mock implementation).
    
    Args:
        query: Query string (ignored for simplicity)
        
    Returns:
        List of logged actions
    """
    logger.info(f"Query executed: {query}")
    
    if not logged_actions:
        return "No actions logged yet."
    
    result = "Logged Actions:\n" + "=" * 50 + "\n"
    for i, action in enumerate(logged_actions, 1):
        result += f"{i}. {action['timestamp']} - {action['agent']}: {action['action']}\n"
        if action.get('details'):
            result += f"   Details: {action['details']}\n"
        result += "\n"
    
    return result

@mcp.tool() 
def log_action(agent: str, action: str, details: str = "") -> str:
    """
    Log an action from an agent.
    
    Args:
        agent: Name of the agent
        action: Action performed
        details: Additional details
        
    Returns:
        Success message
    """
    timestamp = datetime.now().isoformat()
    
    logged_action = {
        "timestamp": timestamp,
        "agent": agent, 
        "action": action,
        "details": details
    }
    
    logged_actions.append(logged_action)
    
    logger.info(f"Action logged: {agent} - {action}")
    
    return f"Action logged successfully!\nAgent: {agent}\nAction: {action}\nTimestamp: {timestamp}"

@mcp.tool()
def get_stats() -> str:
    """
    Get statistics about logged actions.
    
    Returns:
        Statistics summary
    """
    if not logged_actions:
        return "No actions logged yet."
    
    total = len(logged_actions)
    agents = set(action['agent'] for action in logged_actions)
    
    result = f"Action Log Statistics:\n"
    result += f"Total actions: {total}\n"
    result += f"Active agents: {len(agents)}\n"
    result += f"Agents: {', '.join(sorted(agents))}\n"
    
    return result

def main():
    """Main entry point for the simple MCP server."""
    try:
        logger.info("Starting Simple MCP server on localhost:8081...")
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8081)
    except KeyboardInterrupt:
        logger.info("Simple server stopped by user")
    except Exception as e:
        logger.error(f"Simple server error: {str(e)}")

if __name__ == "__main__":
    main()
