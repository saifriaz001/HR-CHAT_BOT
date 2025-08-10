# rag_engine/embedding_generator.py
import os, json, faiss, numpy as np
from sentence_transformers import SentenceTransformer

VECTORSTORE_DIR = "vectorstore"
DATA = "data/employees.json"
INDEX = os.path.join(VECTORSTORE_DIR, "faiss_ip.index")
MAP = os.path.join(VECTORSTORE_DIR, "id_mapping.json")

os.makedirs(VECTORSTORE_DIR, exist_ok=True)

with open(DATA, "r", encoding="utf-8") as f:
    employees = json.load(f)["employees"]

def describe(e):
    return (
        f"{e['name']} | {e['experience_years']} years | "
        f"skills: {', '.join(s.lower() for s in e['skills'])} | "
        f"projects: {', '.join(e['projects'])} | "
        f"availability: {e['availability']}"
    )

corpus = [describe(e) for e in employees]
ids    = [e["id"] for e in employees]

# Full model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Still good to keep batching to avoid spikes
emb = model.encode(
    corpus,
    convert_to_numpy=True,
    normalize_embeddings=True,
    batch_size=32,
    show_progress_bar=True,
).astype("float32")

index = faiss.IndexFlatIP(emb.shape[1])
index.add(emb)

faiss.write_index(index, INDEX)
with open(MAP, "w", encoding="utf-8") as f:
    json.dump({"ids": ids}, f)

print("✅ Cosine FAISS IP index saved to", INDEX)
