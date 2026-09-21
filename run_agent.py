#!/usr/bin/env python3
"""
Protein Design SOTA Research Agent
Automated daily surveillance across arXiv, bioRxiv, and PubMed.
Summarizes, visualizes in HTML, and delivers to Gmail.
"""

import argparse
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path

# Fix Windows console UTF-8 output encoding (GBK / CP936 fix)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Persistent file logging for background scheduled tasks
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "daily_agent.log"

class TeeLogger:
    def __init__(self, filepath, stream):
        self.stream = stream
        self.file = open(filepath, "a", encoding="utf-8", buffering=1)
    def write(self, message):
        self.stream.write(message)
        self.file.write(message)
    def flush(self):
        self.stream.flush()
        self.file.flush()

sys.stdout = TeeLogger(LOG_FILE, sys.stdout)
sys.stderr = TeeLogger(LOG_FILE, sys.stderr)



from protein_sota_agent.config import (
    FETCH_LOOKBACK_DAYS,
    MAX_PAPERS_PER_SOURCE,
    REPORTS_DIR,
    GMAIL_USER,
    GMAIL_APP_PASSWORD,
    RECIPIENT_EMAIL,
    GEMINI_API_KEY
)
from protein_sota_agent.storage import is_paper_seen, mark_papers_seen, get_history_stats
from protein_sota_agent.fetchers.arxiv_fetcher import fetch_arxiv_papers
from protein_sota_agent.fetchers.biorxiv_fetcher import fetch_biorxiv_papers
from protein_sota_agent.fetchers.pubmed_fetcher import fetch_pubmed_papers
from protein_sota_agent.analyzer import analyze_papers_with_gemini
from protein_sota_agent.visualizer import generate_html_digest
from protein_sota_agent.mailer import send_digest_email, test_gmail_connection

def run_pipeline(send_email: bool = False, force: bool = False, lookback: int = FETCH_LOOKBACK_DAYS, open_browser: bool = False):
    print("=" * 65)
    print("🧬 Protein Design SOTA Daily Agent starting...")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔍 Lookback window: {lookback} days")
    print("=" * 65)

    # 1. Fetching from literature sources
    print("\n[1/4] Harvesting literature from multiple sources...")
    arxiv_papers = fetch_arxiv_papers(lookback_days=lookback, max_results=MAX_PAPERS_PER_SOURCE)
    print(f"  ↳ arXiv: {len(arxiv_papers)} papers fetched")

    biorxiv_papers = fetch_biorxiv_papers(lookback_days=lookback, max_results=MAX_PAPERS_PER_SOURCE)
    print(f"  ↳ bioRxiv: {len(biorxiv_papers)} papers fetched")

    pubmed_papers = fetch_pubmed_papers(lookback_days=lookback, max_results=MAX_PAPERS_PER_SOURCE)
    print(f"  ↳ PubMed: {len(pubmed_papers)} papers fetched")

    all_harvested = arxiv_papers + biorxiv_papers + pubmed_papers
    print(f"  ↳ Total candidate papers harvested: {len(all_harvested)}")

    # 2. Deduplication & History Filtering
    if not force:
        unseen_papers = [p for p in all_harvested if not is_paper_seen(p["id"])]
        print(f"[2/4] History filter: {len(unseen_papers)} new / unseen papers ({len(all_harvested) - len(unseen_papers)} already processed previously).")
    else:
        print("[2/4] Force mode active: Skipping SQLite history filter.")
        unseen_papers = all_harvested

    if not unseen_papers:
        print("\n✨ No new unseen papers discovered today. Digest is already up-to-date!")
        stats = get_history_stats()
        print(f"📊 Database Stats: {stats['total_seen']} total tracked, {stats['emailed']} delivered.")
        return

    # 3. AI Analysis & SOTA Ranking
    print("\n[3/4] Analyzing and scoring papers with Gemini AI...")
    analysis_result = analyze_papers_with_gemini(unseen_papers)
    curated_papers = analysis_result.get("papers", [])
    print(f"  ↳ Curated {len(curated_papers)} high-impact protein design breakthroughs.")

    # 4. HTML Visual Digest Generation
    print("\n[4/4] Rendering responsive visual HTML report...")
    html_content = generate_html_digest(analysis_result)

    report_file = REPORTS_DIR / f"digest_{datetime.now().strftime('%Y-%m-%d')}.html"

    # Open in browser if requested or during dry-run
    if open_browser:
        print(f"[Browser] Opening {report_file.name} in default browser...")
        webbrowser.open(report_file.as_uri())

    # 5. Email Dispatch (if enabled)
    if send_email:
        print("\n📧 Dispatching email to Gmail...")
        user_masked = f"{GMAIL_USER[:2]}***@{GMAIL_USER.split('@')[-1]}" if "@" in GMAIL_USER else "(NOT SET)"
        print(f"  ↳ Sender: {user_masked}")
        print(f"  ↳ App Password: {'[CONFIGURED]' if GMAIL_APP_PASSWORD else '[NOT SET]'}")
        print(f"  ↳ Recipient: {RECIPIENT_EMAIL or user_masked}")

        if not GMAIL_USER or not GMAIL_APP_PASSWORD:
            print("\n❌ CRITICAL: Cannot send email because GMAIL_USER or GMAIL_APP_PASSWORD is missing!")
            print("👉 In GitHub: Go to Settings > Secrets and variables > Actions > Add Repository Secrets.")
            sys.exit(1)

        success = send_digest_email(html_content, paper_count=len(curated_papers))
        if success:
            mark_papers_seen(curated_papers, was_emailed=True)
            print("✅ Process complete. Delivered to inbox and recorded in database.")
        else:
            print("\n❌ CRITICAL: Email delivery failed via Gmail SMTP.")
            sys.exit(1)
    else:
        print("\n💡 Note: Dry-run complete. No email was sent.")
        print(f"📂 You can view the generated visual digest at: {report_file}")
        print("To send directly to Gmail, run: python run_agent.py --send")


