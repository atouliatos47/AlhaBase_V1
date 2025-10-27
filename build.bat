@echo off
echo ========================================
echo Building AlphaBase Executable
echo ========================================
echo.
echo This will create a standalone Windows executable.
echo Please wait, this may take several minutes...
echo.

REM Kill any running AlphaBase processes
taskkill /F /IM AlphaBase.exe 2>nul

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Clean previous builds
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul

REM Build with PyInstaller
pyinstaller alphabase.spec

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo The executable is in the 'dist\AlphaBase' folder.
echo.
echo To distribute:
echo 1. Copy the entire 'dist\AlphaBase' folder
echo 2. Users run AlphaBase.exe
echo.
pause