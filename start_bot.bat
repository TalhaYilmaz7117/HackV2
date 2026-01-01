@echo off
echo Starting Telegram Bot...
echo =====================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Running setup...
    python setup.py
    if errorlevel 1 (
        echo Setup failed. Please check the error messages above.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo .env file not found. Please create it with your bot token.
    echo Copy .env.example to .env and edit it.
    pause
    exit /b 1
)

REM Start the bot
echo Starting bot...
python screen_display_bot.py

REM If bot crashes, keep window open
echo Bot stopped. Press any key to exit...
pause
