import sys

print("==== Echo Environment Verification ====")

# NumPy & Pandas
try:
    import numpy as np
    import pandas as pd
    print(f"NumPy version: {np.__version__}")
    print(f"Pandas version: {pd.__version__}")
except Exception as e:
    print(f"Error importing NumPy/Pandas: {e}")

# PyTorch
try:
    import torch
    import torchvision
    import torchaudio
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
except Exception as e:
    print(f"Error importing PyTorch modules: {e}")

# scikit-learn
try:
    import sklearn
    print(f"scikit-learn version: {sklearn.__version__}")
except Exception as e:
    print(f"Error importing scikit-learn: {e}")

# spaCy
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    print(f"spaCy version: {spacy.__version__}")
    print(f"Loaded model: {nlp.meta['name']} ({nlp.meta['version']})")
except Exception as e:
    print(f"Error importing spaCy or loading model: {e}")

# Transformers
try:
    from transformers import pipeline
    print("Transformers pipeline imported successfully")
except Exception as e:
    print(f"Error importing transformers: {e}")

# Sentence Transformers
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("SentenceTransformer loaded successfully")
except Exception as e:
    print(f"Error loading SentenceTransformer: {e}")

# Matplotlib
try:
    import matplotlib
    print(f"Matplotlib version: {matplotlib.__version__}")
except Exception as e:
    print(f"Error importing Matplotlib: {e}")

print("==== Environment Check Complete ====")

