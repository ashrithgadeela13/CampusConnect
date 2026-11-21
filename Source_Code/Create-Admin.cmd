@echo off
setlocal
title CampusConnect - create an administrator
cd /d "%~dp0"
if not exist "%~dp0runtime\windows-x64\python.exe" goto missing
if not exist "%~dp0src\manage.py" goto missing
"%~dp0runtime\windows-x64\python.exe" -X utf8 "%~dp0src\manage.py" create-admin
set "result=%errorlevel%"
pause
exit /b %result%
:missing
echo The app files could not be found. Extract the whole ZIP into a folder,
echo then run this launcher from the Source_Code folder.
pause
exit /b 1
