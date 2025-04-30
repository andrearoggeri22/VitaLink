@echo off
echo Esecuzione dei test per VitaLink...
cd /d %~dp0
python run_tests.py
pause
