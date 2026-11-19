# AI part design replay test (plan 0.3c). Run inside FreeCADCmd:
#   set WQCAD_AI_LIB=...\Library\Mod\FreeCADAIParts\lib
#   set WQCAD_OUT=...\logs\ai-design.json
#   FreeCADCmd.exe run_ai_design_test.py
# Replays the recorded real-model run of the lockstitch upper shaft example: conditions -> proposals -> FEA stress
# concentration -> checks -> 3D model and read-back. No AI model is called. About 5 minutes.
import json
import os
import sys
import time
import traceback

lib = os.path.abspath(os.environ["WQCAD_AI_LIB"])
out = os.environ["WQCAD_OUT"]
sys.path.insert(0, lib)
res = {"lib": lib}
ok = False
t0 = time.time()
try:
    from pathlib import Path

    from freecad_addon.core import ai_design as C
    from kb.library import JsonLibrary

    library = JsonLibrary(Path(lib) / "data" / "library")
    r = C.run(C.example_text(), C.example_client(), library, Path(os.path.dirname(out)) / "ai-design-out", replay=True)
    d, g = r["result"], r["model"] or {}
    res.update(status=d.get("status"), rounds=len(d.get("rounds") or []), readback=g.get("readback"),
               segments=g.get("readback_rows"), mass_kg=g.get("mass_kg"), problems=g.get("problems"))
    ok = d.get("status") == "pass" and g.get("readback") == "pass" and g.get("readback_rows") == 5
except Exception:
    res["error"] = traceback.format_exc()
res["seconds"] = round(time.time() - t0)
res["ok"] = ok
with open(out, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print("WQCAD-AI-DESIGN", "status", res.get("status"), "rounds", res.get("rounds"), "readback", res.get("readback"),
      "segments", res.get("segments"), "seconds", res["seconds"], "OK" if ok else "NOT OK")
