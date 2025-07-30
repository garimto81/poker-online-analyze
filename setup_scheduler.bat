@echo off
echo ========================================
echo 포커 데이터 자동 수집 스케줄러 설정
echo ========================================
echo.

REM 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 이 스크립트는 관리자 권한이 필요합니다!
    echo 마우스 오른쪽 버튼을 클릭하고 "관리자 권한으로 실행"을 선택하세요.
    pause
    exit /b 1
)

echo 작업 스케줄러에 등록 중...
schtasks /create /xml "poker_crawl_task.xml" /tn "PokerDataCrawler" /f

if %errorLevel% equ 0 (
    echo.
    echo ✓ 작업 스케줄러 등록 완료!
    echo.
    echo 설정된 스케줄:
    echo - 작업 이름: PokerDataCrawler
    echo - 실행 시간: 매일 오전 3시
    echo - 실행 파일: %cd%\auto_crawl.bat
    echo.
    echo 작업 정보 확인:
    schtasks /query /tn "PokerDataCrawler" /fo LIST /v | findstr "작업 이름 상태 다음 실행 시간"
    echo.
    echo 즉시 테스트하려면 아래 명령을 실행하세요:
    echo schtasks /run /tn "PokerDataCrawler"
) else (
    echo.
    echo ✗ 작업 스케줄러 등록 실패!
    echo 오류 코드: %errorLevel%
)

echo.
pause