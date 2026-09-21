import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from protein_sota_agent.config import FETCH_LOOKBACK_DAYS, MAX_PAPERS_PER_SOURCE

ARXIV_API_URL = "https://export.arxiv.org/api/query"

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

def fetch_arxiv_papers(lookback_days: int = FETCH_LOOKBACK_DAYS, max_results: int = MAX_PAPERS_PER_SOURCE) -> List[Dict[str, Any]]:
    """
    Fetch recent papers from arXiv covering protein design, inverse folding,
    diffusion, and related structural biology computational methods.
    """
    # Categories: Biomolecules (q-bio.BM), AI (cs.AI), Machine Learning (cs.LG), Quantitative Methods (q-bio.QM)
    cat_terms = ["cat:q-bio.BM", "cat:cs.AI", "cat:cs.LG", "cat:q-bio.QM"]
    kw_terms = [
        # Protein design & foundation AI
        '"protein design"',
        '"de novo protein"',
        '"ProteinMPNN"',
        '"RFdiffusion"',
        '"antibody design"',
        '"binder design"',
        '"inverse folding"',
        '"flow matching protein"',
        '"AlphaFold"',
        '"Chai-1"',
        '"Boltz-1"',
        # Protein Language Models (pLMs)
        '"protein language model"',
        '"protein language models"',
        '"ESM-2"',
        '"ESM3"',
        '"pLM"',
        # Intrinsically disordered proteins, low-complexity regions & conformational ensembles
        '"intrinsically disordered"',
        '"protein disorder"',
        '"conformational ensemble"',
        '"fuzzy complex"',
        '"low complexity domain"',
        '"low complexity region"',
        '"prion-like domain"',
        # Liquid-liquid phase separation & biomolecular condensates
        '"phase separation"',
        '"liquid-liquid phase separation"',
        '"biomolecular condensate"',
        '"biomolecular condensates"',
        '"TDP-43"'
    ]

    cat_query = " OR ".join(cat_terms)
    kw_query = " OR ".join([f'all:{kw}' for kw in kw_terms])
    search_query = f"({cat_query}) AND ({kw_query})"

    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results * 2, # fetch extra to allow date filtering
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    papers = []
    try:
        response = requests.get(ARXIV_API_URL, params=params, headers=headers, timeout=25)
        if response.status_code != 200:
            print(f"[arXiv Fetcher] Warning: Failed to fetch from arXiv: HTTP {response.status_code}")
            return []

        xml_data = response.content
        root = ET.fromstring(xml_data)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        for entry in root.findall("atom:entry", ATOM_NS):
            title = entry.findtext("atom:title", namespaces=ATOM_NS) or ""
            title = " ".join(title.strip().split())

            raw_id = entry.findtext("atom:id", namespaces=ATOM_NS) or ""
            # Extract clean arXiv ID e.g. 2405.12345v1
            arxiv_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id

            summary = entry.findtext("atom:summary", namespaces=ATOM_NS) or ""
            summary = " ".join(summary.strip().split())

            published_str = entry.findtext("atom:published", namespaces=ATOM_NS) or ""
            try:
                # ISO 8601 parsing e.g. 2026-05-12T14:00:00Z
                pub_dt = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
            except Exception:
                pub_dt = datetime.now(timezone.utc)

            # Check cutoff
            if pub_dt < cutoff_date:
                continue

            # Authors
            # Authors & Affiliations
            authors = []
            affiliations = []
            for author_el in entry.findall("atom:author", ATOM_NS):
                name = author_el.findtext("atom:name", namespaces=ATOM_NS)
                if name:
                    authors.append(name.strip())
                aff_text = author_el.findtext("arxiv:affiliation", namespaces={"arxiv": "http://arxiv.org/schemas/atom"})
                if aff_text and aff_text.strip():
                    affiliations.append(aff_text.strip())

            # Journal Ref or Comments (e.g. accepted at NeurIPS / Nature)
            journal_ref = entry.findtext("arxiv:journal_ref", namespaces={"arxiv": "http://arxiv.org/schemas/atom"}) or ""
            comment = entry.findtext("arxiv:comment", namespaces={"arxiv": "http://arxiv.org/schemas/atom"}) or ""
            journal = journal_ref.strip() if journal_ref else ("arXiv" + (f" ({comment.strip()})" if any(c in comment.lower() for c in ["neurips", "icml", "iclr", "cvpr", "nature", "science", "accepted"]) else ""))

            # Links
            abs_url = f"https://arxiv.org/abs/{arxiv_id}"
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            for link in entry.findall("atom:link", ATOM_NS):
                if link.attrib.get("title") == "pdf":
                    pdf_url = link.attrib.get("href", pdf_url)

            # Categories
            primary_cat_el = entry.find("arxiv:primary_category", ATOM_NS)
            primary_cat = primary_cat_el.attrib.get("term", "q-bio.BM") if primary_cat_el is not None else "q-bio.BM"

            papers.append({
                "id": f"arxiv_{arxiv_id}",
                "raw_id": arxiv_id,
                "title": title,
                "abstract": summary,
                "authors": authors[:5], # top authors
                "authors": authors[:8], # top authors
                "affiliations": list(dict.fromkeys(affiliations))[:6],
                "journal": journal,
                "published_date": pub_dt.strftime("%Y-%m-%d"),
                "url": abs_url,
                "pdf_url": pdf_url,
                "source": "arXiv",
                "category": primary_cat
            })

            if len(papers) >= max_results:
                break

    except Exception as e:
        print(f"[arXiv Fetcher] Warning: Failed to fetch from arXiv: {e}")

    return papers

