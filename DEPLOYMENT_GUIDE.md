# Deployment Guide - Multi-Environment Setup

This project uses a **dual-environment strategy** to minimize costs:

## Environments

### 🧪 Staging (F1 Free Tier)
- **Purpose**: Testing and development
- **Cost**: $0/month
- **Deployment**: Automatic on every push to main
- **Pipeline**: `azure-pipelines.yml` (default)
- **URL**: `web-stg-XXXXXX.azurewebsites.net`

### 🎓 Production (B1 Basic Tier)
- **Purpose**: Live workshops with 25 students
- **Cost**: ~$13/month when running
- **Deployment**: Manual trigger only
- **Pipelines**: 
  - `azure-pipelines-production.yml` (create)
  - `azure-pipelines-cleanup.yml` (delete)
- **URL**: `web-prod-XXXXXX.azurewebsites.net`

## Workflow

### Daily Development
1. Push code to main
2. **Staging auto-deploys** to F1 free tier
3. Test on staging URL
4. No production changes

**Cost: $0**

### Before a Workshop
1. Test on staging environment
2. Go to Azure DevOps → Pipelines
3. Click **New pipeline** → **Existing Azure Pipelines YAML file**
4. Select `/azure-pipelines-production.yml`
5. Click **Run** (takes ~5 minutes)
6. Production B1 environment is created
7. Optionally set `allowedIps` variable for school network only

**Cost starts: ~$0.02/hour**

### After a Workshop
1. Go to Azure DevOps → Pipelines
2. Click **New pipeline** → **Existing Azure Pipelines YAML file**
3. Select `/azure-pipelines-cleanup.yml`
4. Click **Run** (takes ~1 minute)
5. Production B1 resources deleted
6. Staging continues running on F1 free tier

**Cost stops: $0/month again**

## Setup Pipelines in Azure DevOps

### One-Time Setup

You only need to set up the pipelines once. After that, you just run them when needed.

#### 1. Setup Staging (Automatic - Already Done)
The default `azure-pipelines.yml` is already configured from the setup guide.

#### 2. Setup Production Pipeline (Manual)
1. Go to Azure DevOps → Pipelines → New pipeline
2. Select **GitHub**
3. Select your repository
4. Select **Existing Azure Pipelines YAML file**
5. Choose `/azure-pipelines-production.yml`
6. Click **Save** (don't run yet!)
7. Rename pipeline to "Production Deployment (B1)"

**Optional**: Set `allowedIps` variable:
- Edit pipeline → Variables → New variable
- Name: `allowedIps`
- Value: Your school's IP range (e.g., `203.0.113.0/24`)

#### 3. Setup Cleanup Pipeline (Manual)
1. Go to Azure DevOps → Pipelines → New pipeline
2. Select **GitHub**
3. Select your repository
4. Select **Existing Azure Pipelines YAML file**
5. Choose `/azure-pipelines-cleanup.yml`
6. Click **Save** (don't run yet!)
7. Rename pipeline to "Cleanup Production (B1)"

## Pipeline Variables

All pipelines use these variables (set in Azure DevOps pipeline settings):

| Variable | Value | Used by |
|----------|-------|---------|
| `azureSubscription` | `Azure-HackenVoorDummies-OIDC` | All |
| `resourceGroupName` | `rg-hacken-voor-dummies` | All |
| `allowedIps` | `203.0.113.0/24` (optional) | Production only |

## Cost Breakdown

### If You Run 4 Workshops/Year

**Old approach (B1 always on):**
- $13/month × 12 months = **$156/year**

**New approach (B1 only when needed):**
- Staging (F1): $0/month × 12 = $0
- Production (B1): $13/month × 1 month = $13
- (Assume each workshop = 1 week, delete after)
- **Total: ~$13/year** (91% savings!)

## Monitoring Costs

Check current resources:
```bash
# List all App Service Plans and their SKUs
az appservice plan list \
  --resource-group rg-hacken-voor-dummies \
  --query "[].{name:name, sku:sku.name, tier:sku.tier}" \
  --output table
```

Should see:
- **Staging**: `asp-stg-XXXXX` with F1 Free
- **Production** (if running): `asp-prod-XXXXX` with B1 Basic

## Emergency: Stop All Costs Immediately

If you forget to run cleanup and want to stop all B1 charges:

```bash
# Find and delete B1 plan
az appservice plan list \
  --resource-group rg-hacken-voor-dummies \
  --query "[?sku.tier=='Basic'].name" \
  --output tsv | \
  xargs -I {} az appservice plan delete \
    --name {} \
    --resource-group rg-hacken-voor-dummies \
    --yes
```

Or just run the cleanup pipeline in Azure DevOps.

## FAQ

**Q: Will staging work for testing with 25 students?**
A: No - F1 will be slow and hit daily quotas. Only use staging for functional testing before deploying production.

**Q: Can I run multiple workshops in the same month?**
A: Yes! Just keep the B1 running for the whole month. It's cheaper than repeatedly creating/destroying.

**Q: What if I forget to cleanup after a workshop?**
A: You'll pay ~$13 that month. Set a reminder or use Azure Cost Alerts.

**Q: Can I change the app while production is running?**
A: Yes - push to main updates staging automatically. To update production, re-run the production pipeline.

## Next Steps

See [AZURE_DEVOPS_SETUP.md](AZURE_DEVOPS_SETUP.md) for detailed setup instructions.
