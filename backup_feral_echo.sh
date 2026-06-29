#!/bin/bash
# FeralEcho GitHub Backup Script
# Run from ~/Desktop/FeralEcho

# Step 0: Ensure Git LFS is installed (optional for large files)
git lfs install

# Step 1: Ensure Git buffer is large enough
git config http.postBuffer 524288000   # 500 MB
git config --global http.maxRequestBuffer 1000M

# Step 2: Add and commit the refactored .gitignore
cat > .gitignore << 'EOF'
# === MEMORY & INDEX ===
*.index
*.faiss
data/
memory/
memory_backup/

# Exclude huge journal/log files individually
memory/reflection_journal.jsonl
memory/self_heal_journal.txt
memory/SELF_EDIT_MASTERY_.log
memory/memory_journal*.log
memory/dream_bridge.log

# === MODELS & BINARIES ===
models/
mistral_models/
llama.cpp/
my_python_project/

# === BACKUPS & SELF-EDIT PLANS ===  
app/core/self_edit_backups/
app/core/self_edit_plans/

# === PYTHON & OS NOISE ===
__pycache__/
*.pyc
*.log
.env
.DS_Store
*.tmp
sandbox/scripts/temp_*.py

# === LARGE FILES ===
*.png
*.zip
*.bin
*.onnx
*.pt
EOF

git add .gitignore
git commit -m "Refactored .gitignore to skip huge files"

# Step 3: Define top-level folders/files to backup in batches
declare -a batches=(
"app"
"archive_optional_files archived_files continuity_backups feral_tools sandbox"
"models mistral_models data"
"*.py *.json *.txt *.md"
"logs"
)

# Step 4: Commit & push each batch sequentially
for batch in "${batches[@]}"; do
    echo "=== Processing batch: $batch ==="
    git add $batch
    git commit -m "Backup batch: $batch" || echo "Nothing to commit in $batch"
    git push origin main
done

echo "=== FeralEcho backup complete! ==="

