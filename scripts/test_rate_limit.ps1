Write-Host "`n=== Testing /api/auth/login Rate Limiting (Limit: 5 req/s) ===" -ForegroundColor Cyan
$loginResults = @()
for ($i = 1; $i -le 15; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost/api/auth/login" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"email":"test@example.com","password":"test"}' -UseBasicParsing -TimeoutSec 3
        $loginResults += $resp.StatusCode
    } catch {
        if ($_.Exception.Response) {
            $loginResults += $_.Exception.Response.StatusCode.value__
        } else {
            $loginResults += "Err"
        }
    }
}
Write-Host "Results for 15 rapid /api/auth/login requests:"
Write-Host ($loginResults -join " ")
$throttledLogin = $loginResults -contains 429
Write-Host "Login HTTP 429 triggered: $throttledLogin" -ForegroundColor $(if ($throttledLogin) { "Green" } else { "Yellow" })

Write-Host "`n=== Testing /api/recommendations Rate Limiting (Limit: 20 req/s) ===" -ForegroundColor Cyan
$recResults = @()
for ($i = 1; $i -le 40; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost/api/recommendations/cold-start?limit=1" -Method GET -UseBasicParsing -TimeoutSec 3
        $recResults += $resp.StatusCode
    } catch {
        if ($_.Exception.Response) {
            $recResults += $_.Exception.Response.StatusCode.value__
        } else {
            $recResults += "Err"
        }
    }
}
Write-Host "Results for 40 rapid /api/recommendations requests:"
Write-Host ($recResults -join " ")
$throttledRec = $recResults -contains 429
Write-Host "Recommendations HTTP 429 triggered: $throttledRec" -ForegroundColor $(if ($throttledRec) { "Green" } else { "Yellow" })
