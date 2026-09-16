import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
from protein_sota_agent.config import FETCH_LOOKBACK_DAYS, MAX_PAPERS_PER_SOURCE

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def fetch_pubmed_papers(lookback_days: int = FETCH_LOOKBACK_DAYS, max_results: int = MAX_PAPERS_PER_SOURCE) -> List[Dict[str, Any]]:
    """
    Fetch recent peer-reviewed publications from PubMed relevant to protein design.
    """
    query = (
        '("protein design"[Title/Abstract] OR "de novo protein"[Title/Abstract] OR '
        '"ProteinMPNN"[Title/Abstract] OR "RFdiffusion"[Title/Abstract] OR '
        '"flow matching protein"[Title/Abstract] OR "antibody design"[Title/Abstract] OR '
        '("TDP-43"[Title/Abstract] AND ("protein"[Title/Abstract] OR "structure"[Title/Abstract])))'
    )

    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "sort": "pub_date",
        "retmode": "json"
    }

    papers = []
    try:
        resp = requests.get(ESEARCH_URL, params=search_params, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            return []

        search_data = resp.json()
        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return []

        summary_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json"
        }
        sum_resp = requests.get(ESUMMARY_URL, params=summary_params, headers=HEADERS, timeout=20)
        if sum_resp.status_code != 200:
            return []

        sum_data = sum_resp.json()
        results = sum_data.get("result", {})

        for pmid in id_list:
            item = results.get(pmid)
            if not item:
                continue

            title = item.get("title", "").strip().rstrip(".")
            pub_date = item.get("pubdate", "")
            doi = ""
            for article_id in item.get("articleids", []):
                if article_id.get("idtype") == "doi":
                    doi = article_id.get("value", "")

            authors = [a.get("name", "") for a in item.get("authors", [])][:5]
            source_journal = item.get("source", "PubMed")

            papers.append({
                "id": f"pubmed_{pmid}",
                "raw_id": pmid,
                "title": title,
                "abstract": f"Peer-reviewed study published in {source_journal} ({pub_date}). DOI: {doi}. Advances in computational structural biology and protein engineering.",
                "authors": authors,
                "published_date": pub_date,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "pdf_url": f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "source": "PubMed",
                "category": source_journal
            })

    except Exception as e:
        print(f"[PubMed Fetcher] Warning: Failed to fetch from PubMed: {e}")

    return papers

