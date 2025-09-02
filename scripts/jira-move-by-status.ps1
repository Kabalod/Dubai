param(
  [Parameter(Mandatory=$false)][string]$Project = 'KAN',
  [Parameter(Mandatory=$false)][string]$Jql,
  [Parameter(Mandatory=$true)][string]$TargetStatus,
  [Parameter(Mandatory=$false)][switch]$DryRun,
  [Parameter(Mandatory=$false)][string]$Email,
  [Parameter(Mandatory=$false)][string]$Token,
  [Parameter(Mandatory=$false)][string]$Site
)

$ErrorActionPreference = 'Stop'

if (-not $Email) { $Email = if ($env:JIRA_EMAIL) { $env:JIRA_EMAIL } else { $env:JIRA_USER_EMAIL } }
if (-not $Token) { $Token = $env:JIRA_TOKEN; if (-not $Token) { $Token = $env:JIRA_API_TOKEN } }
if (-not $Site)  { $Site  = if ($env:JIRA_SITE) { $env:JIRA_SITE } elseif ($env:JIRA_BASE_URL) { ($env:JIRA_BASE_URL -replace '^https?://','') } else { '' } }
if (-not $Email -or -not $Token -or -not $Site) { Write-Error 'Missing Jira credentials. Set JIRA_EMAIL/JIRA_TOKEN/JIRA_SITE (or JIRA_API_TOKEN/JIRA_BASE_URL) or pass -Email/-Token/-Site.' }

if (-not $Jql) {
  if (-not $Project) { Write-Error 'Provide -Project or -Jql' }
  $Jql = "project = $Project ORDER BY updated DESC"
}

$pair = "$Email`:$Token"
$basic = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($pair))
$headers = @{ Authorization = "Basic $basic"; Accept = 'application/json'; 'Content-Type' = 'application/json' }

$baseUrl = if ($Site -match '^https?://') { $Site } else { "https://$Site" }
$encodedJql = [System.Uri]::EscapeDataString($Jql)
$fields = 'key,summary,status'
$max = 200
$searchUrl = "$baseUrl/rest/api/3/search?jql=$encodedJql&maxResults=$max&fields=$fields"

Write-Host "==> Search issues by JQL: $Jql" -ForegroundColor Cyan
$resp = Invoke-RestMethod -Method Get -Uri $searchUrl -Headers $headers
$issues = @()
if ($resp.issues) { $issues = $resp.issues }
Write-Host ("Found issues: {0}" -f $issues.Count) -ForegroundColor Yellow

$mappable = 0
$moved = 0
$report = @()

foreach ($i in $issues) {
  $key = $i.key
  $summary = $i.fields.summary
  $current = $i.fields.status.name

  $transUrl = "$baseUrl/rest/api/3/issue/$key/transitions"
  $tresp = Invoke-RestMethod -Method Get -Uri $transUrl -Headers $headers
  $transitions = @()
  if ($tresp.transitions) { $transitions = $tresp.transitions }

  $target = $transitions | Where-Object { $_.to.name -and ($_.to.name -ieq $TargetStatus) } | Select-Object -First 1

  if ($null -ne $target) {
    $mappable++
    if ($DryRun) {
      $report += "DRYRUN: $key [$current -> $($target.to.name)] - $summary"
    } else {
      $body = @{ transition = @{ id = $target.id } } | ConvertTo-Json -Depth 5
      Invoke-RestMethod -Method Post -Uri $transUrl -Headers $headers -Body $body | Out-Null
      $moved++
      $report += "MOVED:  $key [$current -> $($target.to.name)] - $summary"
    }
  } else {
    $available = ($transitions | ForEach-Object { $_.to.name }) -join ', '
    $report += "SKIP:  $key [$current] - no transition to $TargetStatus (available: $available) - $summary"
  }
}

Write-Host "==> Summary:" -ForegroundColor Cyan
Write-Host ("Transitionable: {0}" -f $mappable)
if (-not $DryRun) { Write-Host ("Moved: {0}" -f $moved) }

$out = $report -join "`n"
Write-Output $out


