@echo off
setlocal EnableExtensions
rem Removes the oversee skill from each agent's skills folder.

set "SRC=%~dp0"
set "FAILED=0"
set "SELF=0"

if not defined USERPROFILE goto :nohome

call :check_self "%USERPROFILE%\.agents\skills\oversee"
call :check_self "%USERPROFILE%\.claude\skills\oversee"
call :check_self "%USERPROFILE%\.gemini\config\skills\oversee"
call :check_self "%USERPROFILE%\.gemini\antigravity-cli\skills\oversee"
if "%SELF%"=="1" goto :self

call :remove_from "%USERPROFILE%\.agents\skills\oversee"
call :remove_from "%USERPROFILE%\.claude\skills\oversee"
call :remove_from "%USERPROFILE%\.gemini\config\skills\oversee"
call :remove_from "%USERPROFILE%\.gemini\antigravity-cli\skills\oversee"

if "%FAILED%"=="1" goto :fail
echo Done.
pause
exit /b 0

:check_self
if /i "%SRC%"=="%~1\" set "SELF=1"
goto :eof

:remove_from
if not exist "%~1\" (
    echo Not installed: "%~1"
    goto :eof
)
rmdir /s /q "%~1"
if exist "%~1\" (
    echo Error: could not remove "%~1"
    set "FAILED=1"
    goto :eof
)
echo Removed: "%~1"
goto :eof

:self
echo Error: this script is inside an installed copy of the skill. Run uninstall.bat from your repo copy instead.
goto :fail

:nohome
echo Error: USERPROFILE is not set.
goto :fail

:fail
pause
exit /b 1
