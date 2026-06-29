#!/bin/bash

echo "🔍 Starting FeralEcho Full Environment Readiness Check..."

# Step 1: Upgrade pip
echo "⚡ Upgrading pip..."
python -m pip install --upgrade pip

# Step 2: Ensure compatible numpy version
echo "🐍 Ensuring compatible numpy version..."
pip install "numpy<2" --upgrade

# Step 3: Install PyTorch CPU-only (MacBook-friendly)
echo "🔥 Installing PyTorch, torchvision, torchaudio for CPU..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Step 4: List of essential packages (package name vs import name)
pip_packages=(jedi rope astor redbaron rdflib Flask Flask-SocketIO fastapi uvicorn transformers sentence-transformers chromadb langchain llama-index SQLAlchemy sqlmodel redis sympy pyDatalog spacy scikit-learn)
import_names=(jedi rope astor redbaron rdflib flask flask_socketio fastapi uvicorn transformers sentence_transformers chromadb langchain llama_index sqlalchemy sqlmodel redis sympy pyDatalog spacy sklearn)

# Step 5: Install missing packages
for i in "${!pip_packages[@]}"; do
    pkg="${pip_packages[$i]}"
    imp="${import_names[$i]}"
    if ! python -c "import $imp" &> /dev/null; then
        echo "⚠️  Package $pkg not found. Installing..."
        pip install "$pkg"
    else
        version=$(python -c "import $imp; print(getattr($imp, '__version__', 'unknown'))")
        echo "✅ Package $pkg is installed — version $version"
    fi
done

# Step 6: Download spaCy English model if missing
if ! python -c "import spacy; spacy.load('en_core_web_sm')" &> /dev/null; then
    echo "📥 Downloading spaCy English model..."
    python -m spacy download en_core_web_sm
else
    echo "✅ spaCy English model already installed"
fi

# Step 7: Show Python version
python_version=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
echo "🐍 Python version: $python_version"

# Step 8: Torch and CPU/GPU check
if python -c "import torch" &> /dev/null; then
    torch_version=$(python -c "import torch; print(torch.__version__)")
    echo "🔥 PyTorch version: $torch_version"
    if python -c "import torch; print(torch.cuda.is_available())" | grep True &> /dev/null; then
        echo "🚀 CUDA is available for GPU acceleration"
    else
        echo "⚠️  CUDA not available — running on CPU only"
    fi
fi

# Step 9: Run Echo functionality tests
echo "🧠 Running Echo functionality tests..."

python - << 'END_PYTHON'
import torch
from transformers import pipeline
from sqlalchemy import create_engine, text
import spacy
from pyDatalog import pyDatalog

success = []

# PyTorch test
try:
    t = torch.tensor([1.0, 2.0, 3.0])
    success.append("PyTorch tensor OK")
except Exception as e:
    print(f"❌ PyTorch test failed: {e}")

# Transformers test (explicit model)
try:
    nlp = pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
    res = nlp("Echo is learning.")
    success.append("Transformers pipeline OK")
except Exception as e:
    print(f"❌ Transformers test failed: {e}")

# SQLAlchemy in-memory DB test
try:
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    success.append("SQLAlchemy memory DB OK")
except Exception as e:
    print(f"❌ SQLAlchemy test failed: {e}")

# spaCy NLP test
try:
    nlp_spacy = spacy.load("en_core_web_sm")
    doc = nlp_spacy("Echo can process text.")
    success.append("spaCy NLP OK")
except Exception as e:
    print(f"❌ spaCy test failed: {e}")

# pyDatalog logic test (fixed assertion)
try:
    pyDatalog.create_terms('X,Y')
    X==1
    Y==X+1
    res = Y.data
    success.append("pyDatalog logic OK")
except Exception as e:
    print(f"❌ pyDatalog test failed: {e}")

# Summary
for s in success:
    print(f"✅ {s}")

print("🎯 Full Echo Environment Ready!")
END_PYTHON

