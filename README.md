# MCP Server for Cursor

A Model Context Protocol (MCP) server implementation for Cursor IDE integration, providing tools and services through SSE (Server-Sent Events).

## Features

- SSE-based communication with Cursor IDE
- Built-in test tool for verifying connectivity
- Google Drive integration for file management
- Extensible architecture for adding new tools

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Cursor IDE

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

## Running the Server

Start the MCP server:
```bash
python mcp_server.py
```

The server will start on `http://localhost:8765` with the following endpoints:
- SSE endpoint: `http://localhost:8765/sse`
- Tool invocation: `http://localhost:8765/invoke/{tool_name}`

## Configuring Cursor IDE

1. Open Cursor IDE
2. Click on the "MCP Servers" section in the sidebar
3. Click "+ Add new MCP server"
4. Configure the server:
   - Name: `MCP-Server`
   - Type: `sse`
   - Server URL: `http://localhost:8765/sse`
5. Click "Save"

## Available Tools

### Test Tool
A simple tool to verify the MCP connection is working.
- Name: `test`
- Parameters:
  - `message`: String to echo back

### Google Drive Tool
Manage files in Google Drive.
- Name: `google_drive`
- Operations:
  - `list`: List files in a folder
  - `upload`: Upload a new file
  - `create_folder`: Create a new folder
  - `delete`: Delete a file or folder
- Parameters vary by operation (see schema in code)

## Development

### Project Structure
```
MCP-Server/
├── mcp_server.py      # Main server implementation
├── services.py        # Service management
├── config.py          # Configuration handling
├── database.py        # Database operations
├── requirements.txt   # Python dependencies
└── service_handlers/  # Tool implementations
```

### Adding New Tools

1. Create a new handler in `service_handlers/`
2. Add tool configuration to `TOOLS` in `mcp_server.py`
3. Implement the tool's logic in the `/invoke/{tool_name}` endpoint

### Configuration

Server settings can be modified in:
- `config.json`: General server configuration
- `services_config.json`: Tool-specific settings

## Configuration

### Initial Setup
1. Copy the template configuration:
```bash
cp services_config.template.json services_config.json
```

2. Update `services_config.json` with your credentials:
   - For Google Drive:
     - Create a project in Google Cloud Console
     - Enable the Google Drive API
     - Create OAuth 2.0 credentials
     - Add your `client_id` and `client_secret`

### Security Notes
- Never commit `services_config.json` to version control
- Keep your API credentials private
- The template file (`services_config.template.json`) is safe to commit
- Use environment variables for production deployments

## Troubleshooting

1. **Connection Issues**
   - Ensure the server is running (`python mcp_server.py`)
   - Verify the URL in Cursor is `http://localhost:8765/sse`
   - Check the server logs for connection attempts

2. **No Tools Available**
   - Verify tools are enabled in `services_config.json`
   - Restart the server after configuration changes
   - Check the server logs for tool initialization

3. **Port Conflicts**
   - If port 8765 is in use, modify the port in `config.json`
   - Kill any existing Python processes if needed
   - Update the Cursor connection URL accordingly

## Logs

Server logs are written to:
- Console output
- `mcp_server.log` file

## Security Notes

- The server accepts all origins (CORS `*`)
- No authentication required for local development
- Google Drive integration requires valid credentials

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

[Add your license information here] 