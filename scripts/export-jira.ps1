param(
  [Parameter(Mandatory=$false)][string]$Project,
  [Parameter(Mandatory=$false)][string]$Jql,
  [Parameter(Mandatory=$false)][string]$Output = 'docs/jira-tasks.md',
  [Parameter(Mandatory=$false)][string]$Email,
  [Parameter(Mandatory=$false)][string]$Token,
  [Parameter(Mandatory=$false)][string]$Site
)
$ErrorActionPreference = 'Stop'

# Read credentials from parameters first, then environment
if (-not $Email) { $Email = $env:JIRA_EMAIL }
if (-not $Token) { $Token = $env:JIRA_TOKEN }
if (-not $Site)  { $Site  = if ($env:JIRA_SITE) { $env:JIRA_SITE } else { 'kbalodk.atlassian.net' } }
if (-not $Email -or -not $Token) {
  Write-Error 'Set env vars JIRA_EMAIL and JIRA_TOKEN before running this script.'
}

if (-not $Jql) {
  if (-not $Project) { Write-Error 'Provide -Project or -Jql' }
  $Jql = "project = $Project ORDER BY status, priority DESC, updated DESC"
}

$pair = "$Email`:$Token"
$basic = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($pair))
$headers = @{ Authorization = "Basic $basic"; Accept = 'application/json' }

$encodedJql = [System.Uri]::EscapeDataString($Jql)
$fields = 'key,summary,status,assignee,priority,updated'
$max = 200
$baseUrl = "https://$Site"
$searchUrl = "$baseUrl/rest/api/3/search?jql=$encodedJql&maxResults=$max&fields=$fields"

$resp = Invoke-RestMethod -Method Get -Uri $searchUrl -Headers $headers
$issues = @()
if ($resp.issues) { $issues = $resp.issues }

# Group by status name
$groups = $issues | Group-Object { $_.fields.status.name } | Sort-Object Name

# Ensure output directory
$fullOut = Join-Path (Get-Location) $Output
$dir = Split-Path $fullOut -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }

# Build markdown
$sb = New-Object System.Text.StringBuilder
$ts = Get-Date -Format 'yyyy-MM-dd HH:mm'
$null = $sb.AppendLine("# Jira Tasks (export $ts)")
$null = $sb.AppendLine("")
$null = $sb.AppendLine(("JQL: {0}" -f $Jql))
$null = $sb.AppendLine("")

foreach ($g in $groups) {
  $statusTitle = "## Status: " + $g.Name
  $null = $sb.AppendLine($statusTitle)
  $sorted = $g.Group | Sort-Object @{Expression={ $_.fields.priority.name }; Ascending=$false}, @{Expression={ $_.fields.updated }; Ascending=$false}
  foreach ($i in $sorted) {
    $key = $i.key
    $summary = $i.fields.summary
    $assignee = if ($i.fields.assignee) { $i.fields.assignee.displayName } else { 'Unassigned' }
    $prio = if ($i.fields.priority) { $i.fields.priority.name } else { 'None' }
    $upd = Get-Date $i.fields.updated -Format 'yyyy-MM-dd HH:mm'
    $url = "$baseUrl/browse/$key"
    $line = "- [" + $key + "](" + $url + ") - " + $summary + " - **" + $assignee + "** - " + $prio + " - " + $upd
    $null = $sb.AppendLine($line)
  }
  $null = $sb.AppendLine("")
}

[IO.File]::WriteAllText($fullOut, $sb.ToString(), [Text.UTF8Encoding]::new($true))
Write-Host ("Exported {0} issues to {1}" -f $issues.Count, $Output) -ForegroundColor Cyan
