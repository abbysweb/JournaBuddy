@echo off
echo ===================================================
echo   JournaBuddy GitHub Upload Helper
echo ===================================================
echo.

:: Check if git is installed
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed or not in your PATH!
    echo Please download and install Git from: https://git-scm.com/
    echo After installing, restart your terminal and run this script again.
    echo.
    pause
    exit /b 1
)

:: Check if .git is initialized
if not exist ".git" (
    echo [INFO] Git repository not initialized. Initializing now...
    git init
    echo.
)

:: Ask for remote repository URL (defaulting to user's profile path)
echo Enter your target GitHub repository URL.
echo (Example: https://github.com/abbysweb/JournaBuddy.git)
set /p REPO_URL="Repository URL: "

if "%REPO_URL%"=="" (
    echo [ERROR] Repository URL cannot be empty.
    pause
    exit /b 1
)

:: Set remote origin (remove existing if any to avoid conflicts)
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%

:: Remove unnecessary files from tracking just in case
echo.
echo Cleaning up unnecessary files...
git rm -r --cached books/ .opencode/ Report/main.aux Report/main.log Report/main.out Report/main.toc backend/dummy.pdf backend/uploads/dummy.pdf backend/uploads/test.pdf "Plan.md" "Free Model.md" >nul 2>&1

:: Stage all files
echo.
echo Staging files for upload...
git add .

:: Commit files
echo.
echo Committing files...
git commit -m "Refactor: Fix security bugs, path errors, runtime crashes, and add clean comments"

:: Push to remote origin
echo.
echo Pushing code to GitHub...
echo (Note: You may be prompted to log in/authenticate with your GitHub account)
git branch -M main
git push -u origin main

echo.
echo ===================================================
echo   Upload process complete!
echo ===================================================
pause
