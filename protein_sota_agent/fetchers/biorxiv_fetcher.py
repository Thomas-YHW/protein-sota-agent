import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
from protein_sota_agent.config import FETCH_LOOKBACK_DAYS, MAX_PAPERS_PER_SOURCE

BIORXIV_API_BASE = "https://api.biorxiv.org/details/biorxiv"

RELEVANT_CATEGORIES = {
    "bioinformatics",
    "bioengineering",
    "biophysics",
    "biochemistry",
    "synthetic biology",
    "molecular biology"
}

KEYWORDS = [
    # Protein Design & Generative Modeling
    "protein design",
    "de novo protein",
    "proteinmpnn",
    "rfdiffusion",
    "diffusion",
    "flow matching",
    "inverse folding",
    "antibody design",
    "nanobody design",
    "binder design",
    "alphafold",
    "esm3",
    "chai-1",
    "boltz-1",
    "structural biology",
    # Protein Language Models & Foundation Models
    "protein language model",
    "protein language models",
    "plm",
    "plms",
    "esm-2",
    "esm3",
    "progen",
    "saprot",
    "ankh",
    # Intrinsically Disordered Proteins, Low Complexity Regions & Ensembles
    "intrinsically disordered",
    "disordered protein",
    "disordered region",
    "conformational ensemble",
    "conformational dynamics",
    "fuzzy complex",
    "low complexity domain",
    "low complexity region",
    "low-complexity domain",
    "low-complexity region",
    "lcr",
    "lcd",
    "prion-like domain",
    "prld",
    "idr",
    "idps",
    # Phase Separation & Condensates
    "phase separation",
    "liquid-liquid phase separation",
    "llps",
    "biomolecular condensate",
    "biomolecular condensates",
    "membraneless organelle",
    "protein condensation",
    "coacervation",
    "coacervate",
    # Disease Targets
    "tdp-43",
    "fus protein",
    "hnrnpa1"
]

def fetch_biorxiv_papers(lookback_days: int = FETCH_LOOKBACK_DAYS, max_results: int = MAX_PAPERS_PER_SOURCE) -> List[Dict[str, Any]]:
    """
    Fetch recent preprints from bioRxiv relevant to protein design and structural engineering.
    """
    today = datetime.now()
    start_date = today - timedelta(days=lookback_days)
    interval = f"{start_date.strftime('%Y-%m-%d')}/{today.strftime('%Y-%m-%d')}"
    url = f"{BIORXIV_API_BASE}/{interval}/0/json"

    papers = []
    try:
        resp = requests.get(url, headers={"User-Agent": "ProteinDesignSOTABot/1.0"}, timeout=25)
        if resp.status_code != 200:
            print(f"[bioRxiv Fetcher] HTTP status {resp.status_code}")
            return []

        data = resp.json()
        collection = data.get("collection", [])

        for item in collection:
            category = item.get("category", "").lower()
            title = " ".join((item.get("title") or "").strip().split())
            abstract = " ".join((item.get("abstract") or "").strip().split())
            text_to_check = f"{title} {abstract}".lower()

            # Filter for relevance
            is_relevant_category = any(cat in category for cat in RELEVANT_CATEGORIES)
            matches_keyword = any(kw in text_to_check for kw in KEYWORDS)

            if not (is_relevant_category and matches_keyword):
                # Also allow if strongly matches specific design keywords even if category is general
                strong_kw = [
                    "protein design", "de novo", "proteinmpnn", "rfdiffusion", "antibody design",
                    "inverse folding", "tdp-43", "phase separation", "liquid-liquid phase separation",
                    "llps", "biomolecular condensate", "intrinsically disordered", "conformational ensemble",
                    "protein language model", "low complexity domain", "low complexity region"
                ]
                if not any(skw in text_to_check for skw in strong_kw):
                    continue

            doi = item.get("doi", "")
            paper_id = f"biorxiv_{doi.replace('/', '_')}" if doi else f"biorxiv_{item.get('biorxiv_url', '')}"

            authors_str = item.get("authors", "")
            authors = [a.strip() for a in authors_str.split(";") if a.strip()][:5]

            papers.append({
                "id": paper_id,
                "raw_id": doi,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published_date": item.get("date", today.strftime("%Y-%m-%d")),
                "url": f"https://doi.org/{doi}" if doi else item.get("biorxiv_url", ""),
                "pdf_url": f"https://www.biorxiv.org/content/{doi}.full.pdf" if doi else "",
                "source": "bioRxiv",
                "category": item.get("category", "bioinformatics")
            })

            if len(papers) >= max_results:
                break

    except Exception as e:
        print(f"[bioRxiv Fetcher] Warning: Failed to fetch from bioRxiv: {e}")

    return papers

