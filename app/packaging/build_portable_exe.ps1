param(
    [string]$PythonExe = "python",
    [switch]$Clean,
    [switch]$SkipSmoke
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$SpecPath = Join-Path $PSScriptRoot "EmailPilotAI.spec"
$ManifestScriptPath = Join-Path $PSScriptRoot "portable_bundle_manifest.py"
$PublishScriptPath = Join-Path $PSScriptRoot "publish_portable_to_runtime.ps1"
$BundleRoot = Join-Path $RepoRoot "dist\\EmailPilotAI"
$ManifestPath = Join-Path $BundleRoot "portable_bundle_manifest.json"
$RuntimeBundleRoot = "D:\\EmailPilotAI\\portable\\EmailPilotAI"

Set-Location $RepoRoot

if ($Clean) {
    if (Test-Path (Join-Path $RepoRoot "build")) {
        Remove-Item -Recurse -Force (Join-Path $RepoRoot "build")
    }
    if (Test-Path (Join-Path $RepoRoot "dist")) {
        Remove-Item -Recurse -Force (Join-Path $RepoRoot "dist")
    }
}

& $PythonExe -m PyInstaller --noconfirm --clean $SpecPath

$WarnFile = Join-Path $RepoRoot "build\\EmailPilotAI\\warn-EmailPilotAI.txt"
if (Test-Path $WarnFile) {
    $warnText = Get-Content $WarnFile -Raw
    if ($warnText -match "missing module named backports") {
        throw "PyInstaller warning file still reports missing module 'backports'."
    }
}

& $PythonExe $ManifestScriptPath check-required --bundle-root $BundleRoot
if ($LASTEXITCODE -ne 0) {
    throw "portable bundle 필수 파일 점검이 실패했다."
}

& $PythonExe $ManifestScriptPath write --bundle-root $BundleRoot --output $ManifestPath
if ($LASTEXITCODE -ne 0) {
    throw "portable bundle manifest 생성이 실패했다."
}

$PublishArgs = @(
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $PublishScriptPath,
    "-SourceBundleRoot",
    $BundleRoot,
    "-RuntimeBundleRoot",
    $RuntimeBundleRoot,
    "-PythonExe",
    $PythonExe
)
if ($SkipSmoke) {
    $PublishArgs += "-SkipSmoke"
}

& "powershell" @PublishArgs
if ($LASTEXITCODE -ne 0) {
    throw "공식 runtime publish가 실패했다."
}

$CleanupTargets = @(
    (Join-Path $RepoRoot "build\\EmailPilotAI"),
    (Join-Path $RepoRoot "dist\\EmailPilotAI"),
    (Join-Path $RepoRoot "dist\\windows-portable\\EmailPilotAI"),
    (Join-Path $env:LOCALAPPDATA "EmailPilotAI\\portable\\EmailPilotAI")
)

foreach ($target in $CleanupTargets) {
    if (Test-Path $target) {
        Remove-Item -Recurse -Force $target
    }
}

$CleanupParents = @(
    (Join-Path $RepoRoot "build"),
    (Join-Path $RepoRoot "dist"),
    (Join-Path $RepoRoot "dist\\windows-portable")
)

foreach ($parent in $CleanupParents) {
    if ((Test-Path $parent) -and -not (Get-ChildItem -Force $parent | Select-Object -First 1)) {
        Remove-Item -Force $parent
    }
}

Write-Host ""
Write-Host "Official runtime executable:"
Write-Host (Join-Path $RuntimeBundleRoot "EmailPilotAI.exe")
Write-Host "Portable manifest:"
Write-Host (Join-Path $RuntimeBundleRoot "portable_bundle_manifest.json")
Write-Host "A100 remote build helper:"
Write-Host "bash ./app/packaging/build_windows_portable_and_publish.sh"
