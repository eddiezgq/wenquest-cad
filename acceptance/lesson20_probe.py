"""第 20 课演示前的核对：同一组操作在官方 FreeCAD 和问渠 CAD 上各跑一次，打印 JSON（"PROBE20 {...}"）。
FreeCADCmd lesson20_probe.py"""
import json
import math
import os
import tempfile

import FreeCAD as App
import Import
import Part
import Sketcher

V = App.Vector
out = {"version": App.Version()[:3]}


def mark(k):
    print("STEP20", k, flush=True)


def state(o):
    return list(o.State)


mark("ch18")
# ch18 / ch42：圆角半径太大
b = Part.makeBox(20, 20, 20)
try:
    s = b.makeFillet(12, b.Edges)
    out["fillet12_part_api"] = {"valid": s.isValid(), "volume": round(s.Volume, 1)}
except Exception as e:  # noqa: BLE001
    out["fillet12_part_api"] = "ERR " + str(e)[:160]
try:
    b.makeFillet(10, b.Edges)
    out["fillet10_msg"] = "ok"
except Exception as e:  # noqa: BLE001
    out["fillet10_msg"] = str(e)[:160]
doc = App.newDocument("f")
body = doc.addObject("PartDesign::Body", "Body")
bx = body.newObject("PartDesign::AdditiveBox", "Box")
bx.Length = bx.Width = bx.Height = 20
doc.recompute()
fl = body.newObject("PartDesign::Fillet", "Fillet")
fl.Base = (bx, [f"Edge{i}" for i in range(1, 13)])
fl.Radius = 12
doc.recompute()
out["pd_fillet12"] = {"state": state(fl), "null": fl.Shape.isNull(),
                      "valid": None if fl.Shape.isNull() else fl.Shape.isValid(),
                      "volume": None if fl.Shape.isNull() else round(fl.Shape.Volume, 1),
                      "tip_volume": round(body.Shape.Volume, 1) if not body.Shape.isNull() else None}

mark("ch20")
# ch20：螺旋节距太小（截面圆 ⌀4，节距 3）
doc = App.newDocument("h")
body = doc.addObject("PartDesign::Body", "Body")
sk = body.newObject("Sketcher::SketchObject", "Sk")
sk.AttachmentSupport = [(body.Origin.OriginFeatures[4], "")]
sk.MapMode = "FlatFace"
sk.addGeometry(Part.Circle(V(10, 0, 0), V(0, 0, 1), 2))
doc.recompute()
hx = body.newObject("PartDesign::AdditiveHelix", "Helix")
hx.Profile = sk
hx.ReferenceAxis = (sk, ["V_Axis"])
hx.Pitch = 3
hx.Height = 15
doc.recompute()
out["helix_p3"] = {"state": state(hx), "valid": None if hx.Shape.isNull() else hx.Shape.isValid(),
                   "volume": None if hx.Shape.isNull() else round(hx.Shape.Volume, 1)}
hx.Pitch = 6
doc.recompute()
out["helix_p6"] = {"state": state(hx), "volume": None if hx.Shape.isNull() else round(hx.Shape.Volume, 1)}

mark("ch21")
# ch21：草图改尺寸，别处有冗余约束
doc = App.newDocument("s")
sk = doc.addObject("Sketcher::SketchObject", "Sk")
pts = [V(0, 0, 0), V(30, 0, 0), V(30, 20, 0), V(0, 20, 0)]
for i in range(4):
    sk.addGeometry(Part.LineSegment(pts[i], pts[(i + 1) % 4]))
for i in range(4):
    sk.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i + 1) % 4, 1))
for c in (("Horizontal", 0), ("Horizontal", 2), ("Vertical", 1), ("Vertical", 3)):
    sk.addConstraint(Sketcher.Constraint(*c))
dx = sk.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, 0, 2, 30))
sk.addConstraint(Sketcher.Constraint("DistanceY", 1, 1, 1, 2, 20))
sk.addConstraint(Sketcher.Constraint("DistanceY", 3, 2, 3, 1, 20))     # 冗余
doc.recompute()
out["sketch_redundant"] = list(sk.RedundantConstraints)
try:
    sk.setDatum(dx, App.Units.Quantity("40 mm"))
    out["setdatum40"] = "ok"
except Exception as e:  # noqa: BLE001
    out["setdatum40"] = "ERR " + str(e)[:160]
out["dx_after"] = sk.Constraints[dx].Value

mark("ch22")
# ch22：前面失败，后面的特征是不是还标“要重算”
doc = App.newDocument("r")
bx = doc.addObject("Part::Box", "Box")
bx.Length = bx.Width = bx.Height = 20
fl = doc.addObject("Part::Fillet", "Fillet")
fl.Base = bx
fl.Edges = [(i + 1, 2.0, 2.0) for i in range(12)]
hole = doc.addObject("Part::Cylinder", "Hole")
hole.Radius = 3
hole.Height = 30
cut = doc.addObject("Part::Cut", "Cut")
cut.Base = fl
cut.Tool = hole
doc.recompute()
v0 = cut.Shape.Volume
fl.Edges = [(i + 1, 10.0, 10.0) for i in range(12)]
doc.recompute()
out["recompute_after_fail"] = {"fillet": state(fl), "cut": state(cut), "cut_volume_unchanged": abs(cut.Shape.Volume - v0) < 1e-6}

mark("ch28")
# ch28：B 样条表示的圆柱、球的体积和惯量
cyl = Part.makeCylinder(3, 10).toNurbs()
out["nurbs_cyl_volume_relerr"] = abs(cyl.Volume - math.pi * 90) / (math.pi * 90)
sp = Part.makeSphere(10).toNurbs().Solids[0]
m = 4 / 3 * math.pi * 1000
out["nurbs_sphere_izz_relerr"] = abs(sp.MatrixOfInertia.A33 - 0.4 * m * 100) / (0.4 * m * 100)

mark("ch33")
# ch33：带颜色导出装配里的零件
doc = App.newDocument("e")
asm = doc.addObject("App::Part", "Assembly")
parts = []
for i in range(2):
    f = doc.addObject("Part::Feature", f"Box{i}")
    f.Shape = Part.makeBox(10, 10, 10, V(20 * i, 0, 0))
    asm.addObject(f)
    parts.append(f)
doc.recompute()
path = os.path.join(tempfile.mkdtemp(), "colors.step")
Import.export([asm] + [(p, [(1.0, 0.0, 0.0, 1.0)] * 6) for p in parts], path)
d2 = App.newDocument("back")
Import.insert(path, d2.Name)
out["export_colors_parts_back"] = len([o for o in d2.Objects if o.TypeId == "Part::Feature"])

print("PROBE20 " + json.dumps(out, ensure_ascii=False, default=str))
