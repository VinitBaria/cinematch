param (
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "reload", "status")]
    [string]$Action = "status"
)

$NginxDir = "C:\Users\vinit baria\OneDrive\Desktop\MLops_new\nginx\nginx-1.30.6"
$NginxExe = Join-Path $NginxDir "nginx.exe"

switch ($Action) {
    "start" {
        $running = Get-Process nginx -ErrorAction SilentlyContinue
        if ($running) {
            Write-Host "Nginx is already running (PID: $($running[0].Id))" -ForegroundColor Yellow
        } else {
            Start-Process -FilePath $NginxExe -WorkingDirectory $NginxDir
            Write-Host "✅ Nginx started on http://localhost" -ForegroundColor Green
        }
    }
    "stop" {
        Start-Process -FilePath $NginxExe -ArgumentList "-s stop" -WorkingDirectory $NginxDir -Wait
        Write-Host "🛑 Nginx stopped." -ForegroundColor Red
    }
    "reload" {
        Start-Process -FilePath $NginxExe -ArgumentList "-s reload" -WorkingDirectory $NginxDir -Wait
        Write-Host "🔄 Nginx configuration reloaded." -ForegroundColor Cyan
    }
    "status" {
        $running = Get-Process nginx -ErrorAction SilentlyContinue
        if ($running) {
            Write-Host "🟢 Nginx is running (PID: $($running[0].Id)) on port 80" -ForegroundColor Green
            Write-Host "   - Frontend UI: http://localhost/" -ForegroundColor Gray
            Write-Host "   - API Gateway: http://localhost/api/" -ForegroundColor Gray
            Write-Host "   - API Docs:    http://localhost/docs" -ForegroundColor Gray
        } else {
            Write-Host "⚪ Nginx is stopped." -ForegroundColor Yellow
        }
    }
}
