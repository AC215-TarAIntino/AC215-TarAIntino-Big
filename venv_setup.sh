#!/bin/bash
# Create and activate virtual environment for TarAIntino

echo "🔧 Creating virtual environment 'taraintino_env'..."
python3 -m venv taraintino_env

echo "🔧 Activating environment..."
source taraintino_env/bin/activate

echo "📦 Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "✅ Setup complete. Activate the environment anytime with:"
echo "   source taraintino_env/bin/activate"
