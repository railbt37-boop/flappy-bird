@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Flappy Bird — сервер
set PORT=8080
set URL=http://localhost:%PORT%/index.html

echo.
echo  === Flappy Bird — запуск сервера ===
echo.

REM 1) Python
where python >nul 2>&1
if %errorlevel%==0 (
    echo  [OK] Python найден, запуск http.server...
    echo  Откройте: %URL%
    echo  Закройте это окно для остановки.
    echo.
    start "" "%URL%"
    python -m http.server %PORT%
    goto :done
)

where py >nul 2>&1
if %errorlevel%==0 (
    echo  [OK] Python (py) найден...
    echo  Откройте: %URL%
    echo.
    start "" "%URL%"
    py -m http.server %PORT%
    goto :done
)

REM 2) PowerShell (всегда есть в Windows)
echo  Python не найден — запуск через PowerShell...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0server.ps1"
goto :done

:done
if errorlevel 1 (
    echo.
    echo  Ошибка запуска. Попробуйте:
    echo    1. Запустить start.bat от имени администратора
    echo    2. Установить Python с https://www.python.org/downloads/
    echo    3. Открыть вручную: %URL%  после успешного запуска
    echo.
)
pause
