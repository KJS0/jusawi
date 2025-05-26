@echo off
echo ========================================
echo   EXIF 데이터 분석 및 촬영 습관 개선 도구
echo   캡스톤 디자인 프로젝트 v1.0
echo ========================================
echo.

REM 가상환경 확인 및 활성화
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo 가상환경이 없습니다. 시스템 Python을 사용합니다.
)

REM 의존성 확인
echo 의존성 확인 중...
python -c "import PIL, pandas, numpy, matplotlib, seaborn, piexif, sklearn" 2>nul
if errorlevel 1 (
    echo.
    echo [경고] 일부 필수 라이브러리가 설치되지 않았습니다.
    echo 다음 명령으로 설치해주세요:
    echo pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM 애플리케이션 실행
echo.
echo 애플리케이션 시작 중...
python main.py

REM 오류 처리
if errorlevel 1 (
    echo.
    echo [오류] 애플리케이션 실행 중 오류가 발생했습니다.
    echo 로그 파일(exif_analyzer.log)을 확인해주세요.
    echo.
    pause
)

echo.
echo 프로그램이 종료되었습니다.
pause 