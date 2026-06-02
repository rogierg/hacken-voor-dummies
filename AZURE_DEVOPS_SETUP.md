# Azure DevOps CI/CD Setup Guide

This guide shows you how to set up automatic deployment from GitHub to Azure App Service using Azure DevOps Pipelines with **Workload Identity Federation** (no secrets!).

## Prerequisites

- ✅ Azure subscription (free tier available)
- ✅ Azure DevOps account (free at https://dev.azure.com)
- ✅ GitHub repository (this repo)
- ✅ Azure CLI installed (for resource group creation)

## Step 1: Create Resource Group

Create a dedicated resource group for this project:

```bash
# Login to Azure
az login

# Create resource group
az group create \
  --name rg-hacken-voor-dummies \
  --location westeurope \
  --tags project=hacken-voor-dummies environment=prod

# Verify it was created
az group show --name rg-hacken-voor-dummies --output table
```

## Step 2: Deploy Infrastructure

Deploy your App Service to the new resource group:

```bash
# Deploy using Bicep
az deployment group create \
  --resource-group rg-hacken-voor-dummies \
  --template-file infra/main.bicep \
  --parameters environmentName=prod

# Get your App Service name (save this for later)
az webapp list \
  --resource-group rg-hacken-voor-dummies \
  --query "[0].name" \
  --output tsv
```

Save the App Service name - you'll need it for pipeline variables!

## Step 3: Create Azure DevOps Project

1. Go to https://dev.azure.com
2. Click **+ New Project**
3. Name it: `hacken-voor-dummies`
4. Set visibility: **Private** (recommended) or **Public**
5. Click **Create**

## Step 4: Connect to GitHub

1. In your Azure DevOps project, go to **Pipelines**
2. Click **Create Pipeline**
3. Select **GitHub**
4. Authenticate with GitHub if needed
5. Select your repository: `rogierg/hacken-voor-dummies`
6. Click **Existing Azure Pipelines YAML file**
7. Select `/azure-pipelines.yml`
8. **DON'T RUN YET** - we need to configure the service connection first

## Step 5: Create Service Connection with Workload Identity Federation

Create a secure connection using OIDC (no secrets needed):

### Create the Connection

1. In Azure DevOps, click **Project settings** (bottom left gear icon)
2. Under **Pipelines**, click **Service connections**
3. Click **New service connection**
4. Select **Azure Resource Manager**
5. Click **Next**

6. **Authentication method**: Select **Workload Identity federation (automatic)**
   - Modern, secure option with no secrets to manage

7. **Scope level**: Select **Resource Group**
   - Limits access to only your RG

8. **Subscription**: Select your Azure subscription

9. **Resource group**: Select `rg-hacken-voor-dummies`

10. **Service connection name**: `Azure-HackenVoorDummies-OIDC`

11. **Security**: ✅ Check **Grant access permission to all pipelines**

12. Click **Save**

## Step 6: Configure Pipeline Variables

1. In Azure DevOps, go to **Pipelines**
2. Find your pipeline and click **Edit**
3. Click the **Variables** button (top right)
4. Click **New variable** and add these:

| Variable Name | Value | Keep secret? | Notes |
|--------------|-------|--------------|-------|
| `azureSubscription` | `Azure-HackenVoorDummies-OIDC` | No | Must match service connection name exactly |
| `webAppName` | Your App Service name | No | From step 2 (e.g., `app-hacken-prod-abc123`) |

5. Click **Save**

## Step 7: Run Your First Deployment

1. Go to **Pipelines**
2. Click your pipeline
3. Click **Run pipeline**
4. Click **Run**

The pipeline will:
- ✅ Authenticate using OIDC (no secrets!)
- ✅ Build your Flask app
- ✅ Package it as a ZIP
- ✅ Deploy to Azure App Service
- ✅ Configure the startup command

## Step 8: Verify Deployment

After the pipeline succeeds:

1. Go to Azure Portal
2. Open your App Service
3. Click **Browse** to open your app
4. You should see your Flask app running!

## Automatic Deployments

Every push to `main` triggers automatic deployment to Azure App Service.

## Troubleshooting

### Pipeline fails with "Service connection not found"
- Verify `azureSubscription` variable matches service connection name exactly (case-sensitive)
- Check: Project Settings → Service connections

### Pipeline fails with "Failed to obtain the Json Web Token(JWT)"
- Verify service connection uses **Workload Identity federation**
- Try recreating the service connection

### Deployment fails with "Forbidden" or "Unauthorized"
- Verify service connection scope is `rg-hacken-voor-dummies`
- Service principal should have **Contributor** role on the RG

### App doesn't start after deployment
- Check Azure Portal → App Service → Log stream for errors
- Verify `requirements.txt` includes all dependencies
- Check startup command is set: `python main.py`

## Free Tier Limitations

Your F1 App Service Plan:
- ✅ FREE (no cost)
- ⚠️ App sleeps after 20 minutes of inactivity (first request takes 10-30 seconds)
- ✅ SSL/TLS included (HTTPS)

## Next Steps

- Set up staging environment (requires paid tier)
- Add automated tests before deployment
- Configure custom domain (requires paid tier)
- Set up monitoring and alerts

## Clean Up

```bash
# Delete resource group
az group delete --name rg-hacken-voor-dummies --yes

# Delete service connection in Azure DevOps
# Project Settings → Service connections → Delete

# Delete Azure DevOps project (optional)
# Project Settings → Overview → Delete
```

## Quick Reference

```bash
# Check deployment status
az webapp deployment list-publishing-profiles \
  --name YOUR_APP_NAME \
  --resource-group rg-hacken-voor-dummies

# Restart app
az webapp restart \
  --name YOUR_APP_NAME \
  --resource-group rg-hacken-voor-dummies

# View app URL
az webapp show \
  --name YOUR_APP_NAME \
  --resource-group rg-hacken-voor-dummies \
  --query "defaultHostName" -o tsv
```
