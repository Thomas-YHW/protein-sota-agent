"""
Protein Paper Check & QA Agent Package.
Provides multi-factor scientific quality assessment (Innovation, Impact, Rigor, Journal IF, Group Prestige)
and interactive/automated question-answering for protein design, pLM, and IDR/LLPS literature.
"""

from .journal_rankings import get_journal_info, score_journal
from .group_directory import match_famous_groups, score_group_prestige
from .paper_checker import PaperChecker, AuditResult
from .qa_engine import PaperQAEngine

__all__ = [
    "get_journal_info",
    "score_journal",
    "match_famous_groups",
    "score_group_prestige",
    "PaperChecker",
    "AuditResult",
    "PaperQAEngine"
]

