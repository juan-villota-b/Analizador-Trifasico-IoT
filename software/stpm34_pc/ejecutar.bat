@echo off
cd /d "%~dp0"
python stpm34_pc.py --wait --plot
if errorlevel 1 pause
