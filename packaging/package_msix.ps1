param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDirectory
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$source = (Resolve-Path -LiteralPath $SourceDirectory).Path
if (-not (Test-Path -LiteralPath (Join-Path $source 'DesktopIsland.exe'))) {
    throw "Built application not found: $source\DesktopIsland.exe"
}
$manifest = Join-Path $PSScriptRoot 'AppxManifest.xml'
$assets = Join-Path $PSScriptRoot 'Assets'
$stage = [IO.Path]::GetFullPath((Join-Path $projectRoot 'build_store\package'))
$stagePrefix = $projectRoot.TrimEnd('\') + '\'
if (-not $stage.StartsWith($stagePrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to stage outside the project directory: $stage"
}
if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stage | Out-Null
Copy-Item -Path (Join-Path $source '*') -Destination $stage -Recurse -Force
Copy-Item -LiteralPath $manifest -Destination (Join-Path $stage 'AppxManifest.xml') -Force
Copy-Item -LiteralPath $assets -Destination (Join-Path $stage 'Assets') -Recurse -Force

$makeAppx = (Get-Command 'MakeAppx.exe' -ErrorAction SilentlyContinue).Source
if (-not $makeAppx) {
    $sdkRoots = @(
        (Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin'),
        (Join-Path $env:ProgramFiles 'Windows Kits\10\bin')
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
    foreach ($sdkRoot in $sdkRoots) {
        $candidate = Get-ChildItem -LiteralPath $sdkRoot -Filter MakeAppx.exe -File -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match '\\x64\\MakeAppx\.exe$' } |
            Sort-Object FullName -Descending | Select-Object -First 1
        if ($candidate) { $makeAppx = $candidate.FullName; break }
    }
}
if (-not $makeAppx) {
    throw 'MakeAppx.exe was not found. Install the Windows 10/11 SDK (Appx Packaging Tools), then run build_store_msix.bat again.'
}
$outputDirectory = Join-Path $projectRoot 'artifacts\store'
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
$output = Join-Path $outputDirectory 'DesktopIsland_1.0.0.0_x64.msix'
& $makeAppx pack /d $stage /p $output /o
if ($LASTEXITCODE -ne 0) { throw "MakeAppx failed with exit code $LASTEXITCODE" }
Write-Host "Created Store submission package: $output"
Write-Host 'This MSIX is prepared for Partner Center submission and is not yet Store-certified or published.'

