param(
  [Parameter(Mandatory=$true)][string]$Project,
  [Parameter(Mandatory=$true)][string]$Jql,
  [Parameter(Mandatory=$false)][string]$PlanFile = 'docs/jira-plan.json',
  [Parameter(Mandatory=$false)][switch]$SetDescriptions,
  [Parameter(Mandatory=$false)][switch]$DryRun,
  [Parameter(Mandatory=$false)][string]$Email,
  [Parameter(Mandatory=$false)][string]$Token,
  [Parameter(Mandatory=$false)][string]$BaseUrl
)

$ErrorActionPreference = 'Stop'
if (-not $Email)   { $Email   = if ($env:JIRA_EMAIL) { $env:JIRA_EMAIL } else { $env:JIRA_USER_EMAIL } }
if (-not $Token)   { $Token   = if ($env:JIRA_TOKEN) { $env:JIRA_TOKEN } else { $env:JIRA_API_TOKEN } }
if (-not $BaseUrl) { $BaseUrl = if ($env:JIRA_BASE_URL) { $env:JIRA_BASE_URL } elseif ($env:JIRA_SITE) { "https://$($env:JIRA_SITE)" } else { '' } }
if (-not $Email -or -not $Token -or -not $BaseUrl) { Write-Error 'Missing Jira credentials.' }

$pair    = "$Email`:$Token"
$basic   = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($pair))
$headers = @{ Authorization = "Basic $basic"; Accept = 'application/json'; 'Content-Type' = 'application/json; charset=utf-8' }

if (-not (Test-Path $PlanFile)) { Write-Error "Plan file not found: $PlanFile" }
$plan = (Get-Content -Raw -Encoding utf8 -Path $PlanFile) | ConvertFrom-Json

$encodedJql = [System.Uri]::EscapeDataString($Jql)
$searchUrl = "$BaseUrl/rest/api/3/search?jql=$encodedJql&maxResults=50&fields=key,summary"
$resp = Invoke-RestMethod -Method Get -Uri $searchUrl -Headers $headers
$issues = @(); if ($resp.issues){ $issues=$resp.issues }

Write-Host ("Found issues: {0}" -f $issues.Count) -ForegroundColor Cyan

for ($idx=0; $idx -lt [Math]::Min($issues.Count, $plan.Count); $idx++) {
  $issue = $issues[$idx]
  $target = $plan[$idx]
  $newSummary = [string]$target.Summary
  $newDesc    = [string]$target.Description

  $adf = @{
    type    = 'doc'
    version = 1
    content = @(@{
      type    = 'paragraph'
      content = if ($newDesc) { @(@{ type='text'; text=$newDesc }) } else { @() }
    })
  }

  $fields = @{ summary = $newSummary }
  if ($SetDescriptions) { $fields.description = $adf }
  $payload = @{ fields = $fields } | ConvertTo-Json -Depth 12
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)

  if ($DryRun) {
    Write-Host ("DRYRUN: {0} -> '{1}'" -f $issue.key, $newSummary)
  } else {
    $url = "$BaseUrl/rest/api/3/issue/$($issue.key)"
    try {
      Invoke-RestMethod -Method Put -Uri $url -Headers $headers -Body $bytes
      Write-Host ("UPDATED: {0}" -f $issue.key) -ForegroundColor Green
    } catch {
      $we = $_.Exception
      $respBody = ''
      if ($we.Response -and $we.Response.GetResponseStream()) {
        $reader = New-Object System.IO.StreamReader($we.Response.GetResponseStream())
        $respBody = $reader.ReadToEnd()
      }
      Write-Host ("ERROR updating: {0}" -f $issue.key) -ForegroundColor Red
      if ($respBody) { Write-Host $respBody } else { Write-Host $_ }
      throw
    }
  }
}


