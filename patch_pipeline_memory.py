import json
from pathlib import Path


notebook_path = Path("MPNN_AF.ipynb")
notebook = json.loads(notebook_path.read_text(encoding="utf-8"))


for cell in notebook["cells"]:
    if cell.get("cell_type") != "code":
        continue

    source = "".join(cell.get("source", []))
    if not source.startswith("#@title AF2-IG Complex"):
        continue

    source = source.replace(
        'import os, glob, math, shutil, subprocess, inspect\n'
        'import numpy as np\n'
        'import pandas as pd\n'
        'import jax.numpy as jnp\n'
        'from colabdesign.af import mk_af_model\n',
        'import os, glob, math, shutil, subprocess, inspect, gc\n'
        'import numpy as np\n'
        'import pandas as pd\n'
        'import jax\n'
        'import jax.numpy as jnp\n'
        'from colabdesign.af import mk_af_model\n',
        1,
    )

    source = source.replace(
        'monomer_num_recycles = 1 #@param ["0","1","2","3"] {type:"raw"}\n',
        'monomer_num_recycles = 1 #@param ["0","1","2","3"] {type:"raw"}\n'
        'run_monomer_af2 = True #@param {type:"boolean"}\n'
        'run_interface_quality = True #@param {type:"boolean"}\n',
        1,
    )

    source = source.replace(
        'def run_af2_ig_complex_af2_monomer_rosetta(\n'
        '    max_designs_per_pdb=4,\n'
        '    designed_chain="",\n'
        '    complex_num_models=1,\n'
        '    complex_num_recycles=1,\n'
        '    monomer_num_models=1,\n'
        '    monomer_num_recycles=1,\n'
        '):\n',
        'def clear_jax_memory():\n'
        '    try:\n'
        '        jax.clear_caches()\n'
        '    except Exception:\n'
        '        pass\n'
        '    gc.collect()\n'
        '\n'
        'def run_af2_ig_complex_af2_monomer_rosetta(\n'
        '    max_designs_per_pdb=4,\n'
        '    designed_chain="",\n'
        '    complex_num_models=1,\n'
        '    complex_num_recycles=1,\n'
        '    monomer_num_models=1,\n'
        '    monomer_num_recycles=1,\n'
        '    run_monomer_af2=True,\n'
        '    run_interface_quality=True,\n'
        '):\n',
        1,
    )

    source = source.replace(
        '        monomer_model = mk_af_model(\n'
        '            use_multimer=False,\n'
        '            use_templates=False,\n'
        '            best_metric="plddt",\n'
        '            initial_guess=False,\n'
        '            data_dir=af_data_dir,\n'
        '        )\n'
        '        monomer_model.prep_inputs(monomer_pdb, design_chain, homooligomer=False)\n'
        '\n'
        '        total_designs = min(out["S"].shape[0], max_designs_per_pdb)\n',
        '        total_designs = min(out["S"].shape[0], max_designs_per_pdb)\n',
        1,
    )

    source = source.replace(
        '            complex_model.restart()\n'
        '            complex_model.predict(\n'
        '                seq=complex_seq,\n'
        '                num_recycles=complex_num_recycles,\n'
        '                num_models=complex_num_models,\n'
        '                verbose=False,\n'
        '            )\n'
        '            c_log = dict(complex_model.aux["log"])\n'
        '            c_log["complex_confidence"] = 0.8 * c_log.get("i_ptm", 0.0) + 0.2 * c_log.get("ptm", 0.0)\n'
        '            complex_model._save_results(save_best=True, best_metric="i_ptm", verbose=False)\n'
        '            complex_pdb = os.path.join(complex_dir, f"{pdb_name}_n{n}_complex_af2ig.pdb")\n'
        '            complex_model.save_current_pdb(complex_pdb)\n'
        '            complex_model._k += 1\n'
        '\n'
        '            monomer_model.restart()\n'
        '            monomer_model.predict(\n'
        '                seq=monomer_seq,\n'
        '                num_recycles=monomer_num_recycles,\n'
        '                num_models=monomer_num_models,\n'
        '                verbose=False,\n'
        '            )\n'
        '            m_log = dict(monomer_model.aux["log"])\n'
        '            monomer_pdb_out = os.path.join(monomer_dir, f"{pdb_name}_n{n}_{design_chain}_monomer_af2.pdb")\n'
        '            monomer_model.save_current_pdb(monomer_pdb_out)\n'
        '\n'
        '            interface_metrics = pyrosetta_interface_quality(complex_pdb, target_chains, [design_chain])\n',
        '            complex_pdb = os.path.join(complex_dir, f"{pdb_name}_n{n}_complex_af2ig.pdb")\n'
        '            monomer_pdb_out = None\n'
        '            c_log = {}\n'
        '            m_log = {}\n'
        '            interface_metrics = {}\n'
        '\n'
        '            try:\n'
        '                complex_model.restart()\n'
        '                complex_model.predict(\n'
        '                    seq=complex_seq,\n'
        '                    num_recycles=complex_num_recycles,\n'
        '                    num_models=complex_num_models,\n'
        '                    verbose=False,\n'
        '                )\n'
        '                c_log = dict(complex_model.aux["log"])\n'
        '                c_log["complex_confidence"] = 0.8 * c_log.get("i_ptm", 0.0) + 0.2 * c_log.get("ptm", 0.0)\n'
        '                complex_model._save_results(save_best=True, best_metric="i_ptm", verbose=False)\n'
        '                complex_model.save_current_pdb(complex_pdb)\n'
        '                complex_model._k += 1\n'
        '            except Exception as e:\n'
        '                row = {\n'
        '                    "pdb": pdb_name,\n'
        '                    "design_index": n,\n'
        '                    "target_chains": ",".join(target_chains),\n'
        '                    "designed_chain": design_chain,\n'
        '                    "error_stage": "af2ig_complex",\n'
        '                    "error": repr(e),\n'
        '                    "mpnn": out["score"][n],\n'
        '                    "seqid": out["seqid"][n],\n'
        '                    "seq": full_seq,\n'
        '                    "monomer_seq": monomer_seq,\n'
        '                }\n'
        '                rows.append(row)\n'
        '                pd.DataFrame(rows).to_csv(result_csv, index=False)\n'
        '                print("Saved error row to pipeline CSV:", result_csv)\n'
        '                clear_jax_memory()\n'
        '                continue\n'
        '\n'
        '            clear_jax_memory()\n'
        '\n'
        '            if run_monomer_af2:\n'
        '                try:\n'
        '                    monomer_model = mk_af_model(\n'
        '                        use_multimer=False,\n'
        '                        use_templates=False,\n'
        '                        best_metric="plddt",\n'
        '                        initial_guess=False,\n'
        '                        data_dir=af_data_dir,\n'
        '                    )\n'
        '                    monomer_model.prep_inputs(monomer_pdb, design_chain, homooligomer=False)\n'
        '                    monomer_model.restart()\n'
        '                    monomer_model.predict(\n'
        '                        seq=monomer_seq,\n'
        '                        num_recycles=monomer_num_recycles,\n'
        '                        num_models=monomer_num_models,\n'
        '                        verbose=False,\n'
        '                    )\n'
        '                    m_log = dict(monomer_model.aux["log"])\n'
        '                    monomer_pdb_out = os.path.join(monomer_dir, f"{pdb_name}_n{n}_{design_chain}_monomer_af2.pdb")\n'
        '                    monomer_model.save_current_pdb(monomer_pdb_out)\n'
        '                    del monomer_model\n'
        '                    clear_jax_memory()\n'
        '                except Exception as e:\n'
        '                    m_log = {"error_stage": "af2_monomer", "error": repr(e)}\n'
        '                    print("Monomer AF2 failed:", repr(e))\n'
        '                    clear_jax_memory()\n'
        '\n'
        '            if run_interface_quality:\n'
        '                interface_metrics = pyrosetta_interface_quality(complex_pdb, target_chains, [design_chain])\n',
        1,
    )

    source = source.replace(
        '                "monomer_pdb": monomer_pdb_out,\n',
        '                "monomer_pdb": monomer_pdb_out,\n'
        '                "error_stage": m_log.get("error_stage"),\n'
        '                "error": m_log.get("error"),\n',
        1,
    )

    source = source.replace(
        '            pd.DataFrame(rows).to_csv(result_csv, index=False)\n'
        '            print("Updated pipeline CSV:", result_csv)\n',
        '            pd.DataFrame(rows).to_csv(result_csv, index=False)\n'
        '            print("Updated pipeline CSV:", result_csv)\n'
        '            clear_jax_memory()\n',
        1,
    )

    source = source.replace(
        '        monomer_num_recycles=monomer_num_recycles,\n'
        '    )\n',
        '        monomer_num_recycles=monomer_num_recycles,\n'
        '        run_monomer_af2=run_monomer_af2,\n'
        '        run_interface_quality=run_interface_quality,\n'
        '    )\n',
        1,
    )

    cell["source"] = [line + "\n" for line in source.splitlines()]
    cell["source"][-1] = cell["source"][-1].rstrip("\n")
    cell["outputs"] = []
    cell["execution_count"] = None
    break
else:
    raise RuntimeError("Could not find AF2/Rosetta pipeline cell.")


notebook_path.write_text(
    json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
    encoding="utf-8",
)
