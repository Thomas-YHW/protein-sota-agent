"""
Famous Research Groups & Pioneer Labs Knowledge Base.
Matches papers against renowned Key Opinion Leaders (KOLs), pioneer institutions,
and elite biophysics/AI labs in Protein Design, pLMs, IDRs, and Liquid-Liquid Phase Separation.
"""

import re
from typing import List, Dict, Any, Optional

# Curated registry of pioneer labs and world leaders
FAMOUS_GROUPS = [
    # -------------------------------------------------------------
    # 1. De Novo Protein Design & Structural Generative AI
    # -------------------------------------------------------------
    {
        "pi": "David Baker",
        "aliases": ["d baker", "david baker", "baker d"],
        "institutions": ["institute for protein design", "ipd", "university of washington", "howard hughes medical institute"],
        "domain": "De Novo Design & RFdiffusion / ProteinMPNN",
        "prestige_score": 100,
        "badge": "Baker Lab (IPD UW)"
    },
    {
        "pi": "Demis Hassabis & John Jumper",
        "aliases": ["demis hassabis", "john jumper", "j jumper", "d hassabis", "pushmeet kohli"],
        "institutions": ["google deepmind", "deepmind", "isomorphic labs"],
        "domain": "Structural AI & AlphaFold Foundation Models",
        "prestige_score": 100,
        "badge": "DeepMind / Isomorphic Labs"
    },
    {
        "pi": "Sergey Ovchinnikov",
        "aliases": ["sergey ovchinnikov", "s ovchinnikov", "ovchinnikov s"],
        "institutions": ["mit", "massachusetts institute of technology", "harvard", "john hancock"],
        "domain": "ColabDesign & Evolutionary Deep Learning",
        "prestige_score": 95,
        "badge": "Ovchinnikov Lab (MIT)"
    },
    {
        "pi": "Mohammed AlQuraishi",
        "aliases": ["mohammed alquraishi", "m alquraishi", "alquraishi m"],
        "institutions": ["columbia university", "columbia"],
        "domain": "OpenFold & Differentiable Structural Biology",
        "prestige_score": 95,
        "badge": "AlQuraishi Lab (Columbia)"
    },
    {
        "pi": "Debora Marks",
        "aliases": ["debora marks", "debora s marks", "d marks", "marks ds"],
        "institutions": ["harvard medical school", "broad institute"],
        "domain": "Generative Sequence Models & EVmutation",
        "prestige_score": 95,
        "badge": "Marks Lab (Harvard)"
    },
    {
        "pi": "Alex Rives (EvolutionaryScale)",
        "aliases": ["alexander rives", "alex rives", "a rives", "rives a"],
        "institutions": ["evolutionaryscale", "meta ai", "fair", "new york university"],
        "domain": "ESM-2 & ESM3 Frontier Language Models",
        "prestige_score": 96,
        "badge": "EvolutionaryScale / Meta FAIR"
    },
    {
        "pi": "Martin Steinegger",
        "aliases": ["martin steinegger", "m steinegger", "steinegger m"],
        "institutions": ["seoul national university", "snu"],
        "domain": "ColabFold, MMseqs2 & Foldseek Search",
        "prestige_score": 94,
        "badge": "Steinegger Lab (ColabFold / Foldseek)"
    },
    {
        "pi": "Brian Kuhlman",
        "aliases": ["brian kuhlman", "b kuhlman", "kuhlman b"],
        "institutions": ["university of north carolina", "unc chapel hill"],
        "domain": "Rosetta Computational Protein Design & Binders",
        "prestige_score": 92,
        "badge": "Kuhlman Lab (UNC)"
    },
    {
        "pi": "Philip Bradley",
        "aliases": ["philip bradley", "p bradley", "bradley p"],
        "institutions": ["fred hutchinson cancer center", "fred hutch", "university of washington"],
        "domain": "TCR & Antibody-Antigen Structural Modeling",
        "prestige_score": 92,
        "badge": "Bradley Lab (Fred Hutch)"
    },
    {
        "pi": "William DeGrado",
        "aliases": ["william degrado", "william f degrado", "w degrado", "degrado wf"],
        "institutions": ["ucsf", "university of california san francisco"],
        "domain": "De Novo Metalloprotein & Helical Bundle Design",
        "prestige_score": 95,
        "badge": "DeGrado Lab (UCSF)"
    },
    {
        "pi": "George Church",
        "aliases": ["george church", "george m church", "g church", "church gm"],
        "institutions": ["harvard medical school", "wyss institute", "broad institute"],
        "domain": "Synthetic Biology & Directed Evolution",
        "prestige_score": 96,
        "badge": "Church Lab (Harvard / Wyss)"
    },
    {
        "pi": "Frances Arnold",
        "aliases": ["frances arnold", "frances h arnold", "f arnold", "arnold fh"],
        "institutions": ["caltech", "california institute of technology"],
        "domain": "Directed Evolution & Machine Learning for Enzymes",
        "prestige_score": 98,
        "badge": "Arnold Lab (Caltech - Nobel Laureate)"
    },

    # -------------------------------------------------------------
    # 2. Liquid-Liquid Phase Separation (LLPS), IDRs & Condensates
    # -------------------------------------------------------------
    {
        "pi": "Anthony Hyman",
        "aliases": ["anthony hyman", "anthony a hyman", "a hyman", "hyman aa"],
        "institutions": ["max planck institute of molecular cell biology and genetics", "mpi cbg", "dresden"],
        "domain": "Phase Separation Discovery & Physical Chemistry of Condensates",
        "prestige_score": 99,
        "badge": "Hyman Lab (MPI-CBG Dresden)"
    },
    {
        "pi": "Clifford Brangwynne",
        "aliases": ["clifford brangwynne", "clifford p brangwynne", "c brangwynne", "brangwynne cp"],
        "institutions": ["princeton university", "princeton", "howard hughes medical institute"],
        "domain": "Biophysical Principles of Liquid Condensates & OptoDroplets",
        "prestige_score": 99,
        "badge": "Brangwynne Lab (Princeton)"
    },
    {
        "pi": "Rohit Pappu",
        "aliases": ["rohit pappu", "rohit v pappu", "r pappu", "pappu rv"],
        "institutions": ["washington university in st louis", "washu", "center for biomolecular condensates"],
        "domain": "Polymer Physics & Sequence Grammar of IDRs / Condensates",
        "prestige_score": 98,
        "badge": "Pappu Lab (WashU)"
    },
    {
        "pi": "Tanja Mittag",
        "aliases": ["tanja mittag", "t mittag", "mittag t"],
        "institutions": ["st jude childrens research hospital", "st jude"],
        "domain": "NMR & Multi-valent Sticker-Spacer Interactions in IDRs",
        "prestige_score": 96,
        "badge": "Mittag Lab (St. Jude)"
    },
    {
        "pi": "Julie Forman-Kay",
        "aliases": ["julie forman kay", "julie d forman kay", "j forman kay", "forman kay jd"],
        "institutions": ["hospital for sick children", "sickkids", "university of toronto"],
        "domain": "Conformational Ensembles & NMR Spectroscopy of IDPs",
        "prestige_score": 96,
        "badge": "Forman-Kay Lab (SickKids / Toronto)"
    },
    {
        "pi": "J. Paul Taylor",
        "aliases": ["paul taylor", "j paul taylor", "jp taylor", "taylor jp"],
        "institutions": ["st jude childrens research hospital", "st jude", "howard hughes medical institute"],
        "domain": "Condensate Dynamics, FUS/TDP-43 & Prion-like Neurodegeneration",
        "prestige_score": 97,
        "badge": "Paul Taylor Lab (St. Jude)"
    },
    {
        "pi": "Michael Rosen",
        "aliases": ["michael rosen", "michael k rosen", "m rosen", "rosen mk"],
        "institutions": ["ut southwestern", "university of texas southwestern", "howard hughes medical institute"],
        "domain": "Multivalent Actin & Signaling Biomolecular Condensates",
        "prestige_score": 96,
        "badge": "Rosen Lab (UT Southwestern)"
    },
    {
        "pi": "Amy Gladfelter",
        "aliases": ["amy gladfelter", "a gladfelter", "gladfelter a"],
        "institutions": ["duke university", "university of north carolina"],
        "domain": "RNA-driven Condensation & Spatial Organization",
        "prestige_score": 93,
        "badge": "Gladfelter Lab (Duke)"
    },
    {
        "pi": "Simon Alberti",
        "aliases": ["simon alberti", "s alberti", "alberti s"],
        "institutions": ["technische universitat dresden", "tu dresden", "biotec dresden"],
        "domain": "Phase Transitions & Molecular Mechanisms of Protein Aggregation",
        "prestige_score": 94,
        "badge": "Alberti Lab (TU Dresden)"
    },
    {
        "pi": "Dirk Görlich",
        "aliases": ["dirk gorlich", "dirk goerlich", "d gorlich", "gorlich d"],
        "institutions": ["max planck institute for multidisciplinary sciences", "mpi gottingen"],
        "domain": "Nuclear Pore Complex FG-repeats Phase Separation",
        "prestige_score": 96,
        "badge": "Görlich Lab (MPI Göttingen)"
    },

    # -------------------------------------------------------------
    # 3. TDP-43, Prion-like Domains & Amyloid Aggregation
    # -------------------------------------------------------------
    {
        "pi": "Don Cleveland",
        "aliases": ["don cleveland", "don w cleveland", "d cleveland", "cleveland dw"],
        "institutions": ["ucsd", "ludwig institute for cancer research"],
        "domain": "TDP-43 Aggregation, ALS/FTD & Antisense Oligonucleotides",
        "prestige_score": 96,
        "badge": "Cleveland Lab (UCSD)"
    },
    {
        "pi": "Aaron Gitler",
        "aliases": ["aaron gitler", "aaron d gitler", "a gitler", "gitler ad"],
        "institutions": ["stanford university", "stanford school of medicine"],
        "domain": "TDP-43 & C9orf72 Dipeptide Repeat Toxicity & Chaperones",
        "prestige_score": 95,
        "badge": "Gitler Lab (Stanford)"
    },
    {
        "pi": "James Shorter",
        "aliases": ["james shorter", "j shorter", "shorter j"],
        "institutions": ["university of pennsylvania", "perelman school of medicine"],
        "domain": "Protein Disaggregases (Hsp104) & TDP-43 Condensate Rescue",
        "prestige_score": 94,
        "badge": "Shorter Lab (UPenn)"
    },
    {
        "pi": "David Eisenberg",
        "aliases": ["david eisenberg", "david s eisenberg", "d eisenberg", "eisenberg ds"],
        "institutions": ["ucla", "university of california los angeles"],
        "domain": "Atomic Structures of Amyloid Fibrils & PrLD Cross-Beta Spines",
        "prestige_score": 96,
        "badge": "Eisenberg Lab (UCLA)"
    }
]

