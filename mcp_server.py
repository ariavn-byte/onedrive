
import os
import json
import uvicorn
from fastapi import FastAPI, Request
from starlette.responses import Response
from starlette.middleware.cors import CORSMiddleware

# Import the existing OneDrive logic
import function_app
from function_app import organizer

# API Key for Copilot Studio authentication
API_KEY_NAME = "X-API-Key"
API_KEY = os.environ.get("MCP_API_KEY", "copilot-studio-secret")

# NOTE: We avoid FastMCP's StreamableHTTP due to strict Host validation behind ACA.
# Implement a minimal JSON-RPC 2.0 HTTP endpoint for tools/list and tools/call.

def move_large_file(drive_id: str, item_id: str, new_parent_id: str) -> str:
    """
    Move a file of ANY size (including files > 5MB) to a new parent folder using server-side Graph API.
    This is a metadata-only operation, not a content transfer, so it works for files of any size.

    Args:
        drive_id: The ID of the drive containing the file (e.g., from Graph /users/{id}/drives).
        item_id: The ID of the file to move.
        new_parent_id: The ID of the destination parent folder.

    Returns:
        JSON with operationId, itemId, name, webUrl, and status="completed".
    """
    try:
        result = organizer.move_large_file(drive_id, item_id, new_parent_id)
        return str(result)
    except Exception as e:
        return f"Error moving large file: {str(e)}"

def copy_large_file(source_drive_id: str, item_id: str, target_drive_id: str, target_parent_id: str) -> str:
    """
    Copy a file of ANY size (including files > 5MB) to a new location using async Graph API.
    This returns a monitor URL that must be polled to check completion status.

    Args:
        source_drive_id: The ID of the drive containing the source file.
        item_id: The ID of the file to copy.
        target_drive_id: The ID of the target drive (can be the same or different from source).
        target_parent_id: The ID of the destination parent folder in the target drive.

    Returns:
        JSON with operationId, monitorUrl, and status="pending". Use pollCopyStatus to track completion.
    """
    try:
        result = organizer.copy_large_file(source_drive_id, item_id, target_drive_id, target_parent_id)
        return str(result)
    except Exception as e:
        return f"Error copying large file: {str(e)}"

def poll_copy_status(monitor_url: str) -> str:
    """
    Poll the status of an async copy operation.
    Use the monitorUrl returned from copy_large_file() to check completion.

    Args:
        monitor_url: The Location header URL returned from copy_large_file.

    Returns:
        JSON with operationId, status (completed/inProgress/failed), and newItemId when complete.
    """
    try:
        result = organizer.poll_copy_status(monitor_url)
        return str(result)
    except Exception as e:
        return f"Error polling copy status: {str(e)}"

def list_files(folder_path: str = "/", limit: int = 20, user_id: str = None) -> str:
    """List files in a specific folder."""
    try:
        result = organizer.list_files(folder_path, limit, user_id)
        return str(result)
    except Exception as e:
        return f"Error listing files: {str(e)}"

def create_folder(name: str, parent_path: str = "/", user_id: str = None) -> str:
    """Create a new folder."""
    try:
        result = organizer.create_folder(name, parent_path, user_id)
        return str(result)
    except Exception as e:
        return f"Error creating folder: {str(e)}"

def delete_file(file_id: str, user_id: str = None) -> str:
    """Delete a file."""
    try:
        result = organizer.delete_file(file_id, user_id)
        return str(result)
    except Exception as e:
        return f"Error deleting file: {str(e)}"

def upload_file(file_path: str, target_path: str, user_id: str = None) -> str:
    """Upload a file from local path to OneDrive."""
    try:
        result = organizer.upload_file(file_path, target_path, user_id)
        return str(result)
    except Exception as e:
        return f"Error uploading file: {str(e)}"

