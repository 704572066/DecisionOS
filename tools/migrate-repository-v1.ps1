$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root
$dirs = @("docs/product","docs/architecture","docs/specs","docs/adr","docs/diagrams","docs/templates","schemas","examples","src/backend","src/frontend","src/ai")
foreach ($d in $dirs) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
function Move-KnownFile($source, $destination) {
    if (Test-Path $source -PathType Leaf) {
        New-Item -ItemType Directory -Force -Path (Split-Path $destination) | Out-Null
        git mv -- $source $destination 2>$null
        if ($LASTEXITCODE -ne 0) { Move-Item -Force $source $destination }
        Write-Host "Moved $source -> $destination"
    }
}
Move-KnownFile "docs/000_Product_Constitution.md" "docs/product/000_Product_Constitution.md"
Move-KnownFile "docs/001_Product_Vision.md" "docs/product/001_Product_Vision.md"
Move-KnownFile "docs/002_MVP_Definition.md" "docs/product/002_MVP_Definition.md"
Move-KnownFile "docs/003_Context_Engine.md" "docs/architecture/003_Context_Engine.md"
Get-ChildItem -Recurse -Filter .gitkeep -Path docs,schemas,examples,src -ErrorAction SilentlyContinue | ForEach-Object {
    $other = Get-ChildItem $_.DirectoryName -Force | Where-Object { $_.Name -ne ".gitkeep" }
    if ($other) { Remove-Item $_.FullName -Force }
}
Write-Host "Repository v1.0 migration completed. Review with: git status"
