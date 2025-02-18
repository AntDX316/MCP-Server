# Activate virtual environment if it exists
if (Test-Path ".venv") {
    .\.venv\Scripts\Activate.ps1
}

# Install requirements if needed
pip install -r requirements.txt

# Run the MCP server
python mcp_server.py 