# Elite Institutions baseline
ELITE_INSTITUTIONS = [
    {"name": "Broad Institute of MIT and Harvard", "keywords": ["broad institute"], "score": 92},
    {"name": "Harvard University / HMS", "keywords": ["harvard university", "harvard medical school"], "score": 92},
    {"name": "MIT (Massachusetts Institute of Technology)", "keywords": ["massachusetts institute of technology", "mit"], "score": 92},
    {"name": "Stanford University", "keywords": ["stanford university"], "score": 92},
    {"name": "University of Cambridge", "keywords": ["university of cambridge", "mrc laboratory of molecular biology", "mrc lmb"], "score": 92},
    {"name": "University of Oxford", "keywords": ["university of oxford"], "score": 90},
    {"name": "Max Planck Society", "keywords": ["max planck institute"], "score": 91},
    {"name": "ETH Zurich", "keywords": ["eth zurich", "eth zürich"], "score": 90},
    {"name": "UC Berkeley", "keywords": ["university of california berkeley", "uc berkeley"], "score": 90},
    {"name": "Francis Crick Institute", "keywords": ["crick institute", "francis crick"], "score": 90},
    {"name": "EMBL (European Molecular Biology Laboratory)", "keywords": ["embl", "european molecular biology laboratory"], "score": 91}
]

