<#
.SYNOPSIS
Registers a daily Windows Scheduled Task to run the Protein Design SOTA Agent every morning.

.DESCRIPTION
This script configures Windows Task Scheduler to execute `run_agent.py --send` every day at 08:00 AM.
#>

param(
    [string]$Time = "08:00",
    [string]$TaskName = "ProteinDesignSOTAAgent"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PythonExe = (Get-Command python).Source
$AgentScript = Join-Path $ScriptDir "run_agent.py"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Protein Design SOTA Agent - Daily Scheduler Setup" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Task Name:        $TaskName"
Write-Host "Trigger Time:     Daily at $Time"
Write-Host "Python Path:      $PythonExe"
Write-Host "Target Script:    $AgentScript"
Write-Host ""

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$AgentScript`" --send" -WorkingDirectory $ScriptDir
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

try {
    # Check if task already exists and unregister
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Write-Host "Removing existing scheduled task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Daily Protein Design SOTA Research surveillance and Gmail digest"
    Write-Host "`n✅ Scheduled task successfully registered!" -ForegroundColor Green
    Write-Host "The agent will automatically run every morning at $Time to deliver your digest." -ForegroundColor Green
    Write-Host "To test it immediately, run: Start-ScheduledTask -TaskName $TaskName" -ForegroundColor Cyan
}
catch {
    Write-Host "`n❌ Error registering task: $_" -ForegroundColor Red
    Write-Host "Note: You may need to run PowerShell as Administrator to register scheduled tasks." -ForegroundColor Yellow
}

