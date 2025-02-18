import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Snackbar,
  Alert,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import { getActiveClients, disconnectClient, createWebSocket } from '../api/client'

interface Client {
  id: string
  status: string
  connectedSince: string
  lastPing: string
}

function Clients() {
  const [clients, setClients] = useState<Client[]>([])
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    // Load initial client data
    const loadClients = async () => {
      try {
        const { data } = await getActiveClients();
        setClients(data);
      } catch (error) {
        console.error('Error loading clients:', error);
        setError('Failed to load clients');
      }
    };

    loadClients();

    // Set up WebSocket connection
    const ws = createWebSocket();
    const cleanup = ws.onmessage((message: any) => {
      if (message.type === 'client_update') {
        setClients(message.clients);
      }
    });

    // Clean up WebSocket connection when component unmounts
    return () => {
      cleanup();
      ws.close();
    };
  }, []);

  const handleDisconnect = async (clientId: string) => {
    try {
      await disconnectClient(clientId)
      setClients((prev) => prev.filter((client) => client.id !== clientId))
      setSuccess(`Client ${clientId} disconnected successfully`)
    } catch (error) {
      console.error('Error disconnecting client:', error)
      setError('Failed to disconnect client')
    }
  }

  const handleCloseError = () => setError(null)
  const handleCloseSuccess = () => setSuccess(null)

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Connected Clients
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Client ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Connected Since</TableCell>
              <TableCell>Last Ping</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {clients.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No clients connected
                </TableCell>
              </TableRow>
            ) : (
              clients.map((client) => (
                <TableRow key={client.id}>
                  <TableCell>{client.id}</TableCell>
                  <TableCell>{client.status}</TableCell>
                  <TableCell>{new Date(client.connectedSince).toLocaleString()}</TableCell>
                  <TableCell>{new Date(client.lastPing).toLocaleString()}</TableCell>
                  <TableCell align="right">
                    <IconButton
                      color="error"
                      onClick={() => handleDisconnect(client.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={handleCloseError}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseError} severity="error">
          {error}
        </Alert>
      </Snackbar>

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

export default Clients 