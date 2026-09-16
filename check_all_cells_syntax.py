import ast
import json
from pathlib import Path


notebook = json.loads(Path("MPNN_AF.ipynb").read_text(encoding="utf-8"))
for i, cell in enumerate(notebook["cells"]):
    if cell.get("cell_type") != "code":
        continue
    source = "".join(cell.get("source", []))
    try:
        ast.parse(source)
    except SyntaxError as e:
        print(f"syntax error in cell {i}: {e}")
        raise
print("all code cells syntax ok")
