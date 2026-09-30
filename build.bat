@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python tools\build_scroll.py %*
) else (
  py -3 tools\build_scroll.py %*
)
exit /b %errorlevel%
