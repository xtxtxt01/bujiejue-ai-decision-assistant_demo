@echo off
chcp 65001 >nul 2>&1
echo ================================
echo   Bu Jiu Jie - AI Decision Demo
echo ================================
echo.
echo Starting backend (port 8000)...
start "Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo.
echo Waiting 3 seconds...
ping -n 4 127.0.0.1 >nul
echo.
echo Starting frontend (port 5173)...
start "Frontend" cmd /k "cd /d %~dp0frontend && npx vite --port 5173"
echo.
echo ================================
echo Done!
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo ================================
echo.
pause
