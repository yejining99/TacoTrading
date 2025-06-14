@echo off
REM TACO Trading 일일 자동 업데이트 배치 파일
REM Windows Task Scheduler에서 이 파일을 실행하도록 설정하세요.

echo ========================================
echo TACO Trading 일일 업데이트 시작
echo 시작 시간: %date% %time%
echo ========================================

REM 스크립트 디렉토리로 이동
cd /d "%~dp0"

REM Python 스크립트 실행
python daily_update.py

REM 결과 확인
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo 업데이트 성공적으로 완료
    echo 완료 시간: %date% %time%
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 업데이트 중 오류 발생 (코드: %ERRORLEVEL%)
    echo 완료 시간: %date% %time%
    echo 로그 파일을 확인해주세요.
    echo ========================================
)

pause 