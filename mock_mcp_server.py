"""
Mock MCP server for testing time_agent integration.
This server provides the same interface as the Cosmos DB MCP server but with mock data.
"""
import json
import logging
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock-mcp-server")

# Initialize FastMCP
mcp = FastMCP("Mock MCP Server")

@mcp.tool()
def query_cosmos(query: str) -> str:
    """
    Mock query tool that returns sample data.
    
    Args:
        query: SQL-like query string
        
    Returns:
        Formatted mock results
    """
    logger.info(f"Mock query executed: {query}")
    
    # Return mock data
    mock_results = [
        {
            "id": "mock-1",
            "timestamp": "2025-08-21T10:30:00Z",
            "action": "time_query",
            "agent": "time_agent",
            "details": "Mock logged action"
        },
        {
            "id": "mock-2", 
            "timestamp": "2025-08-21T10:25:00Z",
            "action": "another_action",
            "agent": "time_agent",
            "details": "Another mock action"
        }
    ]
    
    # Format results similar to real Cosmos DB output
    result = f"Query results (mock data):\n"
    result += f"Found {len(mock_results)} items\n"
    result += "-" * 50 + "\n"
    
    for item in mock_results:
        result += f"ID: {item['id']}\n"
        result += f"Timestamp: {item['timestamp']}\n"
        result += f"Action: {item['action']}\n"
        result += f"Agent: {item['agent']}\n"
        result += f"Details: {item['details']}\n"
        result += "-" * 30 + "\n"
    
    return result

@mcp.tool()
def list_collections() -> str:
    """
    Mock list collections tool.
    
    Returns:
        List of mock container names
    """
    logger.info("Mock list_collections called")
    return "Available containers (mock):\n- actions\n- logs\n- events"

@mcp.tool()
def insert_action(action: str, agent: str, details: str = "") -> str:
    """
    Mock insert tool for testing.
    
    Args:
        action: Action name to log
        agent: Agent name performing the action
        details: Additional details
        
    Returns:
        Success message with mock ID
    """
    logger.info(f"Mock insert: action={action}, agent={agent}, details={details}")
    
    mock_id = f"mock-{hash(f'{action}{agent}{details}') % 10000}"
    return f"Successfully inserted action (mock)\nGenerated ID: {mock_id}\nAction: {action}\nAgent: {agent}\nDetails: {details}"

def main():
    """Main entry point for the mock MCP server."""
    try:
        logger.info("Starting Mock MCP server on localhost:8080...")
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8080)
    except KeyboardInterrupt:
        logger.info("Mock server stopped by user")
    except Exception as e:
        logger.error(f"Mock server error: {str(e)}")

if __name__ == "__main__":
    main()
