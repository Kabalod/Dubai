param(
  [Parameter(Mandatory=$true)][string]$KeysCsv,
  [Parameter(Mandatory=$false)][string]$TargetType = 'Task',
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

function Resolve-IssueTypeId {
  param([string]$ProjectKey,[string]$DesiredName)
  $metaUrl = "$BaseUrl/rest/api/3/issue/createmeta?projectKeys=$ProjectKey&expand=projects.issuetypes.fields"
  $meta = Invoke-RestMethod -Method Get -Uri $metaUrl -Headers $headers
  $proj = $meta.projects | Select-Object -First 1
  if (-not $proj) { return $null }
  $types = @($proj.issuetypes)
  $byName = $types | Where-Object { $_.name -ieq $DesiredName } | Select-Object -First 1
  if ($byName) { return $byName.id }
  return ($types | Select-Object -First 1).id
}

$keys = $KeysCsv.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ }
if ($keys.Count -eq 0) { Write-Error 'No issue keys provided' }

# Infer project from first key
$projKey = ($keys[0] -split '-')[0]
$typeId = Resolve-IssueTypeId -ProjectKey $projKey -DesiredName $TargetType
if (-not $typeId) { Write-Error "Cannot resolve issue type id for $TargetType" }

foreach ($k in $keys) {
  $payload = @{ fields = @{ issuetype = @{ id = $typeId } } } | ConvertTo-Json -Depth 6
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
  $url = "$BaseUrl/rest/api/3/issue/$k"
  try {
    Invoke-RestMethod -Method Put -Uri $url -Headers $headers -Body $bytes
    Write-Host ("TYPE UPDATED: {0} -> {1}" -f $k, $TargetType) -ForegroundColor Green
  } catch {
    $we = $_.Exception
    $respBody = ''
    if ($we.Response -and $we.Response.GetResponseStream()) {
      $reader = New-Object System.IO.StreamReader($we.Response.GetResponseStream())
      $respBody = $reader.ReadToEnd()
    }
    Write-Host ("ERROR updating type: {0}" -f $k) -ForegroundColor Red
    if ($respBody) { Write-Host $respBody } else { Write-Host $_ }
  }
}


