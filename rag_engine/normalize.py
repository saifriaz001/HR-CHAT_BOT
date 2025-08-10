# rag_engine/normalize.py
from .config_retrieval import normalize_token, EXPAND

def normalize_skills(skills):
    return list(dict.fromkeys(normalize_token(s) for s in skills))

def expand_skillset_for_indexing(skills):
    base = set(normalize_skills(skills))
    expanded = set(base)
    for s in base:
        if s in EXPAND:
            expanded |= {normalize_token(x) for x in EXPAND[s]}
    return sorted(expanded)
