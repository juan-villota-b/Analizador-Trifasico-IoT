@echo off
cd /d "%~dp0"
python server.py --close-gui
if errorlevel 1 pause
