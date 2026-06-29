from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from llama_cpp import convert_hf_model_to_gguf

# Hugging Face model name
model_name = "mistralai/Mistral-7B-Instruct-v0.1"

# Output folder
output_dir = Path("models/mistral")
output_dir.mkdir(parents=True, exist_ok=True)

print(f"Loading {model_name}...")
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

print("Converting to GGUF (quantized Q4_0)...")
convert_hf_model_to_gguf(
    model_name,
    str(output_dir / "Mistral-7B-Instruct-v0.1.Q4_0.gguf"),
    vocab_only=False,
    quantize="q4_0"
)

print(f"✅ Done! Saved to {output_dir}/Mistral-7B-Instruct-v0.1.Q4_0.gguf")

