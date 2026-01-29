@echo off
TITLE SPIDER-OPS DISPATCH CONSOLE
COLOR 0A

:: --- CREDENCIAIS ---
IF NOT EXIST ".env" (
    ECHO [ERROR] .env file missing! The operation cannot proceed.
    PAUSE
    EXIT
)

:: --- LANÇA ---
ECHO [SYSTEM] Loading Spider-Ops Server...
ECHO [SYSTEM] Access Dashboard at http://localhost:8000
spider-ops-server.exe
PAUSE
