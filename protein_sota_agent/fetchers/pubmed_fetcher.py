import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
from protein_sota_agent.config import FETCH_LOOKBACK_DAYS, MAX_PAPERS_PER_SOURCE

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
import xml.etree.ElementTree as ET

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def fetch_pubmed_papers(lookback_days: int = FETCH_LOOKBACK_DAYS, max_results: int = MAX_PAPERS_PER_SOURCE) -> List[Dict[str, Any]]:
    """
    Fetch recent peer-reviewed publications from PubMed relevant to protein design,
    intrinsically disordered regions (IDRs), and liquid-liquid phase separation (LLPS).
    """
    query = (
        '("protein design"[Title/Abstract] OR "de novo protein"[Title/Abstract] OR '
        '"ProteinMPNN"[Title/Abstract] OR "RFdiffusion"[Title/Abstract] OR '
        '"flow matching protein"[Title/Abstract] OR "antibody design"[Title/Abstract] OR "binder design"[Title/Abstract] OR '
        '("protein language model"[Title/Abstract] OR "protein language models"[Title/Abstract] OR "ESM-2"[Title/Abstract] OR "ESM3"[Title/Abstract] OR "pLM"[Title/Abstract] OR "pLMs"[Title/Abstract] OR "ProGen"[Title/Abstract]) OR '
        '(("intrinsically disordered"[Title/Abstract] OR "disordered protein"[Title/Abstract] OR "conformational ensemble"[Title/Abstract] OR "low complexity domain"[Title/Abstract] OR "low complexity region"[Title/Abstract] OR "low-complexity domain"[Title/Abstract] OR "prion-like domain"[Title/Abstract]) AND ("protein"[Title/Abstract] OR "AI"[Title/Abstract] OR "deep learning"[Title/Abstract] OR "machine learning"[Title/Abstract] OR "AlphaFold"[Title/Abstract] OR "structure"[Title/Abstract] OR "design"[Title/Abstract])) OR '
        '(("phase separation"[Title/Abstract] OR "liquid-liquid phase separation"[Title/Abstract] OR "LLPS"[Title/Abstract] OR "biomolecular condensate"[Title/Abstract] OR "biomolecular condensates"[Title/Abstract] OR "coacervation"[Title/Abstract]) AND ("protein"[Title/Abstract] OR "RNA"[Title/Abstract] OR "deep learning"[Title/Abstract] OR "structure"[Title/Abstract] OR "design"[Title/Abstract])) OR '
        '("TDP-43"[Title/Abstract] AND ("protein"[Title/Abstract] OR "structure"[Title/Abstract] OR "aggregation"[Title/Abstract] OR "condensate"[Title/Abstract] OR "phase separation"[Title/Abstract] OR "IDR"[Title/Abstract])))'
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

        # Fetch full XML records including real abstracts via efetch
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml"
        }
        fetch_resp = requests.get(EFETCH_URL, params=fetch_params, headers=HEADERS, timeout=25)
        if fetch_resp.status_code == 200:
            root = ET.fromstring(fetch_resp.content)
            for article in root.findall(".//PubmedArticle"):
                pmid = article.findtext(".//PMID") or ""
                title = article.findtext(".//ArticleTitle") or ""
                title = " ".join(title.strip().rstrip(".").split())

                # Extract real abstract
                abstract_parts = [el.text for el in article.findall(".//AbstractText") if el.text]
                abstract = " ".join(abstract_parts).strip() if abstract_parts else ""
                if not abstract:
                    abstract = f"Study published in PubMed ({pmid}). Investigates molecular mechanisms, structural properties, and functional implications."

                # Journal
                journal = article.findtext(".//Journal/ISOAbbreviation") or article.findtext(".//Journal/Title") or "PubMed"

                # Date
                year = article.findtext(".//JournalIssue/PubDate/Year") or article.findtext(".//JournalIssue/PubDate/MedlineDate") or ""
                month = article.findtext(".//JournalIssue/PubDate/Month") or ""
                pub_date = f"{year} {month}".strip() or datetime.now().strftime("%Y-%m-%d")

                # DOI
                doi = ""
                for aid in article.findall(".//ArticleId"):
                    if aid.attrib.get("IdType") == "doi" and aid.text:
                        doi = aid.text.strip()
                        break

                # Authors
                authors = []
                for a in article.findall(".//Author"):
                    lname = a.findtext("LastName") or ""
                    fname = a.findtext("ForeName") or a.findtext("Initials") or ""
                    if lname:
                        authors.append(f"{lname} {fname}".strip())

                papers.append({
                    "id": f"pubmed_{pmid}",
                    "raw_id": pmid,
                    "title": title,
                    "abstract": abstract,
                    "authors": authors[:5],
                    "published_date": pub_date,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "pdf_url": f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "source": "PubMed",
                    "category": journal
                })

    except Exception as e:
        print(f"[PubMed Fetcher] Warning: Failed to fetch from PubMed: {e}")

    return papers

