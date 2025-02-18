import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  TextField,
  Switch,
  Button,
  Grid,
  FormControlLabel,
  Alert,
  Snackbar,
} from '@mui/material'
import { getSettings, updateSettings, Settings as APISettings } from '../api/client'

interface ServerSettings {
  host: string
  port: number
  maxConnections: number
  pingTimeout: number
  debugMode: boolean
  sslEnabled: boolean
}

interface MCPSettings {
  protocolVersion: string
  maxContextLength: number
  defaultTemperature: number
  maxTokens: number
}

function Settings() {
  const defaultServerSettings: ServerSettings = {
    host: '',
    port: 8765,
    maxConnections: 100,
    pingTimeout: 30,
    debugMode: false,
    sslEnabled: false,
  }

  const defaultMCPSettings: MCPSettings = {
    protocolVersion: '1.0.0',
    maxContextLength: 4096,
    defaultTemperature: 0.7,
    maxTokens: 2048,
  }

  const [serverSettings, setServerSettings] = useState<ServerSettings>(defaultServerSettings)
  const [mcpSettings, setMcpSettings] = useState<MCPSettings>(defaultMCPSettings)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isDirty, setIsDirty] = useState(false)

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const { data } = await getSettings()
        if (data.server && data.mcp) {
          setServerSettings({
            host: data.server.host ?? defaultServerSettings.host,
            port: data.server.port ?? defaultServerSettings.port,
            maxConnections: data.server.maxConnections ?? defaultServerSettings.maxConnections,
            pingTimeout: data.server.pingTimeout ?? defaultServerSettings.pingTimeout,
            debugMode: data.server.debugMode ?? defaultServerSettings.debugMode,
            sslEnabled: data.server.sslEnabled ?? defaultServerSettings.sslEnabled,
          })
          
          setMcpSettings({
            protocolVersion: data.mcp.protocolVersion ?? defaultMCPSettings.protocolVersion,
            maxContextLength: data.mcp.maxContextLength ?? defaultMCPSettings.maxContextLength,
            defaultTemperature: data.mcp.defaultTemperature ?? defaultMCPSettings.defaultTemperature,
            maxTokens: data.mcp.maxTokens ?? defaultMCPSettings.maxTokens,
          })
        }
        setLoading(false)
      } catch (error) {
        console.error('Error loading settings:', error)
        setError('Failed to load settings')
        setLoading(false)
      }
    }

    loadSettings()
  }, [])

  const handleServerSettingChange = (field: keyof ServerSettings) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value =
      field === 'debugMode' || field === 'sslEnabled'
        ? event.target.checked
        : field === 'port' || field === 'maxConnections' || field === 'pingTimeout'
        ? parseInt(event.target.value)
        : event.target.value

    setServerSettings((prev) => ({ ...prev, [field]: value }))
    setIsDirty(true)
  }

  const handleMCPSettingChange = (field: keyof MCPSettings) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value =
      field === 'defaultTemperature'
        ? parseFloat(event.target.value)
        : field === 'maxContextLength' || field === 'maxTokens'
        ? parseInt(event.target.value)
        : event.target.value

    setMcpSettings((prev) => ({ ...prev, [field]: value }))
    setIsDirty(true)
  }

  const handleSave = async () => {
    try {
      await updateSettings({
        server: serverSettings,
        mcp: mcpSettings,
      })
      setSuccess('Settings saved successfully')
      setIsDirty(false)
    } catch (error) {
      console.error('Error saving settings:', error)
      setError('Failed to save settings')
    }
  }

  const handleCloseError = () => setError(null)
  const handleCloseSuccess = () => setSuccess(null)

  if (loading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Loading settings...
        </Typography>
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Configure your MCP server and client settings.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Server Configuration
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                label="Host"
                value={serverSettings.host}
                onChange={handleServerSettingChange('host')}
                fullWidth
              />
              <TextField
                label="Port"
                type="number"
                value={serverSettings.port}
                onChange={handleServerSettingChange('port')}
                fullWidth
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={serverSettings.debugMode}
                    onChange={handleServerSettingChange('debugMode')}
                  />
                }
                label="Debug Mode"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={serverSettings.sslEnabled}
                    onChange={handleServerSettingChange('sslEnabled')}
                  />
                }
                label="SSL Enabled"
              />
              <TextField
                label="Max Connections"
                type="number"
                value={serverSettings.maxConnections}
                onChange={handleServerSettingChange('maxConnections')}
                fullWidth
              />
              <TextField
                label="Ping Timeout (seconds)"
                type="number"
                value={serverSettings.pingTimeout}
                onChange={handleServerSettingChange('pingTimeout')}
                fullWidth
              />
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              MCP Configuration
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                label="Protocol Version"
                value={mcpSettings.protocolVersion}
                onChange={handleMCPSettingChange('protocolVersion')}
                fullWidth
              />
              <TextField
                label="Max Context Length"
                type="number"
                value={mcpSettings.maxContextLength}
                onChange={handleMCPSettingChange('maxContextLength')}
                fullWidth
              />
              <TextField
                label="Default Temperature"
                type="number"
                inputProps={{ step: 0.1, min: 0, max: 1 }}
                value={mcpSettings.defaultTemperature}
                onChange={handleMCPSettingChange('defaultTemperature')}
                fullWidth
              />
              <TextField
                label="Max Tokens"
                type="number"
                value={mcpSettings.maxTokens}
                onChange={handleMCPSettingChange('maxTokens')}
                fullWidth
              />
            </Box>
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={!isDirty}
          sx={{ minWidth: 150 }}
        >
          Save Changes
        </Button>
      </Box>

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

export default Settings 