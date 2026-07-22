import json
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "references" / "CoppieGPT" / "README.md"
OUT = Path(__file__).resolve().parent.parent / "references" / "frameworks.json"

LINE_RE = re.compile(r"^\d+\.\s+\*\*(.+?)\*\*\s*-\s*(.+)$")

frameworks = []
for line in SRC.read_text(encoding="utf-8").splitlines():
    m = LINE_RE.match(line.strip())
    if m:
        name, desc = m.group(1).strip(), m.group(2).strip()
        frameworks.append({"name": name, "structure": desc})

OUT.write_text(json.dumps({"source": "https://github.com/WynterJones/CoppieGPT", "frameworks": frameworks}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Parsed {len(frameworks)} frameworks -> {OUT}")
