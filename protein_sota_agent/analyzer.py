import json
import os
from typing import List, Dict, Any, Optional
from protein_sota_agent.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MIN_RELEVANCE_SCORE,
    MAX_PAPERS_IN_DIGEST
)

# Canonical protein design categories
CATEGORIES = [
    "De Novo Generation & Diffusion",
    "Inverse Folding & Sequence Design",
    "Antibodies & Targeted Binders",
    "Conformational Dynamics & IDRs",
    "Structure & Complex Prediction",
    "Therapeutics & Enzyme Engineering"
]

def fallback_heuristic_analyzer(papers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Rule-based analyzer when Gemini API key is not yet configured.
    Scores relevance based on domain keywords and categorizes automatically.
    """
    scored = []
    category_counts = {}

    for p in papers:
        text = f"{p.get('title', '')} {p.get('abstract', '')}".lower()
        score = 5

        # Heuristic scoring
        if any(w in text for w in ["rfdiffusion", "proteinmpnn", "flow matching", "de novo design", "de novo protein"]):
            score += 3
        if any(w in text for w in ["antibody", "nanobody", "binder design", "target binding"]):
            score += 2
        if any(w in text for w in ["tdp-43", "intrinsically disordered", "idr", "phase separation", "condensate"]):
            score += 2
        if any(w in text for w in ["alphafold", "esm3", "chai-1", "boltz-1", "rosetta"]):
            score += 1
        if any(w in text for w in ["experimental validation", "cryo-em", "spr", "crystallography", "in vitro"]):
            score += 1

        score = min(score, 10)

        # Categorize
        cat = "De Novo Generation & Diffusion"
        tag = "Generative AI"
        if any(w in text for w in ["proteinmpnn", "ligandmpnn", "inverse folding", "sequence design"]):
            cat = "Inverse Folding & Sequence Design"
            tag = "MPNN / Sequence"
        elif any(w in text for w in ["antibody", "nanobody", "antigen", "cdr", "binder"]):
            cat = "Antibodies & Targeted Binders"
            tag = "Binders / Antibodies"
        elif any(w in text for w in ["tdp-43", "idr", "intrinsically disordered", "disorder", "condensate", "phase separation"]):
            cat = "Conformational Dynamics & IDRs"
            tag = "IDRs / Dynamics"
        elif any(w in text for w in ["alphafold", "chai-1", "boltz-1", "esmfold", "complex prediction"]):
            cat = "Structure & Complex Prediction"
            tag = "Structure Prediction"
        elif any(w in text for w in ["enzyme", "catalytic", "directed evolution", "therapeutic"]):
            cat = "Therapeutics & Enzyme Engineering"
            tag = "Enzymes / Therapeutics"

        category_counts[cat] = category_counts.get(cat, 0) + 1

        # Summary bullets
        abstract_sentences = [s.strip() for s in p.get("abstract", "").split(". ") if len(s.strip()) > 15]
        problem = abstract_sentences[0] if len(abstract_sentences) > 0 else "Advances in computational protein engineering."
        breakthrough = abstract_sentences[1] if len(abstract_sentences) > 1 else (abstract_sentences[0] if abstract_sentences else "Novel methodological contributions.")
        impact = abstract_sentences[-1] if len(abstract_sentences) > 2 else "Enables improved computational throughput and accuracy."

        paper_item = {
            **p,
            "relevance_score": score,
            "category": cat,
            "tag": tag,
            "headline": p.get("title", ""),
            "the_problem": problem,
            "the_breakthrough": breakthrough,
            "impact": impact
        }
        scored.append(paper_item)

    # Sort descending by relevance score
    scored.sort(key=lambda x: x["relevance_score"], reverse=True)
    filtered = [x for x in scored if x["relevance_score"] >= MIN_RELEVANCE_SCORE][:MAX_PAPERS_IN_DIGEST]

    top_cat = max(category_counts, key=category_counts.get) if category_counts else "Computational Protein Design"
    exec_summary = (
        f"Today's literature digest captured {len(filtered)} high-relevance papers in protein engineering, "
        f"with significant activity in {top_cat}. Key highlights include advances in generative model architectures, "
        f"efficient inverse-folding adaptations, and structural characterizations of biomolecular assemblies."
    )

    return {
        "executive_summary": exec_summary,
        "key_trends": [f"Dominant activity in {top_cat}", "Expansion of multimodal generative protein frameworks"],
        "papers": filtered
    }

def analyze_papers_with_gemini(papers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Uses Gemini 3.8 Flash to deeply evaluate, score, categorize, and synthesize
    each paper for actionable protein design intelligence.
    """
    if not papers:
        return {
            "executive_summary": "No new protein design papers found in the specified lookback window.",
            "key_trends": [],
            "papers": []
        }

    if not GEMINI_API_KEY:
        print("[Analyzer] No GEMINI_API_KEY set in .env. Using intelligent rule-based analyzer.")
        return fallback_heuristic_analyzer(papers)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)

        # Prepare papers payload
        papers_payload = []
        for p in papers:
            papers_payload.append({
                "id": p.get("id"),
                "title": p.get("title"),
                "source": p.get("source"),
                "category": p.get("category"),
                "abstract": p.get("abstract", "")[:1200]
            })

        prompt = f"""
You are an expert computational structural biologist and AI protein design scientist specializing in:
- De novo protein design & generative diffusion / flow matching (RFdiffusion, Chroma)
- Sequence design & inverse folding (ProteinMPNN, LigandMPNN, ESM-IF1)
- Intrinsically disordered regions (IDRs), liquid-liquid phase separation, RNA-binding proteins like TDP-43
- Target binder / antibody / nanobody design
- Structure & complex prediction (AlphaFold3, Chai-1, Boltz-1, ESM3)

Evaluate the following {len(papers_payload)} research papers.
For EACH paper:
1. Assign a `relevance_score` from 1 to 10 (10 = groundbreaking SOTA method in protein design/engineering; < 6 = irrelevant or off-topic).
2. Assign one of these canonical categories:
   - "De Novo Generation & Diffusion"
   - "Inverse Folding & Sequence Design"
   - "Antibodies & Targeted Binders"
   - "Conformational Dynamics & IDRs"
   - "Structure & Complex Prediction"
   - "Therapeutics & Enzyme Engineering"
3. Assign a short punchy `tag` (e.g. "Diffusion", "ProteinMPNN", "TDP-43 / IDR", "Antibody", "AF3 / Boltz").
4. Formulate:
   - `headline`: A clear, scientific 1-line headline summarizing what was accomplished.
   - `the_problem`: 1-2 sentences on what bottleneck or challenge existed.
   - `the_breakthrough`: 1-2 sentences on the novel algorithm, model, or experimental proof.
   - `impact`: 1 sentence on practical significance for protein designers.

Finally, write an `executive_summary` (2-3 paragraphs) surveying the day's key scientific themes, breakthroughs, and actionable trends, along with 2-4 bullet `key_trends`.

Input Papers:
{json.dumps(papers_payload, indent=2)}

Return ONLY valid JSON in this exact structure:
{{
  "executive_summary": "...",
  "key_trends": ["...", "..."],
  "scored_papers": [
    {{
      "id": "...",
      "relevance_score": 9,
      "category": "...",
      "tag": "...",
      "headline": "...",
      "the_problem": "...",
      "the_breakthrough": "...",
      "impact": "..."
    }}
  ]
}}
"""

        import requests

        models_to_try = [GEMINI_MODEL, "gemini-3.6-flash"]
        models_to_try = list(dict.fromkeys(models_to_try))

        output_json = None
        last_err = None
        for mod in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "temperature": 0.2
                    }
                }
                resp = requests.post(url, json=payload, timeout=40)
                if resp.status_code == 200:
                    resp_data = resp.json()
                    raw_text = resp_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if raw_text.startswith("```"):
                        lines = raw_text.splitlines()
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        raw_text = "\n".join(lines).strip()
                    output_json = json.loads(raw_text)
                    print(f"[Analyzer] Successfully synthesized literature using {mod}.")
                    break
                else:
                    last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    print(f"[Analyzer] Model {mod} returned {resp.status_code}. Trying next model...")
            except Exception as err:
                last_err = str(err)
                print(f"[Analyzer] Error calling {mod}: {err}")

        if not output_json:
            raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")

        scored_dict = {sp["id"]: sp for sp in output_json.get("scored_papers", [])}

        enriched_papers = []
        for p in papers:
            p_id = p.get("id")
            if p_id in scored_dict:
                sp = scored_dict[p_id]
                score = sp.get("relevance_score", 5)
                if score >= MIN_RELEVANCE_SCORE:
                    enriched_papers.append({
                        **p,
                        "relevance_score": score,
                        "category": sp.get("category", "De Novo Generation & Diffusion"),
                        "tag": sp.get("tag", "Protein Design"),
                        "headline": sp.get("headline", p.get("title", "")),
                        "the_problem": sp.get("the_problem", ""),
                        "the_breakthrough": sp.get("the_breakthrough", ""),
                        "impact": sp.get("impact", "")
                    })

        enriched_papers.sort(key=lambda x: x["relevance_score"], reverse=True)
        enriched_papers = enriched_papers[:MAX_PAPERS_IN_DIGEST]

        return {
            "executive_summary": output_json.get("executive_summary", ""),
            "key_trends": output_json.get("key_trends", []),
            "papers": enriched_papers
        }

    except Exception as e:
        print(f"[Analyzer] Warning: Gemini analysis failed ({e}). Falling back to heuristic analysis.")
        return fallback_heuristic_analyzer(papers)


