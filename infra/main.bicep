param location string = resourceGroup().location
param environmentName string
param resourceGroupName string = resourceGroup().name

// Generate unique suffix for resources
var resourceToken = uniqueString(resourceGroup().id)

// App Service Plan (Free tier)
resource appServicePlan 'Microsoft.Web/serverfarms@2021-02-01' = {
  name: 'asp-${environmentName}-${resourceToken}'
  location: location
  sku: {
    name: 'F1'
    tier: 'Free'
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// Web App
resource webApp 'Microsoft.Web/sites@2021-02-01' = {
  name: 'web-${environmentName}-${resourceToken}'
  location: location
  kind: 'app,linux'
  tags: {
    'azd-service-name': 'api'
  }
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      alwaysOn: false
      http20Enabled: true
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
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

output appServicePlanId string = appServicePlan.id
output webAppId string = webApp.id
output webAppName string = webApp.name
output webAppUri string = 'https://${webApp.properties.defaultHostName}'
