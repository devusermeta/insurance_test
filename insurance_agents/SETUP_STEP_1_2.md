# Step 1.2: Cosmos DB Collections Setup

This step sets up the Cosmos DB collections based on the CSV schemas from the Docs/ folder.

## Prerequisites

1. **Azure Cosmos DB Account**: You need an active Cosmos DB account
2. **Connection Details**: Endpoint URL and primary key (or Azure Identity setup)
3. **Python Dependencies**: Install required packages

## Setup Instructions

### 1. Install Dependencies
```bash
cd insurance_agents
pip install -r requirements.txt
```

### 2. Configure Cosmos DB Connection
```bash
# Copy example environment file
copy .env.example .env

# Edit .env file with your Cosmos DB details:
# COSMOS_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
# COSMOS_KEY=your-primary-key-here  
# COSMOS_DATABASE=insurance_claims
```

### 3. Run Cosmos Setup
```bash
python cosmos_setup.py
```

### 4. Test MCP Connection
```bash
# Start MCP server (in separate terminal)
cd ../azure-cosmos-mcp-server-samples/python
python cosmos_server.py --port 8000

# Test connection (in original terminal)
cd ../insurance_agents
python test_mcp_connection.py
```

## Expected Terminal Output

When setup runs successfully, you should see:
```
[2025-09-03 10:15:23] 📋 COSMOS_SETUP: Initializing Cosmos DB connection...
[2025-09-03 10:15:23] 🧠 REASONING: Using endpoint: https://your-account.documents.azure.com:443/
[2025-09-03 10:15:24] ✅ COSMOS_SETUP: Connected using primary key authentication
[2025-09-03 10:15:24] 📋 COSMOS_SETUP: Setting up database: insurance_claims
[2025-09-03 10:15:25] ✅ COSMOS_SETUP: Database 'insurance_claims' ready
[2025-09-03 10:15:25] 📋 COLLECTIONS: Creating insurance claims collections...
...
[2025-09-03 10:15:35] ✅ SETUP_COMPLETE: Cosmos DB collections setup completed successfully!
```

## Collections Created

The following collections will be created with proper partition keys:

- **claims** (`/claimId`) - Main claim records
- **artifacts** (`/claimId`) - File metadata
- **agent_runs** (`/claimId`) - A2A execution tracking  
- **events** (`/claimId`) - Audit trail
- **threads** (`/claimThreadId`) - Conversation linkage
- **extractions_files** (`/claimId`) - Per-file extraction results
- **extractions_summary** (`/claimId`) - Claim-level summaries
- **rules_eval** (`/claimId`) - Coverage decisions
- **rules_catalog** (`/ruleId`) - Policy rules reference

## Sample Data

The setup script will load sample data from:
- `../Docs/claims.csv` → claims collection
- `../Docs/artifacts.csv` → artifacts collection

## Testing

After setup, verify:
1. ✅ Collections exist in Cosmos DB
2. ✅ Sample data is loaded
3. ✅ MCP server can connect
4. ✅ Basic read/write operations work

## Troubleshooting

**Connection Issues:**
- Verify COSMOS_ENDPOINT and COSMOS_KEY in .env
- Check firewall/network settings
- Ensure Cosmos DB account is active

**Import Errors:**
- Run `pip install -r requirements.txt`
- Check Python version (3.8+ required)

**MCP Server Issues:**
- Verify server is running on port 8000
- Check azure-cosmos-mcp-server-samples setup
- Ensure no port conflicts
