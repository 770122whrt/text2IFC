@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  wsl.exe --cd "%~dp0." --exec node ui/ifc-viewer/launcher.mjs stop
) else (
  node ui/ifc-viewer/launcher.mjs stop
)
if errorlevel 1 pause
