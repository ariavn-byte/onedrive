# Copilot Studio Configuration - Ready to Connect! ✅

## What Was Fixed

✅ **OAuth Audience Updated**: Changed from Microsoft Graph ID to your app's Client ID
✅ **Container App Redeployed**: New revision `aca-onedrive-mcp--0000009` is running
✅ **Dependencies Added**: PyJWT and cryptography added to requirements.txt
✅ **Health Check Passed**: Server is responding correctly

---

## Copilot Studio Setup Instructions

### Step 1: Open Your Agent in Copilot Studio

1. Go to [Copilot Studio](https://copilotstudio.microsoft.com/)
2. Open your agent
3. Navigate to **Tools** in the left menu
4. Click **Add a tool**

### Step 2: Add MCP Server

1. Select **Model Context Protocol (Preview)**
2. Fill in the following details:

**Basic Information:**
- **Server name**: `OneDrive Advanced MCP`
- **Server description**: `Advanced OneDrive operations including large file management (>5MB), bulk operations, and enhanced search capabilities`
- **Server URL**: `https://aca-onedrive-mcp.blacksand-ad9433b0.eastus.azurecontainerapps.io/mcp`

### Step 3: Configure OAuth 2.0 Authentication

Select **OAuth 2.0** as authentication method and enter:

**OAuth Configuration (Client Credentials Flow - Recommended):**
- **Grant Type**: `Client Credentials`
- **Token URL**: `https://login.microsoftonline.com/77309d40-7f7f-4d68-8fab-1160e06f0c2f/oauth2/v2.0/token`
- **Refresh URL**: `https://login.microsoftonline.com/77309d40-7f7f-4d68-8fab-1160e06f0c2f/oauth2/v2.0/token` (same as Token URL)
- **Client ID**: `f826aacf-5a60-43c3-85ed-c52381263ee0`
- **Client Secret**: [Get from Azure Portal - see below]
- **Scope**: `f826aacf-5a60-43c3-85ed-c52381263ee0/.default` (Use GUID, not api:// URI)

**OAuth Configuration (Authorization Code Flow - If Copilot Studio requires it):**
- **Grant Type**: `Authorization Code`
- **Authorization URL**: `https://login.microsoftonline.com/77309d40-7f7f-4d68-8fab-1160e06f0c2f/oauth2/v2.0/authorize`
- **Token URL**: `https://login.microsoftonline.com/77309d40-7f7f-4d68-8fab-1160e06f0c2f/oauth2/v2.0/token`
- **Refresh URL**: `https://login.microsoftonline.com/77309d40-7f7f-4d68-8fab-1160e06f0c2f/oauth2/v2.0/token` (same as Token URL)
- **Client ID**: `f826aacf-5a60-43c3-85ed-c52381263ee0`
- **Client Secret**: [Get from Azure Portal - see below]
- **Scope**: `api://onedrive-mcp-server/.default` OR `f826aacf-5a60-43c3-85ed-c52381263ee0/.default`
- **Redirect URI**: Copilot Studio will auto-generate (already configured in your Entra ID app)

**How to Get Client Secret:**
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Entra ID** → **App Registrations** → **OneDrive MCP Server**
3. Click **Certificates & secrets**
4. Under **Client secrets**, either:
   - Copy an existing secret value (only visible when created)
   - OR click **New client secret**, add description, set expiry, and copy the **Value**

### Step 4: Test Connection

1. Click **Create** or **Add tool**
2. Copilot Studio will attempt to connect to your MCP server
3. If successful, you should see the available tools listed

---

## Available MCP Tools

Once connected, your agent will have access to these tools:

1. **move_large_file**
   - Move files of ANY size (including >5MB) to a new parent folder
   - Parameters: `drive_id`, `item_id`, `new_parent_id`

2. **copy_large_file**
   - Initiate async copy of large files
   - Returns monitor URL for status polling
   - Parameters: `source_drive_id`, `item_id`, `target_drive_id`, `target_parent_id`

3. **poll_copy_status**
   - Check completion status of async copy operations
   - Parameters: `monitor_url`

---

## Troubleshooting

### ❌ Still Getting 401 Unauthorized?

**Check Client Secret:**
- Ensure you copied the correct client secret value
- Client secrets expire - check if yours is still valid in Azure Portal

**Verify Scope:**
- Must be exactly: `api://onedrive-mcp-server/.default`
- Include the `/.default` suffix

**Check Token URL:**
- Must use your tenant ID: `77309d40-7f7f-4d68-8fab-1160e06f0c2f`
- Must use `/v2.0/` endpoint

### 🔧 Test OAuth Manually

Run this PowerShell script to test if OAuth is working:

```powershell
.\test-oauth-connection.ps1 -ClientSecret "YOUR_SECRET_HERE"
```

This will:
- ✓ Test health endpoint
- ✓ Get OAuth token from Entra ID
- ✓ Call MCP endpoint with token
- ✓ List available tools

### 📋 View Container App Logs

If issues persist, check the logs:

```bash
az containerapp logs show --name aca-onedrive-mcp --resource-group rg-onedrive-mcp --tail 100
```

---

## Alternative: Use API Key Authentication (Fallback)

If OAuth continues to have issues, you can use API Key authentication:

1. **Get the API Key:**
```bash
az containerapp secret show --name aca-onedrive-mcp --resource-group rg-onedrive-mcp --secret-name mcp-api-key --query value -o tsv
```

2. **In Copilot Studio:**
   - **Authentication**: `API Key`
   - **Key type**: `Header`
   - **Header name**: `X-API-Key`
   - **Value**: [Paste the API key from step 1]

---

## Next Steps

After successfully connecting:

1. **Test the tools** in Copilot Studio's test chat:
   - "List my OneDrive files"
   - "Move file [file-id] to folder [folder-id]"

2. **Combine with native Microsoft 365 tools** for best results:
   - Use native tools for file search and basic operations (<5MB)
   - Use custom MCP tools for large file operations and bulk tasks

3. **Monitor usage**:
   - Check Container App metrics in Azure Portal
   - Review Copilot Studio analytics

---

## Summary

Your OneDrive MCP Server is now properly configured with OAuth 2.0 authentication and ready to connect to Copilot Studio!

**Server Details:**
- ✅ URL: `https://aca-onedrive-mcp.blacksand-ad9433b0.eastus.azurecontainerapps.io/mcp`
- ✅ Health: Passing
- ✅ OAuth: Configured with Client ID `f826aacf-5a60-43c3-85ed-c52381263ee0`
- ✅ Revision: `aca-onedrive-mcp--0000009` (latest)
- ✅ Status: Running

**Need Help?** Check [COPILOT_OAUTH_FIX.md](COPILOT_OAUTH_FIX.md) for detailed troubleshooting.