def clean_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text.lower().strip()
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    return " ".join(cleaned.split())

def match_famous_groups(
    authors: Optional[List[str]] = None,
    affiliations: Optional[List[str]] = None,
    extra_text: str = ""
) -> List[Dict[str, Any]]:
    """
    Match paper metadata against pioneer labs, KOLs, and elite institutions.
    Returns list of matched group records.
    """
    authors = authors or []
    affiliations = affiliations or []
    
    clean_authors = [clean_text(a) for a in authors]
    clean_affs = [clean_text(aff) for aff in affiliations]
    clean_extra = clean_text(extra_text)
    full_search_text = " ".join(clean_authors + clean_affs + [clean_extra])

    matched = []

    for group in FAMOUS_GROUPS:
        matched_pi = False
        # 1. Match author names
        for alias in group["aliases"]:
            clean_alias = clean_text(alias)
            if any(clean_alias in ca or ca in clean_alias for ca in clean_authors):
                matched_pi = True
                break
            if re.search(r"\b" + re.escape(clean_alias) + r"\b", full_search_text):
                matched_pi = True
                break

        # 2. Match institution / lab name
        matched_inst = False
        for inst_kw in group["institutions"]:
            clean_inst = clean_text(inst_kw)
            if any(clean_inst in ca for ca in clean_affs) or clean_inst in clean_extra:
                matched_inst = True
                break

        # If PI matched, or (institution matched AND domain context matches)
        if matched_pi:
            matched.append({
                "pi": group["pi"],
                "domain": group["domain"],
                "badge": group["badge"],
                "prestige_score": group["prestige_score"],
                "confidence": "high" if matched_inst else "medium",
                "is_kol": True
            })

    # If no specific KOL matched, check elite institutions
    if not matched:
        for inst in ELITE_INSTITUTIONS:
            if any(any(kw in ca for kw in inst["keywords"]) for ca in clean_affs) or any(kw in clean_extra for kw in inst["keywords"]):
                matched.append({
                    "pi": f"Faculty at {inst['name']}",
                    "domain": "Elite Academic Institution",
                    "badge": inst["name"],
                    "prestige_score": inst["score"],
                    "confidence": "institution_only",
                    "is_kol": False
                })
                break

    return matched

def score_group_prestige(
    authors: Optional[List[str]] = None,
    affiliations: Optional[List[str]] = None,
    extra_text: str = ""
) -> Dict[str, Any]:
    """Calculate overall group prestige score and summary."""
    matches = match_famous_groups(authors, affiliations, extra_text)
    if matches:
        # Highest matched score
        best_match = max(matches, key=lambda x: x["prestige_score"])
        return {
            "group_score": best_match["prestige_score"],
            "matched_groups": matches,
            "top_group_badge": best_match["badge"],
            "is_famous_group": True,
            "domain": best_match["domain"]
        }

    # Baseline for unknown or emerging research groups
    return {
        "group_score": 65,
        "matched_groups": [],
        "top_group_badge": "Emerging / Unaffiliated Lab",
        "is_famous_group": False,
        "domain": "General Research"
    }

