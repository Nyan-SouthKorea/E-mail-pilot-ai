param(
    [string]$ExePath = "D:\\EmailPilotAI\\portable\\EmailPilotAI\\EmailPilotAI.exe",
    [string]$RepoRoot = "D:\\EmailPilotAI\\repo",
    [int]$Port = 8876,
    [int]$StartupTimeoutSeconds = 20,
    [int]$GuiStartupWaitSeconds = 8
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ExePath)) {
    throw "포터블 exe를 찾을 수 없다: $ExePath"
}

$jobUrl = "http://127.0.0.1:$Port/jobs/current"
$metaUrl = "http://127.0.0.1:$Port/app-meta"
$proc = Start-Process -FilePath $ExePath -ArgumentList @("--no-window", "--port", "$Port") -PassThru
$startupLogPath = Join-Path $env:APPDATA "EmailPilotAI\startup.log"

try {
    $deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
    $ready = $false
    while ((Get-Date) -lt $deadline) {
        if ($proc.HasExited) {
            throw "포터블 exe가 서버 기동 전에 종료됐다. exit_code=$($proc.ExitCode)"
        }
        try {
            $metaResponse = Invoke-WebRequest -Uri $metaUrl -UseBasicParsing -TimeoutSec 2
            $metaPayload = $metaResponse.Content | ConvertFrom-Json
            if ($metaResponse.StatusCode -eq 200 -and $metaPayload.app_id -eq "email_pilot_ai_desktop") {
                $response = Invoke-WebRequest -Uri $jobUrl -UseBasicParsing -TimeoutSec 2
                if ($response.StatusCode -eq 200) {
                    $ready = $true
                    break
                }
            }
        }
        catch {
        }
        Start-Sleep -Milliseconds 700
    }

    if (-not $ready) {
        throw "포터블 exe가 제한 시간 안에 올바른 Email Pilot AI /app-meta 와 /jobs/current endpoint를 띄우지 못했다."
    }

    if (-not $metaPayload.build_commit) {
        throw "packaged /app-meta 에 build_commit 이 비어 있다."
    }
    if (-not $metaPayload.build_time) {
        throw "packaged /app-meta 에 build_time 이 비어 있다."
    }
    if (-not $metaPayload.official_exe_path) {
        throw "packaged /app-meta 에 official_exe_path 가 비어 있다."
    }
    if ($metaPayload.official_exe_path -ne $ExePath) {
        throw "packaged /app-meta 의 official_exe_path 가 현재 smoke 대상 exe 와 다르다. meta=$($metaPayload.official_exe_path) exe=$ExePath"
    }
    if (Test-Path (Join-Path $RepoRoot ".git")) {
        $expectedCommit = (git -C $RepoRoot rev-parse HEAD).Trim()
        if ($expectedCommit -and $metaPayload.build_commit -ne $expectedCommit) {
            throw "packaged exe build_commit 이 현재 repo HEAD 와 다르다. meta=$($metaPayload.build_commit) head=$expectedCommit"
        }
    }

    Write-Host "Portable exe smoke passed:"
    Write-Host $jobUrl
    Write-Host $metaUrl
    Write-Host "build_commit=$($metaPayload.build_commit)"
    Write-Host "build_time=$($metaPayload.build_time)"
}
finally {
    if ($proc -and -not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force
    }
}

if (Test-Path $startupLogPath) {
    Remove-Item $startupLogPath -Force
}

$guiProc = Start-Process -FilePath $ExePath -PassThru
try {
    $deadline = (Get-Date).AddSeconds($GuiStartupWaitSeconds)
    while ((Get-Date) -lt $deadline) {
        if ($guiProc.HasExited) {
            throw "GUI smoke 중 포터블 exe가 조기 종료됐다. exit_code=$($guiProc.ExitCode)"
        }
        Start-Sleep -Milliseconds 500
    }

    if (-not (Test-Path $startupLogPath)) {
        throw "GUI smoke 후 startup.log가 생성되지 않았다."
    }

    $startupLog = Get-Content $startupLogPath -Raw
    if ($startupLog -notmatch "launcher: imported pywebview") {
        throw "GUI smoke에서 pywebview import 로그를 찾지 못했다."
    }
    if ($startupLog -notmatch "launcher: pywebview window created and bridge attached") {
        throw "GUI smoke에서 pywebview bridge attach 로그를 찾지 못했다."
    }
    if ($startupLog -notmatch "launcher: confirmed app-meta at http://127.0.0.1:8765") {
        # GUI smoke는 기본 preferred port를 쓰되, 충돌 시 다른 포트를 선택할 수 있다.
        if ($startupLog -notmatch "launcher: confirmed app-meta at http://127.0.0.1:[0-9]+") {
            throw "GUI smoke에서 app-meta 확인 로그를 찾지 못했다."
        }
    }
    if ($startupLog -match "launcher: pywebview failed") {
        throw "GUI smoke에서 pywebview 실패 로그가 감지됐다."
    }

    Write-Host "Portable GUI smoke passed:"
    Write-Host $startupLogPath
}
finally {
    if ($guiProc -and -not $guiProc.HasExited) {
        Stop-Process -Id $guiProc.Id -Force
    }
}
