@echo off
echo Starting Backend and Frontend servers...

REM Start backend in new window
start "Backend Server" cmd /k "cd /d C:\claude\poker-online-analyze\poker-online-analyze\backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001"

REM Wait a bit for backend to start
timeout /t 5

REM Start frontend in new window
start "Frontend Server" cmd /k "cd /d C:\claude\poker-online-analyze\poker-online-analyze\frontend && set PORT=3001 && npm start"

echo.
echo Servers are starting...
echo Backend: http://localhost:8001
echo Frontend: http://localhost:3001
echo API Docs: http://localhost:8001/docs
echo.
echo Press any key to exit this window...
pause >nul