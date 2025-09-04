"""
Shared MCP (Model Context Protocol) Configuration for Insurance Agents
This module provides common MCP server configuration and utilities for all insurance agents.
"""

import os
from typing import Dict, Any, List
import json

class MCPConfig:
    """Configuration class for MCP servers used by insurance agents"""
    
    # Cosmos DB connection settings
    COSMOS_ENDPOINT = os.getenv("AZURE_COSMOS_ENDPOINT", "https://your-cosmos-account.documents.azure.com:443/")
    COSMOS_KEY = os.getenv("AZURE_COSMOS_KEY", "your-cosmos-key")
    COSMOS_DATABASE = "insurance_claims_db"
    
    # MCP Server URLs - Using Cosmos MCP server on port 8080
    MCP_SERVERS = {
        "cosmos_server": "http://localhost:8080"
    }
    
    # Agent-specific MCP server mappings - All agents use cosmos_server
    AGENT_MCP_MAPPING = {
        "claims_orchestrator": ["cosmos_server"],
        "intake_clarifier": ["cosmos_server"],
        "document_intelligence": ["cosmos_server"],
        "coverage_rules_engine": ["cosmos_server"]
    }
    
    # Cosmos DB collections accessible through MCP
    COLLECTIONS = {
        "claims": "claims",
        "artifacts": "artifacts", 
        "agent_runs": "agent_runs",
        "events": "events",
        "threads": "threads",
        "extractions_files": "extractions_files",
        "extractions_summary": "extractions_summary", 
        "rules_catalog": "rules_catalog",
        "rules_eval": "rules_eval"
    }

    @classmethod
    def get_agent_mcp_servers(cls, agent_name: str) -> List[str]:
        """Get the list of MCP servers that an agent should connect to"""
        return cls.AGENT_MCP_MAPPING.get(agent_name, [])
    
    @classmethod
    def get_mcp_server_url(cls, server_name: str) -> str:
        """Get the URL for a specific MCP server"""
        return cls.MCP_SERVERS.get(server_name, "")
    
    @classmethod
    def generate_mcp_config_json(cls, agent_name: str) -> Dict[str, Any]:
        """Generate MCP configuration JSON for a specific agent"""
        agent_servers = cls.get_agent_mcp_servers(agent_name)
        
        config = {
            "mcpServers": {}
        }
        
        for server_name in agent_servers:
            server_url = cls.get_mcp_server_url(server_name)
            config["mcpServers"][server_name] = {
                "command": "uvicorn",
                "args": [f"mcp_servers.{server_name}:app", "--port", server_url.split(":")[-1]],
                "env": {
                    "AZURE_COSMOS_ENDPOINT": cls.COSMOS_ENDPOINT,
                    "AZURE_COSMOS_KEY": cls.COSMOS_KEY,
                    "COSMOS_DATABASE": cls.COSMOS_DATABASE
                }
            }
        
        return config

# Agent port mappings for A2A communication
A2A_AGENT_PORTS = {
    "claims_orchestrator": 8001,
    "intake_clarifier": 8002, 
    "document_intelligence": 8003,
    "coverage_rules_engine": 8004
}

# Shared logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored": {
            "format": "🤖 %(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "colored"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
}
