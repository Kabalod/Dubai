param(
  [Parameter(Mandatory=$false)][string]$Project = 'KAN',
  [Parameter(Mandatory=$false)][object[]]$Plan,
  [Parameter(Mandatory=$false)][string]$PlanFile,
  [Parameter(Mandatory=$false)][string]$IssueType = 'Task',
  [Parameter(Mandatory=$false)][string]$IssueTypeId,
  [Parameter(Mandatory=$false)][switch]$NoDescription,
  [Parameter(Mandatory=$false)][switch]$UsePlainDescription,
  [Parameter(Mandatory=$false)][string]$AfterCreateStatus = 'BACKLOG',
  [Parameter(Mandatory=$false)][switch]$DryRun,
  [Parameter(Mandatory=$false)][string]$Email,
  [Parameter(Mandatory=$false)][string]$Token,
  [Parameter(Mandatory=$false)][string]$BaseUrl
)

$ErrorActionPreference = 'Stop'

if (-not $Email)   { $Email   = if ($env:JIRA_EMAIL) { $env:JIRA_EMAIL } else { $env:JIRA_USER_EMAIL } }
if (-not $Token)   { $Token   = if ($env:JIRA_TOKEN) { $env:JIRA_TOKEN } else { $env:JIRA_API_TOKEN } }
if (-not $BaseUrl) { $BaseUrl = if ($env:JIRA_BASE_URL) { $env:JIRA_BASE_URL } elseif ($env:JIRA_SITE) { "https://$($env:JIRA_SITE)" } else { '' } }
if (-not $Email -or -not $Token -or -not $BaseUrl) { Write-Error 'Missing Jira credentials. Set JIRA_USER_EMAIL/JIRA_API_TOKEN/JIRA_BASE_URL (or pass -Email/-Token/-BaseUrl).' }

$pair    = "$Email`:$Token"
$basic   = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($pair))
$headers = @{ Authorization = "Basic $basic"; Accept = 'application/json'; 'Content-Type' = 'application/json; charset=utf-8' }

# Resolve IssueTypeId via createmeta when not provided
function Resolve-IssueTypeId {
  param(
    [string]$ProjectKey,
    [string]$DesiredName
  )
  $metaUrl = "$BaseUrl/rest/api/3/issue/createmeta?projectKeys=$ProjectKey&expand=projects.issuetypes.fields"
  $meta = Invoke-RestMethod -Method Get -Uri $metaUrl -Headers $headers
  $proj = $meta.projects | Select-Object -First 1
  if (-not $proj) { return $null }
  $types = @($proj.issuetypes)
  if ($DesiredName) {
    $byName = $types | Where-Object { $_.name -ieq $DesiredName } | Select-Object -First 1
    if ($byName) { return $byName.id }
  }
  # Try common names
  foreach ($n in @('Task','Задача','Story','Bug')) {
    $m = $types | Where-Object { $_.name -ieq $n } | Select-Object -First 1
    if ($m) { return $m.id }
  }
  # Fallback to first
  return ($types | Select-Object -First 1).id
}

if (-not $IssueTypeId) {
  try { $IssueTypeId = Resolve-IssueTypeId -ProjectKey $Project -DesiredName $IssueType } catch { $IssueTypeId = $null }
}

if ($PlanFile) {
  if (-not (Test-Path $PlanFile)) { Write-Error "Plan file not found: $PlanFile" }
  $json = Get-Content -Raw -Path $PlanFile -Encoding utf8
  $Plan = $json | ConvertFrom-Json
}

