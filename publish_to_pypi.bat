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
echo Please enter your PyPI token when prompted:
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
