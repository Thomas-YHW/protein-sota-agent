import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root or current directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Gmail Settings
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", GMAIL_USER)

# Gemini AI Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Gemini 3.6 Flash for fast, reliable reasoning and synthesis
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


# Storage & Output paths
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "paper_history.db"

REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Domain Focus & Search Queries
# Specifically tailored for protein design, inverse folding, diffusion, IDRs, and binders
DEFAULT_KEYWORDS = [
    "protein design",
    "de novo protein",
    "ProteinMPNN",
    "diffusion protein",
    "RFdiffusion",
    "flow matching protein",
    "antibody design",
    "binder design",
    "inverse folding",
    "intrinsically disordered",
    "TDP-43",
    "AlphaFold",
    "ESM3",
    "Chai-1",
    "Boltz-1"
]

# Fetching Parameters
FETCH_LOOKBACK_DAYS = int(os.getenv("FETCH_LOOKBACK_DAYS", "3"))
MAX_PAPERS_PER_SOURCE = int(os.getenv("MAX_PAPERS_PER_SOURCE", "15"))
MIN_RELEVANCE_SCORE = int(os.getenv("MIN_RELEVANCE_SCORE", "6"))
MAX_PAPERS_IN_DIGEST = int(os.getenv("MAX_PAPERS_IN_DIGEST", "12"))

