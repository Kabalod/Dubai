    # Проверка наличия winget (менеджера пакетов Windows)
    try { winget --version | Out-Null; $hasWinget = $true } catch { $hasWinget = $false }

    if ($hasWinget) {
        Write-Host "Winget найден. Устанавливаю cloudflared..."
        winget install --id Cloudflare.cloudflared -e --source winget --silent
    } else {
        Write-Host "Winget не найден. Скачиваю и устанавливаю cloudflared через MSI..."
        $msi = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.msi"
        $dst = "$env:TEMP\cloudflared.msi"
        Invoke-WebRequest -Uri $msi -OutFile $dst
        Start-Process msiexec.exe -Wait -ArgumentList "/i `"$dst`" /qn"
        Write-Host "cloudflared установлен."
    }