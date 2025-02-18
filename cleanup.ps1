# Kill any Python processes
taskkill /F /IM python.exe 2>$null

# Kill processes using port 8765 (MCP server)
$mcp = netstat -ano | Select-String ":8765.*LISTENING"
if ($mcp) {
    $pid = $mcp.Line.Split()[-1]
    taskkill /F /PID $pid 2>$null
}

# Kill processes using port 8000 (backend server)
$backend = netstat -ano | Select-String ":8000.*LISTENING"
if ($backend) {
    $pid = $backend.Line.Split()[-1]
    taskkill /F /PID $pid 2>$null
}

# Kill processes using port 3000 (frontend)
$frontend = netstat -ano | Select-String ":3000.*LISTENING"
if ($frontend) {
    $pid = $frontend.Line.Split()[-1]
    taskkill /F /PID $pid 2>$null
}

Write-Host "Cleanup complete!" 