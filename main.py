from fastapi import FastAPI, Request
from function_app import _handle, ALLOWED_TOOLS

app = FastAPI()

@app.post("/invoke/{tool}")
async def invoke_tool(tool: str, request: Request):
    if tool not in ALLOWED_TOOLS:
        return {"success": False, "error": f"Tool '{tool}' is not supported."}
    data = await request.json()
    return _handle(tool, data)
