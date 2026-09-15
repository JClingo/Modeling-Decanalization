$ErrorActionPreference = 'Stop'
$exportScript = Join-Path $PSScriptRoot 'export_unreal_settings.py'
$sourceProject = 'C:\Users\jingo\Documents\Unreal Projects\decanalization'
$exports = @(
    @{ Label = 'current'; Project = (Join-Path $sourceProject 'ue_canalization.uproject') },
    @{ Label = 'committed_b2ec222'; Project = (Join-Path $sourceProject 'Saved\SettingsExportSnapshots\b2ec222f8654\ue_canalization.uproject') },
    @{ Label = 'study_candidate_5e508dd'; Project = (Join-Path $sourceProject 'Saved\SettingsExportSnapshots\5e508dd8b782\ue_canalization.uproject') }
)
foreach ($exportJob in $exports) {
    if (-not (Test-Path -LiteralPath $exportJob.Project)) { throw "Missing export project: $($exportJob.Project)" }
    $env:UE_SETTINGS_LABEL = $exportJob.Label
    $exportLog = Join-Path $PSScriptRoot ($exportJob.Label + '.log')
    & 'C:\Program Files\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' $exportJob.Project -run=pythonscript "-script=$exportScript" -unattended -nullrhi -nosound -nop4 -NoSplash -DisablePipInstall "-abslog=$exportLog"
    if ($LASTEXITCODE -ne 0) { throw "Export failed: $($exportJob.Label), exit $LASTEXITCODE" }
}
Remove-Item Env:\UE_SETTINGS_LABEL
