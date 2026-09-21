import sys
from pathlib import Path

# UTF-8 Console encoding fix for Windows GBK
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from protein_sota_agent.qa_agent.journal_rankings import get_journal_info, score_journal
from protein_sota_agent.qa_agent.group_directory import match_famous_groups, score_group_prestige
from protein_sota_agent.qa_agent.paper_checker import PaperChecker, AuditResult
from protein_sota_agent.qa_agent.qa_engine import PaperQAEngine
from protein_sota_agent.qa_agent.report_generator import generate_markdown_scorecard

def test_journal_rankings():
    print("Testing Journal Rankings...")
    # 1. Nature
    nat = get_journal_info("Nature")
    assert nat["tier"] == 1 and nat["if"] > 40, f"Failed Nature: {nat}"

    # 2. PNAS abbreviation
    pnas = get_journal_info("Proc Natl Acad Sci U S A")
    assert pnas["tier"] == 2 and "PNAS" in pnas["name"], f"Failed PNAS: {pnas}"

    # 3. NAR abbreviation
    nar = get_journal_info("Nucleic Acids Res")
    assert nar["tier"] == 2 and nar["score"] >= 85, f"Failed NAR: {nar}"

    # 4. NeurIPS
    neurips = get_journal_info("NeurIPS")
    assert neurips["score"] >= 90, f"Failed NeurIPS: {neurips}"

    # 5. bioRxiv preprint
    biorxiv = get_journal_info("bioRxiv")
    assert biorxiv["is_preprint"] is True, f"Failed bioRxiv: {biorxiv}"

    print("  ✅ Journal Rankings passed!")

def test_group_directory():
    print("Testing Group Directory & Pioneer Lab matching...")
    # 1. Baker Lab
    baker_matches = match_famous_groups(authors=["Joseph Watson", "David Baker"], affiliations=["Institute for Protein Design, UW"])
    assert len(baker_matches) > 0 and baker_matches[0]["pi"] == "David Baker", f"Failed Baker: {baker_matches}"

    # 2. Anthony Hyman (Condensates)
    hyman_matches = match_famous_groups(authors=["A. Hyman"], affiliations=["MPI-CBG Dresden"])
    assert len(hyman_matches) > 0 and "Hyman" in hyman_matches[0]["pi"], f"Failed Hyman: {hyman_matches}"

    # 3. Rohit Pappu (IDRs)
    pappu_matches = match_famous_groups(authors=["Rohit V. Pappu"], affiliations=["Washington University in St. Louis"])
    assert len(pappu_matches) > 0 and "Pappu" in pappu_matches[0]["pi"], f"Failed Pappu: {pappu_matches}"

    # 4. DeepMind
    dm_matches = match_famous_groups(authors=["John Jumper", "Demis Hassabis"], affiliations=["Google DeepMind"])
    assert len(dm_matches) > 0 and "DeepMind" in dm_matches[0]["badge"], f"Failed DeepMind: {dm_matches}"

    # 5. Unaffiliated
    unknown = score_group_prestige(authors=["John Doe"], affiliations=["Random Lab"])
    assert unknown["is_famous_group"] is False and unknown["group_score"] == 65

    print("  ✅ Group Directory & Pioneer Lab matching passed!")

def test_paper_checker_mock():
    print("Testing PaperChecker multi-factor audit...")
    checker = PaperChecker()
    mock_paper = {
        "id": "test_001",
        "title": "De novo design of allosteric protein switches with RFdiffusion and ProteinMPNN",
        "abstract": "We develop a generalized diffusion framework for allosteric conformational states. We validate binders experimentally using cryo-EM at 2.4 A resolution and surface plasmon resonance (SPR) showing 12 nM affinity.",
        "journal": "Nature Biotechnology",
        "authors": ["Joseph Watson", "David Baker"],
        "affiliations": ["Institute for Protein Design, University of Washington"],
        "url": "https://nature.com/example",
        "published_date": "2026-09-20"
    }

    audit: AuditResult = checker.check_paper(mock_paper)
    print(f"  ↳ Composite Score: {audit.composite_score} / 100")
    print(f"  ↳ Innovation Score: {audit.innovation_score}")
    print(f"  ↳ Impact Score: {audit.impact_score}")
    print(f"  ↳ Rigor Score: {audit.rigor_score}")
    print(f"  ↳ Journal Score: {audit.journal_score} (IF: {audit.impact_factor})")
    print(f"  ↳ Group Score: {audit.group_score} ({audit.top_group_badge})")
    print(f"  ↳ Verdict: {audit.verdict_label}")

    assert audit.composite_score >= 80, f"Expected high score for Baker Nat Biotech paper, got {audit.composite_score}"
    assert audit.is_famous_group is True
    assert audit.impact_factor > 30.0

    md = generate_markdown_scorecard(audit)
    assert "Scorecard" in md and "Baker Lab" in md
    print("  ✅ PaperChecker audit passed!")

def test_qa_engine_mock():
    print("Testing PaperQAEngine...")
    qa_engine = PaperQAEngine()
    mock_paper = {
        "title": "Length-encoded phase separation of proline-alanine-serine polymers",
        "abstract": "We demonstrate that uncharged, disorder-prone PAS polymers undergo liquid-liquid phase separation (LLPS) strictly controlled by polymer length. Microscopy reveals micrometer droplets with liquid recovery dynamics via FRAP. This informs design of artificial condensates.",
        "journal": "bioRxiv",
        "authors": ["Rohit V. Pappu", "Tanja Mittag"]
    }
    ans = qa_engine.answer_question(mock_paper, "What experimental method was used to observe liquid dynamics?")
    print(f"  ↳ QA Answer snippet: {ans[:150]}...")
    assert len(ans) > 20
    print("  ✅ PaperQAEngine passed!")

if __name__ == "__main__":
    print("=== Running Paper Check & QA Agent Test Suite ===")
    test_journal_rankings()
    test_group_directory()
    test_paper_checker_mock()
    test_qa_engine_mock()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
