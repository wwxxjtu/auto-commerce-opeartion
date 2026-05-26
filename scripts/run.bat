@echo off
"""
SMS Receiver Skill Launcher (Windows)
"""

rem Get the directory of this script
set "SCRIPT_DIR=%~dp0"
set "SKILL_DIR=%SCRIPT_DIR%.."

rem Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is required
    pause
    exit /b 1
)

rem Check if the skill script exists
set "SKILL_SCRIPT=%SCRIPT_DIR%sms_receiver.py"
if not exist "%SKILL_SCRIPT%" (
    echo Error: SMS receiver script not found
    pause
    exit /b 1
)

rem Run the skill with provided arguments
python "%SKILL_SCRIPT%" %*
