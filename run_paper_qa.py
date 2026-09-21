#!/usr/bin/env python3
"""
Protein Paper Check & QA Agent CLI.
Audits scientific literature for Innovativeness, Practical Impact, Experimental Rigor,
Journal Impact Factor (IF), and Pioneer Lab / Group Pedigree, with interactive Q&A.

Usage:
  python run_paper_qa.py check --pmid 39281726 --qa
  python run_paper_qa.py check --arxiv 2409.12345 --html
  python run_paper_qa.py qa --pmid 39281726 --question "What experimental methods were used?"
  python run_paper_qa.py chat --pmid 39281726
  python run_paper_qa.py batch-check --recent 5
"""

import argparse
import sys
from pathlib import Path

# UTF-8 Console encoding fix for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from protein_sota_agent.config import REPORTS_DIR, DB_PATH
from protein_sota_agent.storage import get_connection
from protein_sota_agent.qa_agent.paper_checker import PaperChecker, AuditResult
from protein_sota_agent.qa_agent.qa_engine import PaperQAEngine
from protein_sota_agent.qa_agent.report_generator import generate_markdown_scorecard, generate_html_scorecard

def resolve_paper(args) -> dict:
    """Resolve paper dictionary from args (PMID, arXiv ID, or manual text)."""
    if getattr(args, "pmid", None):
        print(f"[QA Agent] Fetching paper metadata for PMID: {args.pmid}...")
        paper = PaperQAEngine.fetch_paper_by_pmid(args.pmid)
        if not paper:
            print(f"[QA Agent] Error: Could not retrieve metadata for PMID {args.pmid}")
            sys.exit(1)
        return paper

    if getattr(args, "arxiv", None):
        print(f"[QA Agent] Fetching paper metadata for arXiv: {args.arxiv}...")
        paper = PaperQAEngine.fetch_paper_by_arxiv(args.arxiv)
        if not paper:
            print(f"[QA Agent] Error: Could not retrieve metadata for arXiv {args.arxiv}")
            sys.exit(1)
        return paper

    if getattr(args, "title", None) and getattr(args, "abstract", None):
        authors = [a.strip() for a in args.authors.split(",")] if getattr(args, "authors", None) else []
        return {
            "id": f"manual_{abs(hash(args.title)) % 100000}",
            "title": args.title,
            "abstract": args.abstract,
            "journal": getattr(args, "journal", "Preprint"),
            "authors": authors,
            "affiliations": [],
            "url": getattr(args, "url", ""),
            "doi": "",
            "source": "Manual Entry"
        }

    print("[QA Agent] Error: Please provide --pmid, --arxiv, or both --title and --abstract.")
    sys.exit(1)

def handle_check(args):
    paper = resolve_paper(args)
    print(f"\n🔬 Auditing Paper: '{paper.get('title')}'")
    print("⏳ Computing multi-factor quality scores (Innovation, Impact, Rigor, Journal IF, Group)...")

    checker = PaperChecker()
    audit: AuditResult = checker.check_paper(paper)

    qa_pairs = None
    if getattr(args, "qa", False):
        print("💬 Running deep 5-point peer-review QA questionnaire...")
        qa_engine = PaperQAEngine()
        qa_pairs = qa_engine.run_standard_audit(paper)

    # Output Markdown Scorecard
    md_report = generate_markdown_scorecard(audit, qa_pairs)
    print("\n" + "="*80)
    print(md_report)
    print("="*80 + "\n")

    if getattr(args, "html", False):
        html_report = generate_html_scorecard(audit, qa_pairs)
        out_path = REPORTS_DIR / f"audit_{audit.paper_id}.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_report)
        print(f"📄 Responsive HTML scorecard written to: {out_path}")

def handle_qa(args):
    paper = resolve_paper(args)
    question = args.question
    print(f"\n🔬 Paper: '{paper.get('title')}'")
    print(f"❓ Question: {question}")
    print("⏳ Querying scientific QA engine...")

    qa_engine = PaperQAEngine()
    answer = qa_engine.answer_question(paper, question)
    print("\n" + "-"*60)
    print(f"💡 ANSWER:\n\n{answer}")
    print("-"*60 + "\n")

def handle_chat(args):
    paper = resolve_paper(args)
    print(f"\n" + "="*70)
    print(f"🔬 Interactive QA Session: '{paper.get('title')}'")
    print(f"Journal: {paper.get('journal', 'Unknown')} | Authors: {', '.join(paper.get('authors', [])[:4])}")
    print("Type your questions below. Type 'exit' or 'quit' to end session.")
    print("="*70 + "\n")

    qa_engine = PaperQAEngine()
    while True:
        try:
            q = input("\n[Ask QA Agent] > ").strip()
            if not q:
                continue
            if q.lower() in ["exit", "quit", "q"]:
                print("Ending QA session. Goodbye!")
                break

            print("Thinking...")
            ans = qa_engine.answer_question(paper, q)
            print(f"\n💡 {ans}\n")
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break

