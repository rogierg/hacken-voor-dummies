# Azure Deployment Guide for hacken-voor-dummies

This guide walks you through deploying the Flask application to Azure using the free tier.

## Prerequisites

- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- [Azure Developer CLI (azd)](https://learn.microsoft.com/en-us/azure/developer/azure-dev/install-azd) installed
- An [Azure subscription](https://azure.microsoft.com/free) (free tier available)
- Git configured with your GitHub credentials

## Option 1: Quick Deploy with Azure CLI (Recommended)

### Step 1: Login to Azure

```bash
az login
```

This opens your browser to authenticate with Azure.

### Step 2: Create a Resource Group

```bash
az group create \
  --name rg-hacken-voor-dummies \
  --location eastus
```

### Step 3: Deploy the Infrastructure

```bash
az deployment group create \
  --resource-group rg-hacken-voor-dummies \
  --template-file infra/main.bicep \
  --parameters environmentName=prod
```

### Step 4: Get Your App URL

```bash
az webapp list \
  --resource-group rg-hacken-voor-dummies \
  --query "[0].{Name:name, URL:defaultHostName}" \
  --output table
```

### Step 5: Deploy Your Code

#### Option A: Using ZIP Deploy

```bash
# Create a zip file of your application
zip -r deployment.zip . -x "*.git*" "__pycache__/*" "*.pyc" ".venv/*"

# Get the app name
RESOURCE_GROUP="rg-hacken-voor-dummies"
APP_NAME=$(az webapp list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv)

# Deploy
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --src deployment.zip
```

#### Option B: Using GitHub Integration

1. Go to Azure Portal
2. Navigate to your App Service
3. Go to Deployment Center
4. Select GitHub as source
5. Authenticate and select your repository and branch

### Step 6: Configure App Service Settings

```bash
RESOURCE_GROUP="rg-hacken-voor-dummies"
APP_NAME=$(az webapp list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv)

# Set environment variables
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    WEBSITES_PORT=8000

# Set startup command
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --startup-file "python main.py"
```

## Option 2: Deploy with Azure Developer CLI (azd)

### Step 1: Initialize Project

```bash
azd init --template hacken-voor-dummies
```

### Step 2: Deploy

```bash
azd up
```

## Free Tier Specifications

### What's Included
- 1 free App Service Plan (F1 tier)
- 1 GB of storage
- Shared CPU resources
- Free SSL/TLS with `*.azurewebsites.net` domain

### Important Limitations
- **No custom domains** (unless you upgrade)
- **No always-on** - App sleeps after 20 minutes of inactivity
- **Cold start delays** - First request takes 10-30 seconds
- **No scaling** - Fixed resources
- **1 GB data transfer per day** (soft limit)

## Update main.py for Production

Modify the last lines of `main.py`:

```python
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
```

Key changes:
- `debug=False` - Disables debug mode in production
- `host='0.0.0.0'` - Listens on all network interfaces
- `port` - Uses Azure's PORT environment variable

## Verify Your Deployment

```bash
# Get your app URL
az webapp show \
  --resource-group rg-hacken-voor-dummies \
  --name $(az webapp list --resource-group rg-hacken-voor-dummies --query "[0].name" -o tsv) \
  --query "defaultHostName" \
  --output tsv
```

Visit the URL in your browser - your Flask app should be live!

## View Logs

```bash
az webapp log tail \
  --resource-group rg-hacken-voor-dummies \
  --name $(az webapp list --resource-group rg-hacken-voor-dummies --query "[0].name" -o tsv)
```

## Troubleshooting

### App Won't Start

1. Check logs:
   ```bash
   az webapp log tail --resource-group rg-hacken-voor-dummies --name $APP_NAME
   ```

2. Verify startup command and ensure main.py is updated for production

### Cold Start Issues

Free tier apps sleep after 20 minutes. To keep app warm:
- Use a monitoring tool like Pingdom to ping every 15 minutes
- Consider upgrading to paid tier if needed

### Port Binding Error

Ensure Flask app listens on PORT environment variable:

```python
port = int(os.environ.get('PORT', 8000))
app.run(host='0.0.0.0', port=port)
```

## Clean Up Resources

```bash
az group delete --name rg-hacken-voor-dummies --yes
```

## Quick Start Commands

```bash
# 1. Login
az login

# 2. Create resource group
az group create --name rg-hacken-voor-dummies --location eastus

# 3. Deploy infrastructure
az deployment group create \
  --resource-group rg-hacken-voor-dummies \
  --template-file infra/main.bicep \
  --parameters environmentName=prod

# 4. Deploy code (ZIP)
zip -r deployment.zip . -x "*.git*" "__pycache__/*" "*.pyc" ".venv/*"
APP_NAME=$(az webapp list --resource-group rg-hacken-voor-dummies --query "[0].name" -o tsv)
az webapp deployment source config-zip \
  --resource-group rg-hacken-voor-dummies \
  --name $APP_NAME \
  --src deployment.zip

# 5. Get URL
az webapp show --resource-group rg-hacken-voor-dummies --name $APP_NAME --query "defaultHostName" -o tsv
```
