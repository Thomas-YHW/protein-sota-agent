"""
Multi-Dimensional Paper Checker & Auditor.
Evaluates protein literature across:
1. Innovativeness & Novelty (30%)
2. Scientific & Practical Impact (25%)
3. Scientific Rigor & Validation (20%)
4. Journal Impact Factor & Tier (15%)
5. Research Group & Pioneer Lab Pedigree (10%)
"""

import json
import os
import re
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from protein_sota_agent.config import GEMINI_API_KEY, GEMINI_MODEL
from .journal_rankings import score_journal
from .group_directory import score_group_prestige

@dataclass
class AuditResult:
    paper_id: str
    title: str
    journal: str
    impact_factor: float
    journal_tier: int
    journal_score: float
    authors: List[str]
    group_score: float
    top_group_badge: str
    is_famous_group: bool
    innovation_score: float
    impact_score: float
    rigor_score: float
    composite_score: float
    verdict: str  # MUST_READ, RECOMMENDED, SKIM, LOW_PRIORITY
    verdict_label: str
    key_novelty: str
    practical_impact: str
    validation_details: str
    pitfalls_and_limitations: List[str]
    tdp43_and_condensate_relevance: str
    url: str
    doi: str
    published_date: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

SYSTEM_PROMPT = """You are a Principal Investigator and elite Senior Peer Reviewer in Computational Structural Biology, Protein Design, and Biophysics of Intrinsically Disordered Proteins (IDPs/IDRs) and Phase Separation.

You will critically evaluate a scientific paper based on its title, abstract, journal, authors, and affiliations.

Evaluate the paper rigorously across three core dimensions on a 0-100 scale:

1. INNOVATION & NOVELTY (0-100):
   - 90-100: Paradigm shift (e.g. first discrete generative tokenization, novel flow matching architecture, first-in-class multi-modal pLM, unprecedented biophysical sequence grammar).
   - 75-89: Genuine technical advance, novel structural formulation, or meaningful algorithmic improvement over standard baselines.
   - 60-74: Incremental adaptation (e.g., routine fine-tuning of ESM-2, slight hyperparameter tweaking on existing RFdiffusion pipelines).
   - <60: Derivative work, minor re-implementation, or repetitive benchmark.

2. SCIENTIFIC & PRACTICAL IMPACT (0-100):
   - 90-100: Transformative practical utility (e.g. enables high-affinity de novo binder design with high wet-lab hit rates, solves protein aggregation bottlenecks, directs condensates in vivo).
   - 75-89: Highly actionable for protein engineers and biophysicists; clearly improves throughput or design reliability.
   - 60-74: Specialized theoretical interest with limited immediate experimental utility.
   - <60: Narrow, ambiguous, or unverifiable real-world utility.

3. SCIENTIFIC RIGOR & VALIDATION (0-100):
   - 85-100: Comprehensive experimental wet-lab validation (e.g. cryo-EM/crystal structure, SPR/BLI binding kinetics, in vitro condensate droplet microscopy, cell-based functional assays) WITH strict negative controls.
   - 70-84: Solid computational validation with strict homology partitioning (e.g. MMseqs2 cluster splits at <30% identity), MD simulations, or orthogonal validation sets; OR preliminary pilot wet-lab experiments.
   - 55-69: Purely in silico validation relying solely on AlphaFold pLDDT, RMSD, or self-consistency without wet-lab verification or homology leakage safeguards.
   - <55: Speculative claims, questionable benchmarks, or severe data leakage.

Also identify:
- Key Novelty: 1-2 sharp sentences.
- Practical Impact: 1-2 sharp sentences.
- Validation Details: Exact validation methodology (Wet-lab vs. In Silico).
- Pitfalls & Limitations: 2-3 bullet points of critical caveats, potential pitfalls, or unaddressed questions.
- Relevance to IDRs, Phase Separation & TDP-43: Specific implications for disordered proteins, biomolecular condensates, or TDP-43 LCD aggregation.
- Verdict: Choose exactly one of ["MUST_READ", "RECOMMENDED", "SKIM", "LOW_PRIORITY"].

Return ONLY valid JSON with this exact schema:
{
  "innovation_score": 85,
  "impact_score": 88,
  "rigor_score": 80,
  "key_novelty": "...",
  "practical_impact": "...",
  "validation_details": "...",
  "pitfalls_and_limitations": ["...", "..."],
  "tdp43_and_condensate_relevance": "...",
  "verdict": "MUST_READ",
  "verdict_rationale": "..."
}
"""

