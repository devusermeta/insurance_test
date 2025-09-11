@echo off
echo 🗄️ Starting Cosmos DB MCP Server for Insurance Claims
echo ================================================================

echo 📍 Navigating to MCP server directory...
cd /d "D:\Metakaal\insurance\azure-cosmos-mcp-server-samples\python"

echo 🔧 Activating Python environment...
call "D:\Metakaal\insurance\insurance_agents\.venv\Scripts\activate.bat"

echo 🚀 Starting MCP server...
python -m mcp_server

echo ✅ MCP Server started successfully!
pause
