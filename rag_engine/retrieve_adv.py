# rag_engine/retrieve_adv.py
import json, faiss, numpy as np
from sentence_transformers import SentenceTransformer
from .config_retrieval import WEIGHTS, AVAIL_ORDER, normalize_token
from .query_parser_adv import parse_query_adv

INDEX = "vectorstore/faiss_ip.index"
MAP   = "vectorstore/id_mapping.json"
DATA  = "data/employees.json"

index = faiss.read_index(INDEX)
ids = json.load(open(MAP))["ids"]
employees = {e["id"]: e for e in json.load(open(DATA))["employees"]}
model = SentenceTransformer("all-MiniLM-L6-v2")

def _embed(text: str):
    return model.encode([text], normalize_embeddings=True, convert_to_numpy=True).astype("float32")

def _base_retrieve(query, top_k=30):
    qv = _embed(query)
    scores, idxs = index.search(qv, top_k)
    return list(zip(scores[0].tolist(), idxs[0].tolist()))

def _has_required(emp, required):
    if not required: return True
    es = {normalize_token(s) for s in emp["skills"]}
    return all(r in es for r in required)

def _meets_years(emp, min_years):
    return True if min_years is None else emp["experience_years"] >= min_years

def _meets_avail(emp, availability):
    return True if availability is None else emp["availability"] == availability

def _soft_boost(emp, parsed):
    score = 0.0
    es = {normalize_token(s) for s in emp["skills"]}
    if parsed["required_skills"]:
        for r in parsed["required_skills"]:
            if r in es: score += WEIGHTS["skill_soft"]
    if parsed["domains"]:
        pj = " ".join(emp["projects"]).lower()
        if any(d in pj for d in parsed["domains"]):
            score += WEIGHTS["domain_soft"]
    if parsed["min_years"] is not None and emp["experience_years"] >= parsed["min_years"]:
        score += WEIGHTS["years_soft"]
    score += WEIGHTS["availability_soft"] * (AVAIL_ORDER.get(emp["availability"], 0) / 3.0)
    return score

def retrieve_with_rerank(query: str, top_k=10, use_cross_encoder=False, parsed=None):
    parsed = parsed or parse_query_adv(query)
    raw = _base_retrieve(query, top_k=30)

    filtered = []
    for s, i in raw:
        if i == -1: continue
        e = employees[ids[i]]
        if _has_required(e, parsed["required_skills"]) and _meets_years(e, parsed["min_years"]) and _meets_avail(e, parsed["availability"]):
            filtered.append({"employee": e, "cosine": float(s)})

    # cold-start relax
    if not filtered:
        for s, i in raw:
            if i == -1: continue
            e = employees[ids[i]]
            if _has_required(e, parsed["required_skills"]) and _meets_years(e, parsed["min_years"]):
                filtered.append({"employee": e, "cosine": float(s)})
        if not filtered:
            for s, i in raw:
                if i == -1: continue
                e = employees[ids[i]]
                if _has_required(e, parsed["required_skills"]):
                    filtered.append({"employee": e, "cosine": float(s)})
        if not filtered:
            filtered = [{"employee": employees[ids[i]], "cosine": float(s)} for s, i in raw if i != -1]

    for r in filtered:
        r["boost"] = _soft_boost(r["employee"], parsed)
        r["score"] = r["cosine"] + r["boost"]

    if use_cross_encoder:
        try:
            from .rerank_ce import cross_encoder_rerank
            filtered = cross_encoder_rerank(query, filtered, top_n=top_k)
        except Exception:
            pass

    filtered.sort(key=lambda x: (x["score"], AVAIL_ORDER.get(x["employee"]["availability"], 0)), reverse=True)
    return filtered[:top_k], parsed
