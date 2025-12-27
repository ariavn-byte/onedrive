#requires -Version 7.0
param(
    [string]$SubscriptionId,
    [string]$ResourceGroup = "rg-onedrive-mcp",
    [string]$Location = "eastus",
    [string]$EnvName = "env-onedrive-mcp",
    [string]$AcrName = "acronedrivemcp",
    [string]$AppName = "aca-onedrive-mcp",
    [string]$ImageTag = "v1",
    [string]$ApiKey,
    [string]$TenantId,
    [string]$ClientId,
    [string]$ClientSecret
)

# Summary: Deploy the MCP server to Azure Container Apps with external ingress, secrets, and scale-to-zero.

Write-Host "==> Logging in to Azure"
$accountStatus = az account show 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Azure CLI not signed in. Please run 'az login' first."
    exit 1
}
if ($SubscriptionId) { az account set --subscription $SubscriptionId }

Write-Host "==> Creating resource group: $ResourceGroup ($Location)"
az group create --name $ResourceGroup --location $Location | Out-Null

Write-Host "==> Ensuring Azure Container Apps extension is installed"
az extension add --name containerapp --upgrade --allow-preview true 2>&1 | Out-Null

Write-Host "==> Creating Azure Container Registry: $AcrName"
az acr create --resource-group $ResourceGroup --name $AcrName --sku Basic --admin-enabled true | Out-Null
$acrLoginServer = (az acr show --resource-group $ResourceGroup --name $AcrName --query "loginServer" -o tsv)
$acrUser = (az acr credential show --name $AcrName --resource-group $ResourceGroup --query "username" -o tsv)
$acrPass = (az acr credential show --name $AcrName --resource-group $ResourceGroup --query "passwords[0].value" -o tsv)

Write-Host "==> Building and pushing image to ACR"
$ImageName = "$acrLoginServer/onedrive-mcp:$ImageTag"
# Use local Docker if available; fallback to ACR build
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker build -t $ImageName .
    docker login $acrLoginServer -u $acrUser -p $acrPass
    docker push $ImageName
}
else {
    az acr build --registry $AcrName --image onedrive-mcp:$ImageTag .
}

Write-Host "==> Creating Container Apps environment: $EnvName"
az containerapp env create --name $EnvName --resource-group $ResourceGroup --location $Location | Out-Null

Write-Host "==> Creating Container App: $AppName"
# Create app with registry and ingress
az containerapp create `
    --name $AppName `
    --resource-group $ResourceGroup `
    --environment $EnvName `
    --image $ImageName `
    --ingress external `
    --target-port 8080 `
    --min-replicas 0 `
    --max-replicas 3 `
    --registry-server $acrLoginServer `
    --registry-username $acrUser `
    --registry-password $acrPass `
    --env-vars PORT=8080 | Out-Null

Write-Host "==> Setting secrets and env vars"
az containerapp secret set --name $AppName --resource-group $ResourceGroup --secrets MCP_API_KEY=$ApiKey TENANT_ID=$TenantId CLIENT_ID=$ClientId CLIENT_SECRET=$ClientSecret | Out-Null
az containerapp update --name $AppName --resource-group $ResourceGroup --set-env-vars MCP_API_KEY=secretref:MCP_API_KEY TENANT_ID=secretref:TENANT_ID CLIENT_ID=secretref:CLIENT_ID CLIENT_SECRET=secretref:CLIENT_SECRET | Out-Null

Write-Host "==> Fetching FQDN"
$Fqdn = (az containerapp show --name $AppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv)
Write-Host "Deployed. Public URL:" $Fqdn
Write-Host "Test health: curl https://$Fqdn/health"
Write-Host "Note: Use header 'X-API-Key' with your MCP_API_KEY when calling /mcp"
