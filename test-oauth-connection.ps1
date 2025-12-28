# Test OAuth connection to MCP Server
param(
    [string]$ClientSecret
)

$TenantId = "77309d40-7f7f-4d68-8fab-1160e06f0c2f"
$ClientId = "f826aacf-5a60-43c3-85ed-c52381263ee0"
$AppUrl = "https://aca-onedrive-mcp.blacksand-ad9433b0.eastus.azurecontainerapps.io"

Write-Host "==> Testing MCP Server OAuth Connection" -ForegroundColor Cyan

# Test 1: Health endpoint (no auth required)
Write-Host "`n[1/3] Testing health endpoint..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$AppUrl/health" -Method Get
    Write-Host "✓ Health check passed: $($healthResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "✗ Health check failed: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Get OAuth token
Write-Host "`n[2/3] Getting OAuth token..." -ForegroundColor Yellow
if (-not $ClientSecret) {
    Write-Host "⚠ No client secret provided. Skipping OAuth tests." -ForegroundColor Yellow
    Write-Host "Run with: .\test-oauth-connection.ps1 -ClientSecret 'your-secret'" -ForegroundColor Yellow
    exit 0
}

$tokenBody = @{
    client_id     = $ClientId
    client_secret = $ClientSecret
    scope         = "$ClientId/.default"
    grant_type    = "client_credentials"
}

try {
    $tokenResponse = Invoke-RestMethod -Uri "https://login.microsoftonline.com/$TenantId/oauth2/v2.0/token" -Method Post -Body $tokenBody -ContentType "application/x-www-form-urlencoded"
    $accessToken = $tokenResponse.access_token
    Write-Host "✓ OAuth token acquired successfully" -ForegroundColor Green

    # Decode token to show claims (just header and payload, not validating signature)
    $tokenParts = $accessToken.Split('.')
    $payload = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($tokenParts[1] + "=="))
    $claims = $payload | ConvertFrom-Json
    Write-Host "  Token issued for: $($claims.aud)" -ForegroundColor Gray
    Write-Host "  Token expires: $(Get-Date -Date '1970-01-01').AddSeconds($($claims.exp))" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to get OAuth token: $_" -ForegroundColor Red
    Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Red
    exit 1
}

# Test 3: Call MCP endpoint with OAuth token
Write-Host "`n[3/3] Testing MCP endpoint with OAuth token..." -ForegroundColor Yellow
$mcpEndpoint = "$AppUrl/mcp"
$mcpRequest = @{
    jsonrpc = "2.0"
    id      = 1
    method  = "tools/list"
    params  = @{}
} | ConvertTo-Json

$headers = @{
    "Authorization" = "Bearer $accessToken"
    "Content-Type"  = "application/json"
}

try {
    $mcpResponse = Invoke-RestMethod -Uri $mcpEndpoint -Method Post -Body $mcpRequest -Headers $headers
    Write-Host "✓ MCP endpoint accessible with OAuth!" -ForegroundColor Green

    if ($mcpResponse.result.tools) {
        Write-Host "`n  Available tools:" -ForegroundColor Cyan
        foreach ($tool in $mcpResponse.result.tools) {
            Write-Host "    - $($tool.name): $($tool.description)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "✗ MCP endpoint call failed: $_" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red

    if ($_.Exception.Response.StatusCode.value__ -eq 401) {
        Write-Host "`n⚠ Still getting 401 Unauthorized!" -ForegroundColor Yellow
        Write-Host "  This means OAUTH_AUDIENCE is still incorrect in Container App." -ForegroundColor Yellow
        Write-Host "  Please verify the Azure Portal change was applied correctly." -ForegroundColor Yellow
    }
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "All tests passed! OAuth is working!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nYou can now connect Copilot Studio using:" -ForegroundColor Cyan
Write-Host "  Server URL: $mcpEndpoint"
Write-Host "  Auth: OAuth 2.0 Client Credentials"
Write-Host "  Token URL: https://login.microsoftonline.com/$TenantId/oauth2/v2.0/token"
Write-Host "  Client ID: $ClientId"
Write-Host "  Scope: $ClientId/.default"
