@echo off
echo =======================================
echo     Starting JournaBuddy via Docker
echo =======================================
echo.
echo Checking if Docker is running...

:: Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running! 
    echo Please start Docker Desktop and try running this script again.
    pause
    exit /b 1
)

echo [OK] Docker is running.
echo.
echo Building and starting the application containers...
docker-compose up --build -d

echo.
echo Waiting for the backend to initialize...
timeout /t 10 /nobreak >nul

echo.
echo Opening the application in your default web browser...
start http://localhost:5000

echo.
echo =======================================
echo     JournaBuddy is now running!
echo =======================================
echo.
echo Keep this window open. When you are finished using the application,
echo press any key in this window to stop the server and shut down Docker.
pause

echo.
echo Stopping the application containers...
docker-compose down
echo.
echo Application stopped successfully.
pause
