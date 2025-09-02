param(
  [Parameter(Mandatory=$false)][string]$IssueKey
)
$ErrorActionPreference = 'Stop'

if (-not $IssueKey) {
  $IssueKey = Read-Host 'Введите ключ задачи (например, PROJECT-123)'
}

if ($IssueKey -notmatch '^[A-Z]+-[0-9]+$') {
  Write-Error 'Неверный формат ключа Jira. Ожидается PROJECT-123'
}

# Создаём ветку с префиксом feature/
$branch = "feature/$IssueKey-$(Get-Date -Format 'yyyyMMdd-HHmm')"

Write-Host "==> Создаю ветку $branch" -ForegroundColor Cyan
& git checkout -b $branch

Write-Host '==> Готово. Сделайте коммит вида:' -ForegroundColor Cyan
Write-Host "$($IssueKey): краткое описание"

