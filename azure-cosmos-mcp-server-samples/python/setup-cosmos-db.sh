# Azure Cosmos DB Setup Commands

# 1. Login to Azure (if not already logged in)
az login

# 2. Create a resource group (if you don't have one)
az group create --name rg-a2a-agents --location eastus

# 3. Create a Cosmos DB account
az cosmosdb create \
  --name cosmos-a2a-agents \
  --resource-group rg-a2a-agents \
  --kind GlobalDocumentDB \
  --locations regionName=eastus \
  --default-consistency-level Session \
  --enable-free-tier true

# 4. Create a database
az cosmosdb sql database create \
  --account-name cosmos-a2a-agents \
  --resource-group rg-a2a-agents \
  --name agent_logs

# 5. Create a container
az cosmosdb sql container create \
  --account-name cosmos-a2a-agents \
  --resource-group rg-a2a-agents \
  --database-name agent_logs \
  --name time_agent_logs \
  --partition-key-path "/partition_key" \
  --throughput 400

# 6. Get the connection details
echo "Getting Cosmos DB URI..."
az cosmosdb show --name cosmos-a2a-agents --resource-group rg-a2a-agents --query documentEndpoint --output tsv

echo "Getting Cosmos DB Primary Key..."
az cosmosdb keys list --name cosmos-a2a-agents --resource-group rg-a2a-agents --query primaryMasterKey --output tsv
