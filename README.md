# MCP Server with Web UI

The MCP Server with Web UI is a powerful and user-friendly ModelContextProtocol server implementation that combines robust backend functionality with an elegant web interface.

It features real-time client monitoring, WebSocket-based communication, and comprehensive configuration options through an intuitive dark-mode UI.

The server supports SSL encryption, client connection management, and provides detailed metrics and charts for monitoring system performance.

Built with Python and React, it's easily deployable via Docker for production use or can be run directly for development, making it ideal for both testing and production environments.

## Features

- Full ModelContextProtocol implementation
- Web-based configuration interface
- Real-time client monitoring
- Client connection management with manual disconnection capability
- WebSocket-based communication
- Configurable server settings
- SSL support
- Dark mode UI
- Real-time metrics and charts
- Auto-reload during development

## Requirements

- Python 3.8+
- Node.js 14+ (for frontend development only)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd MCP-Server
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. The frontend is pre-built and ready to use. No additional setup required!

## Running the Server

### Quick Start
Simply run:
```bash
python server.py
```

This will:
- Start the backend server with auto-reload enabled
- Serve the pre-built frontend
- Make everything available at http://localhost:8000

The server features auto-reload, so any changes to Python files will automatically restart the server.

### Development Notes

- **Backend Changes**: The server will automatically reload when you modify any Python files
- **Frontend Changes**: If you need to modify the frontend:
  1. Make changes in the `frontend/src` directory
  2. Run `cd frontend && npm install` (first time only)
  3. Run `npm run build` to rebuild the frontend
  4. The server will serve the new build automatically

You don't need to run `npm start` for normal usage as the frontend is pre-built and served by the Python server.

### Testing the Connection

Run the test client in a separate terminal:
```bash
python test_client.py
```

## Configuration

The server can be configured through:
1. Web UI (recommended):
   - Access http://localhost:8000
   - Navigate to Settings
   - Modify server and MCP settings
   - Save changes

2. Direct configuration file:
   - Edit `config.json` in the root directory
   - Server will auto-reload to apply changes

### Default Configuration

The server starts with these default settings:
- Host: 0.0.0.0
- Port: 8000
- Max Connections: 100
- Protocol Version: 1.0.0
- Max Context Length: 4096
- Debug Mode: False
- SSL: Disabled

## API Documentation

### Client Management

#### List Connected Clients
```
GET /api/clients
```
Returns a list of all currently connected clients with their connection details.

#### Disconnect Client
```
DELETE /api/clients/{client_id}
```
Forcefully disconnects a specific client from the server. The client_id is the UUID assigned when the client first connects.

### Server Status

#### Get Server Status
```
GET /api/status
```
Returns current server status including:
- Active client count
- Server uptime
- Version information
- Connection history

Query Parameters:
- `hours` (float, default: 1): Number of hours of connection history to retrieve

### Settings Management

#### Update Settings
```
POST /api/settings
```
Updates server and MCP configuration settings. Requires a JSON body with server and MCP configuration parameters.

### WebSocket Endpoint

#### Client Connection
```
WS /ws/{client_id}
```
WebSocket endpoint for client connections. Supports:
- Real-time communication
- Ping/pong heartbeat
- Automatic disconnection on timeout

## Development

### Frontend Development

1. Start the backend server:
   ```bash
   python server.py
   ```

2. Start frontend development server:
   ```bash
   cd frontend
   npm start
   ```

3. Make changes to files in `frontend/src/`
4. Build for production:
   ```bash
   npm run build
   ```

### Backend Development

1. Main server file: `server.py`
2. Configuration handling: `config.py`
3. Test client: `test_client.py`

## Security Considerations

1. In production:
   - Configure CORS settings in `server.py`
   - Enable SSL
   - Set appropriate access controls
   - Use strong authentication
   - Limit max connections

2. SSL Configuration:
   - Enable SSL in settings
   - Provide valid certificate paths
   - Use proper certificate validation

## Troubleshooting

1. "Directory 'frontend/build' does not exist":
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

2. Port 8000 already in use:
   - Change port in settings
   - Or stop existing process using port 8000

3. npm install fails:
   ```bash
   cd frontend
   npm cache clean --force
   rm -rf node_modules
   npm install
   ```

4. WebSocket connection fails:
   - Check server is running
   - Verify port settings
   - Check firewall settings
   - Ensure proper SSL configuration if enabled

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 