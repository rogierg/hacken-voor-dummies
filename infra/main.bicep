param location string = resourceGroup().location
param environmentName string
param resourceGroupName string = resourceGroup().name
param existingAppServicePlanName string = ''
param webAppName string = ''
param allowedIpAddresses array = []

// Reference existing App Service Plan (if provided)
resource existingAppServicePlan 'Microsoft.Web/serverfarms@2021-02-01' existing = if (!empty(existingAppServicePlanName)) {
  name: existingAppServicePlanName
}

// Generate unique suffix for resources
var resourceToken = uniqueString(resourceGroup().id)
var appServicePlanId = !empty(existingAppServicePlanName) ? existingAppServicePlan.id : newAppServicePlan.id

// Create NEW App Service Plan only if not reusing
resource newAppServicePlan 'Microsoft.Web/serverfarms@2021-02-01' = if (empty(existingAppServicePlanName)) {
  name: 'asp-${environmentName}-${resourceToken}'
  location: location
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// Web App
resource webApp 'Microsoft.Web/sites@2021-02-01' = {
  name: !empty(webAppName) ? webAppName : 'web-${environmentName}-${resourceToken}'
  location: location
  kind: 'app,linux'
  tags: {
    'azd-service-name': 'api'
  }
  properties: {
    serverFarmId: appServicePlanId
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      alwaysOn: true
      http20Enabled: true
      minTlsVersion: '1.2'
      ipSecurityRestrictions: [for (ip, index) in allowedIpAddresses: {
        ipAddress: ip
        action: 'Allow'
        priority: 100 + index
        name: 'AllowedIP${index}'
      }]
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'false'
        }
        {
          name: 'FLASK_ENV'
          value: 'production'
        }
        {
          name: 'PYTHONUNBUFFERED'
          value: '1'
        }
        {
          name: 'WEBSITES_PORT'
          value: '80'
        }
      ]
      ftpsState: 'FtpsOnly'
    }
    httpsOnly: true
  }
}

output appServicePlanId string = appServicePlanId
output webAppId string = webApp.id
output webAppName string = webApp.name
output webAppUri string = 'https://${webApp.properties.defaultHostName}'
