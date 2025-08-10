# rag_engine/embedding_generator.py  (replace with this cosine-ready version)
import json, os, faiss, numpy as np
from sentence_transformers import SentenceTransformer

VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "vectorstore")
DATA = os.getenv("EMP_JSON_PATH", "data/employees.json")
INDEX = os.path.join(VECTORSTORE_DIR, "faiss_ip.index")
MAP   = os.path.join(VECTORSTORE_DIR, "id_mapping.json")
os.makedirs("vectorstore", exist_ok=True)

with open(DATA) as f:
    employees = json.load(f)["employees"]

def describe(e):
    # short, signal-dense description works best
    return (
        f"{e['name']} | {e['experience_years']} years | "
        f"skills: {', '.join(s.lower() for s in e['skills'])} | "
        f"projects: {', '.join(e['projects'])} | "
        f"availability: {e['availability']}"
    )

corpus = [describe(e) for e in employees]
ids    = [e["id"] for e in employees]

model = SentenceTransformer("all-MiniLM-L6-v2")
emb = model.encode(corpus, convert_to_numpy=True, normalize_embeddings=True).astype("float32")

index = faiss.IndexFlatIP(emb.shape[1])  # cosine on unit vectors
index.add(emb)

faiss.write_index(index, INDEX)
with open(MAP, "w") as f:
    json.dump({"ids": ids}, f)

print("✅ Cosine FAISS IP index saved to", INDEX)
