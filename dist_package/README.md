# DataLogicEngine - Local/Cloud Desktop Package

This package allows you to run DataLogicEngine locally on your Windows machine. It supports two main modes of operation:

## 1. Local-First Mode (Default)
Runs with a local database and cache. 
- **Database**: PostgreSQL (expected at localhost:5432)
- **Cache**: Redis (expected at localhost:6379)
- **Storage**: Data is stored in `%CD%\local_data` or `C:\ProgramData\DataLogicEngine`.

### How to Start:
1. Ensure PostgreSQL and Redis are installed and running locally.
2. Run `launch-local.bat`.
3. Open `http://localhost:3000` in your browser.

## 2. Cloud-Hybrid Mode
Run the application locally but connect to your existing cloud-based database and cache.
- **How to Config**: Edit the environment variables in `launch-local.bat` or the WinSW XML files in the `service` folder to point to your cloud URIs.

## 3. Windows Service Mode
For a permanent installation, use the provided WinSW configurations to run the Backend and Frontend as Windows Services.
- Runs silently in the background.
- Auto-starts with Windows.
- See `scripts\install.ps1` for orchestration details.

## Security Note
All sensitive data (like LLM API keys entered in the app) are encrypted using **Windows DPAPI** and tied to your Windows user account. They are never sent to the cloud.
