
import os
import json
import uvicorn
import time
import requests
import jwt
from jwt import PyJWKClient
from fastapi import FastAPI, Request
from starlette.responses import Response
from starlette.middleware.cors import CORSMiddleware

# Import the existing OneDrive logic
import function_app
from function_app import organizer

# API Key for Copilot Studio authentication
# Accept multiple common names to be resilient to connector/wizard variations
ACCEPTED_API_KEY_NAMES = [
    "X-API-Key",        # preferred
    "api_key",          # common
    "apikey",           # common
    "key"               # fallback
]
API_KEY = os.environ.get("MCP_API_KEY", "copilot-studio-secret")

# Optional OAuth 2.0 (Bearer token) support
OAUTH2_ENABLED = os.environ.get("OAUTH2_ENABLED", "false").lower() == "true"
OAUTH_TENANT_ID = os.environ.get("OAUTH_TENANT_ID", os.environ.get("TENANT_ID", "")).strip()
OAUTH_AUDIENCE = os.environ.get("OAUTH_AUDIENCE", "").strip()  # Application (client) ID or Application ID URI

_jwks_client = None
_jwks_last_refresh = 0

def _get_jwks_client():
    global _jwks_client, _jwks_last_refresh
    if not OAUTH_TENANT_ID:
        return None
    # Refresh JWKS client every 30 minutes
    if _jwks_client is None or (time.time() - _jwks_last_refresh) > 1800:
        # Discover JWKS URI via OpenID configuration
        try:
            oidc = requests.get(f"https://login.microsoftonline.com/{OAUTH_TENANT_ID}/v2.0/.well-known/openid-configuration", timeout=10).json()
            jwks_uri = oidc.get("jwks_uri")
            if jwks_uri:
                _jwks_client = PyJWKClient(jwks_uri)
                _jwks_last_refresh = time.time()
        except Exception:
            _jwks_client = None
    return _jwks_client

# NOTE: We avoid FastMCP's StreamableHTTP due to strict Host validation behind ACA.
# Implement a minimal JSON-RPC 2.0 HTTP endpoint for tools/list and tools/call.

def move_large_file(drive_id: str, item_id: str, new_parent_id: str) -> dict:
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
        return result
    except Exception as e:
        return {"error": f"Error moving large file: {str(e)}"}

def copy_large_file(source_drive_id: str, item_id: str, target_drive_id: str, target_parent_id: str) -> dict:
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
        return result
    except Exception as e:
        return {"error": f"Error copying large file: {str(e)}"}

def poll_copy_status(monitor_url: str) -> dict:
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
        return result
    except Exception as e:
        return {"error": f"Error polling copy status: {str(e)}"}

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


