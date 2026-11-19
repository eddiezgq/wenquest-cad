# AI part design replay test (plan 0.3c). Run inside FreeCADCmd:
#   set WQCAD_AI_LIB=...\Library\Mod\FreeCADAIParts\lib
#   set WQCAD_OUT=...\logs\ai-design.json
#   FreeCADCmd.exe run_ai_design_test.py
# Replays the recorded real-model runs of both examples: the lockstitch upper shaft (stepped shaft) and the cobot J2
# output shaft (joint hollow shaft): conditions -> proposals -> checks (recorded FEA stress concentration and robot
# dynamics loads) -> 3D model and read-back. No AI model is called. About 1 minute.
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
    ok = True
    for kind, key in (("阶梯轴", "shaft"), ("关节空心轴", "joint")):
        r = C.run(C.example_text(kind), C.example_client(kind), library, Path(os.path.dirname(out)) / f"ai-design-{key}",
                  kind=kind, replay=True)
        d, g = r["result"], r["model"] or {}
        res[key] = {"status": d.get("status"), "rounds": len(d.get("rounds") or []), "chosen_round": d.get("chosen_round"),
                    "readback": g.get("readback"), "segments": g.get("readback_rows"), "mass_kg": g.get("mass_kg"),
                    "problems": g.get("problems")}
        ok = ok and d.get("status") == "pass" and g.get("readback") == "pass" and g.get("readback_rows") == 5
except Exception:
    ok = False
    res["error"] = traceback.format_exc()
res["seconds"] = round(time.time() - t0)
res["ok"] = ok
with open(out, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print("WQCAD-AI-DESIGN", *[f"{k}: {res[k]['status']} rounds {res[k]['rounds']} chosen {res[k]['chosen_round']} readback {res[k]['readback']} "
                            f"segments {res[k]['segments']} mass {res[k]['mass_kg']}" for k in ("shaft", "joint") if k in res],
      "seconds", res["seconds"], "OK" if ok else "NOT OK")
