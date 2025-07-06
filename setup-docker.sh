#!/bin/bash

# Setup script for AI Pull-Up Counter Docker environment
# This script helps you get started quickly with the Docker setup

echo "🐳 AI Pull-Up Counter Docker Setup"
echo "=================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your OpenRouter API key:"
    echo "   OPENROUTER_API_KEY=your_actual_api_key_here"
    echo ""
    read -p "Press Enter to continue after you've updated the .env file..."
else
    echo "✅ .env file already exists"
fi

# Create directories
echo "📁 Creating input and output directories..."
mkdir -p input_videos
mkdir -p output_videos

# Build the Docker image
echo "🏗️  Building Docker image..."
docker-compose build

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
else
    echo "❌ Failed to build Docker image"
    exit 1
fi

# Test the setup
echo "🧪 Testing the setup..."
docker-compose run --rm pullup-counter python -c "
import cv2
import mediapipe as mp
import numpy as np
print('✅ OpenCV version:', cv2.__version__)
print('✅ MediaPipe version:', mp.__version__)
print('✅ NumPy version:', np.__version__)
print('✅ All dependencies are working!')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Place your video files in the 'input_videos/' directory"
    echo "2. Run: docker-compose up"
    echo "3. Or run interactively: docker-compose exec pullup-counter bash"
    echo ""
    echo "For more information, see README-Docker.md"
else
    echo "❌ Setup test failed. Please check the logs above."
fi 