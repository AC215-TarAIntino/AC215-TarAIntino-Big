#!/bin/bash
# TarAIntino - Quick Setup Script
# This script helps set up the environment for local development

set -e

echo "🎬 TarAIntino - Setup Script"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys!"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Copy .env to service directories
echo "📋 Copying .env to service directories..."
cp .env screenplay-writer/.env 2>/dev/null || echo "  ⚠️  screenplay-writer/.env not copied"
cp .env scene-decomposer/.env 2>/dev/null || echo "  ⚠️  scene-decomposer/.env not copied"
echo ""

# Check for GCS credentials
echo "🔐 Checking for GCS credentials..."
if [ ! -f "quiz-vector/secrets/llm-service-account.json" ]; then
    echo "  ⚠️  quiz-vector/secrets/llm-service-account.json not found"
    echo "     Please add your GCS service account JSON file"
fi

if [ ! -f "Video_Generator/secrets.json" ]; then
    echo "  ⚠️  Video_Generator/secrets.json not found"
    echo "     Please add your GCS service account JSON file"
fi
echo ""

# Install Python dependencies for orchestration scripts
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
echo ""

# Build and start services
echo "🚀 Building and starting all services..."
echo "   This may take a few minutes..."
echo ""

docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "🏥 Checking service health..."
echo ""

# Function to check service health
check_health() {
    local service_name=$1
    local url=$2

    if curl -s -f "$url" > /dev/null 2>&1; then
        echo "  ✅ $service_name is healthy"
        return 0
    else
        echo "  ⚠️  $service_name is not responding (may still be starting)"
        return 1
    fi
}

check_health "ChromaDB" "http://localhost:8000/api/v1/heartbeat"
check_health "Quiz Service" "http://localhost:8082/health"
check_health "Screenplay Writer" "http://localhost:8080/health"
check_health "Scene Decomposer" "http://localhost:8001/health"
check_health "Video Generator" "http://localhost:8003/health"
check_health "Frontend" "http://localhost:3000"

echo ""
echo "================================"
echo "🎉 Setup Complete!"
echo "================================"
echo ""
echo "Services are running at:"
echo "  • Frontend:           http://localhost:3000"
echo "  • Quiz Service:       http://localhost:8082"
echo "  • Screenplay Writer:  http://localhost:8080"
echo "  • Scene Decomposer:   http://localhost:8001"
echo "  • Video Generator:    http://localhost:8003"
echo "  • ChromaDB:           http://localhost:8000"
echo ""
echo "Useful commands:"
echo "  • View logs:          docker-compose logs -f"
echo "  • Stop services:      docker-compose down"
echo "  • Restart:            docker-compose restart"
echo ""
echo "Next steps:"
echo "  1. Make sure your API keys are set in .env"
echo "  2. Add GCS credentials to the secrets directories"
echo "  3. Test the pipeline with: python pipeline2.py"
echo ""
echo "📖 See ORCHESTRATION_README.md for detailed documentation"
echo ""
