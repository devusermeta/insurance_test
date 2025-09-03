# Cosmos Query Agent

A specialized agent that uses the Azure Cosmos DB MCP Server to query and explore Cosmos DB data.

## Features

This agent provides tools to:
- Query Cosmos DB using SQL-like syntax
- List available containers/collections
- Describe container schemas
- Get sample documents
- Count documents in containers
- Analyze partition key information
- Inspect indexing policies
- Find implied relationships between collections

## Available Tools (via MCP Server)

1. **query_cosmos**: Run arbitrary SQL-like queries on the active CosmosDB container
2. **list_collections**: List all container names in the current database
3. **describe_container**: Describe the schema of a container by inspecting sample documents
4. **get_sample_documents**: Retrieve sample documents to preview real data
5. **count_documents**: Count total number of documents in a container
6. **get_partition_key_info**: Get partition key information for optimization
7. **get_indexing_policy**: Retrieve indexing policy for performance analysis
8. **find_implied_links**: Detect relationship hints by analyzing field patterns

## Usage

The agent can be queried in natural language to explore and query the Cosmos DB data:

- "Show me all containers in the database"
- "Query the actions container for time_agent entries"
- "Describe the schema of the playwright_logs database"
- "Count how many documents are in the actions container"
- "Show me sample documents from the actions container"

## Requirements

- Azure Cosmos DB MCP Server running on localhost:8080
- Valid Cosmos DB configuration
- A2A SDK for multi-agent framework integration
