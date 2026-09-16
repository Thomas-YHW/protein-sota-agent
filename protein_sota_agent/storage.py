import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from protein_sota_agent.config import DB_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_papers (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                url TEXT,
                doi TEXT,
                published_date TEXT,
                recorded_at TEXT NOT NULL,
                emailed_at TEXT
            )
        """)
        conn.commit()

def is_paper_seen(paper_id: str) -> bool:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM seen_papers WHERE id = ?", (paper_id,))
        return cursor.fetchone() is not None

def mark_paper_seen(paper: Dict[str, Any], was_emailed: bool = False):
    init_db()
    now_iso = datetime.now().isoformat()
    emailed_at = now_iso if was_emailed else None
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO seen_papers (
                id, title, source, url, doi, published_date, recorded_at, emailed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper.get("id"),
            paper.get("title", ""),
            paper.get("source", "unknown"),
            paper.get("url", ""),
            paper.get("doi", ""),
            paper.get("published_date", ""),
            now_iso,
            emailed_at
        ))
        conn.commit()

def mark_papers_seen(papers: List[Dict[str, Any]], was_emailed: bool = False):
    for p in papers:
        mark_paper_seen(p, was_emailed=was_emailed)

def get_history_stats() -> Dict[str, int]:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM seen_papers")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM seen_papers WHERE emailed_at IS NOT NULL")
        emailed = cursor.fetchone()[0]
        return {"total_seen": total, "emailed": emailed}

