
import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from mcp.server.fastmcp import FastMCP

# Import the existing OneDrive logic
import function_app
from function_app import organizer

# API Key for Copilot Studio authentication
API_KEY_NAME = "X-API-Key"
API_KEY = os.environ.get("MCP_API_KEY", "copilot-studio-secret")

# Define the FastMCP server
# "OneDrive Organizer" is the name of the server
mcp = FastMCP("OneDrive Organizer")

@mcp.tool()
def move_large_file(file_id: str, new_parent_path: str, user_id: str = None) -> str:
    """
    Move a file of ANY size (including files > 5MB) to a new parent folder.
    Use this tool when the native 'moveSmallFile' tool fails or for large files.

    Args:
        file_id: The ID of the file to move.
        new_parent_path: The path of the folder to move the file into (e.g. "/Documents/Archive").
        user_id: Optional user ID to act on behalf of.
    """
    # Reuse the existing logic which uses Graph API PATCH
    # This implementation (PATCH /items/{id}) handles large files correctly
    # because it is a metadata operation, not a content transfer.
    try:
        result = organizer.move_file(file_id, new_parent_path, user_id)
        return str(result)
    except Exception as e:
        return f"Error moving file: {str(e)}"

@mcp.tool()
def list_files(folder_path: str = "/", limit: int = 20, user_id: str = None) -> str:
    """List files in a specific folder."""
    try:
        result = organizer.list_files(folder_path, limit, user_id)
        return str(result)
    except Exception as e:
        return f"Error listing files: {str(e)}"

@mcp.tool()
def create_folder(name: str, parent_path: str = "/", user_id: str = None) -> str:
    """Create a new folder."""
    try:
        result = organizer.create_folder(name, parent_path, user_id)
        return str(result)
    except Exception as e:
        return f"Error creating folder: {str(e)}"

@mcp.tool()
def delete_file(file_id: str, user_id: str = None) -> str:
    """Delete a file."""
    try:
        result = organizer.delete_file(file_id, user_id)
        return str(result)
    except Exception as e:
        return f"Error deleting file: {str(e)}"

@mcp.tool()
def upload_file(file_path: str, target_path: str, user_id: str = None) -> str:
    """Upload a file from local path to OneDrive."""
    try:
        result = organizer.upload_file(file_path, target_path, user_id)
        return str(result)
    except Exception as e:
        return f"Error uploading file: {str(e)}"

@mcp.tool()
def bulk_move(file_ids: list[str], target_path: str, user_id: str = None) -> str:
    """Move multiple files at once."""
    try:
        result = organizer.bulk_move(file_ids, target_path, user_id)
        return str(result)
    except Exception as e:
        return f"Error in bulk move: {str(e)}"

@mcp.tool()
def bulk_delete(file_ids: list[str], user_id: str = None) -> str:
    """Delete multiple files at once."""
    try:
        result = organizer.bulk_delete(file_ids, user_id)
        return str(result)
    except Exception as e:
        return f"Error in bulk delete: {str(e)}"


# --- Authentication & Compliance Middleware (Pure ASGI) ---
class APIKeyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "")

        # 1. Compliance Fix for Copilot Studio
        # Inject "text/event-stream" into Accept header if missing for /mcp endpoint
        if path == "/mcp":
            headers = list(scope["headers"])
            accept_index = -1
            accept_value = None

            for i, (k, v) in enumerate(headers):
                if k.lower() == b"accept":
                    accept_index = i
                    accept_value = v
                    break

            required_part = b"text/event-stream"
            json_part = b"application/json"

            if accept_index == -1:
                # Missing Accept header -> Add it
                headers.append((b"accept", b"application/json, text/event-stream"))
            elif required_part not in accept_value:
                # Incomplete Accept header -> Append required part
                # Also ensure application/json is there
                new_value = accept_value + b", " + required_part
                if json_part not in new_value:
                    new_value += b", " + json_part
                headers[accept_index] = (b"accept", new_value)

            scope["headers"] = headers

        # 2. Authentication Check
        # Allow health check and root without auth
        if path in ["/", "/health", "/docs", "/openapi.json"]:
            return await self.app(scope, receive, send)

        # Extract API Key from headers or query
        api_key_name_bytes = API_KEY_NAME.lower().encode()
        provided_key = None

        # Check headers
        for k, v in scope["headers"]:
            if k.lower() == api_key_name_bytes:
                provided_key = v.decode()
                break

        # Check query params if not in header
        if not provided_key:
            query_string = scope.get("query_string", b"").decode()
            if query_string:
                from urllib.parse import parse_qs
                qs = parse_qs(query_string)
                if API_KEY_NAME in qs:
                    provided_key = qs[API_KEY_NAME][0]

        if provided_key != API_KEY:
            print(f"⚠️ Auth Failed for path: {path}")
            if not provided_key:
                print("   Reason: No API Key provided in headers or query.")
            else:
                print(f"   Reason: Key mismatch. Provided length: {len(provided_key)}, Expected length: {len(API_KEY)}")
                # Do not log the full key for security, but maybe the first char helps
                print(f"   Provided start: '{provided_key[:2]}***', Expected start: '{API_KEY[:2]}***'")

            response = Response("Unauthorized: Invalid API Key", status_code=401)
            return await response(scope, receive, send)

        return await self.app(scope, receive, send)

# --- Server Setup ---

# Get the Starlette app from FastMCP
# This app handles the MCP protocol (SSE and messages)
app = mcp.streamable_http_app()

# Add auth middleware to the app
app.add_middleware(APIKeyMiddleware)

# Add health check route
async def health_check(request):
    return Response('{"status": "healthy"}', media_type="application/json")

app.add_route("/health", health_check, methods=["GET"])

if __name__ == "__main__":
    # Get port from environment variable (Render sets this)
    port = int(os.environ.get("PORT", 8000))
    # Run the Starlette app
    uvicorn.run(app, host="0.0.0.0", port=port)
