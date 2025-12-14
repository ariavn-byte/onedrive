# Copilot Studio Integration Guide

This guide explains how to connect your OneDrive MCP Server to Microsoft Copilot Studio to enable advanced file operations (including moving large files > 5MB) alongside the native Microsoft 365 tools.

## 1. Deploy the Server

Ensure your code is deployed to a public cloud provider like Render.

### Render Configuration
1. **Build Command**: `pip install -r requirements.txt`
2. **Start Command**: `python mcp_server.py`
   * Note: We are now running `mcp_server.py` instead of `main.py` or `uvicorn main:app`.
3. **Environment Variables**:
   Add the following variables in your Render dashboard:
   - `CLIENT_ID`: Your Azure App Client ID.
   - `CLIENT_SECRET`: Your Azure App Client Secret.
   - `TENANT_ID`: Your Azure Tenant ID.
   - `MCP_API_KEY`: **Create this variable yourself.** This is NOT your Render account key. It is a password you invent (e.g., `my-super-secret-password-123`) to protect your server. **Save this value, you will need it for Copilot Studio.**

## 2. Connect to Copilot Studio

1. Open your Agent in **Microsoft Copilot Studio**.
2. Navigate to **Tools** > **Add a tool**.
3. Select **Model Context Protocol** (Preview).

### Configure the Connection
* **Server name**: `OneDrive Advanced` (or similar).
* **Server description**: `Advanced OneDrive operations including moving large files and bulk management.`
* **Server URL**: Your Render URL (e.g., `https://your-app-name.onrender.com/mcp`).
  * *Note: The standard endpoint for the MCP SDK is often `/mcp`.*
* **Authentication**: Select **API Key**.
  * **Key type**: `Header`
  * **Header name**: `X-API-Key`
  * **Value**: Paste the `MCP_API_KEY` value you created in the Render Environment Variables step.

Click **Create** or **Add**. Copilot Studio will connect to your server and list the available tools (e.g., `move_large_file`, `bulk_move`).

## 3. Add Native Tools (Hybrid Approach)

To get the best of both worlds (easy auth for basic tasks + power for advanced tasks):

1. In Copilot Studio, go to **Tools** > **Add a tool**.
2. Select **Microsoft SharePoint and OneDrive** (or "SharePoint and OneDrive MCP Server" from the list of Microsoft tools).
3. Add this tool to your agent.

## 4. How it Works (Generative Orchestration)

Your agent now has two sets of tools:
1. **Native Tools**: `moveSmallFile` (limited to 5MB), `createFolder`, etc.
2. **Custom Tools**: `move_large_file` (Unlimited size), `bulk_move`, etc.

When a user asks: *"Move the file 'Budget.mp4' to the Archive folder"*
* If the file is small, the agent might use the native tool.
* If the file is large, or if the user explicitly says *"Use the advanced tool"*, or if the native tool fails, the **Generative Orchestrator** analyzes the tool descriptions.
* It sees your custom tool `move_large_file` with the description: *"Move a file of ANY size (including files > 5MB)..."*.
* It will intelligently choose your custom tool to perform the action.

## Troubleshooting

* **404 on Connection**: Ensure your Server URL is correct. It should end with `/mcp` (e.g., `https://...onrender.com/mcp`).
* **Unauthorized**: Double-check that the `MCP_API_KEY` in Render matches the one you entered in Copilot Studio.
* **Logs**: Check your Render logs to see if Copilot Studio is hitting your endpoints.
