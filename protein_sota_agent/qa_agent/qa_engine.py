"""
Interactive & Automated Paper Question-Answering (QA) Engine.
Enables deep scientific interrogation of papers by ID, DOI, URL, or abstract.
"""

import os
import re
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from protein_sota_agent.config import GEMINI_API_KEY, GEMINI_MODEL

QA_SYSTEM_PROMPT = """You are an expert scientific consultant in Computational Biology, Protein Design, and Biophysics of Intrinsically Disordered Regions (IDRs) and Phase Separation.

You will answer scientific questions about a paper using its metadata, abstract, and text.
Guidelines:
1. Be rigorous, technically precise, and objective.
2. Directly cite specific techniques, numbers, datasets, or claims from the provided paper.
3. If an answer cannot be deduced from the abstract or text, state clearly: "The provided abstract/text does not specify this detail; experimental verification would require full text analysis."
4. Format your response cleanly with clear headings or bullet points where appropriate.
"""

STANDARD_AUDIT_QUESTIONS = [
    ("Core Problem", "What specific biological, structural, or engineering bottleneck does this work solve?"),
    ("Technical Innovation", "What is the exact novel architecture, algorithmic contribution, or biophysical formulation introduced?"),
    ("Validation Rigor", "What experimental wet-lab assays (e.g. cryo-EM, SPR, BLI, microscopy) or computational benchmarks were used to validate the claims?"),
    ("Limitations & Risks", "What are the primary caveats, potential failure modes, missing controls, or risks of data leakage / overfitting?"),
    ("TDP-43 & Condensate Utility", "How can this study's findings, models, or design protocols be applied to IDR engineering, liquid-liquid phase separation (LLPS), or TDP-43 LCD aggregation?")
]

class PaperQAEngine:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name or GEMINI_MODEL
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def answer_question(self, paper: Dict[str, Any], question: str) -> str:
        """Answer a specific question about a paper."""
        if not self.client:
            return "Gemini API key is not configured. Unable to generate deep QA response."

        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        journal = paper.get("journal", paper.get("source", "Unknown"))
        authors = ", ".join(paper.get("authors", []))
        affiliations = "; ".join(paper.get("affiliations", []))

        prompt = f"""PAPER CONTEXT:
Title: {title}
Journal/Source: {journal}
Authors: {authors}
Affiliations: {affiliations}

Abstract:
{abstract}

QUESTION:
{question}
"""
        candidate_models = [self.model_name, "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash", "gemini-3.6-flash"]
        unique_models = list(dict.fromkeys(candidate_models))

        for model in unique_models:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=QA_SYSTEM_PROMPT,
                        temperature=0.2
                    )
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                continue

        return "Error: Unable to query Gemini models at this time."

    def run_standard_audit(self, paper: Dict[str, Any]) -> Dict[str, str]:
        """Run standard 5-point peer-review QA questionnaire."""
        audit_results = {}
        for section, question in STANDARD_AUDIT_QUESTIONS:
            audit_results[section] = self.answer_question(paper, question)
        return audit_results

    @staticmethod
    def fetch_paper_by_pmid(pmid: str) -> Optional[Dict[str, Any]]:
        """Fetch full paper metadata from PubMed NCBI Entrez by PMID."""
        clean_pmid = pmid.replace("pubmed_", "").strip()
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={clean_pmid}&retmode=xml"
        try:
            resp = requests.get(url, headers={"User-Agent": "ProteinQAEngine/1.0"}, timeout=15)
            if resp.status_code != 200:
                return None

            root = ET.fromstring(resp.content)
            article = root.find(".//PubmedArticle")
            if article is None:
                return None

            title = article.findtext(".//ArticleTitle") or "Untitled"
            title = " ".join(title.strip().rstrip(".").split())

            abstract_parts = [el.text for el in article.findall(".//AbstractText") if el.text]
            abstract = " ".join(abstract_parts).strip() if abstract_parts else ""

            journal = article.findtext(".//Journal/ISOAbbreviation") or article.findtext(".//Journal/Title") or "PubMed"
            
            authors = []
            affiliations = []
            for a in article.findall(".//Author"):
                lname = a.findtext("LastName") or ""
                fname = a.findtext("ForeName") or a.findtext("Initials") or ""
                if lname:
                    authors.append(f"{lname} {fname}".strip())
                for aff in a.findall(".//Affiliation"):
                    if aff.text:
                        affiliations.append(aff.text.strip())

            doi = ""
            for aid in article.findall(".//ArticleId"):
                if aid.attrib.get("IdType") == "doi" and aid.text:
                    doi = aid.text.strip()
                    break

            return {
                "id": f"pubmed_{clean_pmid}",
                "raw_id": clean_pmid,
                "title": title,
                "abstract": abstract,
                "journal": journal,
                "authors": authors[:8],
                "affiliations": list(dict.fromkeys(affiliations))[:6],
                "doi": doi,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{clean_pmid}/",
                "source": "PubMed"
            }
        except Exception as e:
            print(f"[QA Engine] Error fetching PMID {clean_pmid}: {e}")
            return None

    @staticmethod
    def fetch_paper_by_arxiv(arxiv_id: str) -> Optional[Dict[str, Any]]:
        """Fetch paper metadata from arXiv API."""
        clean_id = arxiv_id.replace("arxiv_", "").strip()
        url = f"https://export.arxiv.org/api/query?id_list={clean_id}"
        ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
        try:
            resp = requests.get(url, headers={"User-Agent": "ProteinQAEngine/1.0"}, timeout=15)
            if resp.status_code != 200:
                return None

            root = ET.fromstring(resp.content)
            entry = root.find("atom:entry", ATOM_NS)
            if entry is None:
                return None

            title = " ".join((entry.findtext("atom:title", namespaces=ATOM_NS) or "").strip().split())
            abstract = " ".join((entry.findtext("atom:summary", namespaces=ATOM_NS) or "").strip().split())
            authors = [a.findtext("atom:name", namespaces=ATOM_NS).strip() for a in entry.findall("atom:author", ATOM_NS) if a.findtext("atom:name", namespaces=ATOM_NS)]
            
            return {
                "id": f"arxiv_{clean_id}",
                "raw_id": clean_id,
                "title": title,
                "abstract": abstract,
                "journal": "arXiv",
                "authors": authors[:8],
                "affiliations": [],
                "doi": "",
                "url": f"https://arxiv.org/abs/{clean_id}",
                "source": "arXiv"
            }
        except Exception as e:
            print(f"[QA Engine] Error fetching arXiv {clean_id}: {e}")
            return None

