@echo off
echo ==========================================================
echo  Registering Protein Design SOTA Agent Daily Task
echo ==========================================================
powershell -ExecutionPolicy Bypass -File "%~dp0setup_daily_task.ps1"
pause

