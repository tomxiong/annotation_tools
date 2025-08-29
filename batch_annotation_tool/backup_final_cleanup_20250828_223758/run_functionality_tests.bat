@echo off
REM ===================================================================
REM Panoramic Annotation GUI - Automated Functionality Testing
REM Windows Batch Script for Easy Test Execution
REM ===================================================================

title Panoramic GUI Functionality Tests

echo.
echo ===================================================================
echo    Panoramic Annotation GUI - Functionality Testing
echo ===================================================================
echo.

REM Navigate to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python or add it to your PATH
    pause
    exit /b 1
)

REM Show menu options
echo Available test options:
echo.
echo [1] Quick Functionality Test (3 cycles, ~2-5 minutes)
echo [2] Comprehensive Functionality Test (10 cycles, ~10-20 minutes)
echo [3] Create Test Data Only
echo [4] View Latest Test Report
echo [5] Exit
echo.

set /p choice="Select option [1-5]: "

REM Execute based on choice
if "%choice%"=="1" (
    echo.
    echo Running Quick Functionality Test...
    echo ===================================
    python run_functionality_tests.py --quick
    goto :end
)

if "%choice%"=="2" (
    echo.
    echo Running Comprehensive Functionality Test...
    echo ==========================================
    python run_functionality_tests.py
    goto :end
)

if "%choice%"=="3" (
    echo.
    echo Creating Test Data...
    echo ====================
    python run_functionality_tests.py --test-data-only
    goto :end
)

if "%choice%"=="4" (
    echo.
    echo Generating Latest Test Report...
    echo ===============================
    python run_functionality_tests.py --report-only
    goto :end
)

if "%choice%"=="5" (
    echo Exiting...
    goto :end
)

echo Invalid choice. Please select 1-5.
pause
goto :start

:end
echo.
echo ===================================================================
echo Test execution completed.
echo.
echo Log files location: test_logs\
echo Report files location: test_reports\
echo Test data location: D:\test\images
echo.
echo Press any key to exit...
pause >nul