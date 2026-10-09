param(
    [string]$BackendRoot = 'D:\projects\477-backend',
    [string]$PythonPath = '',
    [int]$Port = 8000,
    [switch]$Analyze,
    [string]$KeyEnvFile = '',
    [double]$RequestBudgetUsd = 1
)
$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path -Parent $PSScriptRoot
$taskMediaRoot = Join-Path $taskProjectRoot 'data\mock_cctv\media'
foreach ($taskNumber in 1..9) {
    $taskFile = Join-Path $taskMediaRoot ('CAM_{0:00}.mp4' -f $taskNumber)
    if (!(Test-Path -LiteralPath $taskFile)) { throw "Missing video: $taskFile" }
}
if (!$PythonPath) {
    foreach ($taskCandidate in @('.venv-test\Scripts\python.exe', '.venv\Scripts\python.exe')) {
        $taskInterpreter = Join-Path $BackendRoot $taskCandidate
        if (Test-Path -LiteralPath $taskInterpreter) { $PythonPath = $taskInterpreter; break }
    }
    if (!$PythonPath) { $PythonPath = 'python' }
}
$env:APP_MODE = 'demo'
$env:MEDIA_ROOT = $taskMediaRoot
$env:ASSET_ROOT = $taskMediaRoot
$env:ASSET_MAP = Join-Path $PSScriptRoot 'asset-map.json'
$env:DEMO_SCENARIO_PATH = Join-Path $PSScriptRoot 'demo-scenario.json'
$env:MODEL_ADAPTER = 'local_cv'
if ($Analyze) {
    $env:APP_MODE = 'development'
    $env:MODEL_ADAPTER = 'cascade_v1'
    $env:ASSET_ROOT = Join-Path $taskProjectRoot 'data\mock_cctv'
    $env:ASSET_MAP = Join-Path $PSScriptRoot 'analysis-asset-map.json'
    Remove-Item Env:DEMO_SCENARIO_PATH -ErrorAction SilentlyContinue
    $env:AI_MODE = 'shadow'
    $env:AI_PYTHON = $PythonPath
    $env:AI_CV_PYTHON = Join-Path $taskProjectRoot 'experiments\p0_cv_only\.venv\Scripts\python.exe'
    $env:AI_WEIGHTS = Join-Path $taskProjectRoot 'experiments\p0_cv_only\models\yolo26n-pose.pt'
    $env:AI_STAGE_TIMEOUT_SEC = '300'
    $env:AI_TOTAL_TIMEOUT_SEC = '1200'
    $env:AI_MAX_RETRIES = '0'
    if ($RequestBudgetUsd -le 0 -or [double]::IsNaN($RequestBudgetUsd) -or [double]::IsInfinity($RequestBudgetUsd)) { throw 'RequestBudgetUsd must be positive and finite' }
    $env:AI_REQUEST_BUDGET_USD = $RequestBudgetUsd.ToString([Globalization.CultureInfo]::InvariantCulture)
    if (!$KeyEnvFile) { $KeyEnvFile = Join-Path $taskProjectRoot 'experiments\.env' }
    foreach ($taskRequired in @($env:AI_CV_PYTHON,$env:AI_WEIGHTS,$env:ASSET_MAP)) {
        if (!(Test-Path -LiteralPath $taskRequired)) { throw "Missing AI asset: $taskRequired" }
    }
}
Push-Location -LiteralPath $BackendRoot
try {
    $taskUvicornArgs = @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port',"$Port",'--workers','1')
    if ($Analyze) {
        if (Test-Path -LiteralPath $KeyEnvFile) { $taskUvicornArgs += @('--env-file',$KeyEnvFile) }
        $taskPreflight = 'import os,sys; from dotenv import load_dotenv; load_dotenv(sys.argv[1],override=False); assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY is not configured"; import openai,PIL; print("AI runtime and API key are configured")'
        & $PythonPath -c $taskPreflight $KeyEnvFile
        if ($LASTEXITCODE -ne 0) { throw 'AI preflight failed; no provider requests were made' }
    }
    & $PythonPath @taskUvicornArgs
    if ($LASTEXITCODE -ne 0) { throw "Backend exited with code $LASTEXITCODE" }
} finally { Pop-Location }
