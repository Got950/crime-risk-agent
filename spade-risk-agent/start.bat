@echo off
echo ========================================
echo   SPADE Risk Assessment Agent
echo   Starting Backend and Frontend...
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/4] Checking dependencies...
echo.

REM Check if backend dependencies are installed
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found
    pause
    exit /b 1
)

REM Check if frontend directory exists
if not exist "..\frontend\package.json" (
    echo ERROR: Frontend directory not found
    pause
    exit /b 1
)

echo [2/4] Starting FastAPI Backend...
echo    Backend will run on: http://127.0.0.1:8000
echo    API Docs: http://127.0.0.1:8000/docs
echo.

REM Start backend in a new window
start "SPADE Backend Server" cmd /k "cd /d %~dp0 && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

echo [3/4] Starting React Frontend...
echo    Frontend will run on: http://localhost:3000
echo.

REM Change to frontend directory
cd ..\frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo [4/4] Installing frontend dependencies (first time only)...
    call npm install
    echo.
) else (
    echo [4/4] Frontend dependencies already installed.
    echo.
)

REM Start frontend in a new window
start "SPADE React Frontend" cmd /k "npm start"

cd ..\spade-risk-agent

echo.
echo ========================================
echo   Both servers are starting...
echo ========================================
echo.
echo   Backend:  http://127.0.0.1:8000
echo   Frontend: http://localhost:3000
echo.
echo   Press any key to exit this window
echo   (Servers will continue running in separate windows)
echo.
pause >nul

