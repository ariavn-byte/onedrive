# Quick redeploy with OAuth fix
$ResourceGroup = "rg-onedrive-mcp"
$AppName = "aca-onedrive-mcp"
$acrName = "acronedrivemcp"

Write-Host "==> Quick Redeploy with OAuth Logging Fix" -ForegroundColor Cyan

# Get ACR credentials
$acrLoginServer = (az acr show --resource-group $ResourceGroup --name $acrName --query "loginServer" -o tsv)
$acrUser = (az acr credential show --name $acrName --resource-group $ResourceGroup --query "username" -o tsv)
$acrPass = (az acr credential show --name $acrName --resource-group $ResourceGroup --query "passwords[0].value" -o tsv)

# Build and push new image
$ImageName = "$acrLoginServer/onedrive-mcp:oauth-fix-v2"
Write-Host "Building image: $ImageName"

if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker build -t $ImageName .
    docker login $acrLoginServer -u $acrUser -p $acrPass
    docker push $ImageName
} else {
    az acr build --registry $acrName --image onedrive-mcp:oauth-fix-v2 .
}

Write-Host "==> Updating Container App with new image..." -ForegroundColor Yellow
az rest --method PATCH `
    --url "/subscriptions/221502e7-a7cc-4567-99bc-9b7432bb0afd/resourceGroups/$ResourceGroup/providers/Microsoft.App/containerApps/$AppName`?api-version=2023-05-01" `
    --body "{`"properties`":{`"template`":{`"containers`":[{`"name`":`"$AppName`",`"image`":`"$ImageName`"}]}}}"

Write-Host "==> Done! Wait 2-3 minutes for deployment." -ForegroundColor Green
Write-Host "Check logs with: az rest --method GET --url '/subscriptions/221502e7-a7cc-4567-99bc-9b7432bb0afd/resourceGroups/$ResourceGroup/providers/Microsoft.App/containerApps/$AppName/revisions?api-version=2023-05-01'"
