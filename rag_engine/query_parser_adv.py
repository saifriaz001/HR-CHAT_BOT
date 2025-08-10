# rag_engine/query_parser_adv.py
import re
from .config_retrieval import normalize_token

DOMAINS = ["healthcare","medical","fintech","ecommerce","education","banking","insurance","retail","saas","govt","logistics","pharma"]

def parse_query_adv(q: str):
    ql = q.lower()
    m = re.search(r"(\d+)\s*\+?\s*years?", ql)
    min_years = int(m.group(1)) if m else None

    availability = None
    if "immediate" in ql or "available" in ql: availability = "available"
    elif "2 weeks" in ql or "two weeks" in ql or "2_weeks" in ql: availability = "2_weeks"
    elif "1 month" in ql or "one month" in ql or "1_month" in ql: availability = "1_month"

    tokens = re.findall(r"[a-z0-9\.\+\#\-]+", ql)
    STOP = {"find","need","someone","with","for","who","has","experience","years","year","in","a","an","the","project"}
    req = [normalize_token(t) for t in tokens if t not in STOP and not t.isdigit()]
    domains = [d for d in DOMAINS if d in ql]

    return {
        "min_years": min_years,
        "availability": availability,
        "required_skills": req or None,
        "nice_skills": None,
        "domains": domains or None,
        "raw_query": q,
    }
