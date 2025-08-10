# rag_engine/config_retrieval.py
SYNONYMS = {
    "k8s": "kubernetes", "tf": "tensorflow", "rn": "react native",
    "js": "javascript", "ts": "typescript", "sklearn": "scikit-learn",
    "pgsql": "postgresql", "py": "python",
}
EXPAND = {
    "kubernetes": {"k8s"},
    "tensorflow": {"tf"},
    "react native": {"rn"},
    "javascript": {"js"},
    "typescript": {"ts"},
    "scikit-learn": {"sklearn"},
    "postgresql": {"pgsql"},
    "python": {"py"},
    "aws": {"amazon web services"},
    "amazon web services": {"aws"},
}
def normalize_token(t: str) -> str:
    t = t.strip().lower()
    return SYNONYMS.get(t, t)

WEIGHTS = {
    "skill_soft": 0.05,
    "domain_soft": 0.10,
    "years_soft": 0.10,
    "availability_soft": 0.05,
}
AVAIL_ORDER = {"available": 3, "2_weeks": 2, "1_month": 1, "allocated": 0}