def handle_batch_check(args):
    limit = args.recent or 5
    print(f"\n📊 Batch Auditing recent {limit} papers from local database...")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, source, url, doi, published_date FROM seen_papers ORDER BY recorded_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()

    if not rows:
        print("[QA Agent] No papers found in seen_papers database. Run 'python run_agent.py' first.")
        return

    checker = PaperChecker()
    audited = []

    for r in rows:
        paper_id = r["id"]
        title = r["title"]
        source = r["source"]
        doi = r["doi"]
        url = r["url"]
        pub_date = r["published_date"]

        # Fetch abstract if it's PubMed or arXiv
        paper_dict = {
            "id": paper_id,
            "title": title,
            "source": source,
            "url": url,
            "doi": doi,
            "published_date": pub_date,
            "journal": source,
            "authors": [],
            "abstract": f"Study on computational protein design and biophysical mechanisms ({title})."
        }

        if "pubmed_" in paper_id:
            fetched = PaperQAEngine.fetch_paper_by_pmid(paper_id)
            if fetched:
                paper_dict = fetched
        elif "arxiv_" in paper_id:
            fetched = PaperQAEngine.fetch_paper_by_arxiv(paper_id)
            if fetched:
                paper_dict = fetched

        print(f"  ↳ Auditing: {title[:70]}...")
        audit = checker.check_paper(paper_dict)
        audited.append(audit)

    # Sort by composite score
    audited.sort(key=lambda x: x.composite_score, reverse=True)

    print("\n" + "="*95)
    print(f"{'SCORE':<8} | {'VERDICT':<14} | {'JOURNAL / IF':<22} | {'LAB':<22} | {'TITLE'}")
    print("-" * 95)
    for a in audited:
        v_short = a.verdict
        j_short = f"{a.journal[:15]} ({a.impact_factor:.1f})" if a.impact_factor > 0 else a.journal[:20]
        l_short = a.top_group_badge[:20]
        t_short = a.title[:45] + "..." if len(a.title) > 45 else a.title
        print(f"{a.composite_score:<8.1f} | {v_short:<14} | {j_short:<22} | {l_short:<22} | {t_short}")
    print("="*95 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Protein Literature Paper Check & QA Agent")
    subparsers = parser.add_subparsers(dest="command", help="Agent Command")

    # Command: check
    check_p = subparsers.add_parser("check", help="Run multi-factor quality audit on a paper")
    check_p.add_argument("--pmid", help="PubMed ID (e.g. 39281726)")
    check_p.add_argument("--arxiv", help="arXiv ID (e.g. 2409.12345)")
    check_p.add_argument("--title", help="Paper title (for manual input)")
    check_p.add_argument("--abstract", help="Paper abstract (for manual input)")
    check_p.add_argument("--journal", default="Preprint", help="Journal name")
    check_p.add_argument("--authors", help="Comma-separated authors")
    check_p.add_argument("--qa", action="store_true", help="Include deep 5-point peer-review QA analysis")
    check_p.add_argument("--html", action="store_true", help="Save responsive HTML scorecard in reports/")

    # Command: qa
    qa_p = subparsers.add_parser("qa", help="Ask a specific scientific question about a paper")
    qa_p.add_argument("--pmid", help="PubMed ID")
    qa_p.add_argument("--arxiv", help="arXiv ID")
    qa_p.add_argument("--title", help="Paper title")
    qa_p.add_argument("--abstract", help="Paper abstract")
    qa_p.add_argument("--question", required=True, help="Scientific question to interrogate")

    # Command: chat
    chat_p = subparsers.add_parser("chat", help="Start interactive Q&A interrogation session")
    chat_p.add_argument("--pmid", help="PubMed ID")
    chat_p.add_argument("--arxiv", help="arXiv ID")

    # Command: batch-check
    batch_p = subparsers.add_parser("batch-check", help="Batch audit recent papers from database")
    batch_p.add_argument("--recent", type=int, default=5, help="Number of recent papers to audit")

    args = parser.parse_args()

    if args.command == "check":
        handle_check(args)
    elif args.command == "qa":
        handle_qa(args)
    elif args.command == "chat":
        handle_chat(args)
    elif args.command == "batch-check":
        handle_batch_check(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

