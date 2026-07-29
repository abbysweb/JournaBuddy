@echo off
echo =======================================
echo     Starting JournaBuddy Application
echo =======================================
echo.

set PATH=%PATH%;C:\Users\PC\AppData\Roaming\Python\Python312\Scripts

:: Check if Podman is available
where podman >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Podman Desktop detected.
    echo Building and starting containers via Podman Compose...
    podman compose up -d --build
    goto STARTED
)

:: Check if Docker is available
docker info >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Docker Desktop detected.
    echo Building and starting containers via Docker Compose...
    docker-compose up -d --build
    goto STARTED
)

echo [ERROR] Neither Podman Desktop nor Docker Desktop could be detected or started!
echo Please ensure Podman Desktop or Docker Desktop is installed and running.
pause
exit /b 1

:STARTED
echo.
echo =======================================
echo   JournaBuddy Stack Running:
echo   - Frontend: http://localhost
echo   - FastAPI Backend API: http://localhost:8000/api
echo   - MinIO Object Store: http://localhost:9001
echo =======================================
echo.
pause
