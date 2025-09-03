#!/usr/bin/env python3
"""
Insurance Dashboard Startup Script

Quick script to start the insurance claims processing dashboard
with proper terminal logging and environment setup.
"""

import os
import sys
from pathlib import Path

# Add the dashboard directory to path
dashboard_dir = Path(__file__).parent / "insurance_agents_registry_dashboard"
sys.path.append(str(dashboard_dir))

def main():
    """Start the insurance dashboard"""
    print("🖥️  Starting Insurance Claims Processing Dashboard...")
    print("📋 Loading environment and dependencies...")
    
    try:
        # Import and run the dashboard
        from insurance_agents_registry_dashboard.app import app
        import uvicorn
        
        print("✅ Dashboard loaded successfully!")
        print("🌐 Starting web server on http://localhost:3000")
        print("📊 Access the professional claims processing interface")
        print("🔧 Press Ctrl+C to stop the server")
        print("-" * 60)
        
        # Run the dashboard
        uvicorn.run(
            "insurance_agents_registry_dashboard.app:app",
            host="0.0.0.0",
            port=3000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure to install dependencies:")
        print("   pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Startup error: {e}")
        return False

if __name__ == "__main__":
    main()
