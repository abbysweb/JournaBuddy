@echo off
echo =======================================
echo     Starting JournaBuddy Locally
echo =======================================
echo.

REM Check if Python is in path
python --version >nul 2>&1
if errorlevel 1 goto :NoPython

REM Create virtual environment if it doesn't exist
if exist .venv goto :VenvExists
echo [INFO] Creating Python virtual environment (.venv)...
python -m venv .venv
if errorlevel 1 goto :VenvFailed

:VenvExists
REM Install requirements
echo [INFO] Installing/verifying backend dependencies.
echo        Please wait. This may take a minute on first run...
call .venv\Scripts\pip.exe install -r backend\requirements.txt
if errorlevel 1 goto :PipFailed

echo [OK] Backend dependencies ready.
echo.

REM Start browser (async)
echo [INFO] Opening JournaBuddy in your default browser...
start "" http://localhost:5000

REM Start the Flask app
echo [INFO] Starting Flask backend server...
call .venv\Scripts\python.exe backend\app.py
goto :EOF

:NoPython
echo [ERROR] Python is not installed or not in your PATH!
echo Please install Python and try running this script again.
pause
exit /b 1

:VenvFailed
echo [ERROR] Failed to create virtual environment!
pause
exit /b 1

:PipFailed
echo [ERROR] Failed to install dependencies!
pause
exit /b 1

:EOF
