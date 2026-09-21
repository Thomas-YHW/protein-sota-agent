"""
Report Generator for Paper Check & QA Agent.
Produces professional Markdown and responsive HTML scorecards for paper audits.
"""

from typing import Dict, Any, List
from .paper_checker import AuditResult

def generate_markdown_scorecard(audit: AuditResult, qa_qa_pairs: Dict[str, str] = None) -> str:
    """Generate a clean GitHub-Flavored Markdown audit report."""
    md = []
    md.append(f"# 🔬 Scientific Paper Audit: {audit.title}\n")
    md.append(f"**Publication / Venue:** {audit.journal} &nbsp;|&nbsp; **Impact Factor:** `{audit.impact_factor:.1f}` &nbsp;|&nbsp; **Tier:** `Tier {audit.journal_tier}`")
    md.append(f"**Research Group:** `{audit.top_group_badge}` ({'🌟 KOL Pioneer Lab' if audit.is_famous_group else 'Standard Research Group'})")
    md.append(f"**Authors:** {', '.join(audit.authors[:6]) if audit.authors else 'N/A'}")
    if audit.url:
        md.append(f"**Direct Link:** [{audit.paper_id}]({audit.url})")
    md.append("\n---\n")

    # Scorecard Table
    md.append("### 📊 Multi-Factor Evaluation Scorecard\n")
    md.append("| Dimension | Weight | Score (0-100) | Assessment / Baseline |")
    md.append("| :--- | :---: | :---: | :--- |")
    md.append(f"| **Innovativeness & Novelty** | 30% | **`{audit.innovation_score:.1f}`** | {audit.key_novelty} |")
    md.append(f"| **Scientific & Practical Impact** | 25% | **`{audit.impact_score:.1f}`** | {audit.practical_impact} |")
    md.append(f"| **Scientific Rigor & Validation** | 20% | **`{audit.rigor_score:.1f}`** | {audit.validation_details} |")
    md.append(f"| **Journal Prestige & IF** | 15% | **`{audit.journal_score:.1f}`** | {audit.journal} (IF: {audit.impact_factor:.1f}) |")
    md.append(f"| **Research Group / Lab Pedigree** | 10% | **`{audit.group_score:.1f}`** | {audit.top_group_badge} |")
    md.append(f"| **COMPOSITE QUALITY INDEX** | **100%** | 🏆 **`{audit.composite_score:.1f} / 100`** | **{audit.verdict_label}** |\n")

    # Critical Analysis
    md.append("### 🔍 Critical Findings & Peer-Review Checks\n")
    md.append(f"- **Core Novelty:** {audit.key_novelty}")
    md.append(f"- **Real-World Impact:** {audit.practical_impact}")
    md.append(f"- **Validation Depth:** {audit.validation_details}")
    md.append(f"- **Relevance to IDRs / Condensates / TDP-43:** {audit.tdp43_and_condensate_relevance}\n")

    # Caveats
    if audit.pitfalls_and_limitations:
        md.append("### ⚠️ Methodological Pitfalls & Caveats\n")
        for caveat in audit.pitfalls_and_limitations:
            md.append(f"- {caveat}")
        md.append("")

    # QA Q&A Section
    if qa_qa_pairs:
        md.append("### 💬 Deep QA Interrogation\n")
        for heading, answer in qa_qa_pairs.items():
            md.append(f"#### ❓ {heading}\n{answer}\n")

    return "\n".join(md)

