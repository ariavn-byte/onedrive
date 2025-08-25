#!/usr/bin/env python3
"""
Demo script for OneDrive Organizer MCP Server
This shows the API structure and available tools
"""

import json
from function_app import ALLOWED_TOOLS

def print_api_info():
    """Print API information and available tools"""
    print("🚀 OneDrive Organizer MCP Server - API Demo")
    print("=" * 60)
    
    print("\n📡 Available Endpoints:")
    print("  GET  /                    - API information")
    print("  GET  /health              - Health check")
    print("  GET  /tools               - List available tools")
    print("  POST /invoke/{tool}       - Invoke a specific tool")
    
    print(f"\n🛠️  Available Tools ({len(ALLOWED_TOOLS)}):")
    for i, tool in enumerate(ALLOWED_TOOLS, 1):
        print(f"  {i:2d}. {tool}")
    
    print("\n📚 API Documentation:")
    print("  When server is running, visit: http://localhost:8000/docs")
    print("  Interactive Swagger UI with all endpoints and schemas")

def print_tool_examples():
    """Print example tool invocations"""
    print("\n💡 Tool Usage Examples:")
    print("=" * 60)
    
    examples = {
        "list_files": {
            "description": "List files in a OneDrive folder",
            "data": {"folder_path": "/", "limit": 20},
            "curl": 'curl -X POST "http://localhost:8000/invoke/list_files" -H "Content-Type: application/json" -d \'{"folder_path": "/", "limit": 20}\''
        },
        "create_folder": {
            "description": "Create a new folder",
            "data": {"name": "Work Documents", "parent_path": "/"},
            "curl": 'curl -X POST "http://localhost:8000/invoke/create_folder" -H "Content-Type: application/json" -d \'{"name": "Work Documents", "parent_path": "/"}\''
        },
        "search_files": {
            "description": "Search for files by query",
            "data": {"query": "*.pdf", "limit": 50},
            "curl": 'curl -X POST "http://localhost:8000/invoke/search_files" -H "Content-Type: application/json" -d \'{"query": "*.pdf", "limit": 50}\''
        },
        "organize_files": {
            "description": "Apply organization rules to files",
            "data": {
                "rules": [
                    {"action": "move", "search_query": "*.pdf", "target_folder": "PDFs"},
                    {"action": "move", "search_query": "*.docx", "target_folder": "Documents"}
                ]
            },
            "curl": 'curl -X POST "http://localhost:8000/invoke/organize_files" -H "Content-Type: application/json" -d \'{"rules": [{"action": "move", "search_query": "*.pdf", "target_folder": "PDFs"}]}\''
        }
    }
    
    for tool, example in examples.items():
        print(f"\n🔧 {tool.upper()}")
        print(f"   Description: {example['description']}")
        print(f"   Request Data: {json.dumps(example['data'], indent=3)}")
        print(f"   cURL Command: {example['curl']}")

def print_setup_instructions():
    """Print setup instructions"""
    print("\n📋 Setup Instructions:")
    print("=" * 60)
    
    print("1. 🔐 Configure Microsoft Graph API:")
    print("   - Go to Azure Portal > App Registrations")
    print("   - Create new app or use existing one")
    print("   - Add API permissions: Files.ReadWrite.All, Sites.ReadWrite.All")
    print("   - Generate client secret")
    
    print("\n2. 📝 Update .env file:")
    print("   - Replace placeholder values with real credentials")
    print("   - CLIENT_ID, CLIENT_SECRET, TENANT_ID")
    
    print("\n3. 🚀 Start the server:")
    print("   - Run: python run.py")
    print("   - Or: uvicorn main:app --reload")
    
    print("\n4. 🧪 Test the API:")
    print("   - Visit: http://localhost:8000/docs")
    print("   - Use the examples above to test endpoints")

def main():
    """Main demo function"""
    print_api_info()
    print_tool_examples()
    print_setup_instructions()
    
    print("\n" + "=" * 60)
    print("🎯 Next Steps:")
    print("1. Configure your Microsoft Graph API credentials in .env")
    print("2. Start the server with: python run.py")
    print("3. Test the API endpoints")
    print("4. Deploy to Render when ready")
    print("=" * 60)

if __name__ == "__main__":
    main()
