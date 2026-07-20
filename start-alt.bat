@echo off
chcp 65001 >nul 2>&1
echo ================================
echo   Bu Jiu Jie - AI Decision Demo
echo   (Alternative Ports)
echo ================================
echo.
echo Starting backend (port 8001)...
start "Backend-Alt" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
echo.
echo Waiting 3 seconds...
ping -n 4 127.0.0.1 >nul
echo.
echo Starting frontend (port 5174)...
start "Frontend-Alt" cmd /k "cd /d %~dp0frontend && npx vite --port 5174"
echo.
echo ================================
echo Done!
echo Frontend: http://localhost:5174
echo Backend:  http://localhost:8001
echo ================================
echo.
echo NOTE: Remember to update frontend API URL to port 8001
echo.
pause
