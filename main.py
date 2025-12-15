
# Redirect 'main.app' to the new MCP server app
# This allows the existing Render Start Command ("uvicorn main:app") to work
# without manual configuration changes.

from mcp_server import app

# For local testing if running python main.py
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