def generate_html_scorecard(audit: AuditResult, qa_qa_pairs: Dict[str, str] = None) -> str:
    """Generate responsive HTML scorecard."""
    color_map = {
        "MUST_READ": "#4f46e5",
        "RECOMMENDED": "#059669",
        "SKIM": "#d97706",
        "LOW_PRIORITY": "#dc2626"
    }
    badge_color = color_map.get(audit.verdict, "#4f46e5")

    qa_html = ""
    if qa_qa_pairs:
        qa_cards = []
        for h, ans in qa_qa_pairs.items():
            qa_cards.append(f"""
            <div style="background:#f8fafc; border-left:4px solid #4f46e5; padding:12px 16px; margin-bottom:12px; border-radius:4px;">
              <strong style="color:#1e293b; display:block; margin-bottom:6px;">❓ {h}</strong>
              <div style="color:#334155; font-size:13px; line-height:1.5;">{ans.replace(chr(10), '<br>')}</div>
            </div>
            """)
        qa_html = f"""
        <div style="margin-top:24px;">
          <h3 style="color:#0f172a; margin-bottom:12px;">💬 Scientific Q&A Interrogation</h3>
          {''.join(qa_cards)}
        </div>
        """

    pitfalls_html = ""
    if audit.pitfalls_and_limitations:
        items = "".join([f"<li style='margin-bottom:6px;'>{c}</li>" for c in audit.pitfalls_and_limitations])
        pitfalls_html = f"""
        <div style="background:#fffbeb; border:1px solid #fef3c7; border-radius:8px; padding:16px; margin-top:20px;">
          <strong style="color:#92400e;">⚠️ Methodological Pitfalls & Risks:</strong>
          <ul style="color:#78350f; font-size:13px; margin:8px 0 0 18px; padding:0;">{items}</ul>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Audit: {audit.title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background:#f1f5f9; padding:24px; color:#1e293b; }}
    .card {{ background:#ffffff; max-width:860px; margin:0 auto; padding:32px; border-radius:12px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05); }}
    .badge {{ display:inline-block; padding:4px 10px; border-radius:9999px; font-weight:700; font-size:12px; color:#ffffff; }}
    table {{ width:100%; border-collapse:collapse; margin-top:16px; }}
    th, td {{ padding:10px 12px; border-bottom:1px solid #e2e8f0; font-size:13px; text-align:left; }}
    th {{ background:#f8fafc; font-weight:700; color:#475569; }}
    .score-num {{ font-weight:800; font-size:15px; color:#0f172a; }}
  </style>
</head>
<body>
  <div class="card">
    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
      <span class="badge" style="background:{badge_color};">{audit.verdict_label}</span>
      <div style="font-size:20px; font-weight:900; color:#4f46e5;">Quality Score: {audit.composite_score:.1f} / 100</div>
    </div>
    <h2 style="color:#0f172a; margin:16px 0 8px 0;">{audit.title}</h2>
    <div style="color:#64748b; font-size:13px; margin-bottom:16px;">
      <strong>Venue:</strong> {audit.journal} (IF: {audit.impact_factor:.1f}) &nbsp;|&nbsp;
      <strong>Lab:</strong> {audit.top_group_badge} &nbsp;|&nbsp;
      <strong>Authors:</strong> {', '.join(audit.authors[:4]) if audit.authors else 'N/A'}
    </div>

    <table>
      <thead>
        <tr>
          <th>Evaluation Dimension</th>
          <th>Weight</th>
          <th>Score</th>
          <th>Key Finding</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Innovativeness & Novelty</strong></td>
          <td>30%</td>
          <td class="score-num">{audit.innovation_score:.1f}</td>
          <td>{audit.key_novelty}</td>
        </tr>
        <tr>
          <td><strong>Practical & Scientific Impact</strong></td>
          <td>25%</td>
          <td class="score-num">{audit.impact_score:.1f}</td>
          <td>{audit.practical_impact}</td>
        </tr>
        <tr>
          <td><strong>Scientific Rigor & Validation</strong></td>
          <td>20%</td>
          <td class="score-num">{audit.rigor_score:.1f}</td>
          <td>{audit.validation_details}</td>
        </tr>
        <tr>
          <td><strong>Journal Prestige & IF</strong></td>
          <td>15%</td>
          <td class="score-num">{audit.journal_score:.1f}</td>
          <td>{audit.journal} (Tier {audit.journal_tier})</td>
        </tr>
        <tr>
          <td><strong>Research Group Pedigree</strong></td>
          <td>10%</td>
          <td class="score-num">{audit.group_score:.1f}</td>
          <td>{audit.top_group_badge}</td>
        </tr>
      </tbody>
    </table>

    <div style="margin-top:20px; background:#f8fafc; padding:16px; border-radius:8px; font-size:13px;">
      <strong style="color:#1e293b;">🎯 IDR / Condensate / TDP-43 Relevance:</strong>
      <p style="margin:6px 0 0 0; color:#475569;">{audit.tdp43_and_condensate_relevance}</p>
    </div>

    {pitfalls_html}
    {qa_html}

    <div style="margin-top:24px; text-align:right;">
      <a href="{audit.url}" target="_blank" style="display:inline-block; padding:8px 18px; background:#4f46e5; color:#ffffff; text-decoration:none; border-radius:6px; font-size:12px; font-weight:700;">View Original Paper &rarr;</a>
    </div>
  </div>
</body>
</html>
"""
    return html

