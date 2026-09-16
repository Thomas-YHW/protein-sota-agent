import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from protein_sota_agent.config import (
    GMAIL_USER,
    GMAIL_APP_PASSWORD,
    RECIPIENT_EMAIL
)

GMAIL_SMTP_SERVER = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

def send_digest_email(html_content: str, paper_count: int, recipient: Optional[str] = None) -> bool:
    """
    Sends the generated HTML digest email to the recipient via Gmail SMTP.
    """
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise ValueError(
            "Gmail credentials missing in .env!\n"
            "Please configure GMAIL_USER and GMAIL_APP_PASSWORD in your .env file.\n"
            "Generate your 16-character Google App Password at: https://myaccount.google.com/apppasswords"
        )

    clean_user = GMAIL_USER.strip()
    clean_password = GMAIL_APP_PASSWORD.replace(" ", "").strip()
    clean_to = (recipient or RECIPIENT_EMAIL or GMAIL_USER).strip()

    date_str = datetime.now().strftime("%b %d, %Y")
    subject = f"🧬 [Protein Design SOTA] Daily Digest - {date_str} ({paper_count} Breakthroughs)"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Protein Design SOTA Agent", clean_user))
    msg["To"] = clean_to

    # Plain text fallback
    plain_text = (
        f"Protein Design SOTA Daily Briefing - {date_str}\n"
        f"{paper_count} new high-relevance papers detected.\n\n"
        f"Please view this email in an HTML-capable client to see full visual cards and structured breakdowns."
    )
    part1 = MIMEText(plain_text, "plain", "utf-8")
    part2 = MIMEText(html_content, "html", "utf-8")

    msg.attach(part1)
    msg.attach(part2)

    # Attempt 1: Port 587 with STARTTLS
    try:
        print(f"[Mailer] Connecting to Gmail SMTP server ({GMAIL_SMTP_SERVER}:587 STARTTLS)...")
        with smtplib.SMTP(GMAIL_SMTP_SERVER, 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(clean_user, clean_password)
            server.sendmail(clean_user, [clean_to], msg.as_string())
        print(f"[Mailer] ✅ Successfully dispatched digest to: {clean_to}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"[Mailer] ❌ Authentication failed on port 587: {e}")
        print("[Mailer] Tip: Check that GMAIL_APP_PASSWORD is your 16-character Google App Password.")
    except Exception as e:
        print(f"[Mailer] ⚠️ Port 587 attempt failed: {type(e).__name__}: {e}. Trying port 465 (SSL)...")

    # Attempt 2: Fallback to Port 465 with SSL
    try:
        print(f"[Mailer] Connecting to Gmail SMTP server ({GMAIL_SMTP_SERVER}:465 SSL)...")
        with smtplib.SMTP_SSL(GMAIL_SMTP_SERVER, 465, timeout=30) as server:
            server.ehlo()
            server.login(clean_user, clean_password)
            server.sendmail(clean_user, [clean_to], msg.as_string())
        print(f"[Mailer] ✅ Successfully dispatched digest via SSL (465) to: {clean_to}")
        return True
    except Exception as e:
        import traceback
        print(f"[Mailer] ❌ All SMTP attempts failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False


def test_gmail_connection() -> bool:
    """
    Validates Gmail credentials and sends a small ping email to verify delivery.
    """
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("[Mailer] ⚠️  GMAIL_USER or GMAIL_APP_PASSWORD not set in .env.")
        print("[Mailer] Please copy .env.example to .env and fill in your credentials.")
        return False

    test_html = """
    <div style="font-family: sans-serif; padding: 20px; background-color: #f8fafc; border-radius: 8px;">
      <h2 style="color: #4f46e5;">🧬 Protein Design SOTA Agent: Connection Verified!</h2>
      <p>Your Gmail credentials are working correctly.</p>
      <p>The daily research digest will be delivered to this email address every morning.</p>
    </div>
    """
    return send_digest_email(test_html, paper_count=0)
