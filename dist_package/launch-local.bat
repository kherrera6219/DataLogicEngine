@echo off
SETLOCAL

echo Starting DataLogicEngine Local...

:: 1. Setup Environment
SET UKG_DATA_DIR=%CD%\local_data
SET API_HOST=127.0.0.1
SET DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ukg_db
SET REDIS_URL=redis://localhost:6379/0

IF NOT EXIST "%UKG_DATA_DIR%" mkdir "%UKG_DATA_DIR%"

:: 2. Start Backend in separate window
echo Launching Backend...
start "DataLogic_Backend" cmd /k "backend\DataLogic_Backend.exe"

:: 3. Start Frontend
echo Launching Frontend...
cd frontend
node server.js

pause
