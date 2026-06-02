# Azure DevOps CI/CD Setup Guide

This guide shows you how to set up automatic deployment from GitHub to Azure App Service using Azure DevOps Pipelines.

## Prerequisites

- ✅ Azure subscription with F1 App Service Plan
- ✅ Azure DevOps account (free at https://dev.azure.com)
- ✅ GitHub repository (this repo)
- ✅ Azure App Service already created

## Step 1: Create Azure DevOps Project

1. Go to https://dev.azure.com
2. Click **+ New Project**
3. Name it: `hacken-voor-dummies`
4. Set visibility: **Private** or **Public**
5. Click **Create**

## Step 2: Connect to GitHub

1. In your Azure DevOps project, go to **Pipelines**
2. Click **Create Pipeline**
3. Select **GitHub**
4. Authenticate with GitHub if needed
5. Select your repository: `rogierg/hacken-voor-dummies`
6. Click **Existing Azure Pipelines YAML file**
7. Select `/azure-pipelines.yml`
8. **DON'T RUN YET** - we need to configure variables first

## Step 3: Create Azure Service Connection

This allows Azure DevOps to deploy to your Azure subscription.

1. In Azure DevOps, click **Project settings** (bottom left)
2. Go to **Service connections**
3. Click **New service connection**
4. Select **Azure Resource Manager**
5. Click **Next**
6. Authentication method: **Service principal (automatic)**
7. Scope: **Subscription**
8. Select your Azure subscription
9. Resource group: Leave empty or select `rg-hacken-voor-dummies`
10. Service connection name: `Azure-ServiceConnection`
11. ✅ Check **Grant access permission to all pipelines**
12. Click **Save**

## Step 4: Get Your App Service Name

You need to know the name of your existing App Service:

```bash
# List your app services
az webapp list --query "[].{name:name, resourceGroup:resourceGroup}" --output table
```

Or go to Azure Portal → App Services and copy the name.

## Step 5: Configure Pipeline Variables

1. In Azure DevOps, go to **Pipelines**
2. Find your pipeline and click **Edit**
3. Click the **Variables** button (top right)
4. Add these variables:

| Variable Name | Value | Keep secret? |
|--------------|-------|--------------|
| `azureSubscription` | `Azure-ServiceConnection` | No |
| `webAppName` | Your App Service name (e.g., `hacken-app-prod`) | No |

5. Click **Save**

## Step 6: Run Your First Deployment

1. Go to **Pipelines**
2. Click your pipeline
3. Click **Run pipeline**
4. Click **Run**

The pipeline will:
- ✅ Build your Flask app
- ✅ Package it as a ZIP
- ✅ Deploy to Azure App Service
- ✅ Configure the startup command

## Step 7: Verify Deployment

After the pipeline succeeds:

1. Go to Azure Portal
2. Open your App Service
3. Click **Browse** to open your app
4. You should see your Flask app running!

## Automatic Deployments

Now every time you push to the `main` branch:
1. Azure DevOps detects the change
2. Runs the pipeline automatically
3. Deploys to Azure App Service

## Pipeline Status Badge (Optional)

Add a build status badge to your README:

1. In Azure DevOps, go to **Pipelines**
2. Click your pipeline
3. Click **...** (three dots) → **Status badge**
4. Copy the Markdown
5. Paste in your README.md

## Troubleshooting

### Pipeline fails with "Service connection not found"

- Make sure `azureSubscription` variable matches your service connection name exactly
- Check the service connection has permissions to your subscription

### App Service deployment fails

Check that:
- Your App Service exists
- `webAppName` variable is set correctly
- The service connection has permissions to the resource group

### App doesn't start after deployment

1. Go to Azure Portal → Your App Service → Log stream
2. Look for errors
3. Common fixes:
   - Check `requirements.txt` includes all dependencies
   - Verify `main.py` has the production configuration
   - Check startup command is set: `python main.py`

### View Deployment Logs

```bash
# Install Azure CLI
az login

# Stream logs
az webapp log tail --name YOUR_APP_NAME --resource-group rg-hacken-voor-dummies
```

## Free Tier Limitations

Your F1 App Service Plan has:
- ✅ FREE (no cost)
- ⚠️ App sleeps after 20 minutes of inactivity
- ⚠️ First request after sleep takes 10-30 seconds (cold start)
- ⚠️ Shared CPU resources
- ⚠️ 1 GB storage
- ✅ SSL/TLS included (HTTPS)

## Manual Deployment (Alternative)

If you prefer manual control, you can trigger deployments from:

1. **Azure DevOps**: Pipelines → Run pipeline
2. **Azure CLI**:
   ```bash
   az webapp deployment source config-zip \
     --resource-group rg-hacken-voor-dummies \
     --name YOUR_APP_NAME \
     --src deployment.zip
   ```

## Next Steps

- Set up staging environment (requires paid tier)
- Add automated tests before deployment
- Configure custom domain (requires paid tier)
- Set up monitoring and alerts

## Clean Up

To delete everything:

```bash
# Delete resource group (removes App Service too)
az group delete --name rg-hacken-voor-dummies --yes

# Delete Azure DevOps project
# Go to Project Settings → Overview → Delete
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
