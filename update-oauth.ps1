# Update OAuth configuration for Azure Container App
$ResourceGroup = "rg-onedrive-mcp"
$AppName = "aca-onedrive-mcp"
$ClientId = "f826aacf-5a60-43c3-85ed-c52381263ee0"

Write-Host "Updating OAuth configuration for $AppName..."

# Update environment variable using az resource update
az resource update `
    --resource-group $ResourceGroup `
    --name $AppName `
    --resource-type "Microsoft.App/containerApps" `
    --set "properties.template.containers[0].env[?name=='OAUTH_AUDIENCE'].value='$ClientId'"

Write-Host "OAuth audience updated to: $ClientId"
Write-Host "Restarting container app to apply changes..."

# Get current revision name
$revisions = az resource show `
    --resource-group $ResourceGroup `
    --name $AppName `
    --resource-type "Microsoft.App/containerApps" `
    --query "properties.latestRevisionName" -o tsv

Write-Host "Current revision: $revisions"
Write-Host "Done! Please wait 1-2 minutes for the app to restart."
