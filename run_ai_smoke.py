# Smoke check of the AI Parts workbench installed into WenQuest CAD (plan 0.2a). Run inside FreeCADCmd:
#   set WQCAD_AI_LIB=...\Library\Mod\FreeCADAIParts\lib
#   set WQCAD_OUT=...\logs\ai-smoke.json
#   FreeCADCmd.exe run_ai_smoke.py
# No AI model is called: the golden cases exercise the deterministic selection and checking engine only.
import json
import os
import sys
import traceback

lib = os.path.normcase(os.path.abspath(os.environ["WQCAD_AI_LIB"]))
out = os.environ["WQCAD_OUT"]
sys.path.insert(0, lib)
if os.environ.get("WQCAD_AI_SITE"):  # only for testing outside WenQuest CAD; there pip installs into the environment
    sys.path.append(os.environ["WQCAD_AI_SITE"])
res = {"lib": lib}
ok = False
try:
    import FreeCAD

    res["freecad"] = ".".join(FreeCAD.Version()[:3])
    import freecad_addon
    import llm_gateway
    from engine import golden

    addon = os.path.normcase(os.path.abspath(freecad_addon.__file__))
    res["from_install_dir"] = addon.startswith(lib)
    res["init_gui"] = os.path.isfile(os.path.join(os.path.dirname(lib), "InitGui.py"))
    res["anthropic"] = __import__("importlib").util.find_spec("anthropic") is not None
    res["ai_region_here"] = llm_gateway.region_of(os.environ)
    res["ai_provider_here"] = llm_gateway.preferred(os.environ)
    res["ai_keys_set"] = llm_gateway.order(os.environ)
    runs = golden.run()
    good = sum(1 for r in runs if r["ok"])
    res["golden"] = f"{good}/{len(runs)}"
    res["golden_not_ok"] = [r["id"] for r in runs if not r["ok"]]
    # AI part design (plan 0.3c): local mesher and solver, plus the example and its recording shipped with the workbench
    res["gmsh"] = __import__("importlib").util.find_spec("gmsh") is not None
    from analysis.common.solvers import find_ccx

    res["ccx"] = find_ccx()
    res["ai_design_example"] = os.path.isfile(os.path.join(lib, "examples", "ai-design", "ls-upper-shaft", "requirement.txt"))
    rec = os.path.join(lib, "tests", "recordings", "design")
    res["ai_design_recordings"] = len(os.listdir(rec)) if os.path.isdir(rec) else 0
    ok = (bool(runs) and good == len(runs) and res["from_install_dir"] and res["init_gui"] and res["anthropic"]
          and res["gmsh"] and bool(res["ccx"]) and res["ai_design_example"] and res["ai_design_recordings"] > 0)
except Exception:
    res["error"] = traceback.format_exc()
res["ok"] = ok
with open(out, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print("WQCAD-AI", "golden", res.get("golden"), "gmsh", res.get("gmsh"), "ccx", bool(res.get("ccx")),
      "ai-design-example", res.get("ai_design_example"), "OK" if ok else "NOT OK")