class PaperChecker:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name or GEMINI_MODEL
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def check_paper(self, paper: Dict[str, Any]) -> AuditResult:
        """
        Audit a paper dictionary and compute multi-factor scores.
        """
        title = paper.get("title", "").strip()
        abstract = paper.get("abstract", "").strip()
        journal_str = paper.get("journal") or paper.get("category") or paper.get("source", "Preprint")
        authors = paper.get("authors") or []
        affiliations = paper.get("affiliations") or []
        doi = paper.get("doi") or paper.get("raw_id", "")
        url = paper.get("url") or ""
        pub_date = paper.get("published_date") or ""
        paper_id = paper.get("id") or f"paper_{hash(title) % 1000000}"

        # 1. Score Journal IF & Tier
        j_info = score_journal(journal_str)
        journal_score = j_info["journal_score"]
        impact_factor = j_info["impact_factor"]
        journal_tier = j_info["tier"]
        normalized_journal = j_info["journal_name"]

        # 2. Score Group Prestige & KOL Pedigree
        g_info = score_group_prestige(authors, affiliations, extra_text=f"{title} {abstract}")
        group_score = g_info["group_score"]
        top_group_badge = g_info["top_group_badge"]
        is_famous_group = g_info["is_famous_group"]

        # 3. Gemini Deep Evaluation or Heuristic Fallback
        gemini_eval = self._evaluate_with_gemini(
            title=title,
            abstract=abstract,
            journal=normalized_journal,
            impact_factor=impact_factor,
            authors=authors,
            affiliations=affiliations,
            group_badge=top_group_badge
        )

        if not gemini_eval:
            gemini_eval = self._heuristic_fallback(
                title=title,
                abstract=abstract,
                is_famous_group=is_famous_group,
                journal_tier=journal_tier
            )

        inn_score = float(gemini_eval.get("innovation_score", 70))
        imp_score = float(gemini_eval.get("impact_score", 70))
        rig_score = float(gemini_eval.get("rigor_score", 65))

        # 4. Composite Quality Formula:
        # 30% Innovation + 25% Impact + 20% Rigor + 15% Journal + 10% Group
        composite = round(
            0.30 * inn_score +
            0.25 * imp_score +
            0.20 * rig_score +
            0.15 * journal_score +
            0.10 * group_score,
            1
        )

        # Map verdict label
        verdict = gemini_eval.get("verdict", "RECOMMENDED")
        if composite >= 88:
            verdict = "MUST_READ"
        elif composite >= 78 and verdict != "MUST_READ":
            verdict = "RECOMMENDED"
        elif composite < 68 and verdict in ["MUST_READ", "RECOMMENDED"]:
            verdict = "SKIM"

        verdict_labels = {
            "MUST_READ": "⭐ MUST READ (Essential Milestone)",
            "RECOMMENDED": "✅ HIGH VALUE (Recommended In-Depth Read)",
            "SKIM": "📖 WORTH SKIMMING (Specialized Context / Incremental)",
            "LOW_PRIORITY": "⚠️ LOW PRIORITY / METHODOLOGICALLY SUSPECT"
        }

        return AuditResult(
            paper_id=paper_id,
            title=title,
            journal=normalized_journal,
            impact_factor=impact_factor,
            journal_tier=journal_tier,
            journal_score=journal_score,
            authors=authors,
            group_score=group_score,
            top_group_badge=top_group_badge,
            is_famous_group=is_famous_group,
            innovation_score=inn_score,
            impact_score=imp_score,
            rigor_score=rig_score,
            composite_score=composite,
            verdict=verdict,
            verdict_label=verdict_labels.get(verdict, verdict),
            key_novelty=gemini_eval.get("key_novelty", "Novel methodology in protein modeling."),
            practical_impact=gemini_eval.get("practical_impact", "Advances computational protein engineering workflows."),
            validation_details=gemini_eval.get("validation_details", "In silico validation on standard benchmark sets."),
            pitfalls_and_limitations=gemini_eval.get("pitfalls_and_limitations", ["Requires experimental validation in vitro."]),
            tdp43_and_condensate_relevance=gemini_eval.get("tdp43_and_condensate_relevance", "Applicable to conformational ensemble and sequence analysis."),
            url=url,
            doi=doi,
            published_date=pub_date
        )

    def _evaluate_with_gemini(
        self,
        title: str,
        abstract: str,
        journal: str,
        impact_factor: float,
        authors: List[str],
        affiliations: List[str],
        group_badge: str
    ) -> Optional[Dict[str, Any]]:
        """Call Gemini to extract rigorous peer review metrics."""
        if not self.client:
            return None

        prompt = f"""Evaluate this paper with academic rigor:

PAPER TITLE: {title}
JOURNAL: {journal} (Impact Factor: {impact_factor if impact_factor > 0 else 'Preprint / Not Indexed'})
DETECTED RESEARCH LAB / AFFILIATION: {group_badge}
AUTHORS: {', '.join(authors[:6]) if authors else 'Not listed'}
AFFILIATIONS: {'; '.join(affiliations[:4]) if affiliations else 'Not listed'}

ABSTRACT:
{abstract}
"""

        candidate_models = [self.model_name, "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash", "gemini-3.6-flash"]
        # deduplicate preserving order
        unique_models = list(dict.fromkeys(candidate_models))

        for model in unique_models:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )
                if response and response.text:
                    cleaned_text = response.text.strip()
                    if cleaned_text.startswith("```"):
                        cleaned_text = re.sub(r"^```(?:json)?\s*", "", cleaned_text)
                        cleaned_text = re.sub(r"\s*```$", "", cleaned_text)
                    data = json.loads(cleaned_text)
                    return data
            except Exception as e:
                # Try next model in chain
                continue

        return None

    def _heuristic_fallback(
        self,
        title: str,
        abstract: str,
        is_famous_group: bool,
        journal_tier: int
    ) -> Dict[str, Any]:
        """Fallback rule-based assessment when API is unreachable."""
        text = f"{title} {abstract}".lower()
        inn = 70.0
        imp = 70.0
        rig = 65.0

        # Innovation checks
        if any(w in text for w in ["first", "unprecedented", "novel architecture", "flow matching", "diffusion", "tokeniz"]):
            inn += 12
        if any(w in text for w in ["plm", "esm-2", "esm3", "representation learning", "discrete"]):
            inn += 8

        # Impact checks
        if any(w in text for w in ["nanomolar", "therapeutic", "high hit rate", "solubility", "inhibit aggregation"]):
            imp += 12
        if any(w in text for w in ["phase separation", "llps", "condensate", "tdp-43", "disorder"]):
            imp += 10

        # Rigor checks
        has_wetlab = any(w in text for w in ["cryo-em", "crystallography", "spr", "bli", "microscopy", "in vitro", "cell-based"])
        if has_wetlab:
            rig += 20
        else:
            rig += 5

        if is_famous_group:
            inn += 4
            imp += 4

        inn = min(98.0, max(50.0, inn))
        imp = min(98.0, max(50.0, imp))
        rig = min(98.0, max(50.0, rig))

        verdict = "RECOMMENDED"
        if (inn + imp + rig) / 3 >= 85:
            verdict = "MUST_READ"
        elif (inn + imp + rig) / 3 < 68:
            verdict = "SKIM"

        return {
            "innovation_score": inn,
            "impact_score": imp,
            "rigor_score": rig,
            "key_novelty": "Novel computational and biophysical modeling framework.",
            "practical_impact": "Directly impacts protein sequence and structural design workflows.",
            "validation_details": "Wet-lab experimental assays reported" if has_wetlab else "Evaluated in silico on benchmark datasets.",
            "pitfalls_and_limitations": [
                "Full scope of wet-lab validation should be verified across clinical targets.",
                "Homology partitioning and out-of-distribution generalization requires inspection."
            ],
            "tdp43_and_condensate_relevance": "Provides useful paradigms for conformational ensemble and low-complexity sequence design.",
            "verdict": verdict,
            "verdict_rationale": "Strong domain relevance with quantitative evaluation."
        }

