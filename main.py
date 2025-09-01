from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from function_app import _handle, ALLOWED_TOOLS
import config

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate configuration on startup"""
    try:
        config.validate_config()
        print("✅ Configuration validated successfully")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print(config.CONFIG_HELP)
        raise e
    yield

app = FastAPI(
    title="OneDrive Organizer MCP Server",
    description="A FastAPI-based MCP server for organizing OneDrive content using Microsoft Graph API",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "OneDrive Organizer MCP Server",
        "version": "1.0.0",
        "available_tools": ALLOWED_TOOLS,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

@app.get("/tools")
async def list_tools():
    """List all available tools"""
    return {
        "tools": ALLOWED_TOOLS,
        "count": len(ALLOWED_TOOLS)
    }

@app.post("/invoke/{tool}")
async def invoke_tool(tool: str, request: Request):
    """Invoke a specific tool with the provided data"""
    if tool not in ALLOWED_TOOLS:
        raise HTTPException(
            status_code=400, 
            detail=f"Tool '{tool}' is not supported. Available tools: {ALLOWED_TOOLS}"
        )
    
    try:
        data = await request.json()
        result = _handle(tool, data)
        return result
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Tool execution failed: {str(e)}"}
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": f"Internal server error: {str(exc)}"}
    )
