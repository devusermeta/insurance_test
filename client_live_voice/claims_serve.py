#!/usr/bin/env python3
"""
Enhanced HTTP server for Claims Assistant Voice Live web frontend with CosmosDB integration
Run this to serve the claims HTML/JS files locally and provide API endpoints for real claims data
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import json
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
from azure.cosmos import CosmosClient, exceptions

# Load environment variables
load_dotenv()

class CosmosDBService:
    """Service class to handle CosmosDB operations for claims data"""
    
    def __init__(self):
        self.endpoint = os.getenv('COSMOS_DB_ENDPOINT')
        self.key = os.getenv('COSMOS_DB_KEY')
        self.database_name = os.getenv('COSMOS_DATABASE')
        self.container_name = os.getenv('COSMOS_CONTAINER')
        
        if not all([self.endpoint, self.key, self.database_name, self.container_name]):
            raise ValueError("Missing required CosmosDB environment variables")
        
        try:
            self.client = CosmosClient(self.endpoint, self.key)
            self.database = self.client.get_database_client(self.database_name)
            self.container = self.database.get_container_client(self.container_name)
            print(f"✅ Connected to CosmosDB: {self.database_name}/{self.container_name}")
        except Exception as e:
            print(f"❌ Failed to connect to CosmosDB: {e}")
            self.client = None
    
    def get_claim_by_id(self, claim_id):
        """Get a claim by its ID"""
        if not self.client:
            return {"error": "CosmosDB connection not available"}
        
        try:
            # Try to get by document id first
            try:
                item = self.container.read_item(item=claim_id, partition_key=claim_id)
                return item
            except exceptions.CosmosResourceNotFoundError:
                # If not found by id, try querying by claimId field
                query = "SELECT * FROM c WHERE c.claimId = @claim_id"
                items = list(self.container.query_items(
                    query=query,
                    parameters=[{"name": "@claim_id", "value": claim_id}],
                    enable_cross_partition_query=True
                ))
                if items:
                    return items[0]
                else:
                    return {"error": f"Claim {claim_id} not found"}
        except Exception as e:
            return {"error": f"Error querying CosmosDB: {str(e)}"}
    
    def search_claims(self, search_term):
        """Search claims by patient name, claim ID, or other fields"""
        if not self.client:
            return {"error": "CosmosDB connection not available"}
        
        try:
            # Search across multiple fields
            query = """
            SELECT * FROM c WHERE 
            CONTAINS(UPPER(c.patientName), UPPER(@search_term)) OR
            CONTAINS(UPPER(c.claimId), UPPER(@search_term)) OR
            CONTAINS(UPPER(c.diagnosis), UPPER(@search_term)) OR
            CONTAINS(UPPER(c.status), UPPER(@search_term))
            """
            items = list(self.container.query_items(
                query=query,
                parameters=[{"name": "@search_term", "value": search_term}],
                enable_cross_partition_query=True
            ))
            return {"claims": items, "count": len(items)}
        except Exception as e:
            return {"error": f"Error searching CosmosDB: {str(e)}"}
    
    def get_all_claims(self, limit=100):
        """Get all claims with optional limit"""
        if not self.client:
            return {"error": "CosmosDB connection not available"}
        
        try:
            query = "SELECT * FROM c ORDER BY c.submittedAt DESC"
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            # Apply limit
            if limit:
                items = items[:limit]
            return {"claims": items, "count": len(items)}
        except Exception as e:
            return {"error": f"Error querying CosmosDB: {str(e)}"}

class EnhancedClaimsHandler(http.server.SimpleHTTPRequestHandler):
    """Enhanced HTTP handler with CosmosDB API endpoints"""
    
    def __init__(self, *args, cosmos_service=None, **kwargs):
        self.cosmos_service = cosmos_service
        super().__init__(*args, **kwargs)
    
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        # Required for audio worklets
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests for both files and API endpoints"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # API endpoints
        if path.startswith('/api/'):
            self.handle_api_request(path, query_params)
        else:
            # Serve static files
            if path == '/' or path == '/index.html':
                self.path = '/claims.html'
            super().do_GET()
    
    def handle_api_request(self, path, query_params):
        """Handle API requests for claims data"""
        try:
            if path == '/api/claims/search':
                # Search claims: /api/claims/search?q=search_term
                search_term = query_params.get('q', [''])[0]
                if search_term:
                    result = self.cosmos_service.search_claims(search_term)
                else:
                    result = self.cosmos_service.get_all_claims()
                self.send_json_response(result)
            
            elif path.startswith('/api/claims/'):
                # Get specific claim: /api/claims/{claim_id}
                claim_id = path.split('/')[-1]
                if claim_id:
                    result = self.cosmos_service.get_claim_by_id(claim_id)
                    self.send_json_response(result)
                else:
                    self.send_json_response({"error": "Claim ID required"}, 400)
            
            elif path == '/api/claims':
                # Get all claims: /api/claims?limit=50
                limit = int(query_params.get('limit', [100])[0])
                result = self.cosmos_service.get_all_claims(limit)
                self.send_json_response(result)
            
            else:
                self.send_json_response({"error": "API endpoint not found"}, 404)
                
        except Exception as e:
            self.send_json_response({"error": f"Server error: {str(e)}"}, 500)
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response with proper headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = json.dumps(data, indent=2, default=str)
        self.wfile.write(response.encode('utf-8'))

def main():
    # Change to the directory containing this script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    PORT = 8001
    
    # Initialize CosmosDB service
    try:
        cosmos_service = CosmosDBService()
    except Exception as e:
        print(f"❌ Failed to initialize CosmosDB service: {e}")
        print("💡 Check your .env file and CosmosDB credentials")
        sys.exit(1)
    
    # Create handler class with CosmosDB service
    def handler_factory(*args, **kwargs):
        return EnhancedClaimsHandler(*args, cosmos_service=cosmos_service, **kwargs)
    
    try:
        with socketserver.TCPServer(("", PORT), handler_factory) as httpd:
            print(f"🏥 Claims Assistant Voice Live Web Frontend with CosmosDB Integration")
            print(f"📡 Server running at http://localhost:{PORT}")
            print(f"📁 Serving claims interface from: {script_dir}")
            print(f"🗄️  CosmosDB endpoints available:")
            print(f"   • GET /api/claims - Get all claims")
            print(f"   • GET /api/claims/{'{claim_id}'} - Get specific claim") 
            print(f"   • GET /api/claims/search?q=term - Search claims")
            print(f"🔗 Opening browser...")
            print(f"📝 Press Ctrl+C to stop the server")
            print()
            
            # Open browser automatically
            webbrowser.open(f'http://localhost:{PORT}')
            
            print("🎤 Ready to use Claims Assistant Voice Chat with live CosmosDB data!")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
    except OSError as e:
        if e.errno == 48:  # Port already in use
            print(f"❌ Port {PORT} is already in use.")
            print(f"💡 Try a different port or stop the existing server.")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()