import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Grid,
  Paper,
  Switch,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Alert,
  Snackbar,
} from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import GitHubIcon from '@mui/icons-material/GitHub'
import { Google as GoogleIcon } from '@mui/icons-material'
import SlackIcon from '@mui/icons-material/AlternateEmail'
import CloudIcon from '@mui/icons-material/Cloud'
import CodeIcon from '@mui/icons-material/Code'
import { getServiceConfig, updateServiceConfig, toggleService } from '../api/client'
import { Visibility, VisibilityOff } from '@mui/icons-material'

interface Service {
  id: string
  name: string
  icon: JSX.Element
  description: string
  enabled: boolean
  configFields: {
    name: string
    type: string
    label: string
    sensitive?: boolean
  }[]
  instructions: string[]
}

const services: Service[] = [
  {
    id: 'github',
    name: 'GitHub',
    icon: <GitHubIcon />,
    description: 'Connect to GitHub repositories for code analysis and automation',
    enabled: false,
    configFields: [
      { name: 'accessToken', type: 'text', label: 'Access Token', sensitive: true },
      { name: 'organization', type: 'text', label: 'Organization' },
    ],
    instructions: [
      'Go to GitHub Settings > Developer Settings > Personal Access Tokens > Tokens (classic)',
      'Click \'Generate new token\' and select \'classic\'',
      'Give it a name and select these permissions: repo, workflow, read:org',
      'Copy the generated token and paste it here',
      'Enter your organization name (found in your GitHub URL)',
    ],
  },
  {
    id: 'slack',
    name: 'Slack',
    icon: <SlackIcon />,
    description: 'Integrate with Slack for team collaboration and notifications',
    enabled: false,
    configFields: [
      { name: 'botToken', type: 'text', label: 'Bot Token', sensitive: true },
      { name: 'channel', type: 'text', label: 'Channel' },
    ],
    instructions: [
      'Go to api.slack.com and create a new app in your workspace',
      'Under \'OAuth & Permissions\', add these scopes: chat:write, files:write',
      'Install the app to your workspace',
      'Copy the \'Bot User OAuth Token\' and paste it here',
      'Enter the channel name where you want the bot to post (e.g., #general)',
    ],
  },
  {
    id: 'google_drive',
    name: 'Google Drive',
    icon: <GoogleIcon />,
    description: 'Access and analyze documents from Google Drive',
    enabled: false,
    configFields: [
      { name: 'clientId', type: 'text', label: 'Client ID' },
      { name: 'clientSecret', type: 'text', label: 'Client Secret', sensitive: true },
    ],
    instructions: [
      'Go to Google Cloud Console and create/select a project',
      'Enable the Google Drive API for your project',
      'Go to Credentials and create an OAuth 2.0 Client ID',
      'Choose \'Desktop Application\' as the application type',
      'Copy the Client ID and Client Secret and paste them here',
    ],
  },
  {
    id: 'azure',
    name: 'Azure',
    icon: <CloudIcon />,
    description: 'Connect to Azure services for cloud integration',
    enabled: false,
    configFields: [
      { name: 'tenantId', type: 'text', label: 'Tenant ID', sensitive: true },
      { name: 'clientId', type: 'text', label: 'Client ID' },
      { name: 'clientSecret', type: 'text', label: 'Client Secret', sensitive: true },
    ],
    instructions: [
      'Go to Azure Portal > Azure Active Directory',
      'Register a new application or select existing one',
      'Under \'Certificates & secrets\', create a new client secret',
      'Copy these values and paste them here:',
      '- Tenant ID (from Overview)',
      '- Client ID (Application ID)',
      '- Client Secret (value you just created)',
    ],
  },
  {
    id: 'vscode',
    name: 'VS Code',
    icon: <CodeIcon />,
    description: 'Enable VS Code extension support',
    enabled: false,
    configFields: [
      { name: 'workspaceFolder', type: 'text', label: 'Workspace Folder Path' },
      { name: 'serverUrl', type: 'text', label: 'MCP Server URL', sensitive: false },
    ],
    instructions: [
      'Install Visual Studio Code if you haven\'t already',
      'Open VS Code and go to the Extensions view (Ctrl+Shift+X)',
      'Search for "MCP Server" in the Extensions Marketplace',
      'Click Install to add the MCP Server extension',
      'Enter your workspace folder path where .vscode settings will be created',
      'Optionally customize the MCP Server URL (defaults to ws://localhost:8000)',
      'The extension will automatically connect to your MCP server'
    ],
  },
]

