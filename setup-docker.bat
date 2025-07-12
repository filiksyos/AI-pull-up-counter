@echo off
:: Setup script for AI Pull-Up Counter Docker environment (Windows)
:: This script helps you get started quickly with the Docker setup

echo 🐳 AI Pull-Up Counter Docker Setup
echo ==================================

:: Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo    Visit: https://docs.docker.com/desktop/windows/
    pause
    exit /b 1
)

:: Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Desktop first.
    echo    Visit: https://docs.docker.com/desktop/windows/
    pause
    exit /b 1
)

echo ✅ Docker and Docker Compose are installed

:: Create .env file if it doesn't exist
if not exist ".env" (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env file and add your OpenRouter API key:
    echo    OPENROUTER_API_KEY=your_actual_api_key_here
    echo.
    echo Opening .env file for editing...
    start notepad .env
    echo.
    pause
) else (
    echo ✅ .env file already exists
)

:: Create directories
echo 📁 Creating input and output directories...
if not exist "input_videos" mkdir input_videos
if not exist "output_videos" mkdir output_videos

:: Build the Docker image
echo 🏗️  Building Docker image...
docker-compose build

if %errorlevel% equ 0 (
    echo ✅ Docker image built successfully!
) else (
    echo ❌ Failed to build Docker image
    pause
    exit /b 1
)

:: Test the setup
echo 🧪 Testing the setup...
docker-compose run --rm pullup-counter python -c "import cv2; import mediapipe as mp; import numpy as np; print('✅ OpenCV version:', cv2.__version__); print('✅ MediaPipe version:', mp.__version__); print('✅ NumPy version:', np.__version__); print('✅ All dependencies are working!')"

if %errorlevel% equ 0 (
    echo.
    echo 🎉 Setup completed successfully!
    echo.
    echo Next steps:
    echo 1. Place your video files in the 'input_videos/' directory
    echo 2. Run: docker-compose up
    echo 3. Or run interactively: docker-compose exec pullup-counter bash
    echo.
    echo For more information, see README-Docker.md
) else (
    echo ❌ Setup test failed. Please check the logs above.
)

pause 