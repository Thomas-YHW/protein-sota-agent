import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from jinja2 import Template
from protein_sota_agent.config import REPORTS_DIR

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Protein Design SOTA Digest - {{ date }}</title>
  <style>
    /* Client-safe resets */
    body, table, td, a { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }
    body {
      margin: 0;
      padding: 0;
      width: 100% !important;
      background-color: #f1f5f9;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: #1e293b;
      line-height: 1.6;
    }
    .wrapper {
      max-width: 680px;
      margin: 0 auto;
      padding: 24px 16px;
    }
    .header-card {
      background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
      border-radius: 16px;
      padding: 32px 28px;
      color: #ffffff;
      box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
      margin-bottom: 24px;
    }
    .header-badge {
      display: inline-block;
      background-color: rgba(99, 102, 241, 0.25);
      border: 1px solid rgba(165, 180, 252, 0.4);
      color: #c7d2fe;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      padding: 4px 12px;
      border-radius: 9999px;
      margin-bottom: 12px;
    }
    .header-title {
      margin: 0 0 8px 0;
      font-size: 26px;
      font-weight: 800;
      line-height: 1.25;
      color: #ffffff;
      letter-spacing: -0.5px;
    }
    .header-sub {
      margin: 0;
      color: #cbd5e1;
      font-size: 14px;
    }
    .stats-bar {
      margin-top: 20px;
      padding-top: 16px;
      border-top: 1px solid rgba(255, 255, 255, 0.15);
      font-size: 13px;
      color: #94a3b8;
    }
    .stats-highlight {
      color: #38bdf8;
      font-weight: 700;
    }

    /* Executive Summary Card */
    .exec-card {
      background-color: #ffffff;
      border: 1px solid #e2e8f0;
      border-left: 5px solid #6366f1;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .exec-title {
      font-size: 17px;
      font-weight: 700;
      color: #0f172a;
      margin: 0 0 12px 0;
      display: flex;
      align-items: center;
    }
    .exec-text {
      font-size: 14px;
      color: #334155;
      margin: 0 0 16px 0;
      line-height: 1.65;
    }
    .trend-pill {
      display: inline-block;
      background-color: #f8fafc;
      border: 1px solid #cbd5e1;
      color: #334155;
      font-size: 12px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 6px;
      margin-right: 6px;
      margin-bottom: 6px;
    }

    /* Paper Card */
    .paper-card {
      background-color: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 14px;
      padding: 24px;
      margin-bottom: 20px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04);
      transition: all 0.2s ease;
    }
    .spotlight {
      border: 2px solid #818cf8;
      background: linear-gradient(180deg, #fafafa 0%, #ffffff 100%);
    }
    .badge-row {
      margin-bottom: 12px;
    }
    .cat-badge {
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding: 3px 9px;
      border-radius: 6px;
      margin-right: 6px;
    }
    .source-badge {
      display: inline-block;
      background-color: #f1f5f9;
      color: #475569;
      font-size: 11px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 6px;
    }
    .score-badge {
      float: right;
      background-color: #ecfdf5;
      border: 1px solid #a7f3d0;
      color: #065f46;
      font-size: 12px;
      font-weight: 800;
      padding: 3px 10px;
      border-radius: 9999px;
    }
    .paper-title {
      font-size: 18px;
      font-weight: 700;
      line-height: 1.35;
      color: #0f172a;
      margin: 0 0 8px 0;
    }
    .paper-title a {
      color: #0f172a;
      text-decoration: none;
    }
    .paper-title a:hover {
      color: #4f46e5;
      text-decoration: underline;
    }
    .paper-meta {
      font-size: 12px;
      color: #64748b;
      margin-bottom: 14px;
    }
    .key-points {
      background-color: #f8fafc;
      border-radius: 8px;
      padding: 14px 16px;
      margin-bottom: 16px;
      font-size: 13px;
    }
    .point-item {
      margin-bottom: 8px;
      line-height: 1.5;
    }
    .point-item:last-child {
      margin-bottom: 0;
    }
    .point-label {
      font-weight: 700;
      color: #1e293b;
    }
    .action-row {
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid #f1f5f9;
    }
    .btn {
      display: inline-block;
      padding: 7px 16px;
      font-size: 12px;
      font-weight: 600;
      text-decoration: none;
      border-radius: 8px;
      margin-right: 8px;
    }
    .btn-primary {
      background-color: #4f46e5;
      color: #ffffff !important;
    }
    .btn-secondary {
      background-color: #f1f5f9;
      color: #334155 !important;
      border: 1px solid #cbd5e1;
    }

    /* Footer */
    .footer {
      text-align: center;
      padding: 24px 12px;
      font-size: 12px;
      color: #94a3b8;
    }
    .footer a {
      color: #64748b;
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <div class="wrapper">
    <!-- Header -->
    <div class="header-card">
      <div class="header-badge">🧬 SOTA RESEARCH AGENT</div>
      <h1 class="header-title">Protein Design Daily Briefing</h1>
      <p class="header-sub">Automated literature surveillance across arXiv, bioRxiv & PubMed</p>
      <div class="stats-bar">
        📅 <strong>{{ date }}</strong> &nbsp;|&nbsp; 
        📄 <span class="stats-highlight">{{ papers|length }} Curated Breakthroughs</span> &nbsp;|&nbsp;
        🎯 Focus: <em>De Novo, MPNN, Diffusion, IDRs & Binders</em>
      </div>
    </div>

    <!-- Executive Summary -->
    {% if executive_summary %}
    <div class="exec-card">
      <h2 class="exec-title">⚡ Today's State of the Art Snapshot</h2>
      <p class="exec-text">{{ executive_summary }}</p>
      {% if key_trends %}
      <div style="margin-top: 12px;">
        <strong style="font-size: 12px; text-transform: uppercase; color: #64748b; letter-spacing: 0.5px; display: block; margin-bottom: 6px;">Key Emerging Trends:</strong>
        {% for trend in key_trends %}
        <span class="trend-pill">✦ {{ trend }}</span>
        {% endfor %}
      </div>
      {% endif %}
    </div>
    {% endif %}

    <!-- Paper Stream -->
    {% for paper in papers %}
    <div class="paper-card {% if loop.first and paper.relevance_score >= 9 %}spotlight{% endif %}">
      <div class="badge-row">
        <!-- Category Pill -->
        {% if "Diffusion" in paper.category or "De Novo" in paper.category %}
        <span class="cat-badge" style="background-color: #ede9fe; color: #5b21b6;">{{ paper.category }}</span>
        {% elif "Inverse" in paper.category or "Sequence" in paper.category %}
        <span class="cat-badge" style="background-color: #e0f2fe; color: #0369a1;">{{ paper.category }}</span>
        {% elif "Antibod" in paper.category or "Binder" in paper.category %}
        <span class="cat-badge" style="background-color: #d1fae5; color: #047857;">{{ paper.category }}</span>
        {% elif "IDR" in paper.category or "Dynamics" in paper.category %}
        <span class="cat-badge" style="background-color: #fef3c7; color: #b45309;">{{ paper.category }}</span>
        {% else %}
        <span class="cat-badge" style="background-color: #f3e8ff; color: #6b21a8;">{{ paper.category }}</span>
        {% endif %}

        <!-- Source Pill -->
        <span class="source-badge">{{ paper.source }}</span>

        <!-- Relevance Score Pill -->
        <span class="score-badge">★ {{ paper.relevance_score }}/10 SOTA</span>
      </div>

      <h3 class="paper-title">
        <a href="{{ paper.url }}" target="_blank">{{ paper.title }}</a>
      </h3>

      <div class="paper-meta">
        ✍️ {{ paper.authors|join(', ') if paper.authors else 'Research Consortium' }} &nbsp;•&nbsp; 
        🗓️ {{ paper.published_date }}
      </div>

      <!-- Structured Breakdown -->
      <div class="key-points">
        {% if paper.the_problem %}
        <div class="point-item">
          <span class="point-label">🎯 Bottleneck:</span> {{ paper.the_problem }}
        </div>
        {% endif %}
        {% if paper.the_breakthrough %}
        <div class="point-item">
          <span class="point-label">⚡ Innovation:</span> {{ paper.the_breakthrough }}
        </div>
        {% endif %}
        {% if paper.impact %}
        <div class="point-item">
          <span class="point-label">🚀 Design Impact:</span> {{ paper.impact }}
        </div>
        {% endif %}
      </div>

      <!-- Action Row -->
      <div class="action-row">
        <a href="{{ paper.url }}" class="btn btn-primary" target="_blank">View Paper ↗</a>
        {% if paper.pdf_url %}
        <a href="{{ paper.pdf_url }}" class="btn btn-secondary" target="_blank">PDF ↗</a>
        {% endif %}
        {% if paper.tag %}
        <span style="float: right; font-size: 11px; color: #94a3b8; line-height: 28px;">#{{ paper.tag }}</span>
        {% endif %}
      </div>
    </div>
    {% endfor %}

    <!-- Footer -->
    <div class="footer">
      <p>This automated digest was generated by your <strong>Protein Design SOTA Agent</strong>.</p>
      <p>Target domains: <em>De Novo Diffusion, ProteinMPNN, TDP-43 / IDRs, Targeted Binders & AlphaFold/Boltz</em></p>
      <p style="font-size: 11px; color: #cbd5e1; margin-top: 12px;">Saved locally at <code>{{ report_file }}</code></p>
    </div>
  </div>
</body>
</html>
"""

def generate_html_digest(analysis_data: Dict[str, Any]) -> str:
    """
    Renders the HTML email digest from analyzed paper data and saves a local copy.
    """
    today_str = datetime.now().strftime("%B %d, %Y")
    file_date_str = datetime.now().strftime("%Y-%m-%d")
    report_filename = f"digest_{file_date_str}.html"
    report_path = REPORTS_DIR / report_filename

    template = Template(HTML_TEMPLATE)
    html_content = template.render(
        date=today_str,
        executive_summary=analysis_data.get("executive_summary", ""),
        key_trends=analysis_data.get("key_trends", []),
        papers=analysis_data.get("papers", []),
        report_file=str(report_path)
    )

    # Save local copy for offline viewing / archive
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[Visualizer] HTML report successfully saved to: {report_path}")
    return html_content

