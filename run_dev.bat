@echo off
REM Quick development server starter for Windows

echo Starting RiftboundOCR Development Server...
echo.

REM Check if venv exists
if not exist venv\ (
    echo ERROR: Virtual environment not found!
    echo Please run setup_local_dev.bat first
    pause
    exit /b 1
)

REM Activate venv
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist .env (
    echo WARNING: .env file not found!
    echo Creating from template...
    copy env.example .env
    echo Please edit .env with your settings
    pause
)

REM Start server
echo.
echo ============================================
echo Starting OCR service on http://localhost:8002
echo API Docs: http://localhost:8002/docs
echo Main API should be on port 8000 or 8001
echo Press CTRL+C to stop
echo ============================================
echo.

python src\main.py

