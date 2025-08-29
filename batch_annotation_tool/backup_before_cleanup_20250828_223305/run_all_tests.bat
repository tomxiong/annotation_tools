@echo off
echo ========================================
echo GUI Environment Test Suite
echo ========================================
echo.

echo [1/3] Running Quick Environment Check...
echo ----------------------------------------
python quick_env_check.py
echo.

echo [2/3] Running Comprehensive Environment Test...  
echo ----------------------------------------
python test_gui_environment_setup.py
echo.

echo [3/3] Running Launch Method Tests...
echo ----------------------------------------
python test_gui_launch_methods.py
echo.

echo ========================================
echo Test Suite Complete
echo ========================================
echo.
echo Next steps:
echo 1. Review test results above
echo 2. Fix any failed tests using the suggestions
echo 3. Launch GUI with: python start_gui.py
echo.
pause