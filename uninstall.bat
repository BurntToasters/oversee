@echo off
setlocal EnableExtensions
rem Removes the oversee skill from each agent's skills folder.

set "SRC=%~dp0"
set "FAILED=0"
set "SELF=0"

if not defined USERPROFILE goto :nohome

set "TARGET=%USERPROFILE%\.agents\skills\oversee"
call :check_self
set "TARGET=%USERPROFILE%\.claude\skills\oversee"
call :check_self
set "TARGET=%USERPROFILE%\.gemini\config\skills\oversee"
call :check_self
set "TARGET=%USERPROFILE%\.gemini\antigravity-cli\skills\oversee"
call :check_self
if "%SELF%"=="1" goto :self

set "TARGET=%USERPROFILE%\.agents\skills\oversee"
call :remove_from
set "TARGET=%USERPROFILE%\.claude\skills\oversee"
call :remove_from
set "TARGET=%USERPROFILE%\.gemini\config\skills\oversee"
call :remove_from
set "TARGET=%USERPROFILE%\.gemini\antigravity-cli\skills\oversee"
call :remove_from

if "%FAILED%"=="1" goto :fail
echo Done.
pause
exit /b 0

:check_self
if /i "%SRC%"=="%TARGET%\" set "SELF=1"
goto :eof

:remove_from
if not exist "%TARGET%\" (
    echo Not installed: "%TARGET%"
    goto :eof
)
rmdir /s /q "%TARGET%"
if exist "%TARGET%\" (
    echo Error: could not remove "%TARGET%"
    set "FAILED=1"
    goto :eof
)
echo Removed: "%TARGET%"
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
