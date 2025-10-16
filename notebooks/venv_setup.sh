#!/bin/bash
# Create and activate virtual environment for TarAIntino

echo "🔧 Creating virtual environment 'taraintino_env'..."
python3.12 -m venv notebooks/taraintino_env

echo "🔧 Activating environment..."
source notebooks/taraintino_env/bin/activate

echo "📦 Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing dependencies from requirements.txt..."
pip install -r notebooks/requirements.txt

echo "🧩 Installing Jupyter kernel support..."
pip install ipykernel jupyter

echo "🧠 Registering environment as Jupyter kernel..."
python -m ipykernel install --user --name=taraintino_env --display-name "Python (taraintino_env)"

echo "✅ Setup complete."
echo "   Activate anytime with: source notebooks/taraintino_env/bin/activate"
echo "   Then in Jupyter, select kernel: Python (taraintino_env)"
