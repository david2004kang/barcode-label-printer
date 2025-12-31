@echo off
REM Script to build and upload package to PyPI

echo Building package...
python -m pip install --upgrade build twine
python -m build

echo.
echo Checking package...
python -m twine check dist/*

echo.
echo Uploading to PyPI...
if "%PYPI_TOKEN%"=="" (
    echo Error: PYPI_TOKEN environment variable not set
    echo Please set it using: set PYPI_TOKEN=your-token-here
    pause
    exit /b 1
)
python -m twine upload dist/* --username __token__ --password %PYPI_TOKEN%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Package uploaded successfully!
    echo ========================================
    echo.
    echo Your package is now available at:
    echo https://pypi.org/project/barcode-label-printer/
) else (
    echo.
    echo Upload failed. Please check the error messages above.
)

pause
