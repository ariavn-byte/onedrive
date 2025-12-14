
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


# --- Authentication Middleware ---
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow health check and root without auth
        # FastMCP endpoints might differ, but usually /sse and /messages are used.
        if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Check for API Key in header or query
        # Copilot Studio sends it in header if configured
        key = request.headers.get(API_KEY_NAME) or request.query_params.get(API_KEY_NAME)

        if key != API_KEY:
             return Response("Unauthorized: Invalid API Key", status_code=401)

        return await call_next(request)

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
