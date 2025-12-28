# Fix OAuth 2.0 Connection Between Copilot Studio and Azure Container Apps

## Problem
Getting 401 Unauthorized when connecting Copilot Studio to the OneDrive MCP Server on Azure Container Apps.

## Root Cause
The `OAUTH_AUDIENCE` environment variable was set to the generic Microsoft Graph audience (`00000003-0000-0000-c000-000000000000`) instead of your app's Client ID.

## Your App Details
- **Azure Container App URL**: `https://aca-onedrive-mcp.blacksand-ad9433b0.eastus.azurecontainerapps.io`
- **MCP Endpoint**: `https://aca-onedrive-mcp.blacksand-ad9433b0.eastus.azurecontainerapps.io/mcp`
- **Client ID**: `f826aacf-5a60-43c3-85ed-c52381263ee0`
- **Tenant ID**: `77309d40-7f7f-4d68-8fab-1160e06f0c2f`

---

## Solution Options

### Option 1: Quick Fix via Azure Portal (Recommended)

1. **Go to Azure Portal**: https://portal.azure.com
2. **Navigate to your Container App**:
   - Resource Groups → `rg-onedrive-mcp` → `aca-onedrive-mcp`
3. **Update Environment Variables**:
   - Click "Containers" in left menu
   - Click "Edit and deploy"
   - Under "Container image", find the environment variables section
   - Find `OAUTH_AUDIENCE` and change value to: `f826aacf-5a60-43c3-85ed-c52381263ee0`
   - Click "Create" to deploy new revision
4. **Wait 2-3 minutes** for deployment

### Option 2: Rebuild and Redeploy with Correct Config

Run the provided PowerShell script:
```powershell
.\fix-oauth-deployment.ps1
```

This will:
- Build new Docker image with updated requirements.txt (includes PyJWT)
- Update all OAuth environment variables correctly
- Redeploy the container app

---

## Entra ID App Registration Setup

### Required Configuration

1. **Go to Azure Portal** → **Entra ID** → **App Registrations** → Your App (`f826aacf-5a60-43c3-85ed-c52381263ee0`)

2. **Authentication Settings**:
   - Click "Authentication"
   - Under "Platform configurations", add "Web" if not present
   - Add Redirect URI: `https://copilotstudio.microsoft.com/environments/<your-env-id>/bots/<your-bot-id>/auth/callback`
   - Enable "Access tokens" and "ID tokens" under Implicit grant
   - Click "Save"

3. **API Permissions** (Required for OneDrive access):
   - Click "API permissions"
   - Ensure these Microsoft Graph permissions are present:
     - `Files.ReadWrite.All` (Application permission)
     - `Sites.ReadWrite.All` (Application permission)
     - `User.Read.All` (Application permission)
   - Click "Grant admin consent" if not already granted

4. **Expose an API** (For MCP Server Access):
   - Click "Expose an API"
   - If no Application ID URI, click "Add" and use: `api://f826aacf-5a60-43c3-85ed-c52381263ee0`
   - Add a scope:
     - Scope name: `access_as_user`
     - Who can consent: Admins and users
     - Admin consent display name: `Access MCP Server`
     - Admin consent description: `Allow access to OneDrive MCP Server`
     - User consent display name: `Access MCP Server`
     - User consent description: `Allow access to OneDrive MCP Server`
     - State: Enabled
   - Click "Add scope"

5. **App Roles** (Optional - for application-level access):
   - Click "App roles"
   - Create role if not exists:
     - Display name: `MCP.Access`
     - Allowed member types: `Applications` and `Users`
     - Value: `MCP.Access`
     - Description: `Access MCP server`
   - Click "Apply"

---

## Copilot Studio Configuration

### Connection Settings

1. **Open Copilot Studio** → Your Agent → **Tools**

2. **Add MCP Tool**:
   - Click "Add a tool" → "Model Context Protocol"
   - **Server name**: `OneDrive Advanced MCP`
   - **Server URL**: `https://aca-onedrive-mcp.blacksand-ad9433b0.eastus.azurecontainerapps.io/mcp`
   - **Authentication**: `OAuth 2.0`

3. **OAuth 2.0 Configuration**:
   - **Grant type**: `Client Credentials`
   - **Token URL**: `https://login.microsoftonline.com/77309d40-7f7f-4d68-8fab-1160e06f0c2f/oauth2/v2.0/token`
   - **Client ID**: `f826aacf-5a60-43c3-85ed-c52381263ee0`
   - **Client Secret**: (Get from Entra ID → App Registration → Certificates & secrets)
   - **Scope**: `api://f826aacf-5a60-43c3-85ed-c52381263ee0/.default`

4. **Click "Create"**

### Alternative: Use API Key (Simpler)

If OAuth continues to have issues, you can use API Key authentication:

1. **In Copilot Studio**:
   - **Authentication**: `API Key`
   - **Key type**: `Header`
   - **Header name**: `X-API-Key`
   - **Value**: (Get MCP_API_KEY secret from Azure Container App secrets)

2. **Get API Key from Azure**:
```bash
az containerapp secret show --name aca-onedrive-mcp --resource-group rg-onedrive-mcp --secret-name mcp-api-key --query value -o tsv
```

---

## Testing the Connection

### Test Health Endpoint
```bash
curl https://aca-onedrive-mcp.blacksand-ad9433b0.eastus.azurecontainerapps.io/health
```
Expected: `{"status":"healthy"}`

### Test MCP Endpoint (After OAuth Fix)

With OAuth token:
```bash
# Get token first
TOKEN=$(curl -X POST "https://login.microsoftonline.com/77309d40-7f7f-4d68-8fab-1160e06f0c2f/oauth2/v2.0/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=f826aacf-5a60-43c3-85ed-c52381263ee0" \
  -d "client_secret=YOUR_SECRET" \
  -d "scope=api://f826aacf-5a60-43c3-85ed-c52381263ee0/.default" \
  -d "grant_type=client_credentials" | jq -r .access_token)

# Test MCP endpoint
curl -X POST "https://aca-onedrive-mcp.blacksand-ad9433b0.eastus.azurecontainerapps.io/mcp" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

Expected: JSON response with tools list

---

## Troubleshooting

### Still Getting 401?

1. **Check logs**:
```bash
az containerapp logs show --name aca-onedrive-mcp --resource-group rg-onedrive-mcp --tail 50
```

2. **Verify environment variables**:
```bash
az containerapp show --name aca-onedrive-mcp --resource-group rg-onedrive-mcp --query "properties.template.containers[0].env"
```

3. **Verify OAUTH_AUDIENCE matches Client ID**:
Should be: `f826aacf-5a60-43c3-85ed-c52381263ee0`

### Token Validation Failing?

- Ensure `OAUTH_TENANT_ID` = `77309d40-7f7f-4d68-8fab-1160e06f0c2f`
- Ensure `OAUTH_AUDIENCE` = `f826aacf-5a60-43c3-85ed-c52381263ee0`
- Check that PyJWT and cryptography are installed (rebuild with updated requirements.txt)

---

## Summary of Changes Made

1. ✅ Added `PyJWT>=2.8.0` and `cryptography>=41.0.0` to requirements.txt
2. ✅ Identified correct Client ID for OAuth audience
3. ✅ Created deployment scripts to fix OAuth configuration
4. ✅ Documented complete Entra ID setup
5. ✅ Provided both OAuth and API Key authentication options

**Next Step**: Choose Option 1 (Azure Portal) or Option 2 (PowerShell script) to apply the fix.
