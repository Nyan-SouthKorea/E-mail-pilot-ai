param(
    [string]$ExePath = "D:\\EmailPilotAI\\portable\\EmailPilotAI\\EmailPilotAI.exe",
    [int]$Port = 8876,
    [int]$StartupTimeoutSeconds = 20,
    [int]$GuiStartupWaitSeconds = 8
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ExePath)) {
    throw "포터블 exe를 찾을 수 없다: $ExePath"
}

$jobUrl = "http://127.0.0.1:$Port/jobs/current"
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
            $response = Invoke-WebRequest -Uri $jobUrl -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                $ready = $true
                break
            }
        }
        catch {
        }
        Start-Sleep -Milliseconds 700
    }

    if (-not $ready) {
        throw "포터블 exe가 제한 시간 안에 /jobs/current endpoint를 띄우지 못했다."
    }

    Write-Host "Portable exe smoke passed:"
    Write-Host $jobUrl
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
