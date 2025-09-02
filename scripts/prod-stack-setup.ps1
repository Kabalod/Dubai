param(
    [switch]$ForceRebuild
)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path) | Out-Null
Set-Location ..

function Test-Port {
    param([Parameter(Mandatory)][int]$Port)
    try {
        return (Test-NetConnection -ComputerName 'localhost' -Port $Port -InformationLevel Quiet)
    } catch {
        return $false
    }
}

function Get-PortsPlan {
    $desired = [ordered]@{
        POSTGRES_PORT   = 5490
        REDIS_PORT      = 6379
        PARSER_PORT     = 8002
        API_PORT        = 8090
        FRONTEND_PORT   = 3000
        PROMETHEUS_PORT = 9090
        GRAFANA_PORT    = 3003
    }

    $alts = @{
        POSTGRES_PORT   = 5590
        REDIS_PORT      = 6390
        PARSER_PORT     = 8190
        API_PORT        = 8190
        FRONTEND_PORT   = 3090
        PROMETHEUS_PORT = 9190
        GRAFANA_PORT    = 3190
    }

    $resolved = @{}
    foreach ($k in $desired.Keys) {
        $v = [int]$desired[$k]
        if (-not (Test-Port -Port $v)) {
            $resolved[$k] = $v
        } else {
            $alt = $alts[$k]
            if ($alt -and (-not (Test-Port -Port $alt))) {
                Write-Host "[PORT] $k busy on $v, using $alt" -ForegroundColor Yellow
                $resolved[$k] = [int]$alt
            } else {
                $resolved[$k] = $v
            }
        }
    }
    return $resolved
}

function New-Rand {
    param([int]$Length = 24)
    $chars = (48..57 + 65..90 + 97..122) | ForEach-Object { [char]$_ }
    -join (1..$Length | ForEach-Object { $chars | Get-Random })
}

function Write-EnvFiles {
    param([hashtable]$Ports)
    $envLines = @(
        "POSTGRES_PORT=$($Ports.POSTGRES_PORT)",
        "API_PORT=$($Ports.API_PORT)",
        "PARSER_PORT=$($Ports.PARSER_PORT)",
        "FRONTEND_PORT=$($Ports.FRONTEND_PORT)",
        "PROMETHEUS_PORT=$($Ports.PROMETHEUS_PORT)",
        "GRAFANA_PORT=$($Ports.GRAFANA_PORT)",
        "REDIS_PORT=$($Ports.REDIS_PORT)"
    )
    $envLines | Set-Content -Path '.env' -Encoding ascii

    $POSTGRES_PASSWORD = New-Rand -Length 24
    $API_SECRET_KEY = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((New-Rand -Length 48)))
    $PARSER_SECRET_KEY = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((New-Rand -Length 48)))
    $GRAFANA_PASSWORD = New-Rand -Length 20

    $envProdLines = $envLines + @(
        'POSTGRES_DB=dubai_realty',
        'POSTGRES_USER=postgres',
        "POSTGRES_PASSWORD=$POSTGRES_PASSWORD",
        "API_SECRET_KEY=$API_SECRET_KEY",
        "PARSER_SECRET_KEY=$PARSER_SECRET_KEY",
        "GRAFANA_PASSWORD=$GRAFANA_PASSWORD"
    )
    $envProdLines | Set-Content -Path '.env.prod' -Encoding ascii
}

