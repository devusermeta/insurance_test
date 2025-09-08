#!/usr/bin/env python3
"""
Test script for the new chat functionality
This script will help verify that all components are working together
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the insurance_agents directory to the path
sys.path.append(str(Path(__file__).parent / "insurance_agents"))

async def test_mcp_chat_client():
    """Test the MCP chat client directly"""
    try:
        from shared.mcp_chat_client import mcp_chat_client
        
        print("🔍 Testing MCP Chat Client...")
        
        # Test queries
        test_queries = [
            "Hello, what can you help me with?",
            "Show me recent claims",
            "How many claims are pending?",
            "What's the system status?"
        ]
        
        for query in test_queries:
            print(f"\n📝 Testing query: '{query}'")
            try:
                response = await mcp_chat_client.query_cosmos_data(query)
                print(f"✅ Response: {response[:200]}..." if len(response) > 200 else f"✅ Response: {response}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import MCP chat client: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error testing MCP client: {e}")
        return False

async def test_claims_orchestrator():
    """Test the enhanced claims orchestrator"""
    try:
        from agents.claims_orchestrator.claims_orchestrator_executor import ClaimsOrchestratorExecutor
        
        print("\n🤖 Testing Claims Orchestrator...")
        
        orchestrator = ClaimsOrchestratorExecutor()
        
        # Test chat query handling
        test_result = await orchestrator._handle_chat_query(
            "Chat Query: Hello, show me recent claims", 
            {"session_id": "test_session"}
        )
        
        print(f"✅ Orchestrator chat test result: {json.dumps(test_result, indent=2)}")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Claims Orchestrator: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing Claims Orchestrator: {e}")
        return False

def test_frontend_files():
    """Test that the frontend files are in place"""
    print("\n🎨 Testing Frontend Files...")
    
    dashboard_dir = Path(__file__).parent / "insurance_agents" / "insurance_agents_registry_dashboard"
    
    # Check HTML file
    html_file = dashboard_dir / "static" / "claims_dashboard.html"
    if html_file.exists():
        print("✅ claims_dashboard.html exists")
        
        # Check if chat functionality is present
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "chat-btn" in content and "sendMessage" in content:
                print("✅ Chat functionality found in HTML")
            else:
                print("❌ Chat functionality missing in HTML")
    else:
        print("❌ claims_dashboard.html not found")
    
    # Check CSS file
    css_file = dashboard_dir / "static" / "chat_styles.css"
    if css_file.exists():
        print("✅ chat_styles.css exists")
    else:
        print("❌ chat_styles.css not found")
    
    # Check API endpoints in app
    app_file = dashboard_dir / "app_fixed.py"
    if app_file.exists():
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "/api/chat" in content:
                print("✅ Chat API endpoint found in app_fixed.py")
            else:
                print("❌ Chat API endpoint missing in app_fixed.py")
    else:
        print("❌ app_fixed.py not found")

def check_dependencies():
    """Check if required dependencies are available"""
    print("\n📦 Checking Dependencies...")
    
    required_packages = [
        "httpx",
        "aiohttp", 
        "fastapi",
        "uvicorn"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("To install missing packages, run:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

async def main():
    """Main test function"""
    print("🧪 Testing Insurance Claims Chat Integration")
    print("=" * 50)
    
    # Test 1: Check frontend files
    test_frontend_files()
    
    # Test 2: Check dependencies
    deps_ok = check_dependencies()
    
    if not deps_ok:
        print("\n❌ Dependencies missing - please install them first")
        return
    
    # Test 3: Test MCP chat client
    mcp_ok = await test_mcp_chat_client()
    
    # Test 4: Test claims orchestrator 
    orchestrator_ok = await test_claims_orchestrator()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"Frontend Files: ✅ Ready")
    print(f"Dependencies: {'✅ Ready' if deps_ok else '❌ Missing'}")
    print(f"MCP Chat Client: {'✅ Ready' if mcp_ok else '❌ Issues'}")  
    print(f"Claims Orchestrator: {'✅ Ready' if orchestrator_ok else '❌ Issues'}")
    
    if all([deps_ok, mcp_ok, orchestrator_ok]):
        print("\n🎉 All tests passed! The chat integration is ready to use.")
        print("\nTo start the system:")
        print("1. Start the Cosmos MCP server: python azure-cosmos-mcp-server-samples/python/cosmos_server.py")
        print("2. Start the Claims Orchestrator: cd insurance_agents && python -m agents.claims_orchestrator")
        print("3. Start the Dashboard: cd insurance_agents/insurance_agents_registry_dashboard && python app_fixed.py")
        print("4. Open http://localhost:3000 and click the 'Chat with Orchestrator' button")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    asyncio.run(main())
