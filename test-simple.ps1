$headers = @{'Content-Type' = 'application/json'}
$body = '{"email":"test@example.com","first_name":"Test","last_name":"User"}'

try {
    $response = Invoke-WebRequest -Uri 'http://localhost:8000/api/auth/register/' -Method POST -Headers $headers -Body $body
    Write-Host "Response:" $response.Content
} catch {
    Write-Host "Error:" $_.Exception.Message
}