function Ensure-SSL {
    if (-not (Test-Path 'ssl')) { New-Item -ItemType Directory -Path 'ssl' | Out-Null }
    $needCert = (-not (Test-Path 'ssl/cert.pem' -PathType Leaf)) -or (-not (Test-Path 'ssl/key.pem' -PathType Leaf))
    if (-not $needCert) { return }

    if (Get-Command openssl -ErrorAction SilentlyContinue) {
        & openssl req -x509 -newkey rsa:2048 -sha256 -days 365 -nodes -keyout ssl/key.pem -out ssl/cert.pem -subj '/CN=localhost'
        Write-Host 'Generated self-signed SSL via OpenSSL' -ForegroundColor Green
    } else {
        Write-Warning 'OpenSSL не найден. Пробую сгенерировать через Docker alpine...'
        $mount = (Join-Path (Get-Location) 'ssl') + ':/ssl'
        docker run --rm -v $mount alpine sh -c "apk add --no-cache openssl && openssl req -x509 -newkey rsa:2048 -sha256 -days 365 -nodes -keyout /ssl/key.pem -out /ssl/cert.pem -subj '/CN=localhost'" | Out-Null
        if ((Test-Path 'ssl/cert.pem') -and (Test-Path 'ssl/key.pem')) {
            Write-Host 'Generated self-signed SSL via Docker alpine' -ForegroundColor Green
        } else {
            Write-Warning 'Не удалось сгенерировать SSL. Добавьте ssl/cert.pem и ssl/key.pem вручную.'
        }
    }
}

function Compose-Up {
    param([switch]$Rebuild)
    $composeArgs = @('-f','docker-compose.prod.yml','--env-file','.env.prod')
    if ($Rebuild) {
        docker compose @composeArgs build | Write-Host
    }
    docker compose @composeArgs up -d | Write-Host
}

function Get-Status {
    param([string]$Url)
    try {
        return (Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 20).StatusCode
    } catch {
        if ($_.Exception.Response) { return $_.Exception.Response.StatusCode.value__ }
        return 0
    }
}

function Check-Health {
    param([hashtable]$Ports)
    $results = [ordered]@{}
    $results['NGINX http://localhost:80/health'] = Get-Status -Url 'http://localhost:80/health'
    $results["API http://localhost:$($Ports.API_PORT)/api/health/"] = Get-Status -Url "http://localhost:$($Ports.API_PORT)/api/health/"
    $results["Parser http://localhost:$($Ports.PARSER_PORT)/health/"] = Get-Status -Url "http://localhost:$($Ports.PARSER_PORT)/health/"
    $results["Frontend http://localhost:$($Ports.FRONTEND_PORT)/"] = Get-Status -Url "http://localhost:$($Ports.FRONTEND_PORT)/"

    $ok = $true
    foreach ($k in $results.Keys) {
        Write-Host ("{0} => {1}" -f $k, $results[$k])
        if ($results[$k] -ne 200) { $ok = $false }
    }
    return $ok
}

function Save-Artifacts {
    param([bool]$HealthOk)
    $ts = (Get-Date).ToString('yyyy-MM-dd_HH-mm-ss')
    $outDir = Join-Path 'backups' "prod-deploy-$ts"
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
    docker compose -f docker-compose.prod.yml ps | Out-File -FilePath (Join-Path $outDir 'docker-ps.txt') -Encoding utf8
    docker compose -f docker-compose.prod.yml logs --no-log-prefix --since=10m | Out-File -FilePath (Join-Path $outDir 'docker-logs.txt') -Encoding utf8
    "HealthOK=$HealthOk" | Out-File -FilePath (Join-Path $outDir 'health.txt') -Encoding utf8
}

Write-Host '==> Resolving ports and writing .env files'
$ports = Get-PortsPlan
Write-EnvFiles -Ports $ports

Write-Host '==> Ensuring SSL certs'
Ensure-SSL

Write-Host '==> Building and starting compose'
Compose-Up -Rebuild:$ForceRebuild.IsPresent

Write-Host '==> Checking health endpoints'
$healthOk = Check-Health -Ports $ports

Write-Host '==> Capturing artifacts'
Save-Artifacts -HealthOk:$healthOk

git add .env .env.prod ssl/cert.pem ssl/key.pem 2>$null
git commit -m "prod: sync env ports, ensure SSL, compose up (ForceRebuild=$($ForceRebuild.IsPresent))" 2>$null

if ($healthOk) {
    Write-Host 'All health checks passed.' -ForegroundColor Green
    exit 0
} else {
    Write-Host 'Some health checks failed. Inspect logs above.' -ForegroundColor Yellow
    exit 1
}


