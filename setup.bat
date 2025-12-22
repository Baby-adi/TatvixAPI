@echo off
setlocal enabledelayedexpansion

:: ---------------------------------------------
:: Check and create virtual environment
:: ---------------------------------------------
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment.
        pause
        exit /b
    )
)

:: ---------------------------------------------
:: Activate virtual environment
:: ---------------------------------------------
call .venv\Scripts\activate
echo Virtual environment activated.
echo.

:: ---------------------------------------------
:: Check if requirements.txt exists
:: ---------------------------------------------
if exist requirements.txt (
    echo Requirements file detected.

    :: Ask user whether to install dependencies
    set /p install_req="Install dependencies from requirements.txt (y/n): "

    if /i "!install_req!"=="y" (
        echo Installing dependencies...
        pip install -r requirements.txt
        if !errorlevel! neq 0 (
            echo Dependency installation failed.
            pause
            exit /b
        )
    )
)

:: ------------------------------
:: MAIN MENU
:: ------------------------------
:MENU
cls
echo ========================================
echo        SYSTEM STARTUP MENU
echo ========================================
echo.
echo 1. Start Weaviate Database
echo 2. Start Setup Server
echo 3. Start Application Server
echo 4. Stop Weaviate Database
echo 5. Stop Setup Server
echo 6. Stop Application Server
echo 7. Exit
echo.
set /p choice="Enter your choice: "

if "%choice%"=="1" goto START_WEAVIATE
if "%choice%"=="2" goto START_SETUP
if "%choice%"=="3" goto START_APP
if "%choice%"=="4" goto STOP_WEAVIATE
if "%choice%"=="5" goto STOP_SETUP
if "%choice%"=="6" goto STOP_APP
if "%choice%"=="7" goto EXIT

goto MENU


:START_WEAVIATE
echo Starting Weaviate + Transformers...
cd Gemma_Inference_API

:: ===== Check model folder =====
if exist models (
    echo Models folder already exists. Skipping download.
) else (
    echo Models folder not found. Running model_script.py...
    python model_script.py
    if !errorlevel! neq 0 (
        echo model_script.py failed!
        cd..
        pause
        goto MENU
    )
)

echo Starting docker compose...
docker compose up -d

cd ..
pause
goto MENU


:START_SETUP
echo Starting setup server...
start "Setup Server" cmd /k "python -m setupAPI.setup"
pause
goto MENU


:START_APP
echo Starting MCP server...
start "MCP Server" cmd /k "python -m McpServer.server"

echo Starting application server...
start "Application Server" cmd /k "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
pause
goto MENU


:STOP_WEAVIATE
echo Stopping Weaviate + Transformers...
cd Gemma_Inference_API
docker compose down
cd ..
pause
goto MENU

:STOP_SETUP
echo Stopping Setup Server...

taskkill /FI "WINDOWTITLE eq Setup Server*" /T /F >nul 2>&1

echo Setup server stopped.
pause
goto MENU

:STOP_APP
echo Stopping Application Server and MCP Server...

taskkill /FI "WINDOWTITLE eq MCP Server*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Application Server*" /T /F >nul 2>&1

echo All application processes stopped.
pause
goto MENU


:EXIT
echo Exiting...
pause
exit /b
