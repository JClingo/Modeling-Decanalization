"""Print selected graph nodes with linked input sources for human review."""
import json
from pathlib import Path
import re
import sys

label, asset, pattern = sys.argv[1:4]
nodes = json.loads((Path(__file__).resolve().parent / "derived" / label / (asset + ".json")).read_text())
index = {(n["graph"], n["name"]): n for n in nodes}
def name(n):
    p = n["properties"]
    ref = p.get("VariableReference", p.get("FunctionReference", ""))
    member = re.search(r'MemberName="([^"]+)"', ref)
    return (member.group(1) if member else n["name"]) + (" [SET]" if "VariableSet" in n["name"] else "")
for n in nodes:
    if n["graph"].endswith("_MERGED") or n["graph"].startswith("ExecuteUbergraph"):
        continue
    if not re.search(pattern, n["graph"] + "/" + n["name"] + " " + name(n), re.I):
        continue
    print(n["graph"] + "/" + n["name"], name(n), "T3D:" + str(n["line"]), n["properties"].get("EnabledState", ""))
    for p in n["pins"]:
        if p["PinName"] == "self" or p.get("PinType.PinCategory") == "exec" or p["direction"] != "input":
            continue
        values = []
        for source, pid in p["links"]:
            other = index.get((n["graph"], source))
            values.append((name(other) if other else source) + "@" + source)
        print(" ", p["PinName"], "<-" if values else "=", ", ".join(values) if values else p.get("DefaultValue", p.get("DefaultObject", "(implicit)")))
