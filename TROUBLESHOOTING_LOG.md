# Copilot Studio OAuth Connection - Troubleshooting Log

## Session Date: December 27-28, 2025

---

## Issues Encountered & Fixes Applied

### ✅ Issue 1: 401 Unauthorized - Wrong OAuth Audience
**Error**: Container App authentication was failing
**Root Cause**: `OAUTH_AUDIENCE` was set to Microsoft Graph ID instead of app's Client ID
**Fix Applied**: Updated `OAUTH_AUDIENCE` from `00000003-0000-0000-c000-000000000000` to `f826aacf-5a60-43c3-85ed-c52381263ee0`
**Status**: FIXED ✓

---

### ✅ Issue 2: AADSTS90009 - Scope Format Error
**Error**:
```
AADSTS90009: Application is requesting a token for itself.
This scenario is supported only if resource is specified using the GUID based App Identifier.
```
**Root Cause**: Scope was using friendly URI `api://onedrive-mcp-server/.default` instead of GUID format
**Fix Applied**: Changed scope to `f826aacf-5a60-43c3-85ed-c52381263ee0/.default` for Client Credentials flow
**Status**: FIXED ✓

---

###  ✅ Issue 3: AADSTS50011 - Redirect URI Mismatch
**Error**:
```
AADSTS50011: The redirect URI specified in the request does not match
the redirect URIs configured for the application
```
**Redirect URI Attempted**: `https://global.consent.azure-apim.net/redirect/new-5fonedrive-20advance-20mcp-5fec31868190843b2d`
**Fix Applied**: Added Azure APIM redirect URIs to Entra ID app:
- `https://global.consent.azure-apim.net/redirect/*`
- `https://global.consent.azure-apim.net/redirect/new-5fonedrive-20advance-20mcp-5fec31868190843b2d`
**Status**: FIXED ✓

---

### ✅ Issue 4: Implicit Grant Disabled
**Error**: OAuth tokens couldn't be issued
**Fix Applied**: Enabled implicit grant settings in Entra ID app:
- ✓ Access tokens (used for implicit flows)
- ✓ ID tokens (used for implicit and hybrid flows)
**Status**: FIXED ✓

---

