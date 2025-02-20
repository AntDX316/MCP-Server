# MCP Server for Cursor

[![smithery badge](https://smithery.ai/badge/@AntDX316/MCP-Server)](https://smithery.ai/server/@AntDX316/MCP-Server)

A Model Context Protocol (MCP) server implementation for Cursor IDE integration, providing a modern web dashboard and tools through SSE (Server-Sent Events) and WebSocket connections.

## Features

- Real-time connection monitoring with WebSocket support
- Modern web dashboard for server management
- SSE-based communication with Cursor IDE
- Built-in test tool for verifying connectivity
- Google Drive integration for file management
- Extensible architecture for adding new tools
- Connection history visualization
- Client management interface
- Service configuration UI
- Customizable server settings

## Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- npm (Node.js package manager)
- pip (Python package manager)
- Cursor IDE

## Installation

### Installing via Smithery

To install MCP Server for Cursor for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@AntDX316/MCP-Server):

```bash
npx -y @smithery/cli install @AntDX316/MCP-Server --client claude
```

### Manual Installation
1. Clone the repository:
```bash
git clone <repository-url>
cd MCP-Server
```

2. Install dependencies:
```bash
# Install all dependencies (both backend and frontend)
npm run install-all

# Or install separately:
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

## Development

Start the development servers:
```bash
# Start both backend and frontend in development mode
npm run dev   # This will start both servers concurrently
```

The servers will start at:
- Backend: `http://localhost:8765`
- Frontend: `http://localhost:3000` (or `3001` if port 3000 is in use)

You can also start the servers separately:
```bash
# Backend (in one terminal)
python mcp_server.py

# Frontend (in another terminal)
cd frontend
npm run dev
```

The development servers provide:
- Hot reloading for frontend changes
- Automatic proxy of API requests to the backend
- WebSocket connection handling
- Concurrent backend and frontend development

If you're running other applications that use port 3000, the frontend will automatically try port 3001 and increment until it finds an available port. The actual URL will be displayed in the terminal when you run `npm run dev`.

### Project Structure
```
MCP-Server/
├── frontend/                # Frontend application
│   ├── src/                # Source code
│   │   ├── api/           # API clients
│   │   ├── pages/         # React components
│   │   └── main.tsx       # Entry point
│   ├── package.json       # Frontend dependencies
│   └── vite.config.ts     # Vite configuration
├── mcp_server.py          # Main server implementation
├── services.py            # Service management
├── test_client.py         # Test client implementation
├── requirements.txt       # Python dependencies
├── package.json           # Root package.json
└── services_config.json   # Service configurations
```

### Available Endpoints

#### HTTP Endpoints
- `/api/status` - Get server status
- `/api/connections/history` - Get connection history
- `/api/clients` - Get active clients
- `/api/services/{service_id}` - Service configuration
- `/api/settings` - Server settings

#### WebSocket Endpoint
- `/ws/{client_id}` - Real-time updates and ping/pong

#### SSE Endpoint
- `/sse` - Server-Sent Events for Cursor IDE

### Tool Endpoints
- `/invoke/test` - Test tool
- `/invoke/google_drive` - Google Drive operations

## Production Deployment

Build and start the production server:
```bash
# Build frontend and start production server
npm run prod

# Or build frontend separately:
npm run build
python mcp_server.py
```

## Configuration

### Initial Setup
1. Copy the template configuration:
```bash
cp services_config.template.json services_config.json
```

2. Update `services_config.json` with your service credentials:
   - For Google Drive:
     - Create a project in Google Cloud Console
     - Enable the Google Drive API
     - Create OAuth 2.0 credentials
     - Add your `client_id` and `client_secret`

### Server Settings
Configure server settings through the web dashboard:
- Debug mode
- SSL settings
- Connection limits
- Ping timeout
- Protocol settings

## Testing

Test the server using the provided test client:
```bash
python test_client.py
```

The test client will:
- Connect to both SSE and WebSocket endpoints
- Send periodic pings
- Test available tools
- Monitor connection status

## Troubleshooting

1. **Connection Issues**
   - Check both backend and frontend logs
   - Verify the WebSocket connection in browser DevTools
   - Ensure the proxy settings in `vite.config.ts` are correct
   - Check for port conflicts

2. **Frontend Issues**
   - Clear browser cache
   - Check browser console for errors
   - Verify Node.js and npm versions
   - Check for TypeScript compilation errors

3. **Backend Issues**
   - Check `mcp_server.log` for errors
   - Verify Python dependencies are installed
   - Check port availability
   - Ensure service configurations are valid

## Security Notes

- The server accepts all origins (CORS `*`) in development
- WebSocket connections use client IDs for basic identification
- Service credentials are stored in `services_config.json`
- Environment variables should be used for sensitive data in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

[Add your license information here] 