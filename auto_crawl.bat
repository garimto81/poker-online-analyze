@echo off
echo [%date% %time%] 자동 크롤링 시작 >> crawl_log.txt

REM 백엔드 서버 시작 (백그라운드에서)
echo 백엔드 서버 시작 중...
cd /d "C:\claude\poker-online-analyze\poker-online-analyze\backend"
start /B python -m uvicorn main:app --host 0.0.0.0 --port 4001 > nul 2>&1

REM 서버가 완전히 시작될 때까지 대기
echo 서버 시작 대기 중...
timeout /t 15 /nobreak > nul

REM 크롤링 실행
echo 크롤링 실행 중...
python scheduled_crawler.py

REM 백엔드 서버 종료
echo 서버 종료 중...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq uvicorn*" > nul 2>&1

echo [%date% %time%] 자동 크롤링 완료 >> ..\crawl_log.txt
exit