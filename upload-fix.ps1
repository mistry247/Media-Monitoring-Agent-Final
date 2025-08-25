# PowerShell script to upload the JavaScript fix
$serverIP = "138.68.143.170"
$username = "root"
$localFile = "static/app.js"
$remotePath = "/opt/media-monitoring-agent/static/app.js"

Write-Host "Uploading JavaScript fix to server..." -ForegroundColor Green

# Try using SCP if available
try {
    scp $localFile "${username}@${serverIP}:${remotePath}"
    Write-Host "File uploaded successfully!" -ForegroundColor Green
    
    # Restart the server
    Write-Host "Restarting server..." -ForegroundColor Yellow
    ssh "${username}@${serverIP}" "cd /opt/media-monitoring-agent && pkill -f 'python main.py' && nohup python main.py > app.log 2>&1 &"
    Write-Host "Server restarted!" -ForegroundColor Green
    
    Write-Host "`nPlease test the application at: http://138.68.143.170:8000" -ForegroundColor Cyan
    Write-Host "The pending articles table should now display properly." -ForegroundColor Cyan
}
catch {
    Write-Host "SCP not available. Please use one of these alternatives:" -ForegroundColor Red
    Write-Host "1. Install Git for Windows (includes SSH/SCP)" -ForegroundColor Yellow
    Write-Host "2. Use WinSCP or FileZilla to upload static/app.js" -ForegroundColor Yellow
    Write-Host "3. Copy the file content and paste it directly on the server" -ForegroundColor Yellow
}