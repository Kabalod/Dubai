<#
.SYNOPSIS
    Выполняет очистку проекта от устаревших скриптов и конфигураций.
.DESCRIPTION
    Этот скрипт автоматизирует удаление ненужных файлов и реструктуризацию,
    чтобы привести проект в соответствие с новой системой управления через Taskfile и Nx.
#>

$VerbosePreference = "Continue"

Write-Host "--- Начало очистки проекта ---" -ForegroundColor Cyan

# --- Файлы для удаления ---
$filesToDelete = @(
    "scripts/simple-manager.ps1",
    "scripts/simple-reorganize.ps1",
    "check-all-ports.ps1",
    "check-ports.ps1",
    "start-docker-services.ps1",
    "start-services.ps1",
    "start-docker-services.bat",
    "start-all-services.bat",
    "start-react.bat",
    "apps/DXB-frontend-develop/start.bat",
    "apps/realty-main/quick_start.sh",
    "apps/realty-main/quick_start.bat",
    "docs/lint-docs.sh",
    "scripts/reorganize-project.sh",
    "apps/realty-main/Dockerfile.simple",
    "apps/realty-main/deploy/Dockerfile.binary"
)

foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Verbose "Удален файл: $file"
    } else {
        Write-Warning "Файл не найден (возможно, уже удален): $file"
    }
}

# --- Файлы для переноса ---
$fileToMove = @{
    Source = "apps/realty-main/auto_import.sh"
    DestinationDir = "apps/realty-main/scripts"
    DestinationFile = "apps/realty-main/scripts/auto_import.sh"
}

if (Test-Path $fileToMove.Source) {
    if (-not (Test-Path $fileToMove.DestinationDir)) {
        New-Item -ItemType Directory -Path $fileToMove.DestinationDir | Out-Null
    }
    Move-Item -Path $fileToMove.Source -Destination $fileToMove.DestinationFile -Force
    Write-Verbose "Файл $($fileToMove.Source) перенесен в $($fileToMove.DestinationFile)"
} else {
    Write-Warning "Файл для переноса не найден: $($fileToMove.Source)"
}

Write-Host "--- Очистка проекта завершена ---" -ForegroundColor Green