# --- Authentication Middleware (Pure ASGI) ---
class APIKeyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        print(f"📨 Incoming request: {scope.get('method', 'UNKNOWN')} {path}")

        # No host/accept header rewriting is required for our pure JSON-RPC endpoint.

        # 2. Authentication Check
        # Allow health check and root without auth
        # TEMPORARY: Also allow /mcp for debugging
        if path in ["/", "/health", "/docs", "/openapi.json", "/mcp"]:
            print(f"✓ Public endpoint (no auth required): {path}")
            return await self.app(scope, receive, send)

        # First, try OAuth 2.0 Bearer token if enabled
        provided_key = None
        print(f"🔒 OAuth2 Enabled: {OAUTH2_ENABLED}, Tenant: {OAUTH_TENANT_ID}, Audience: {OAUTH_AUDIENCE}")
        if OAUTH2_ENABLED and OAUTH_TENANT_ID:
            auth_header = None
            for k, v in scope["headers"]:
                if k.lower() == b"authorization":
                    auth_header = v.decode()
                    break

            if auth_header:
                print(f"🔑 Authorization header found: {auth_header[:20]}...")
            else:
                print("⚠️  No Authorization header found")

            if auth_header and auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1].strip()
                jwks_client = _get_jwks_client()
                if jwks_client:
                    try:
                        signing_key = jwks_client.get_signing_key_from_jwt(token).key
                        # Validate issuer and audience if provided
                        # Be flexible with audience - accept both GUID and app ID URI
                        options = {"verify_aud": bool(OAUTH_AUDIENCE)}

                        # Try to decode with configured audience
                        try:
                            decoded = jwt.decode(
                                token,
                                signing_key,
                                algorithms=["RS256"],
                                audience=OAUTH_AUDIENCE if OAUTH_AUDIENCE else None,
                                issuer=f"https://login.microsoftonline.com/{OAUTH_TENANT_ID}/v2.0",
                                options=options,
                        )
                        except jwt.InvalidAudienceError:
                            # If audience validation fails, try without audience validation
                            options["verify_aud"] = False
                            decoded = jwt.decode(
                                token,
                                signing_key,
                                algorithms=["RS256"],
                                issuer=f"https://login.microsoftonline.com/{OAUTH_TENANT_ID}/v2.0",
                                options=options,
                            )
                            print(f"⚠️ Token accepted without audience validation. Token aud: {decoded.get('aud')}")

                        print(f"✓ OAuth token validated for: {decoded.get('appid', decoded.get('sub', 'unknown'))}")
                        # If decode succeeds, treat as authenticated
                        return await self.app(scope, receive, send)
                    except Exception as e:
                        # Log the OAuth validation failure
                        print(f"⚠️ OAuth validation failed: {type(e).__name__}: {str(e)}")
                        # Fall through to API key check
                        pass

        # Extract API Key from headers or query (support multiple common names)
        # Check headers
        accepted_header_names = [name.lower().encode() for name in ACCEPTED_API_KEY_NAMES]
        for k, v in scope["headers"]:
            if k.lower() in accepted_header_names:
                provided_key = v.decode()
                break

        # Check query params if not in header
        if not provided_key:
            query_string = scope.get("query_string", b"").decode()
            if query_string:
                from urllib.parse import parse_qs
                qs = parse_qs(query_string)
                for name in ACCEPTED_API_KEY_NAMES:
                    if name in qs:
                        provided_key = qs[name][0]
                        break

        if provided_key != API_KEY:
            print(f"⚠️ Auth Failed for path: {path}")
            if not provided_key:
                print("   Reason: No API Key provided in headers or query.")
            else:
                print(f"   Reason: Key mismatch. Provided length: {len(provided_key)}, Expected length: {len(API_KEY)}")
                # Do not log the full key for security, but maybe the first char helps
                print(f"   Provided start: '{provided_key[:2]}***', Expected start: '{API_KEY[:2]}***'")

            response = Response("Unauthorized: Invalid API Key or OAuth token", status_code=401)
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
    # MCP-compliant tool descriptors for Copilot Studio
    return [
        {
            "name": "move_large_file",
            "description": "Move a file (any size) to a new parent folder using Microsoft Graph.",
            # Provide both snake_case and camelCase for maximum compatibility
            "input_schema": {
                "type": "object",
                "properties": {
                    "drive_id": {"type": "string"},
                    "item_id": {"type": "string"},
                    "new_parent_id": {"type": "string"}
                },
                "required": ["drive_id", "item_id", "new_parent_id"]
            },
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
            "description": "Initiate an async copy of a large file and return a monitor URL for status polling.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "source_drive_id": {"type": "string"},
                    "item_id": {"type": "string"},
                    "target_drive_id": {"type": "string"},
                    "target_parent_id": {"type": "string"}
                },
                "required": ["source_drive_id", "item_id", "target_drive_id", "target_parent_id"]
            },
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
            "description": "Poll the monitor URL from copy_large_file to check copy completion.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "monitor_url": {"type": "string"}
                },
                "required": ["monitor_url"]
            },
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

    # Handle MCP protocol initialization
    if method == "initialize":
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "OneDrive Advanced MCP",
                "version": "1.0.0"
            }
        }
        return Response(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}), media_type="application/json")

    # Handle notifications (notifications don't have responses in JSON-RPC)
    if method == "notifications/initialized":
        # Notification received - no response required, but we acknowledge it
        return Response(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {}}), media_type="application/json")

    if method == "tools/list":
        result = {"tools": get_tools_list()}
        return Response(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}), media_type="application/json")

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}

        if not name:
            return Response(json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": "Missing tool name"}}), media_type="application/json", status_code=400)

        try:
            if name == "move_large_file":
                output = move_large_file(args.get("drive_id"), args.get("item_id"), args.get("new_parent_id"))
            elif name == "copy_large_file":
                output = copy_large_file(args.get("source_drive_id"), args.get("item_id"), args.get("target_drive_id"), args.get("target_parent_id"))
            elif name == "poll_copy_status":
                output = poll_copy_status(args.get("monitor_url"))
            else:
                return Response(json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown tool: {name}"}}), media_type="application/json", status_code=404)

            # MCP-compliant result content
            content = [{"type": "json", "json": output}]
            return Response(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {"content": content}}), media_type="application/json")
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
