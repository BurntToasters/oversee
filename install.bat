@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Installs or updates only the oversee payload, with per-target recovery.

set "SRC=%~dp0"
set "STAGE="
if not defined USERPROFILE goto :nohome
if not exist "%SRC%SKILL.md" goto :missing
if not exist "%SRC%references\harnesses.md" goto :missing
for %%F in ("%SRC%SKILL.md" "%SRC%references\harnesses.md") do if %%~zF==0 goto :missing

set "DEST=%USERPROFILE%\.agents\skills\oversee"
call :install_to
if errorlevel 1 goto :fail
set "DEST=%USERPROFILE%\.claude\skills\oversee"
call :install_to
if errorlevel 1 goto :fail
set "DEST=%USERPROFILE%\.gemini\config\skills\oversee"
call :install_to
if errorlevel 1 goto :fail
set "DEST=%USERPROFILE%\.gemini\antigravity-cli\skills\oversee"
call :install_to
if errorlevel 1 goto :fail
echo Start a new agent session to load the skill.
pause
exit /b 0

:install_to
set "OLD_SKILL=0"
set "OLD_REFS=0"
set "NEW_SKILL=0"
set "NEW_REFS=0"
if /i "%SRC%"=="%DEST%\" goto :skip_self
if not exist "%DEST%\" mkdir "%DEST%"
if not exist "%DEST%\" goto :install_failed
set "STAGE=%DEST%.stage-%RANDOM%-%RANDOM%"
if exist "%STAGE%" goto :stage_collision
mkdir "%STAGE%"
if errorlevel 1 goto :stage_collision
copy /y "%SRC%SKILL.md" "%STAGE%\SKILL.md" >nul
if errorlevel 1 goto :install_failed
xcopy "%SRC%references" "%STAGE%\references\" /e /i /y /q >nul
if errorlevel 1 goto :install_failed
if not exist "%STAGE%\references\harnesses.md" goto :install_failed
if exist "%DEST%\SKILL.md\" goto :install_failed
if exist "%DEST%\SKILL.md" (
    move "%DEST%\SKILL.md" "%STAGE%\old-skill" >nul
    if errorlevel 1 goto :install_failed
    set "OLD_SKILL=1"
)
if exist "%DEST%\references" (
    if not exist "%DEST%\references\" goto :install_failed
    move "%DEST%\references" "%STAGE%\old-references" >nul
    if errorlevel 1 goto :install_failed
    set "OLD_REFS=1"
)
move "%STAGE%\SKILL.md" "%DEST%\SKILL.md" >nul
if errorlevel 1 goto :install_failed
set "NEW_SKILL=1"
move "%STAGE%\references" "%DEST%\references" >nul
if errorlevel 1 goto :install_failed
set "NEW_REFS=1"
rmdir /s /q "%STAGE%"
if exist "%STAGE%\" (
    echo Warning: updated payload; backup cleanup failed at "%STAGE%"
    exit /b 1
)
set "STAGE="
echo Installed/updated: "%DEST%"
exit /b 0

:skip_self
echo Skipped: "%DEST%" is this folder.
exit /b 0

:stage_collision
set "STAGE="
goto :install_failed

:install_failed
echo Error: could not install to "%DEST%"
if not defined STAGE exit /b 1
if "%NEW_SKILL%"=="1" del /q "%DEST%\SKILL.md"
if "%NEW_SKILL%"=="1" if exist "%DEST%\SKILL.md" goto :recovery
if "%NEW_REFS%"=="1" rmdir /s /q "%DEST%\references"
if "%NEW_REFS%"=="1" if exist "%DEST%\references" goto :recovery
if "%OLD_SKILL%"=="1" (
    move "%STAGE%\old-skill" "%DEST%\SKILL.md" >nul
    if errorlevel 1 goto :recovery
)
if "%OLD_REFS%"=="1" (
    move "%STAGE%\old-references" "%DEST%\references" >nul
    if errorlevel 1 goto :recovery
)
rmdir /s /q "%STAGE%"
set "STAGE="
exit /b 1

:recovery
echo Error: restore failed; recovery files retained at "%STAGE%"
exit /b 1

:missing
echo Error: SKILL.md and references\harnesses.md must be next to this script.
goto :fail

:nohome
echo Error: USERPROFILE is not set.
goto :fail

:fail
pause
exit /b 1
