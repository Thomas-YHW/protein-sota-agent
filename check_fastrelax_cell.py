import ast
import json
from pathlib import Path


notebook = json.loads(Path("MPNN_AF.ipynb").read_text(encoding="utf-8"))
for i, cell in enumerate(notebook["cells"]):
    if cell.get("cell_type") == "code" and cell.get("source"):
        source = "".join(cell["source"])
        if source.startswith("#@title Rosetta FastRelax"):
            ast.parse(source)
            print(f"FastRelax cell syntax ok at index {i}")
            break
else:
    raise RuntimeError("FastRelax cell not found")
