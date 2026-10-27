param([string]$EngineExe = 'D:\Dev\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe')
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$projectFile = Join-Path $projectRoot 'ue_canalization.uproject'
foreach ($requiredPath in @($EngineExe, $projectFile, (Join-Path $projectRoot 'Intermediate/PipInstall/Scripts/python.exe'))) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) { throw "Required file missing: $requiredPath" }
}
$existingRuns = Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor-Cmd.exe'" |
    Where-Object { $_.CommandLine -like "*$projectFile*" -and $_.CommandLine -match '(?i)\s-game(?:\s|$)' }
if ($existingRuns) {
    throw "A standalone run for this project is already active (PID $($existingRuns.ProcessId -join ', '))."
}
$runPath = Join-Path $projectRoot ('Saved/HeadlessTraining/' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path (Join-Path $runPath 'backup') -Force | Out-Null
Get-ChildItem -LiteralPath (Join-Path $projectRoot 'Content/Learning') -Filter 'DA_Agent*.uasset' |
    Copy-Item -Destination (Join-Path $runPath 'backup')
$logPath = Join-Path $runPath 'training.log'
$arguments = @(
    ('"' + $projectFile + '"'),
    '/Game/Level/Landscape', '-game', '-nullrhi', '-nosound', '-unattended', '-nop4', '-NoVSync',
    '-UseFixedTimeStep', '-FPS=20',
    ('-abslog="' + $logPath + '"')
)
$trainingProcess = Start-Process -FilePath $engineExe -ArgumentList $arguments `
    -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $runPath 'stdout.log') `
    -RedirectStandardError (Join-Path $runPath 'stderr.log')
@{pid=$trainingProcess.Id; started=(Get-Date -Format o); log=$logPath; arguments=$arguments} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runPath 'run.json')
Write-Output "Headless training PID $($trainingProcess.Id)"
Write-Output "Run directory: $runPath"
Write-Output 'Simulation clock: uncapped, fixed 0.05-second steps (training and trials).'
Write-Output 'Waiting for a PPO update or trial completion (up to 120 seconds)...'
$deadline = (Get-Date).AddSeconds(120)
while ((Get-Date) -lt $deadline) {
    if (Test-Path -LiteralPath $logPath) {
        $tail = Get-Content -LiteralPath $logPath -Tail 250
        $completion = $tail | Select-String -SimpleMatch '[TRIALS_COMPLETE]' | Select-Object -Last 1
        if ($completion) {
            Write-Output $completion.Line
            Write-Output 'Trial run complete. A Windows completion dialog shows the results path.'
            return
        }
        if ($tail -match 'Training has failed|LogLearning: Error|Traceback \(most recent call last\)') {
            $tail | Select-Object -Last 25 | Write-Host
            throw "Training reported a failure. The process is still available as PID $($trainingProcess.Id); see $logPath"
        }
        if ($tail -match 'Subprocess: Iter:\s+\d+') {
            Write-Output 'PPO update confirmed. Training continues in the background.'
            Write-Output 'TensorBoard: http://127.0.0.1:6006/'
            return
        }
    }
    $trainingProcess.Refresh()
    if ($trainingProcess.HasExited) {
        # Read once more after exit to include the final flushed log messages.
        $completion = if (Test-Path -LiteralPath $logPath) {
            Get-Content -LiteralPath $logPath -Tail 250 | Select-String -SimpleMatch '[TRIALS_COMPLETE]' | Select-Object -Last 1
        }
        if ($completion) { Write-Output $completion.Line; return }
        if (Test-Path -LiteralPath $logPath) { Get-Content -LiteralPath $logPath -Tail 25 | Write-Host }
        throw "Unreal exited before a PPO update or confirmed trial completion (code $($trainingProcess.ExitCode)). See $runPath"
    }
    Start-Sleep -Seconds 2
}
Write-Warning "Unreal is running (PID $($trainingProcess.Id)), but no PPO update or completed trial batch was confirmed within 120 seconds. Check $logPath"