if (-not $Plan -or $Plan.Count -eq 0) {
  $Plan = @(
    @{ Summary = 'Enable auto-run for MCP Jira in Cursor'; Description = 'Configure auto-run for Jira MCP tools in Cursor.' },
    @{ Summary = 'Define PR/commit-driven transitions'; Description = 'Automate issue transitions linked to Jira keys in commits/PRs.' },
    @{ Summary = 'Add Confluence MCP'; Description = 'Add Confluence MCP and base commands: get_page, search_pages, add_comment.' },
    @{ Summary = 'Fix check-ports.ps1'; Description = 'Fix quotes/braces and resolve syntax errors.' },
    @{ Summary = 'Extend MCP docs'; Description = 'Expand MCP-SETUP and mcp-jira.md with workflow and security.' },
    @{ Summary = 'Tune Jira workflow for Kanban'; Description = 'Verify statuses and transitions: BACKLOG, To Do, In Progress, Code Review, Testing.' },
    @{ Summary = 'Configure Jira webhooks'; Description = 'Notifications and CI integration for issue events.' },
    @{ Summary = 'Prepare and import MVP backlog'; Description = 'Compile full backlog and import into project.' }
  )
}

Write-Host ("Planned issues: {0}" -f $Plan.Count) -ForegroundColor Cyan
foreach ($p in $Plan) {
  $sum = $p.Summary
  $descText = if ($p.Description) { [string]$p.Description } else { '' }

  # Build Atlassian Document Format for description
  $adf = @{
    type    = 'doc'
    version = 1
    content = @(@{
      type    = 'paragraph'
      content = if ($descText) { @(@{ type='text'; text=$descText }) } else { @() }
    })
  }

  $fields = @{
    project   = @{ key = $Project }
    summary   = $sum
    issuetype = if ($IssueTypeId) { @{ id = $IssueTypeId } } else { @{ name = $IssueType } }
  }
  if (-not $NoDescription) {
    if ($UsePlainDescription) {
      $fields.description = @{ type='doc'; version=1; content=@(@{ type='paragraph'; content=@(@{ type='text'; text=$descText }) }) }
    } else {
      $fields.description = $adf
    }
  }
  $payload = @{ fields = $fields } | ConvertTo-Json -Depth 12

  if ($DryRun) {
    Write-Host ("DRYRUN: create '{0}' as {1}" -f $sum, $IssueType)
  } else {
    $url = "$BaseUrl/rest/api/3/issue"
    try {
      $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
      $resp = Invoke-RestMethod -Method Post -Uri $url -Headers $headers -Body $bytes
      Write-Host ("CREATED: {0} - {1}" -f $resp.key, $sum) -ForegroundColor Green

      if ($AfterCreateStatus) {
        try {
          $transUrl = "$BaseUrl/rest/api/3/issue/$($resp.key)/transitions"
          $tresp = Invoke-RestMethod -Method Get -Uri $transUrl -Headers $headers
          $transitions = @(); if ($tresp.transitions) { $transitions = $tresp.transitions }
          $target = $transitions | Where-Object { $_.to.name -and ($_.to.name -ieq $AfterCreateStatus) } | Select-Object -First 1
          if ($null -ne $target) {
            $tBody = @{ transition = @{ id = $target.id } } | ConvertTo-Json -Depth 5
            $tBytes = [System.Text.Encoding]::UTF8.GetBytes($tBody)
            Invoke-RestMethod -Method Post -Uri $transUrl -Headers $headers -Body $tBytes | Out-Null
            Write-Host ("MOVED: {0} -> {1}" -f $resp.key, $AfterCreateStatus) -ForegroundColor Cyan
          } else {
            Write-Host ("NO TRANSITION: {0} -> {1}" -f $resp.key, $AfterCreateStatus) -ForegroundColor Yellow
          }
        } catch {
          Write-Host ("MOVE ERROR: {0} -> {1}" -f $resp.key, $AfterCreateStatus) -ForegroundColor Red
        }
      }
    } catch {
      $we = $_.Exception
      $respBody = ''
      if ($we.Response -and $we.Response.GetResponseStream()) {
        $reader = New-Object System.IO.StreamReader($we.Response.GetResponseStream())
        $respBody = $reader.ReadToEnd()
      }
      Write-Host "ERROR creating: $sum" -ForegroundColor Red
      if ($respBody) { Write-Host $respBody } else { Write-Host $_ }
      throw
    }
  }
}