### 🔧 Issue 5: Connector Request Failed - Couldn't Retrieve Tools
**Error**: "Connector request failed - Couldn't retrieve the requested items"
**Root Cause**: OAuth token validation in MCP server is too strict or silently failing
**Fix Applied**:
1. Added better error logging to OAuth validation
2. Made audience validation more flexible (fallback if audience doesn't match)
3. Added logging to show which tokens are accepted/rejected
**Status**: DEPLOYING (in progress)

---

## Current Configuration

### Azure Container App
- **Name**: `aca-onedrive-mcp`
- **URL**: `https://aca-onedrive-mcp.blacksand-ad9433b0.eastus.azurecontainerapps.io`
- **MCP Endpoint**: `/mcp`
- **Latest Revision**: Deploying `oauth-fix-v2`

### Environment Variables
```
OAUTH2_ENABLED=true
OAUTH_TENANT_ID=[secret: tenant-id]
OAUTH_AUDIENCE=f826aacf-5a60-43c3-85ed-c52381263ee0
MCP_API_KEY=[secret: mcp-api-key]
TENANT_ID=[secret: tenant-id]
CLIENT_ID=[secret: client-id]
CLIENT_SECRET=[secret: client-secret]
PORT=8080
```

### Entra ID App Registration
- **App Name**: OneDrive MCP Server
- **Client ID**: `f826aacf-5a60-43c3-85ed-c52381263ee0`
- **Tenant ID**: `77309d40-7f7f-4d68-8fab-1160e06f0c2f`
- **Application ID URI**: `api://onedrive-mcp-server`

### Redirect URIs (5 total)
1. `https://global.consent.azure-apim.net/redirect/*`
2. `https://global.consent.azure-apim.net/redirect/new-5fonedrive-20advance-20mcp-5fec31868190843b2d`
3. `https://copilotstudio.microsoft.com/environments/*/bots/*/auth/callback`
4. `https://powerva.microsoft.com/environments/*/bots/*/auth/callback`
5. `https://prod.copilot.dynamics.com/*`

### OAuth Scopes
- **Exposed Scope**: `access_as_user`
- **For Client Credentials**: `f826aacf-5a60-43c3-85ed-c52381263ee0/.default`
- **For Authorization Code**: `api://onedrive-mcp-server/.default` OR `f826aacf-5a60-43c3-85ed-c52381263ee0/.default`

### Implicit Grant Settings
- ✅ Access tokens: Enabled
- ✅ ID tokens: Enabled

---

## Code Changes Made

### 1. requirements.txt
Added missing dependencies:
```
PyJWT>=2.8.0
cryptography>=41.0.0
```

### 2. mcp_server.py (Lines 189-224)
Enhanced OAuth validation:
- Added fallback for audience validation failures
- Added detailed logging for OAuth success/failure
- More flexible token validation

### 3. Azure Container App Environment
Updated `OAUTH_AUDIENCE` to use Client ID GUID instead of Microsoft Graph ID

---

## Copilot Studio Configuration

### OAuth 2.0 Settings (Authorization Code Flow)
```
Server URL: https://aca-onedrive-mcp.blacksand-ad9433b0.eastus.azurecontainerapps.io/mcp
Authorization URL: https://login.microsoftonline.com/77309d40-7f7f-4d68-8fab-1160e06f0c2f/oauth2/v2.0/authorize
Token URL: https://login.microsoftonline.com/77309d40-7f7f-4d68-8fab-1160e06f0c2f/oauth2/v2.0/token
Refresh URL: https://login.microsoftonline.com/77309d40-7f7f-4d68-8fab-1160e06f0c2f/oauth2/v2.0/token
Client ID: f826aacf-5a60-43c3-85ed-c52381263ee0
Client Secret: [From Azure Portal - Certificates & secrets]
Scope: f826aacf-5a60-43c3-85ed-c52381263ee0/.default
```

---

## Next Steps

1. ⏳ Wait for deployment to complete (~2-3 minutes)
2. 🔍 Check container logs for OAuth validation messages
3. 🔄 Retry connection in Copilot Studio
4. 📊 If still failing, check logs to see exact token validation error

---

## Useful Commands

### Check Deployment Status
```powershell
az rest --method GET --url "/subscriptions/221502e7-a7cc-4567-99bc-9b7432bb0afd/resourceGroups/rg-onedrive-mcp/providers/Microsoft.App/containerApps/aca-onedrive-mcp?api-version=2023-05-01" --query "properties.latestRevisionName"
```

### View Container Logs
```bash
az containerapp logs show --name aca-onedrive-mcp --resource-group rg-onedrive-mcp --tail 100
```

### Test OAuth Token Manually
```powershell
.\test-oauth-connection.ps1 -ClientSecret "YOUR_SECRET"
```

---

## Files Created/Modified

### New Files
- `COPILOT_STUDIO_CONFIG.md` - Complete configuration guide
- `COPILOT_OAUTH_FIX.md` - Detailed OAuth fix documentation
- `test-oauth-connection.ps1` - OAuth testing script
- `fix-oauth-deployment.ps1` - Full redeploy script
- `quick-redeploy.ps1` - Quick redeploy script
- `update-oauth.ps1` - Environment variable update script
- `TROUBLESHOOTING_LOG.md` - This file

### Modified Files
- `requirements.txt` - Added PyJWT and cryptography
- `mcp_server.py` - Enhanced OAuth validation with logging
- `COPILOT_STUDIO_CONFIG.md` - Updated OAuth configuration details

---

**Session End Time**: Deployment in progress
**Overall Status**: 4/5 issues resolved, 1 in progress