def run_daemon(schedule_hour: int = 8, schedule_minute: int = 0):
    """
    Continuous daemon loop that triggers the pipeline every morning at specified time.
    """
    print(f"🚀 Protein SOTA Agent daemon started. Scheduled to run daily at {schedule_hour:02d}:{schedule_minute:02d}.")
    print("Press Ctrl+C to terminate.")

    last_run_day = None
    while True:
        now = datetime.now()
        if now.hour == schedule_hour and now.minute == schedule_minute and now.day != last_run_day:
            print(f"\n⏰ Triggering daily scheduled run at {now.strftime('%Y-%m-%d %H:%M:%S')}")
            try:
                run_pipeline(send_email=True)
                last_run_day = now.day
            except Exception as e:
                print(f"❌ Error during scheduled run: {e}")
        time.sleep(30)

def main():
    parser = argparse.ArgumentParser(description="Automated Daily SOTA Protein Design Research Agent")
    parser.add_argument("--dry-run", action="store_true", help="Generate HTML digest, open in browser, but do not send email")
    parser.add_argument("--send", action="store_true", help="Run pipeline, generate HTML, and email to Gmail")
    parser.add_argument("--test-email", action="store_true", help="Send a test verification email via Gmail")
    parser.add_argument("--force", action="store_true", help="Ignore seen paper database and analyze all harvested papers")
    parser.add_argument("--lookback", type=int, default=FETCH_LOOKBACK_DAYS, help="Number of past days to harvest (default: 3)")
    parser.add_argument("--daemon", action="store_true", help="Run in continuous background daemon mode (triggers daily at 08:00 AM)")
    parser.add_argument("--hour", type=int, default=8, help="Daemon trigger hour (0-23, default: 8)")
    parser.add_argument("--minute", type=int, default=0, help="Daemon trigger minute (0-59, default: 0)")

    args = parser.parse_args()

    if args.test_email:
        print("🔍 Testing Gmail SMTP connection...")
        test_gmail_connection()
    elif args.daemon:
        run_daemon(schedule_hour=args.hour, schedule_minute=args.minute)
    elif args.send:
        run_pipeline(send_email=True, force=args.force, lookback=args.lookback)
    else:
        # Default behavior: dry-run with browser preview
        run_pipeline(send_email=False, force=args.force, lookback=args.lookback, open_browser=True)

if __name__ == "__main__":
    main()
