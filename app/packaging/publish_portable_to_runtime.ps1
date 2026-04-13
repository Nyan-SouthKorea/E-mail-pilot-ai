param(
    [string]$SourceBundleRoot,
    [string]$RuntimeBundleRoot = "D:\\EmailPilotAI\\portable\\EmailPilotAI",
    [string]$PythonExe = "python",
    [switch]$SkipSmoke
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$ManifestScriptPath = Join-Path $PSScriptRoot "portable_bundle_manifest.py"
$SmokeScriptPath = Join-Path $PSScriptRoot "smoke_portable_exe.ps1"
$ManifestFileName = "portable_bundle_manifest.json"

function Resolve-SourceBundleRoot {
    param(
        [string]$ExplicitPath
    )

    if ($ExplicitPath) {
        return (Resolve-Path $ExplicitPath).Path
    }

    $candidate = Join-Path $RepoRoot "dist\\EmailPilotAI"
    if (Test-Path $candidate) {
        return (Resolve-Path $candidate).Path
    }

    throw "공식 portable source bundle을 찾을 수 없다. dist\\EmailPilotAI 경로가 필요하다."
}

function Invoke-PortableManifest {
    param(
        [string[]]$Arguments
    )

    & $PythonExe $ManifestScriptPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "portable bundle manifest helper가 실패했다: $($Arguments -join ' ')"
    }
}

$ResolvedSourceBundleRoot = Resolve-SourceBundleRoot -ExplicitPath $SourceBundleRoot
$ResolvedRuntimeBundleRoot = [System.IO.Path]::GetFullPath($RuntimeBundleRoot)
$RuntimeParent = Split-Path -Parent $ResolvedRuntimeBundleRoot
$RuntimeExePath = Join-Path $ResolvedRuntimeBundleRoot "EmailPilotAI.exe"
$ExpectedManifestPath = Join-Path $ResolvedSourceBundleRoot $ManifestFileName
$ActualManifestPath = Join-Path $env:TEMP ("portable_bundle_manifest_runtime_" + [guid]::NewGuid().ToString("N") + ".json")

function Stop-OfficialRuntimeProcess {
    param(
        [string]$ExePath
    )

    $normalizedExePath = [System.IO.Path]::GetFullPath($ExePath)
    $targets = @()

    foreach ($process in Get-Process -Name "EmailPilotAI" -ErrorAction SilentlyContinue) {
        try {
            if ($process.Path -and ([System.IO.Path]::GetFullPath($process.Path) -eq $normalizedExePath)) {
                $targets += $process
            }
        }
        catch {
            continue
        }
    }

    if ($targets.Count -eq 0) {
        return
    }

    Write-Host "Stopping running official runtime process before publish..."
    foreach ($target in $targets) {
        Stop-Process -Id $target.Id -Force
    }

    Start-Sleep -Milliseconds 700
}

try {
    Invoke-PortableManifest @("check-required", "--bundle-root", $ResolvedSourceBundleRoot)

    if (-not (Test-Path $ExpectedManifestPath)) {
        Invoke-PortableManifest @("write", "--bundle-root", $ResolvedSourceBundleRoot, "--output", $ExpectedManifestPath)
    }

    New-Item -ItemType Directory -Force -Path $RuntimeParent | Out-Null
    New-Item -ItemType Directory -Force -Path $ResolvedRuntimeBundleRoot | Out-Null
    Stop-OfficialRuntimeProcess -ExePath $RuntimeExePath

    $null = robocopy $ResolvedSourceBundleRoot $ResolvedRuntimeBundleRoot /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy가 공식 runtime publish 중 실패했다. exit_code=$LASTEXITCODE"
    }

    Invoke-PortableManifest @("check-required", "--bundle-root", $ResolvedRuntimeBundleRoot)
    Invoke-PortableManifest @("write", "--bundle-root", $ResolvedRuntimeBundleRoot, "--output", $ActualManifestPath)
    Invoke-PortableManifest @("compare", "--expected", $ExpectedManifestPath, "--actual", $ActualManifestPath)

    if (-not $SkipSmoke) {
        & "powershell" -ExecutionPolicy Bypass -File $SmokeScriptPath -ExePath $RuntimeExePath
        if ($LASTEXITCODE -ne 0) {
            throw "공식 runtime portable exe smoke가 실패했다."
        }
    }

    Write-Host ""
    Write-Host "Official runtime bundle ready:"
    Write-Host $RuntimeExePath
    Write-Host "Published from:"
    Write-Host $ResolvedSourceBundleRoot
}
finally {
    if (Test-Path $ActualManifestPath) {
        Remove-Item -Force $ActualManifestPath
    }
}
