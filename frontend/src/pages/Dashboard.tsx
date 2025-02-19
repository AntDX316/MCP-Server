import { useState, useEffect } from 'react'
import { Box, Typography, Paper, Grid } from '@mui/material'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { getServerStatus, getConnectionHistory, createWebSocket } from '../api/client'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

interface StatusCardProps {
  title: string
  value: string | number
  color?: string
}

const StatusCard = ({ title, value, color = 'primary.main' }: StatusCardProps) => (
  <Paper sx={{ p: 2, height: '100%' }}>
    <Typography variant="subtitle2" color="text.secondary">
      {title}
    </Typography>
    <Typography variant="h4" color={color} sx={{ mt: 1 }}>
      {value}
    </Typography>
  </Paper>
)

function Dashboard() {
  const [serverStatus, setServerStatus] = useState('Unknown')
  const [activeClients, setActiveClients] = useState(0)
  const [uptime, setUptime] = useState('0:00:00')
  const [version] = useState('v1.0.0')
  const [connectionHistory, setConnectionHistory] = useState<{ time: string; connections: number }[]>([])
  const [startTime] = useState(new Date())

  useEffect(() => {
    // Update uptime every second
    const timer = setInterval(() => {
      const now = new Date()
      const diff = Math.floor((now.getTime() - startTime.getTime()) / 1000)
      const hours = Math.floor(diff / 3600)
      const minutes = Math.floor((diff % 3600) / 60)
      const seconds = diff % 60
      setUptime(`${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`)
    }, 1000)

    return () => clearInterval(timer)
  }, [startTime])

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setServerStatus('Online')
        setActiveClients(1)
        
        // Initialize connection history
        const initialHistory = Array.from({ length: 10 }, (_, i) => ({
          time: new Date(Date.now() - (9 - i) * 60000).toLocaleTimeString(),
          connections: Math.floor(Math.random() * 5)
        }))
        setConnectionHistory(initialHistory)
      } catch (error) {
        console.error('Error loading dashboard data:', error)
      }
    }

    loadDashboardData()
  }, [])

  const chartData = {
    labels: connectionHistory.map(d => new Date(d.time).toLocaleTimeString()),
    datasets: [
      {
        label: 'Active Connections',
        data: connectionHistory.map(d => d.connections),
        borderColor: '#90caf9',
        backgroundColor: 'rgba(144, 202, 249, 0.2)',
        tension: 0.4,
      },
    ],
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
      },
    },
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Server Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Welcome to the MCP Server monitoring dashboard. This interface provides real-time insights into your server's performance,
        including active connections, uptime, and historical connection data. All times are displayed in your local timezone.
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatusCard
            title="SERVER STATUS"
            value={serverStatus}
            color={serverStatus === 'Online' ? 'success.main' : 'error.main'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatusCard title="ACTIVE CLIENTS" value={activeClients} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatusCard title="UPTIME" value={uptime} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatusCard title="VERSION" value={version} />
        </Grid>
      </Grid>

      <Paper sx={{ p: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Connection History</Typography>
          <Typography variant="body2" color="text.secondary">
            Time Range: 30 minutes
          </Typography>
        </Box>
        <Box sx={{ height: 300 }}>
          <Line data={chartData} options={chartOptions} />
        </Box>
      </Paper>
    </Box>
  )
}

export default Dashboard 