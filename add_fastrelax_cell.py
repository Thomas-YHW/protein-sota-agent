import json
from pathlib import Path


notebook_path = Path("MPNN_AF.ipynb")
notebook = json.loads(notebook_path.read_text(encoding="utf-8"))


cell_source = r'''#@title Rosetta FastRelax on AF2 Complex Outputs

#@markdown Run this after the AF2-IG pipeline cell.
run_fastrelax_now = False #@param {type:"boolean"}
max_relax_models = 10 #@param {type:"integer"}
relax_repeats = 1 #@param {type:"integer"}
resume_fastrelax = True #@param {type:"boolean"}
force_rerun_fastrelax = False #@param {type:"boolean"}

import os, math
import numpy as np
import pandas as pd

if "output_dir" not in dir():
    output_dir = os.path.join(
        "/content/drive/MyDrive/sequence_input_diffusion_example_outputs",
        "proteinmpnn_alphafold_results"
    )

pipeline_dir = os.path.join(output_dir, "af2ig_complex_af2monomer_rosetta")
pipeline_csv = os.path.join(pipeline_dir, "af2ig_complex_af2monomer_rosetta_results.csv")
relax_dir = os.path.join(pipeline_dir, "fastrelax")
relax_csv = os.path.join(pipeline_dir, "fastrelax_interface_results.csv")

os.makedirs(relax_dir, exist_ok=True)

def read_heavy_atoms_for_relax(pdb_path, chains):
    chain_set = set(chains)
    atoms = []
    with open(pdb_path) as handle:
        for line in handle:
            if not line.startswith(("ATOM", "HETATM")) or len(line) < 54:
                continue
            chain = line[21].strip()
            atom = line[12:16].strip()
            element = line[76:78].strip() if len(line) >= 78 else atom[0]
            if chain not in chain_set or element.upper() == "H":
                continue
            try:
                xyz = np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])])
            except ValueError:
                continue
            atoms.append((chain, atom, xyz))
    return atoms

def fallback_interface_quality_relax(pdb_path, target_chains, binder_chains, contact_cutoff=5.0, clash_cutoff=2.2):
    target_atoms = read_heavy_atoms_for_relax(pdb_path, target_chains)
    binder_atoms = read_heavy_atoms_for_relax(pdb_path, binder_chains)
    contacts = 0
    clashes = 0
    min_dist = math.inf

    for _, _, a in target_atoms:
        for _, _, b in binder_atoms:
            d = float(np.linalg.norm(a - b))
            min_dist = min(min_dist, d)
            if d <= contact_cutoff:
                contacts += 1
            if d <= clash_cutoff:
                clashes += 1

    return {
        "relaxed_interface_contacts_5A": contacts,
        "relaxed_interface_clashes_2p2A": clashes,
        "relaxed_interface_min_distance": None if math.isinf(min_dist) else min_dist,
    }

def run_fastrelax_one_pdb(input_pdb, output_pdb, target_chains, binder_chains, relax_repeats=1):
    try:
        import pyrosetta
        from pyrosetta.rosetta.protocols.relax import FastRelax
        from pyrosetta.rosetta.protocols.analysis import InterfaceAnalyzerMover
    except Exception as e:
        raise ImportError(
            "PyRosetta is required for FastRelax. Install/import PyRosetta first. "
            "The fallback geometry metrics do not perform relaxation."
        ) from e

    try:
        initialized = pyrosetta.rosetta.basic.was_init_called()
    except Exception:
        initialized = False

    if not initialized:
        pyrosetta.init("-mute all")

    pose = pyrosetta.pose_from_pdb(input_pdb)
    scorefxn = pyrosetta.get_fa_scorefxn()

    relax = FastRelax()
    relax.set_scorefxn(scorefxn)
    relax.max_iter(200)

    for _ in range(max(1, int(relax_repeats))):
        relax.apply(pose)

    pose.dump_pdb(output_pdb)

    interface = "".join(target_chains) + "_" + "".join(binder_chains)
    metrics = {
        "relaxed_pdb": output_pdb,
        "relaxed_total_score": float(scorefxn(pose)),
        "fastrelax_available": True,
    }

    try:
        mover = InterfaceAnalyzerMover(interface)
        mover.apply(pose)
        for key, method in [
            ("relaxed_rosetta_dG_separated", "get_interface_dG"),
            ("relaxed_rosetta_delta_sasa", "get_interface_delta_sasa"),
            ("relaxed_rosetta_shape_complementarity", "get_interface_sc"),
            ("relaxed_rosetta_packstat", "get_interface_packstat"),
        ]:
            try:
                metrics[key] = float(getattr(mover, method)())
            except Exception:
                metrics[key] = None
    except Exception as e:
        metrics["fastrelax_interface_error"] = repr(e)

    metrics.update(fallback_interface_quality_relax(output_pdb, target_chains, binder_chains))
    return metrics

def run_fastrelax_pipeline(max_relax_models=10, relax_repeats=1):
    if not os.path.isfile(pipeline_csv):
        raise FileNotFoundError(f"Pipeline CSV not found: {pipeline_csv}")

    source_df = pd.read_csv(pipeline_csv)
    if len(source_df) == 0:
        raise ValueError(f"Pipeline CSV is empty: {pipeline_csv}")

    rows = []
    completed = set()

    print("FastRelax input CSV:", pipeline_csv)
    print("FastRelax output directory:", relax_dir)
    print("FastRelax result CSV:", relax_csv)

    if resume_fastrelax and not force_rerun_fastrelax and os.path.isfile(relax_csv):
        try:
            cached = pd.read_csv(relax_csv)
            rows = cached.to_dict("records")
            completed = {
                (str(row["pdb"]), int(row["design_index"]))
                for row in rows
                if pd.notna(row.get("pdb")) and pd.notna(row.get("design_index")) and pd.isna(row.get("fastrelax_error"))
            }
            print(f"Loaded {len(rows)} cached FastRelax rows.")
        except pd.errors.EmptyDataError:
            rows = []

    candidates = source_df.copy()
    if "error" in candidates.columns:
        candidates = candidates[candidates["error"].isna()]
    if "complex_pdb" in candidates.columns:
        candidates = candidates[candidates["complex_pdb"].notna()]

    if "af2ig_complex_confidence" in candidates.columns:
        candidates = candidates.sort_values("af2ig_complex_confidence", ascending=False)

    candidates = candidates.head(max_relax_models)

    for _, row in candidates.iterrows():
        pdb_name = str(row["pdb"])
        design_index = int(row["design_index"])

        if (pdb_name, design_index) in completed:
            print(f"Skipping FastRelax for {pdb_name} design {design_index}; cached result exists.")
            continue

        input_pdb = str(row["complex_pdb"])
        if not os.path.isfile(input_pdb):
            result = row.to_dict()
            result.update({
                "fastrelax_available": False,
                "fastrelax_error": f"Missing complex PDB: {input_pdb}",
            })
            rows.append(result)
            pd.DataFrame(rows).to_csv(relax_csv, index=False)
            continue

        target = str(row["target_chains"]).split(",")
        binder = [str(row["designed_chain"])]
        output_pdb = os.path.join(relax_dir, f"{pdb_name}_n{design_index}_fastrelax.pdb")

        print(f"FastRelax: {pdb_name} design {design_index}")
        print("Input:", input_pdb)
        print("Output:", output_pdb)

        result = row.to_dict()
        try:
            result.update(
                run_fastrelax_one_pdb(
                    input_pdb=input_pdb,
                    output_pdb=output_pdb,
                    target_chains=target,
                    binder_chains=binder,
                    relax_repeats=relax_repeats,
                )
            )
            result["fastrelax_error"] = None
        except Exception as e:
            result.update(fallback_interface_quality_relax(input_pdb, target, binder))
            result["fastrelax_available"] = False
            result["fastrelax_error"] = repr(e)
            result["relaxed_pdb"] = None
            print("FastRelax failed:", repr(e))

        rows.append(result)
        pd.DataFrame(rows).to_csv(relax_csv, index=False)
        print("Updated FastRelax CSV:", relax_csv)

    df = pd.DataFrame(rows)
    df.to_csv(relax_csv, index=False)
    print("Saved FastRelax results:", relax_csv)
    return df

if run_fastrelax_now:
    fastrelax_df = run_fastrelax_pipeline(
        max_relax_models=max_relax_models,
        relax_repeats=relax_repeats,
    )
    data_table.DataTable(
        fastrelax_df.sort_values(
            ["relaxed_rosetta_dG_separated", "relaxed_interface_clashes_2p2A"],
            ascending=[True, True],
            na_position="last",
        ).round(3)
    )
'''


new_cell = {
    "cell_type": "code",
    "execution_count": None,
    "id": "rosetta-fastrelax",
    "metadata": {},
    "outputs": [],
    "source": [line + "\n" for line in cell_source.splitlines()],
}
new_cell["source"][-1] = new_cell["source"][-1].rstrip("\n")


for i, cell in enumerate(notebook["cells"]):
    if cell.get("cell_type") == "code" and cell.get("source"):
        if cell["source"][0].startswith("#@title Rosetta FastRelax"):
            notebook["cells"][i] = new_cell
            break
else:
    notebook["cells"].append(new_cell)

notebook_path.write_text(
    json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
    encoding="utf-8",
)