function Services() {
  const [configOpen, setConfigOpen] = useState(false)
  const [selectedService, setSelectedService] = useState<Service | null>(null)
  const [configValues, setConfigValues] = useState<Record<string, string>>({})
  const [showSensitive, setShowSensitive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [servicesState, setServicesState] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadServices = async () => {
      try {
        const results = await Promise.all(
          services.map(async (service) => {
            try {
              const { data } = await getServiceConfig(service.id)
              return { id: service.id, enabled: data.enabled, config: data.config }
            } catch {
              return { id: service.id, enabled: false, config: {} }
            }
          })
        )

        const state: Record<string, boolean> = {}
        const configs: Record<string, Record<string, string>> = {}
        results.forEach((result) => {
          state[result.id] = result.enabled
          configs[result.id] = result.config
        })

        setServicesState(state)
        setLoading(false)
      } catch (error) {
        console.error('Error loading services:', error)
        setError('Failed to load services configuration')
        setLoading(false)
      }
    }

    loadServices()
  }, [])

  const handleToggle = async (serviceId: string) => {
    try {
      const newEnabled = !servicesState[serviceId]
      await toggleService(serviceId, newEnabled)
      setServicesState((prev) => ({ ...prev, [serviceId]: newEnabled }))
      setSuccess(`${serviceId} ${newEnabled ? 'enabled' : 'disabled'} successfully`)
    } catch (error) {
      console.error('Error toggling service:', error)
      setError('Failed to toggle service')
    }
  }

  const handleConfigure = async (service: Service) => {
    try {
      const { data } = await getServiceConfig(service.id)
      setSelectedService(service)
      setConfigValues(data.config || {})
      setConfigOpen(true)
    } catch (error) {
      console.error('Error loading service config:', error)
      setError('Failed to load service configuration')
    }
  }

  const handleSave = async () => {
    if (!selectedService) return

    try {
      await updateServiceConfig(selectedService.id, {
        enabled: servicesState[selectedService.id] || false,
        config: configValues,
      })
      setSuccess('Configuration saved successfully')
      setConfigOpen(false)
    } catch (error) {
      console.error('Error saving config:', error)
      setError('Failed to save configuration')
    }
  }

  const handleCloseError = () => setError(null)
  const handleCloseSuccess = () => setSuccess(null)

  if (loading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Service Integrations
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Loading services...
        </Typography>
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Service Integrations
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Enable and configure various service integrations to extend your MCP server's capabilities.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {services.map((service) => (
          <Grid item xs={12} sm={6} key={service.id}>
            <Paper sx={{ p: 3, display: 'flex', alignItems: 'center' }}>
              <Box sx={{ mr: 2 }}>{service.icon}</Box>
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="h6">{service.name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {service.description}
                </Typography>
                <Button
                  variant="text"
                  size="small"
                  sx={{ mt: 1 }}
                  onClick={() => {
                    const docUrls: Record<string, string> = {
                      github: 'https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens',
                      slack: 'https://api.slack.com/authentication/basics',
                      google_drive: 'https://developers.google.com/drive/api/quickstart/python',
                      azure: 'https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app',
                      vscode: 'https://code.visualstudio.com/api/get-started/your-first-extension'
                    };
                    window.open(docUrls[service.id], '_blank');
                  }}
                >
                  CLICK HERE FOR DETAILED DOCUMENTATION
                </Button>
              </Box>
              <Box sx={{ ml: 2, display: 'flex', alignItems: 'center' }}>
                {service.configFields.length > 0 && (
                  <IconButton
                    onClick={() => handleConfigure(service)}
                    sx={{ mr: 1 }}
                  >
                    <EditIcon />
                  </IconButton>
                )}
                <Switch
                  checked={servicesState[service.id] || false}
                  onChange={() => handleToggle(service.id)}
                />
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Dialog
        open={configOpen}
        onClose={() => setConfigOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            background: 'rgba(18, 18, 18, 0.85)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderRadius: 2,
            boxShadow: '0 4px 30px rgba(0, 0, 0, 0.1)'
          }
        }}
      >
        {selectedService && (
          <>
            <DialogTitle
              sx={{
                background: 'rgba(255, 255, 255, 0.03)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.12)'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {selectedService.icon}
                <Typography variant="h6" sx={{ ml: 1 }}>
                  Configure {selectedService.name}
                </Typography>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Box sx={{ 
                mb: 3, 
                mt: 1, 
                p: 2, 
                bgcolor: 'rgba(255, 255, 255, 0.03)',
                borderRadius: 1,
                border: '1px solid rgba(255, 255, 255, 0.08)'
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2" color="info.main">
                    To configure {selectedService.name} integration:
                  </Typography>
                </Box>
                {selectedService.instructions.map((instruction, index) => (
                  <Typography key={index} variant="body2" sx={{ ml: 2, color: 'rgba(255, 255, 255, 0.7)' }}>
                    {index + 1}. {instruction}
                  </Typography>
                ))}
                <Button
                  variant="text"
                  size="small"
                  sx={{ 
                    mt: 1,
                    color: 'primary.main',
                    '&:hover': {
                      background: 'rgba(144, 202, 249, 0.08)'
                    }
                  }}
                  onClick={() => {
                    const docUrls: Record<string, string> = {
                      github: 'https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens',
                      slack: 'https://api.slack.com/authentication/basics',
                      google_drive: 'https://developers.google.com/drive/api/quickstart/python',
                      azure: 'https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app',
                      vscode: 'https://code.visualstudio.com/api/get-started/your-first-extension'
                    };
                    window.open(docUrls[selectedService.id], '_blank');
                  }}
                >
                  CLICK HERE FOR DETAILED DOCUMENTATION
                </Button>
              </Box>

              {selectedService.configFields.map((field) => (
                <TextField
                  key={field.name}
                  fullWidth
                  margin="normal"
                  label={field.label}
                  type={field.sensitive && !showSensitive ? 'password' : 'text'}
                  value={configValues[field.name] || ''}
                  onChange={(e) =>
                    setConfigValues((prev) => ({
                      ...prev,
                      [field.name]: e.target.value,
                    }))
                  }
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': {
                        borderColor: 'rgba(255, 255, 255, 0.12)',
                      },
                      '&:hover fieldset': {
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                      },
                      '&.Mui-focused fieldset': {
                        borderColor: 'primary.main',
                      },
                      backgroundColor: 'rgba(255, 255, 255, 0.03)'
                    },
                    '& .MuiInputLabel-root': {
                      color: 'rgba(255, 255, 255, 0.7)'
                    },
                    '& .MuiInputBase-input': {
                      color: 'rgba(255, 255, 255, 0.9)'
                    }
                  }}
                  InputProps={{
                    endAdornment: field.sensitive && (
                      <IconButton
                        size="small"
                        onClick={() => setShowSensitive(!showSensitive)}
                        sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
                      >
                        {showSensitive ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    )
                  }}
                />
              ))}

              {selectedService.configFields.some((f) => f.sensitive) && (
                <Button
                  variant="text"
                  size="small"
                  onClick={() => setShowSensitive(!showSensitive)}
                  sx={{ 
                    mt: 1,
                    color: 'primary.main',
                    '&:hover': {
                      background: 'rgba(144, 202, 249, 0.08)'
                    }
                  }}
                >
                  {showSensitive ? 'Hide' : 'Show'} sensitive fields
                </Button>
              )}
            </DialogContent>
            <DialogActions sx={{ 
              borderTop: '1px solid rgba(255, 255, 255, 0.12)',
              background: 'rgba(255, 255, 255, 0.03)',
              px: 3,
              py: 2
            }}>
              <Button 
                onClick={() => setConfigOpen(false)}
                sx={{
                  color: 'rgba(255, 255, 255, 0.7)',
                  '&:hover': {
                    background: 'rgba(255, 255, 255, 0.08)'
                  }
                }}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                onClick={handleSave}
                sx={{ 
                  minWidth: 150,
                  background: 'linear-gradient(45deg, rgba(144, 202, 249, 0.6) 30%, rgba(30, 136, 229, 0.6) 90%)',
                  backdropFilter: 'blur(5px)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  color: '#fff',
                  fontWeight: 'bold',
                  textShadow: '0 1px 2px rgba(0,0,0,0.2)',
                  boxShadow: '0 3px 10px rgba(144, 202, 249, 0.2)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, rgba(144, 202, 249, 0.8) 30%, rgba(30, 136, 229, 0.8) 90%)',
                    boxShadow: '0 5px 15px rgba(144, 202, 249, 0.3)'
                  }
                }}
              >
                Save Configuration
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={handleCloseSuccess}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSuccess} severity="success">
          {success}
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default Services 