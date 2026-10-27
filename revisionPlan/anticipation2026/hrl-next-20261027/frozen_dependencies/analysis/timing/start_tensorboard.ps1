param([int]$Port = 6006)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$pythonPath = Join-Path $projectRoot 'Intermediate/PipInstall/Scripts/python.exe'
$logPath = Join-Path $projectRoot 'Intermediate/LearningAgents/TensorBoard/runs'
$servicePath = Join-Path $projectRoot 'Saved/TensorBoard'
New-Item -ItemType Directory -Path $logPath, $servicePath -Force | Out-Null
$service = Start-Process -FilePath $pythonPath -ArgumentList @(
    '-m', 'tensorboard.main', '--logdir', ('"' + $logPath + '"'),
    '--host', '127.0.0.1', '--port', $Port, '--reload_interval', '5'
) -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru `
  -RedirectStandardOutput (Join-Path $servicePath 'stdout.log') `
  -RedirectStandardError (Join-Path $servicePath 'stderr.log')
$service.Id | Set-Content -LiteralPath (Join-Path $servicePath 'server.pid')
Write-Output "TensorBoard PID $($service.Id): http://127.0.0.1:$Port/"
