#requires -Version 7.0
# Fix OAuth configuration for OneDrive MCP Server

$ResourceGroup = "rg-onedrive-mcp"
$AppName = "aca-onedrive-mcp"
$Location = "eastus"
$ClientId = "f826aacf-5a60-43c3-85ed-c52381263ee0"
$TenantId = "77309d40-7f7f-4d68-8fab-1160e06f0c2f"

Write-Host "==> Fixing OAuth Configuration for $AppName" -ForegroundColor Cyan

# Get current secrets
Write-Host "==> Retrieving current secrets..."
$secrets = az containerapp secret list --name $AppName --resource-group $ResourceGroup -o json | ConvertFrom-Json

# Extract secret names
$mcpApiKey = ($secrets | Where-Object { $_.name -eq "mcp-api-key" }).value
$clientSecret = ($secrets | Where-Object { $_.name -eq "client-secret" }).value

Write-Host "==> Building and pushing updated image..."
# Get ACR details
$acrName = "acronedrivemcp"
$acrLoginServer = (az acr show --resource-group $ResourceGroup --name $acrName --query "loginServer" -o tsv)
$acrUser = (az acr credential show --name $acrName --resource-group $ResourceGroup --query "username" -o tsv)
$acrPass = (az acr credential show --name $acrName --resource-group $ResourceGroup --query "passwords[0].value" -o tsv)

# Build image with updated requirements.txt
$ImageName = "$acrLoginServer/onedrive-mcp:v-oauth-fix"
Write-Host "Building image: $ImageName"

if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker build -t $ImageName .
    docker login $acrLoginServer -u $acrUser -p $acrPass
    docker push $ImageName
} else {
    az acr build --registry $acrName --image onedrive-mcp:v-oauth-fix .
}

Write-Host "==> Updating Container App with corrected OAuth settings..." -ForegroundColor Yellow

# Update the container app with new image and correct env vars
az containerapp update `
    --name $AppName `
    --resource-group $ResourceGroup `
    --image $ImageName `
    --replace-env-vars `
        "PORT=8080" `
        "OAUTH2_ENABLED=true" `
        "OAUTH_TENANT_ID=$TenantId" `
        "OAUTH_AUDIENCE=$ClientId" `
        "MCP_API_KEY=secretref:mcp-api-key" `
        "TENANT_ID=secretref:tenant-id" `
        "CLIENT_ID=secretref:client-id" `
        "CLIENT_SECRET=secretref:client-secret"

Write-Host "==> Getting app URL..." -ForegroundColor Cyan
$Fqdn = (az containerapp show --name $AppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv)

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "OAuth Configuration Fixed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "App URL: https://$Fqdn"
Write-Host "MCP Endpoint: https://$Fqdn/mcp"
Write-Host "Health Check: https://$Fqdn/health"
Write-Host "`nCopilot Studio Configuration:" -ForegroundColor Yellow
Write-Host "  - Server URL: https://$Fqdn/mcp"
Write-Host "  - Authentication: OAuth 2.0"
Write-Host "  - Token URL: https://login.microsoftonline.com/$TenantId/oauth2/v2.0/token"
Write-Host "  - Client ID: $ClientId"
Write-Host "  - Scope: $ClientId/.default"
Write-Host "`nWait 2-3 minutes for deployment to complete, then test with:"
Write-Host "curl https://$Fqdn/health" -ForegroundColor Cyan
