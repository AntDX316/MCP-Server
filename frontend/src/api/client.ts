import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

export interface ServerStatus {
  status: string
  activeClients: number
  uptime: string
  version: string
}

export interface ConnectionHistory {
  time: string
  connections: number
}

export interface ServiceConfig {
  enabled: boolean
  config: Record<string, string>
}

export interface Settings {
  server: {
    host: string
    port: number
    maxConnections: number
    pingTimeout: number
    debugMode: boolean
    sslEnabled: boolean
  }
  mcp: {
    protocolVersion: string
    maxContextLength: number
    defaultTemperature: number
    maxTokens: number
  }
}

// Server status and monitoring
export const getServerStatus = () => api.get<ServerStatus>('/status')
export const getConnectionHistory = () => api.get<ConnectionHistory[]>('/connections/history')
export const getActiveClients = () => api.get('/clients')
export const disconnectClient = (clientId: string) => api.post(`/clients/${clientId}/disconnect`)

// Service management
export const getServiceConfig = (serviceId: string) => 
  api.get<ServiceConfig>(`/services/${serviceId}`)
export const updateServiceConfig = (serviceId: string, config: ServiceConfig) =>
  api.put(`/services/${serviceId}`, config)
export const toggleService = (serviceId: string, enabled: boolean) =>
  api.post(`/services/${serviceId}/toggle`, { enabled })

// Settings management
export const getSettings = () => api.get<Settings>('/settings')
export const updateSettings = (settings: Settings) => api.put('/settings', settings)

// WebSocket singleton manager
class WebSocketManager {
  private static instance: WebSocketManager;
  private ws: WebSocket | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private listeners: Set<(data: any) => void> = new Set();
  private clientId: string;
  private isReconnecting: boolean = false;

  private constructor() {
    // Generate a stable client ID that persists across page reloads
    this.clientId = localStorage.getItem('mcp_client_id') || this.generateClientId();
    localStorage.setItem('mcp_client_id', this.clientId);
  }

  private generateClientId(): string {
    return 'mcp-' + Math.random().toString(36).substring(2, 15);
  }

  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }

  private startPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 30000); // Send ping every 30 seconds
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN || this.isReconnecting) return;

    this.isReconnecting = true;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.ws = new WebSocket(`${protocol}//${window.location.host}/ws/${this.clientId}`);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.isReconnecting = false;
      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = null;
      }
      this.startPingInterval();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.isReconnecting = false;
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.isReconnecting = false;
      this.ws = null;
      if (this.pingInterval) {
        clearInterval(this.pingInterval);
        this.pingInterval = null;
      }
      // Attempt to reconnect after 5 seconds if we still have listeners
      if (!this.reconnectTimeout && this.listeners.size > 0) {
        this.reconnectTimeout = setTimeout(() => {
          if (this.listeners.size > 0) {
            this.connect();
          }
        }, 5000);
      }
    };

    this.ws.onmessage = (event) => {
      try {
        if (event.data === 'pong') {
          // Received pong response, connection is healthy
          return;
        }
        const data = JSON.parse(event.data);
        this.listeners.forEach(listener => listener(data));
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
  }

  addListener(listener: (data: any) => void) {
    this.listeners.add(listener);
    if (!this.ws && !this.isReconnecting) {
      this.connect();
    }
    return () => this.removeListener(listener);
  }

  removeListener(listener: (data: any) => void) {
    this.listeners.delete(listener);
    if (this.listeners.size === 0) {
      if (this.ws) {
        this.ws.close(1000, "No active listeners");
        this.ws = null;
      }
      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = null;
      }
      if (this.pingInterval) {
        clearInterval(this.pingInterval);
        this.pingInterval = null;
      }
    }
  }
}

// Update createWebSocket to use the singleton manager
export const createWebSocket = () => {
  const wsManager = WebSocketManager.getInstance();
  wsManager.connect();
  return {
    onmessage: (callback: (data: any) => void) => wsManager.addListener(callback),
    close: () => {},  // No-op since connection is managed by the singleton
  };
};

export default api 