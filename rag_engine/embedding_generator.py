# rag_engine/embedding_generator.py
import os, json, faiss, numpy as np
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from sentence_transformers import SentenceTransformer

VECTORSTORE_DIR = "vectorstore"
DATA = "data/employees.json"
INDEX = os.path.join(VECTORSTORE_DIR, "faiss_ip.index")
MAP = os.path.join(VECTORSTORE_DIR, "id_mapping.json")

# create the directory you actually intend to use
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

# If Free tier crashes on RAM, swap to "sentence-transformers/paraphrase-MiniLM-L3-v2"
model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L3-v2")

# Add batching to be memory-safe
emb = model.encode(
    corpus,
    convert_to_numpy=True,
    normalize_embeddings=True,
    batch_size=8,              # adjust up if you have more RAM
    show_progress_bar=False,
).astype("float32")

index = faiss.IndexFlatIP(emb.shape[1])  # cosine on unit vectors when normalized
index.add(emb)

faiss.write_index(index, INDEX)
with open(MAP, "w", encoding="utf-8") as f:
    json.dump({"ids": ids}, f)

print("✅ Cosine FAISS IP index saved to", INDEX)
