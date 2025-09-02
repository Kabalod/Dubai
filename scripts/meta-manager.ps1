<#
.SYNOPSIS
    Управляет несколькими Git-репозиториями в проекте.
.DESCRIPTION
    Этот скрипт-оркестратор читает конфигурацию из `repos.json` и выполняет пакетные Git-команды 
    (status, pull, push, exec) для каждого репозитория.
.PARAMETER Command
    Команда для выполнения:
    - status: Показать `git status -s`
    - pull: Выполнить `git pull`
    - push: Выполнить `git push`
    - exec: Выполнить произвольную команду, переданную в -Args
.PARAMETER Args
    Строка с командой для выполнения при использовании `exec`.
.EXAMPLE
    # Посмотреть статус всех репозиториев
    .\scripts\meta-manager.ps1 -Command status

    # Обновить все репозитории
    .\scripts\meta-manager.ps1 -Command pull

    # Выполнить `npm install` во всех репозиториях (где это применимо)
    .\scripts\meta-manager.ps1 -Command exec -Args "npm install"
#>
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("status", "pull", "push", "exec")]
    [string]$Command,

    [Parameter(Mandatory=$false)]
    [string]$Args
)

# --- Начало скрипта ---

$configFile = "repos.json"
if (-not (Test-Path $configFile)) {
    Write-Host "ОШИБКА: Файл конфигурации '$configFile' не найден в корне проекта." -ForegroundColor Red
    exit 1
}

try {
    $config = Get-Content $configFile | ConvertFrom-Json
    $repos = $config.repositories
}
catch {
    Write-Host "ОШИБКА: Не удалось прочитать или разобрать '$configFile'." -ForegroundColor Red
    exit 1
}

foreach ($repo in $repos) {
    Write-Host "--- [ $($repo.name) ] ---" -ForegroundColor Cyan
    
    if (-not (Test-Path $repo.path)) {
        Write-Host "ПРЕДУПРЕЖДЕНИЕ: Директория '$($repo.path)' не найдена. Пропускаем." -ForegroundColor Yellow
        continue
    }

    Push-Location $repo.path
    
    # Проверяем, что это Git-репозиторий
    $isGitRepo = git rev-parse --is-inside-work-tree 2>$null
    if ($isGitRepo -ne "true") {
        Write-Host "ПРЕДУПРЕЖДЕНИЕ: '$($repo.path)' не является Git-репозиторием. Пропускаем." -ForegroundColor Yellow
        Pop-Location
        continue
    }

    try {
        switch ($Command) {
            "status" { 
                git status -s 
            }
            "pull"   { 
                $branch = $repo.default_branch | "main"
                git pull origin $branch --rebase 
            }
            "push"   { 
                git push 
            }
            "exec"   {
                if (-not ([string]::IsNullOrWhiteSpace($Args))) {
                    Write-Host "Выполнение: $Args" -ForegroundColor Green
                    Invoke-Expression $Args
                } else {
                    Write-Host "ОШИБКА: Для команды 'exec' необходимо указать аргументы в -Args." -ForegroundColor Red
                }
            }
        }
    }
    catch {
        Write-Host "ОШИБКА при выполнении команды '$Command' в репозитории '$($repo.name)'." -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
    
    Pop-Location
    Write-Host "" # Пустая строка для читаемости
}

Write-Host "--- Готово! ---" -ForegroundColor Green
