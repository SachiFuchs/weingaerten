@echo off
rem Start the Weingaerten web server in the background.  Usage: start.cmd [-port ####]   (default 8008)
rem The generated server code lives in code\weingaerten-web (run weingaerten-web.md once to create it).
setlocal
set "PORT=8008"
:args
if "%~1"=="" goto argsdone
if /i "%~1"=="-port" (
  if "%~2"=="" goto usage
  set "PORT=%~2"
  shift & shift
  goto args
)
goto usage
:usage
echo Usage: start.cmd [-port ####]
exit /b 1
:argsdone
echo %PORT%| findstr /r "^[0-9][0-9]*$" >nul || goto usage
set "HERE=%~dp0"
set "HERE=%HERE:~0,-1%"
set "SERVER=%~dp0code\weingaerten_web"
if not exist "%SERVER%\__main__.py" (
  echo Server code missing: %SERVER% - run weingaerten-web.md first.
  exit /b 1
)
set "WEINGAERTEN_HOME=%HERE%"
set "PYTHON=python"
if exist "%HERE%\.env\Scripts\python.exe" set "PYTHON=%HERE%\.env\Scripts\python.exe"
start "Weingaerten web :%PORT%" /min "%PYTHON%" "%SERVER%" %PORT%
echo Weingaerten web server starting on http://localhost:%PORT%/haus3d
endlocal
