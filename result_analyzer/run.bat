@echo off
REM Hide this window and run the actual installation in a hidden window
if "%~1"=="" (
    start "" /min cmd /c "%~f0" :hidden
    exit
)

REM Get the directory where the batch file is located
set "SCRIPT_DIR=%~dp0"
cd "%SCRIPT_DIR%"

REM Launch the loading screen first - starting it directly instead of importing
start "" python "%SCRIPT_DIR%background_system\loading_screen.py"

REM Make sure any existing marker file is gone before starting
if exist "%SCRIPT_DIR%background_system\installation_complete.tmp" (
    del /f "%SCRIPT_DIR%background_system\installation_complete.tmp"
)

REM Give the loading screen a moment to initialize
timeout /t 2 /nobreak > nul

REM Create virtual environment in the background_system folder if it doesn't exist
if not exist "%SCRIPT_DIR%background_system\myenv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv "%SCRIPT_DIR%background_system\myenv"
    set INSTALL_PACKAGES=1
) else (
    echo Virtual environment already exists.
    set INSTALL_PACKAGES=0
)

REM Use direct references to the Python interpreter and pip
set "PYTHON_EXE=%SCRIPT_DIR%background_system\myenv\Scripts\python.exe"
set "PIP_EXE=%SCRIPT_DIR%background_system\myenv\Scripts\pip.exe"

REM Check if required packages are installed
REM Create a temporary file to verify package installation
echo import pandas, matplotlib, numpy, PIL, openpyxl > "%SCRIPT_DIR%background_system\check_packages.py"
"%PYTHON_EXE%" "%SCRIPT_DIR%background_system\check_packages.py" 2>nul
if not %ERRORLEVEL%==0 (
    echo Some packages are missing. Installing required packages...
    set INSTALL_PACKAGES=1
) else (
    echo All required packages already installed.
)

REM Install required packages if needed
if %INSTALL_PACKAGES%==1 (
    echo Installing required packages...
    "%PYTHON_EXE%" -m pip install pandas matplotlib numpy pillow openpyxl --quiet
)

REM Clean up temporary file
if exist "%SCRIPT_DIR%background_system\check_packages.py" (
    del /f "%SCRIPT_DIR%background_system\check_packages.py"
)

REM Sleep a bit to ensure animation is shown
timeout /t 3 /nobreak > nul

REM Create a marker file to indicate installation complete
echo Installation complete > "%SCRIPT_DIR%background_system\installation_complete.tmp"
echo Created marker file at: "%SCRIPT_DIR%background_system\installation_complete.tmp"

REM Give the loading screen time to detect the completion marker
timeout /t 5 /nobreak > nul

REM Make sure the loading screen has exited before continuing
tasklist /FI "WINDOWTITLE eq Setup in Progress" 2>NUL | find /I /N "python.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Waiting for loading screen to close...
    timeout /t 3 /nobreak > nul
)

REM Launch the main application with the virtual environment's Python
"%PYTHON_EXE%" "%SCRIPT_DIR%background_system\student_analysis.py"

REM Exit the hidden window
exit