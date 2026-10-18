@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  wsl.exe --cd "%~dp0." --exec node ui/ifc-viewer/launcher.mjs start
) else (
  node ui/ifc-viewer/launcher.mjs start
)
if errorlevel 1 (
  echo Viewer failed to start. See ui\ifc-viewer\.artifacts\service-4178.log
  pause
  exit /b 1
)
start "" "http://127.0.0.1:4178/"
