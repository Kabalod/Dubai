param()
$ErrorActionPreference = 'Stop'

Write-Host '==> Backend: compile & check deps' -ForegroundColor Cyan
Push-Location 'apps/realty-main'
python -m pip install --upgrade pip pip-tools | Out-Null
python -m piptools compile -q -o requirements.compiled.txt requirements.in
python -m pip install --no-deps --require-hashes -r requirements.compiled.txt
python -m pip check
Pop-Location

Write-Host '==> Frontend: install & build' -ForegroundColor Cyan
Push-Location 'apps/DXB-frontend-develop'
if (-not (Get-Command yarn -ErrorAction SilentlyContinue)) {
  Write-Warning 'yarn не найден. Установите Node.js 22+ и включите corepack (npm i -g corepack; corepack enable).'
} else {
  yarn install --immutable
  yarn build
}
Pop-Location

Write-Host '==> Done'

