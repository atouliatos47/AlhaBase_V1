@echo off
echo ========================================
echo Starting AlphaBase v4.0
echo ========================================
echo.

REM Check if config exists
if not exist alphabase_config.json (
    echo No configuration found. Running setup wizard...
    python setup.py
    echo.
)

echo Starting server...
echo Access the console at: http://localhost:8000/console/index.html
echo Press CTRL+C to stop the server
echo.

python main.py

pause