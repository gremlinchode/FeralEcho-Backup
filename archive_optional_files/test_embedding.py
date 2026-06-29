from sentence_transformers import SentenceTransformer

print("Initializing embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded. Generating embeddings...")

sentences = ["Hello world!", "Echo is alive."]
embeddings = model.encode(sentences)

print("Embeddings generated:")
for i, emb in enumerate(embeddings):
    print(f"Sentence: {sentences[i]}, Embedding length: {len(emb)}")

