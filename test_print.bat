@echo off
REM Test script for barcode-label-printer package

echo Installing/upgrading barcode-label-printer package...
python -m pip install --upgrade barcode-label-printer

echo.
echo Running test script...
python test_print.py

pause
