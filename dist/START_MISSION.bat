@echo off
TITLE DISPATCH CONSOLE // CENTRAL
COLOR 0A

:: --- SECURITY CHECK ---
IF NOT EXIST ".env" (
    ECHO [ERROR] .env file missing! The operation cannot proceed.
    PAUSE
    EXIT
)

:: --- LAUNCH ---
ECHO [SYSTEM] Loading Dispatch Core...
ECHO [SYSTEM] Reading credentials from encrypted environment (.env)...
ECHO [SYSTEM] Dashboard accessible at http://localhost:8000

dispatch.exe
PAUSE
