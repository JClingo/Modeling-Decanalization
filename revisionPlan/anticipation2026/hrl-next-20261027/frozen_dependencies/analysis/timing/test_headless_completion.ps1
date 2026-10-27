# Exercise the launcher's polling code without launching Unreal or showing UI.
$ErrorActionPreference = 'Stop'
$source = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'start_headless_training.ps1') -Raw
$tokens = $null; $parseErrors = $null
$tree = [Management.Automation.Language.Parser]::ParseInput($source, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors) { throw $parseErrors }
$loop = $tree.Find({ param($node) $node -is [Management.Automation.Language.WhileStatementAst] }, $true)
$poll = [scriptblock]::Create($loop.Extent.Text)
function Test-Path { param($LiteralPath) return $true }
function Get-Content {
    param($LiteralPath, $Tail)
    $index = [Math]::Min($script:reads, $script:responses.Count - 1)
    $script:reads++
    return $script:responses[$index]
}
function Start-Sleep { throw 'Unexpected wait in launcher regression test' }
$cases = @(
    @{name='completed exit'; responses=@('[TRIALS_COMPLETE] All 3/3 trials are complete. Results: run.yml'); exited=$true; error=$false},
    @{name='completion flushed at exit'; responses=@('', '[TRIALS_COMPLETE] All 3/3 trials are complete.'); exited=$true; error=$false},
    @{name='PPO continues'; responses=@('Subprocess: Iter: 1'); exited=$false; error=$false},
    @{name='early exit'; responses=@(''); exited=$true; error=$true},
    @{name='training failure'; responses=@('Traceback (most recent call last)'); exited=$false; error=$true}
)
foreach ($case in $cases) {
    $script:reads = 0; $script:responses = $case.responses
    $trainingProcess = [pscustomobject]@{Id=123; HasExited=$case.exited; ExitCode=1}
    $trainingProcess | Add-Member -MemberType ScriptMethod -Name Refresh -Value {}
    $deadline = (Get-Date).AddSeconds(10); $logPath = 'test.log'; $runPath = 'test-run'
    $failed = $false
    try { $output = & $poll } catch { $failed = $true }
    if ($failed -ne $case.error) { throw "Unexpected launcher outcome: $($case.name)" }
    if (-not $failed -and $case.name -like '*complet*' -and ($output -join ' ') -notmatch '\[TRIALS_COMPLETE\]') {
        throw "Missing completion output: $($case.name)"
    }
    Write-Output "PASS: $($case.name)"
}
