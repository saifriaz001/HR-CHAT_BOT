# rag_engine/rag_pipeline.py  (replace the whole file with this)
import json
import os
import logging
from typing import List, Dict, Tuple
import numpy as np
import faiss
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import re

# ---------------------- setup ----------------------
load_dotenv()

# Gemini (optional; kept from your version)
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    GEMINI_MODEL = genai.GenerativeModel("gemini-2.5-flash")
except Exception:
    GEMINI_MODEL = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler("chatbot.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Data + FAISS cosine index
with open("data/employees.json") as f:
    EMPLOYEES = json.load(f)["employees"]

with open("vectorstore/id_mapping.json") as f:
    ID_MAPPING = json.load(f)["ids"]

FAISS_INDEX = faiss.read_index("vectorstore/faiss_ip.index")  # <— cosine/IP
EMB = SentenceTransformer("all-MiniLM-L6-v2")

# knobs
AVAIL_ORDER = {"available": 3, "2_weeks": 2, "1_month": 1, "allocated": 0}
WEIGHTS = {
    "skill_soft": 0.05,   # per required skill matched
    "domain_soft": 0.10,  # if domain tokens appear in projects
    "years_soft": 0.10,   # if exp >= requested
    "availability_soft": 0.05,  # prefer sooner availability
}
DOMAINS = ["healthcare","medical","fintech","ecommerce","education","banking","insurance","retail","saas","govt","logistics","pharma"]

# ---------------------- tiny parser ----------------------
def parse_query(q: str) -> Dict:
    ql = q.lower()
    m = re.search(r"(\d+)\s*\+?\s*years?", ql)
    min_years = int(m.group(1)) if m else None

    availability = None
    if "immediate" in ql or "available" in ql:
        availability = "available"
    elif "2 weeks" in ql or "two weeks" in ql or "2_weeks" in ql:
        availability = "2_weeks"
    elif "1 month" in ql or "one month" in ql or "1_month" in ql:
        availability = "1_month"

    # crude skill tokens
    tokens = re.findall(r"[a-z0-9\.\+\#\-]+", ql)
    STOP = {"find","need","someone","with","for","who","has","experience","years","year","in","a","an","the","project"}
    skills = [t for t in tokens if t not in STOP and not t.isdigit()]

    domains = [d for d in DOMAINS if d in ql]
    return {
        "min_years": min_years,
        "availability": availability,
        "required_skills": skills or None,
        "domains": domains or None,
        "raw_query": q,
    }

# ---------------------- retrieval ----------------------
def _embed_query(text: str) -> np.ndarray:
    return EMB.encode([text], convert_to_numpy=True, normalize_embeddings=True).astype("float32")

def _soft_boost(emp: Dict, parsed: Dict) -> float:
    score = 0.0
    es = {s.lower() for s in emp["skills"]}

    # + per required skill match (soft confirmation)
    if parsed["required_skills"]:
        for r in parsed["required_skills"]:
            if r in es:
                score += WEIGHTS["skill_soft"]

    # + domain in projects
    if parsed["domains"]:
        pj = " ".join(emp["projects"]).lower()
        if any(d in pj for d in parsed["domains"]):
            score += WEIGHTS["domain_soft"]

    # + years satisfied
    if parsed["min_years"] is not None and emp["experience_years"] >= parsed["min_years"]:
        score += WEIGHTS["years_soft"]

    # + availability preference
    score += WEIGHTS["availability_soft"] * (AVAIL_ORDER.get(emp["availability"], 0) / 3.0)

    return score

def _passes_hard(emp: Dict, parsed: Dict) -> bool:
    # hard filters kept minimal: years + availability + (strict skill if you want)
    if parsed["min_years"] is not None and emp["experience_years"] < parsed["min_years"]:
        return False
    if parsed["availability"] and emp["availability"] != parsed["availability"]:
        return False
    # NOTE: for strict skill hard‑filtering, uncomment below:
    # if parsed["required_skills"]:
    #     es = {s.lower() for s in emp["skills"]}
    #     for r in parsed["required_skills"]:
    #         if r not in es:
    #             return False
    return True

def retrieve_candidates(query: str, top_k: int = 3) -> List[Dict]:
    """
    Cosine top‑K (higher = better) + hard post‑filters + soft boosts.
    Returns list shaped for your CandidateOut schema, with match_score in [~0..1+boosts].
    """
    parsed = parse_query(query)
    qv = _embed_query(query)
    scores, idxs = FAISS_INDEX.search(qv, max(30, top_k))  # widen first stage
    scores = scores[0].tolist()
    idxs   = idxs[0].tolist()

    pool: List[Tuple[float, Dict]] = []
    for s, i in zip(scores, idxs):
        if i == -1:
            continue
        emp_id = ID_MAPPING[i]
        emp = next((e for e in EMPLOYEES if e["id"] == emp_id), None)
        if not emp: 
            continue
        if not _passes_hard(emp, parsed):
            continue
        pool.append((float(s), emp))

    # cold‑start relax if nothing passed hard filters
    if not pool:
        for s, i in zip(scores, idxs):
            if i == -1:
                continue
            emp_id = ID_MAPPING[i]
            emp = next((e for e in EMPLOYEES if e["id"] == emp_id), None)
            if emp:
                pool.append((float(s), emp))

    # add soft boosts and compute final score
    ranked = []
    for cos, emp in pool:
        boost = _soft_boost(emp, parsed)
        final = cos + boost
        ranked.append({
            "id": emp["id"],
            "name": emp["name"],
            "skills": emp["skills"],
            "experience_years": emp["experience_years"],
            "projects": emp["projects"],
            "availability": emp["availability"],
            "match_score": round(final, 4),
            "_cosine": round(cos, 4),
            "_boost": round(boost, 4),
        })

    ranked.sort(key=lambda r: (r["match_score"], AVAIL_ORDER.get(r["availability"], 0)), reverse=True)
    return ranked[:top_k]

# ---------------------- augmentation ----------------------
def augment_with_context(query: str, candidates: List[Dict]) -> str:
    lines = [f"User request:\n{query}\n", "Candidates:"]
    for c in candidates:
        lines.append(
            f"Name: {c['name']}\n"
            f"Experience: {c['experience_years']} years\n"
            f"Skills: {', '.join(c['skills'])}\n"
            f"Projects: {', '.join(c['projects'])}\n"
            f"Availability: {c['availability']}\n---"
        )
    return "\n".join(lines)

# ---------------------- generation ----------------------
def generate_response(context: str) -> str:
    prompt = (
        f"{context}\n\n"
        "You're an experienced HR assistant helping a hiring manager.\n"
        "Write a friendly, professional, and **narrative** style recommendation.\n"
        "Your response MUST:\n"
        "1. Start with 'Thank you for your query! I've reviewed the candidates...'\n"
        "2. Give 2–3 top recommendations in paragraph form, not as a bulleted list.\n"
        "3. For each candidate:\n"
        "   - Mention their name in bold.\n"
        "   - Describe their years of experience naturally.\n"
        "   - Highlight relevant skills inline (no **Key skills:** label).\n"
        "   - Briefly describe 1–2 standout projects in a sentence or two.\n"
        "   - Optionally include availability at the end of the paragraph.\n"
        "4. End with a closing sentence offering further assistance, e.g. asking if the user wants more profiles or to check availability.\n"
        "5. Avoid bullet points, numbered lists, or structured headings — keep it conversational."
    )

    try:
        response = GEMINI_MODEL.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"[Gemini ERROR] {e}")
        return (
            "Thank you for your query! I've found some matching candidates. "
            "Would you like me to share their details?"
        )
