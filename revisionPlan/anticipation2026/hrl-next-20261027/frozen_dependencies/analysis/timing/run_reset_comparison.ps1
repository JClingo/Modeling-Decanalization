param([string[]]$Cases = @('legacy_startup', 'legacy_matched', 'current_matched', 'current_matched_velocity', 'current_startup', 'current_legacy_startup', 'current_matched_velocity_stream'))
$ErrorActionPreference = 'Stop'
$auditRoot = Join-Path (Get-Location) 'Saved/ResetPerformanceAudit'
$projectRoot = Join-Path $auditRoot 'TestProject'
$editor = 'D:/Dev/UE_5.5/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$project = Join-Path $projectRoot 'ue_canalization.uproject'
$assets = @('Agent/BP_Agent', 'Agent/BP_GameMode', 'Level/BP_Tile', 'Resource/BP_Resource')
foreach ($case in $Cases) {
    foreach ($asset in $assets) {
        $name = Split-Path $asset -Leaf
        $source = if ($case.StartsWith('legacy')) { "Saved/TrialStateAudit/$name.uasset" } else { "Content/$asset.uasset" }
        Copy-Item -LiteralPath $source -Destination (Join-Path $projectRoot "Content/$asset.uasset") -Force
    }
    $configLog = Join-Path $auditRoot "$case.configure.log"
    & $editor $project -run=pythonscript "-script=$((Get-Location).Path)/analysis/timing/configure_reset_comparison.py" -DisablePipInstall -nullrhi -nosound -unattended -nop4 "-abslog=$configLog" *> (Join-Path $auditRoot "$case.configure.stdout.log")
    if (!(Select-String -LiteralPath $configLog -Pattern 'RESET_COMPARISON_CONFIGURED' -Quiet)) { throw "Configuration failed: $case" }
    $caseArgs = @("-AuditLabel=$case")
    if ($case.Contains('matched')) { $caseArgs += '-MatchedScene' }
    if ($case.Contains('velocity')) { $caseArgs += '-RestoreVelocity' }
    if ($case.EndsWith('stream')) { $caseArgs += '-RestoreStream' }
    if ($case -eq 'current_legacy_startup') { $caseArgs += '-BypassBootstrap' }
    Write-Output "Running $case"
    & $editor $project /Game/Level/Landscape -game "-ExecCmds=py $((Get-Location).Path)/analysis/timing/validate_reset_comparison.py" @caseArgs -UseFixedTimeStep -FPS=20 -NoTrialCompletionDialog -DisablePipInstall -nullrhi -nosound -unattended -nop4 "-abslog=$(Join-Path $auditRoot "$case.log")" *> (Join-Path $auditRoot "$case.stdout.log")
    $result = Get-Content -LiteralPath (Join-Path $auditRoot "$case.json") -Raw | ConvertFrom-Json
    if (!$result.passed) { throw "$case failed: $($result.error)" }
    Write-Output "$case completed"
}
