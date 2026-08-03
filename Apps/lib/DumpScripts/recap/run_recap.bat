@echo off
REM EnneadTab usage recap launcher. Finds a usable Python 3 and runs recap_main.py.
REM Forwards all args (e.g. --run, --dry-run, --selftest) to the script.
REM
REM Exit code is PROPAGATED, not masked -- Task Scheduler's "Last Result" must
REM reflect the actual recap outcome, not merely whether the bat ran. This is
REM the same trap run_collectors.bat documents; do not reintroduce it.
REM The "no Python interpreter found" branch still exits 0 because that is a
REM deployment gap, not a per-run failure worth alarming on every cycle.

setlocal
set SCRIPT_DIR=%~dp0
set RECAP=%SCRIPT_DIR%recap_main.py

REM 1. EnneadTab-OS dev venv
set VENV=%SCRIPT_DIR%..\..\..\..\.venv\Scripts\pythonw.exe
if exist "%VENV%" (
    "%VENV%" "%RECAP%" %* >nul 2>&1
    exit /b %ERRORLEVEL%
)

REM 2. Python Launcher (reliable on workstations with Python 3)
where py >nul 2>&1
if %ERRORLEVEL%==0 (
    py -3 "%RECAP%" %* >nul 2>&1
    exit /b %ERRORLEVEL%
)

REM 3. python.exe on PATH
where python >nul 2>&1
if %ERRORLEVEL%==0 (
    python "%RECAP%" %* >nul 2>&1
    exit /b %ERRORLEVEL%
)

REM 4. No Python found. Exit 0 -- a deployment gap, not a run failure.
exit /b 0
