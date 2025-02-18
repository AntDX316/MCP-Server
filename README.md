# MCP Server with Web UI

A ModelContextProtocol server implementation with an easy-to-use web interface for configuration and monitoring.

## Features

- Full ModelContextProtocol implementation
- Web-based configuration interface
- Real-time client monitoring
- WebSocket-based communication
- Configurable server settings
- SSL support
- Client connection management
- Dark mode UI
- Real-time metrics and charts

## Requirements

- Python 3.8+
- Node.js 14+ (for frontend development)
- npm (usually comes with Node.js)

## Installation & Setup

### Option 1: Direct Installation (Development)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd MCP-Server
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

### Option 2: Docker Installation (Recommended for Production)

1. Make sure Docker and Docker Compose are installed
2. Clone the repository
3. Run:
   ```bash
   docker-compose up --build
   ```

## Running the Server

### Development Mode

1. Start the backend server:
   ```bash
   python server.py
   ```
   The server will run on http://localhost:8000

2. (Optional) For frontend development with hot reloading:
   ```bash
   cd frontend
   npm start
   ```
   The development server will run on http://localhost:3000

### Production Mode

1. Using Docker (recommended):
   ```bash
   docker-compose up --build
   ```

2. Direct running:
   ```bash
   python server.py
   ```

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
   - Restart the server to apply changes

3. Environment variables:
   - Set environment variables before starting the server
   - Available in Docker using the `environment` section in `docker-compose.yml`

### Default Configuration

The server starts with these default settings:
- Host: 0.0.0.0
- Port: 8000
- Max Connections: 100
- Protocol Version: 1.0.0
- Max Context Length: 4096
- Debug Mode: False
- SSL: Disabled

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