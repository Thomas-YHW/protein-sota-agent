# 🧬 Protein Design SOTA Research Agent

An automated AI-powered surveillance agent that tracks state-of-the-art (SOTA) research in protein design, inverse folding, diffusion models, TDP-43 / IDRs, and targeted binders. It synthesizes literature, generates a modern responsive HTML visual digest, and delivers it to your Gmail inbox daily.

---

## 🌟 Key Features

1. **Multi-Source Literature Harvesting**:
   - **arXiv**: `q-bio.BM`, `cs.AI`, `cs.LG`, `q-bio.QM` (ProteinMPNN, RFdiffusion, flow matching, de novo design).
   - **bioRxiv**: Cutting-edge preprints across bioinformatics, biophysics, and bioengineering.
   - **PubMed**: Peer-reviewed articles from Nature, Science, Cell, PNAS, etc.

2. **Deduplication & Smart Caching**:
   - Built-in SQLite database (`data/paper_history.db`) prevents duplicate alerts. Only fresh, unread papers are sent.

3. **Gemini 3.8 Flash Synthesis**:
   - Categorization: *De Novo Generation & Diffusion*, *Inverse Folding & Sequence Design*, *Antibodies & Targeted Binders*, *Conformational Dynamics & IDRs*, *Structure & Complex Prediction*.
   - Evaluates a **SOTA Impact Score (1-10)**.
   - Formulates structured takeaways: **🎯 The Bottleneck**, **⚡ The Innovation**, and **🚀 Design Impact**.
   - Includes fallback heuristic analysis if no API key is set.

4. **Aesthetic HTML Visualizer**:
   - Card-based, clean newsletter optimized specifically for Gmail rendering on desktop and mobile.
   - Color-coded badges, direct links to paper DOI and PDF, and executive trend snapshots.
   - Saves local archives to `reports/digest_YYYY-MM-DD.html`.

5. **Flexible Scheduling**:
   - Windows Task Scheduler (runs daily at 8:00 AM).
   - Python Daemon (`--daemon`).
   - GitHub Actions (zero-maintenance cloud execution).

---

## 🚀 Quick Start Guide

### Step 1: Set Up Credentials in `.env`
Copy the example file to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` and fill in:
1. `GMAIL_USER`: Your Gmail address (e.g. `you@gmail.com`).
2. `GMAIL_APP_PASSWORD`: A 16-character Google App Password.
   - Generate at: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - *(Note: Ensure 2-Step Verification is active on your Google account)*.
3. `GEMINI_API_KEY`: Get a free key at [https://aistudio.google.com/](https://aistudio.google.com/).

---

### Step 2: Test the Agent

#### A. Dry-Run (Preview in Browser without sending email):
```powershell
python run_agent.py --dry-run
```
This fetches live papers, synthesizes them, saves `reports/digest_YYYY-MM-DD.html`, and automatically opens the visual digest in your web browser.

#### B. Verify Gmail SMTP Connection:
```powershell
python run_agent.py --test-email
```
Sends a test confirmation email to verify your Gmail App Password.

#### C. Run and Send Full Digest Now:
```powershell
python run_agent.py --send
```

---

## ⏰ Daily Automation

### Option 1: Windows Task Scheduler (Recommended for Local PC)
Run the setup script (in PowerShell or by double-clicking `setup_daily_task.bat`):
```powershell
.\setup_daily_task.ps1 -Time "08:00"
```
This registers a daily task named `ProteinDesignSOTAAgent` that executes quietly in the background at 8:00 AM every day.

### Option 2: Python Background Daemon
```powershell
python run_agent.py --daemon --hour 8 --minute 0
```

### Option 3: GitHub Actions (Free Serverless Cloud Runner)
If you push this repository to GitHub:
1. Go to repository **Settings > Secrets and variables > Actions**.
2. Add secrets: `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `RECIPIENT_EMAIL`, and `GEMINI_API_KEY`.
3. The workflow in `.github/workflows/daily_digest.yml` will automatically run every morning at 07:00 UTC and email you!

---

## 📂 Project Structure

```
protein_design_tdp43/
├── run_agent.py                 # Main CLI entrypoint
├── setup_daily_task.ps1         # Windows Task Scheduler registration script
├── setup_daily_task.bat         # Batch launcher
├── requirements.txt             # Dependencies
├── .env.example                 # Credentials template
├── protein_sota_agent/
│   ├── config.py                # Configuration & keywords
│   ├── storage.py               # SQLite deduplication
│   ├── analyzer.py              # Gemini 3.8 Flash evaluation & fallback
│   ├── visualizer.py            # Responsive HTML email engine
│   ├── mailer.py                # Gmail SMTP dispatcher
│   └── fetchers/
│       ├── arxiv_fetcher.py     # arXiv API
│       ├── biorxiv_fetcher.py   # bioRxiv REST API
│       └── pubmed_fetcher.py    # PubMed NCBI E-utilities
├── data/
│   └── paper_history.db         # SQLite history tracking
└── reports/
    └── digest_YYYY-MM-DD.html   # Archived daily HTML reports
```

