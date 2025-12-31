# PowerShell script to build and upload package to PyPI

Write-Host "Building package..." -ForegroundColor Green
python -m pip install --upgrade build twine
python -m build

Write-Host "`nChecking package..." -ForegroundColor Green
python -m twine check dist/*

Write-Host "`nUploading to PyPI..." -ForegroundColor Green

# Get PyPI token from environment variable
$PYPI_TOKEN = $env:PYPI_TOKEN
if (-not $PYPI_TOKEN) {
    Write-Host "Error: PYPI_TOKEN environment variable not set" -ForegroundColor Red
    Write-Host "Please set it using: `$env:PYPI_TOKEN = 'your-token-here'" -ForegroundColor Yellow
    exit 1
}

if ($LASTEXITCODE -eq 0) {
    python -m twine upload dist/* --username __token__ --password $PYPI_TOKEN
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n========================================" -ForegroundColor Green
        Write-Host "Package uploaded successfully!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "`nYour package is now available at:" -ForegroundColor Cyan
        Write-Host "https://pypi.org/project/barcode-label-printer/" -ForegroundColor Cyan
    } else {
        Write-Host "`nUpload failed. Please check the error messages above." -ForegroundColor Red
    }
} else {
    Write-Host "`nBuild or check failed. Please check the error messages above." -ForegroundColor Red
}
