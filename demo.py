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
        },
        # New enhanced tools examples
        "upload_file": {
            "description": "Upload a file to OneDrive",
            "data": {"file_path": "/local/path/file.txt", "target_path": "/Documents/file.txt"},
            "curl": 'curl -X POST "http://localhost:8000/invoke/upload_file" -H "Content-Type: application/json" -d \'{"file_path": "/local/path/file.txt", "target_path": "/Documents/file.txt"}\''
        },
        "download_file": {
            "description": "Download a file from OneDrive",
            "data": {"file_id": "file-id-here", "local_path": "/local/download/file.txt"},
            "curl": 'curl -X POST "http://localhost:8000/invoke/download_file" -H "Content-Type: application/json" -d \'{"file_id": "file-id-here", "local_path": "/local/download/file.txt"}\''
        },
        "copy_file": {
            "description": "Copy a file to a new location",
            "data": {"file_id": "file-id-here", "new_name": "copy_of_file.txt", "target_path": "/Backups"},
            "curl": 'curl -X POST "http://localhost:8000/invoke/copy_file" -H "Content-Type: application/json" -d \'{"file_id": "file-id-here", "new_name": "copy_of_file.txt", "target_path": "/Backups"}\''
        },
        "rename_file": {
            "description": "Rename a file or folder",
            "data": {"file_id": "file-id-here", "new_name": "new_filename.txt"},
            "curl": 'curl -X POST "http://localhost:8000/invoke/rename_file" -H "Content-Type: application/json" -d \'{"file_id": "file-id-here", "new_name": "new_filename.txt"}\''
        },
        "get_file_content": {
            "description": "Get content of text files",
            "data": {"file_id": "file-id-here"},
            "curl": 'curl -X POST "http://localhost:8000/invoke/get_file_content" -H "Content-Type: application/json" -d \'{"file_id": "file-id-here"}\''
        },
        "get_file_thumbnail": {
            "description": "Get file thumbnails",
            "data": {"file_id": "file-id-here", "size": "large"},
            "curl": 'curl -X POST "http://localhost:8000/invoke/get_file_thumbnail" -H "Content-Type: application/json" -d \'{"file_id": "file-id-here", "size": "large"}\''
        },
        "search_by_type": {
            "description": "Search files by type/extension",
            "data": {"file_type": "*.pdf", "limit": 50},
            "curl": 'curl -X POST "http://localhost:8000/invoke/search_by_type" -H "Content-Type: application/json" -d \'{"file_type": "*.pdf", "limit": 50}\''
        },
        "search_by_date": {
            "description": "Search files by modification date",
            "data": {"start_date": "2024-01-01T00:00:00Z", "end_date": "2024-12-31T23:59:59Z", "limit": 50},
            "curl": 'curl -X POST "http://localhost:8000/invoke/search_by_date" -H "Content-Type: application/json" -d \'{"start_date": "2024-01-01T00:00:00Z", "end_date": "2024-12-31T23:59:59Z", "limit": 50}\''
        },
        "get_recent_files": {
            "description": "Get recently modified files",
            "data": {"days": 7, "limit": 50},
            "curl": 'curl -X POST "http://localhost:8000/invoke/get_recent_files" -H "Content-Type: application/json" -d \'{"days": 7, "limit": 50}\''
        },
        "get_storage_usage": {
            "description": "Get OneDrive storage statistics",
            "data": {},
            "curl": 'curl -X POST "http://localhost:8000/invoke/get_storage_usage" -H "Content-Type: application/json" -d \'{}\''
        },
        "bulk_move": {
            "description": "Move multiple files to a target folder",
            "data": {"file_ids": ["file1-id", "file2-id"], "target_path": "/Archive"},
            "curl": 'curl -X POST "http://localhost:8000/invoke/bulk_move" -H "Content-Type: application/json" -d \'{"file_ids": ["file1-id", "file2-id"], "target_path": "/Archive"}\''
        },
        "bulk_delete": {
            "description": "Delete multiple files",
            "data": {"file_ids": ["file1-id", "file2-id"]},
            "curl": 'curl -X POST "http://localhost:8000/invoke/bulk_delete" -H "Content-Type: application/json" -d \'{"file_ids": ["file1-id", "file2-id"]}\''
        },
        "bulk_copy": {
            "description": "Copy multiple files to a target folder",
            "data": {"file_ids": ["file1-id", "file2-id"], "target_path": "/Backups"},
            "curl": 'curl -X POST "http://localhost:8000/invoke/bulk_copy" -H "Content-Type: application/json" -d \'{"file_ids": ["file1-id", "file2-id"], "target_path": "/Backups"}\''
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

def print_new_features():
    """Print information about new enhanced features"""
    print("\n🚀 New Enhanced Features:")
    print("=" * 60)
    
    print("✨ File Operations:")
    print("   • Upload files to OneDrive")
    print("   • Download files from OneDrive")
    print("   • Copy files to different locations")
    print("   • Rename files and folders")
    
    print("\n🔍 Advanced Search:")
    print("   • Search by file type/extension")
    print("   • Search by modification date")
    print("   • Get recently modified files")
    print("   • Enhanced file information")
    
    print("\n📊 Analytics & Insights:")
    print("   • Storage usage statistics")
    print("   • File activity tracking")
    print("   • Enhanced metadata retrieval")
    
    print("\n⚡ Bulk Operations:")
    print("   • Move multiple files at once")
    print("   • Delete multiple files at once")
    print("   • Copy multiple files at once")
    print("   • Batch organization rules")

def main():
    """Main demo function"""
    print_api_info()
    print_new_features()
    print_tool_examples()
    print_setup_instructions()
    
    print("\n" + "=" * 60)
    print("🎯 Next Steps:")
    print("1. Configure your Microsoft Graph API credentials in .env")
    print("2. Start the server with: python run.py")
    print("3. Explore the enhanced tools via the API documentation")
    print("4. Test file operations with the new capabilities")

if __name__ == "__main__":
    main()