def bulk_move(file_ids: list[str], target_path: str, user_id: str = None) -> str:
    """Move multiple files at once."""
    try:
        result = organizer.bulk_move(file_ids, target_path, user_id)
        return str(result)
    except Exception as e:
        return f"Error in bulk move: {str(e)}"

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
        # 0. Normalize Host header for /mcp endpoint to fix Azure Container Apps issue
        # Apply to any subpath under /mcp (e.g., /mcp, /mcp/, /mcp/tools, etc.)
        if path.startswith("/mcp"):
            # Rewrite Host and related headers to safe localhost values to satisfy FastMCP
            headers = list(scope["headers"])

            def upsert(name: bytes, value: bytes):
                idx = -1
                for i, (k, v) in enumerate(headers):
                    if k.lower() == name:
                        idx = i
                        break
                if idx == -1:
                    headers.append((name, value))
                else:
                    headers[idx] = (name, value)

            upsert(b"host", b"localhost")
            upsert(b"x-forwarded-host", b"localhost")
            upsert(b"origin", b"http://localhost")
            scope["headers"] = headers


        # 1. Compliance Fix for Copilot Studio
        # Inject "text/event-stream" into Accept header if missing for /mcp endpoint
        # Apply to any subpath under /mcp
        if path.startswith("/mcp"):
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

# Create a minimal FastAPI app that serves JSON-RPC 2.0 over HTTP at /mcp
app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (ACA ingress, Copilot Studio, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def get_tools_list():
    # Minimal MCP-like tool descriptors for Copilot Studio
    return [
        {
            "name": "move_large_file",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "drive_id": {"type": "string"},
                    "item_id": {"type": "string"},
                    "new_parent_id": {"type": "string"}
                },
                "required": ["drive_id", "item_id", "new_parent_id"]
            }
        },
        {
            "name": "copy_large_file",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "source_drive_id": {"type": "string"},
                    "item_id": {"type": "string"},
                    "target_drive_id": {"type": "string"},
                    "target_parent_id": {"type": "string"}
                },
                "required": ["source_drive_id", "item_id", "target_drive_id", "target_parent_id"]
            }
        },
        {
            "name": "poll_copy_status",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "monitor_url": {"type": "string"}
                },
                "required": ["monitor_url"]
            }
        }
    ]

@app.post("/mcp")
async def mcp_jsonrpc(request: Request):
    try:
        body = await request.json()
    except Exception as e:
        return Response(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Parse error: {str(e)}"}}), media_type="application/json", status_code=400)
    
    jsonrpc = body.get("jsonrpc")
    req_id = body.get("id")
    method = body.get("method")
    params = body.get("params") or {}

    # Basic JSON-RPC validation
    if jsonrpc != "2.0":
        return Response(json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32600, "message": "Invalid Request: jsonrpc must be '2.0'"}}), media_type="application/json", status_code=400)

    if method == "tools/list":
        result = {"tools": get_tools_list()}
        return Response(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}), media_type="application/json")

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}

        try:
            if name == "move_large_file":
                output = move_large_file(args.get("drive_id"), args.get("item_id"), args.get("new_parent_id"))
            elif name == "copy_large_file":
                output = copy_large_file(args.get("source_drive_id"), args.get("item_id"), args.get("target_drive_id"), args.get("target_parent_id"))
            elif name == "poll_copy_status":
                output = poll_copy_status(args.get("monitor_url"))
            else:
                return Response(json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown tool: {name}"}}), media_type="application/json", status_code=404)

            return Response(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {"output": output}}), media_type="application/json")
        except Exception as e:
            return Response(json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(e)}}), media_type="application/json", status_code=500)

    # Unsupported method
    return Response(json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}), media_type="application/json", status_code=404)

if __name__ == "__main__":
    # Get port from environment variable (Azure Container Apps sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Wrap the app with middleware at the outermost level
    wrapped_app = APIKeyMiddleware(app)

    # Run the wrapped FastAPI app
    uvicorn.run(wrapped_app, host="0.0.0.0", port=port)
