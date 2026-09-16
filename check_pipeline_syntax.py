import ast
import json
from pathlib import Path


notebook = json.loads(Path("MPNN_AF.ipynb").read_text(encoding="utf-8"))
for cell in notebook["cells"]:
    if cell.get("cell_type") == "code" and cell.get("source"):
        source = "".join(cell["source"])
        if source.startswith("#@title AF2-IG Complex"):
            ast.parse(source)
            print("pipeline syntax ok")
            break
else:
    raise RuntimeError("pipeline cell not found")
