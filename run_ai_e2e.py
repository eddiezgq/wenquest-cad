# Installed WenQuest CAD: the AI workbench features that need FreeCAD 1.1 and the extra packages really work
# (11-20: “装配体多体动力学” failed on FreeCAD 1.1 — getMovingPart signature; “出报告” needs python-docx).
# Run inside the installed environment:
#   set WQCAD_AI_LIB=...\Library\Mod\FreeCADAIParts\lib
#   set WQCAD_OUT=...\logs\ai-e2e.json
#   FreeCADCmd.exe run_ai_e2e.py      (or the environment's python with FreeCAD's lib on PYTHONPATH)
import json
import os
import sys
import traceback

lib = os.path.abspath(os.environ["WQCAD_AI_LIB"])
out = os.environ.get("WQCAD_OUT", "ai-e2e.json")
sys.path.insert(0, lib)
res = {"lib": lib}


def check(name, fn):
    try:
        res[name] = fn()
    except Exception:
        res[name] = False
        res[name + "_error"] = traceback.format_exc()[-1500:]


def report_packages():
    import docx  # noqa: F401  (问渠有限元 / 问渠多体动力学“出报告”写 Word)
    import matplotlib  # noqa: F401  (报告里的云图、曲线)

    return True


def mbd_packages():
    import mujoco  # noqa: F401  (多体动力学的 MuJoCo 求解)

    return True


def mbd_from_assembly():
    """两块方块、一个转动副，引用以零件为根（FreeCAD 1.1 界面的写法）；导出的运动副两端要是这两个零件"""
    import FreeCAD as App
    import Part
    from freecad_addon.fc.assembly_modules import load
    from freecad_addon.fc.mbd_assembly import describe

    JointObject, _ = load()
    doc = App.newDocument("e2e")
    asm = doc.addObject("Assembly::AssemblyObject", "Assembly")
    jg = asm.newObject("Assembly::JointGroup", "Joints")
    a = asm.newObject("Part::Feature", "Base")
    a.Shape = Part.makeBox(10, 10, 10)
    b = asm.newObject("Part::Feature", "Lid")
    b.Shape = Part.makeBox(10, 10, 2)
    b.Placement.Base = App.Vector(0, 0, 10)
    doc.recompute()
    g = jg.newObject("App::FeaturePython", "Ground")
    JointObject.GroundedJoint(g, a)
    j = jg.newObject("App::FeaturePython", "Hinge")
    JointObject.Joint(j, 1)
    j.Proxy.setJointConnectors(j, [[a, ["Face6", "Vertex8"]], [b, ["Face5", "Vertex2"]]])
    doc.recompute()
    d = describe(asm, {"Base": 1.0, "Lid": 0.5})
    ends = [(x["part1"], x["part2"]) for x in d["joints"]]
    res["mbd_joint_ends"] = ends
    App.closeDocument(doc.Name)
    return ends == [("Base", "Lid")] or ends == [("Lid", "Base")]


check("report_packages", report_packages)
check("mbd_packages", mbd_packages)
check("mbd_from_assembly", mbd_from_assembly)
res["ok"] = all(res.get(k) is True for k in ("report_packages", "mbd_packages", "mbd_from_assembly"))
with open(out, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print("WQCAD-AI-E2E", {k: res.get(k) for k in ("report_packages", "mbd_packages", "mbd_from_assembly")}, "OK" if res["ok"] else "NOT OK")
for k, v in res.items():
    if k.endswith("_error"):
        print(k, v)
sys.exit(0 if res["ok"] else 1)
