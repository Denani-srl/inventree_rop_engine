# Build script for ROP Engine Plugin Frontend
# Run this on Windows before installing the plugin

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Building ROP Engine Plugin Frontend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Navigate to frontend directory
$frontendDir = Join-Path $PSScriptRoot "inventreeropengine\frontend"
$staticDir = Join-Path $PSScriptRoot "inventreeropengine\inventree_rop_engine\static"

if (-not (Test-Path $frontendDir)) {
    Write-Host "ERROR: Frontend directory not found: $frontendDir" -ForegroundColor Red
    exit 1
}

Write-Host "📁 Frontend directory: $frontendDir" -ForegroundColor Gray
Write-Host ""

# Check if node is installed
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js version: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Node.js not found. Please install Node.js 18+ first." -ForegroundColor Red
    exit 1
}

# Navigate to frontend
Set-Location $frontendDir

# Install dependencies
Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: npm install failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Build frontend
Write-Host ""
Write-Host "🔨 Building frontend..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Build completed" -ForegroundColor Green

# Verify output files
Write-Host ""
Write-Host "🔍 Verifying build output..." -ForegroundColor Yellow

if (-not (Test-Path $staticDir)) {
    Write-Host "ERROR: Static directory not created: $staticDir" -ForegroundColor Red
    exit 1
}

$requiredFiles = @("Dashboard.js", "Panel.js", "Settings.js")
$missingFiles = @()

foreach ($file in $requiredFiles) {
    $filePath = Join-Path $staticDir $file
    if (Test-Path $filePath) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file (missing)" -ForegroundColor Red
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "ERROR: Some required files were not built:" -ForegroundColor Red
    $missingFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}

# Show file sizes
Write-Host ""
Write-Host "📊 Built files:" -ForegroundColor Cyan
Get-ChildItem $staticDir -Recurse -File | ForEach-Object {
    $size = [math]::Round($_.Length / 1KB, 2)
    $relativePath = $_.FullName.Replace($staticDir, "").TrimStart("\")
    Write-Host "  $relativePath - $size KB" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ Build completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Commit the built files: git add inventree_rop_engine/static/" -ForegroundColor White
Write-Host "  2. Push to repository: git commit -m 'Add built frontend' && git push" -ForegroundColor White
Write-Host "  3. Pull on server and install plugin" -ForegroundColor White
Write-Host ""
