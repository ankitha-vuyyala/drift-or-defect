# Registers the drift-or-defect job runner with Windows Task Scheduler for the current user (no admin needed).
# Starts every 5 minutes; a second copy exits at once while one is running (lock file + IgnoreNew).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$pyw = Join-Path $root ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $pyw)) { throw "Missing $pyw - create the venv first." }
$runner = Join-Path $root "runner\runner.py"
$action = New-ScheduledTaskAction -Execute $pyw -Argument "`"$runner`"" -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
  -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -StartWhenAvailable
Register-ScheduledTask -TaskName "DriftOrDefectRunner" -Action $action -Trigger $trigger -Settings $settings `
  -Description "Runs jobs from Documents\drift-or-defect\jobs\queue one at a time" -Force | Out-Null
Start-ScheduledTask -TaskName "DriftOrDefectRunner"
Write-Output "Registered and started DriftOrDefectRunner"
