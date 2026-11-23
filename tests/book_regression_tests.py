# SPDX-License-Identifier: LGPL-2.1-or-later
"""Regression tests for kernel behaviour found while writing
"FreeCAD kernel: decode, verify, correct" (chapters 25-29).

Each test states the correct behaviour. On FreeCAD 1.1.3 without the corresponding
patch the test fails; the failure documents the problem.
"""

import math
import unittest

import FreeCAD as App
import Part

V = App.Vector

# 12 spheres (centre, radius), overlapping in places
BALLS = [((5.232243, 5.969823, 16.284515), 1.683832), ((12.002011, 14.571211, 3.758021), 1.610293),
         ((5.499387, 13.14866, 11.245313), 1.800125), ((8.652616, 13.385946, 8.455693), 2.766369),
         ((19.348719, 13.661296, 7.832497), 1.874505), ((6.919213, 10.221319, 17.824188), 3.051128),
         ((6.362932, 18.484338, 9.418198), 2.887518), ((2.144146, 2.090871, 4.038149), 3.268899),
         ((13.596229, 16.984726, 12.888725), 2.313085), ((10.331564, 11.86887, 17.24236), 2.376372),
         ((17.844802, 12.274339, 16.587123), 2.496112), ((13.850363, 6.780507, 10.45657), 1.932447)]


class BookRegressionTests(unittest.TestCase):
    def test_curvature_at_sphere_pole(self):
        # chapter 25: the pole of a sphere is a removable singularity; both principal
        # curvatures have the limit 1/R there
        face = Part.makeSphere(10).Faces[0]
        k1, k2 = face.curvatureAt(0.0, math.pi / 2)
        self.assertAlmostEqual(abs(k1), 0.1, places=6)
        self.assertAlmostEqual(abs(k2), 0.1, places=6)

    def test_arc_parameter_returns_nearest_point(self):
        # chapter 27: beyond the end of an arc the nearest point is the end point,
        # not the orthogonal projection on the far side
        arc = Part.ArcOfCircle(Part.Circle(V(0, 0, 0), V(0, 0, 1), 5), 0, math.pi / 2)
        p = V(-1, -10, 0)
        d = (arc.value(arc.parameter(p)) - p).Length
        self.assertAlmostEqual(d, math.hypot(6, 10), places=9)

    def test_circle_parameter_at_centre(self):
        # chapter 27: every point of the circle is nearest to its centre; any parameter is an answer
        circle = Part.Circle(V(0, 0, 0), V(0, 0, 1), 5)
        u = circle.parameter(V(0, 0, 0))
        self.assertAlmostEqual((circle.value(u) - V(0, 0, 0)).Length, 5.0, places=12)

    def test_volume_of_nurbs_cylinder(self):
        # chapter 28: the same geometry as NURBS must have the same volume
        cyl = Part.makeCylinder(3, 10).toNurbs()
        exact = math.pi * 9 * 10
        self.assertLess(abs(cyl.Volume - exact) / exact, 1e-9)

    def test_inertia_of_nurbs_sphere(self):
        # chapter 28: inertia of a NURBS sphere about its centre, 2/5 m R^2
        s = Part.makeSphere(10).toNurbs().Solids[0]
        m = 4 / 3 * math.pi * 1000
        izz = s.MatrixOfInertia.A33
        self.assertLess(abs(izz - 0.4 * m * 100) / (0.4 * m * 100), 1e-6)

    def test_volume_of_invalid_fillet_returns(self):
        # chapter 28 (0002): the accurate integration must not run on an invalid solid; a box
        # filleted with a radius above half its edge used to hang Volume for more than 15 minutes
        import time
        box = Part.makeBox(20, 20, 20)
        bad = box.makeFillet(12, box.Edges)
        self.assertFalse(bad.isValid())
        t = time.time()
        bad.Volume
        self.assertLess(time.time() - t, 30.0)

    def test_helix_pitch_below_profile_is_refused(self):
        # chapter 20 (0002): a helix whose pitch is smaller than its profile intersects itself;
        # built by script (profile and axis set, then recompute) it used to be stored silently
        doc = App.newDocument("BookHelixPitch")
        try:
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
            self.assertIn("Invalid", hx.State)
            hx.Pitch = 6
            doc.recompute()
            self.assertNotIn("Invalid", hx.State)
        finally:
            App.closeDocument(doc.Name)

    def test_multifuse_does_not_depend_on_order(self):
        # chapter 29: a fusion is commutative; reordering Shapes must not change the result
        doc = App.newDocument("BookMultiFuseOrder")
        try:
            objs = []
            for k, (c, r) in enumerate(BALLS):
                o = doc.addObject("Part::Sphere", f"S{k}")
                o.Radius = r
                o.Placement.Base = V(*c)
                objs.append(o)
            results = []
            for name, order in (("F1", objs), ("F2", list(reversed(objs)))):
                f = doc.addObject("Part::MultiFuse", name)
                f.Shapes = order
                doc.recompute()
                s = f.Shape
                results.append((len(s.Vertexes), float(s.Volume).hex(),
                                sorted((round(v.Point.x, 9), round(v.Point.y, 9), round(v.Point.z, 9)) for v in s.Vertexes)))
            self.assertEqual(results[0], results[1])
        finally:
            App.closeDocument(doc.Name)
