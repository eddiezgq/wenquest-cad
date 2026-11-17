# SPDX-License-Identifier: LGPL-2.1-or-later
"""Face.curvatureAt() must measure curvature against the same normal as Face.normalAt().

normalAt() reverses the normal of a reversed face (the outward normal of a solid), curvatureAt() did not:
a hole and a boss of the same radius, a ball and a spherical cavity, gave identical curvatures.
"""

import unittest

import FreeCAD as App
import Part


def cylinder_faces(shape):
    return [f for f in shape.Faces if f.Surface.__class__.__name__ == "Cylinder"]


def mid(face):
    u0, u1, v0, v1 = face.ParameterRange
    return (u0 + u1) / 2, (v0 + v1) / 2


class TestPartFaceCurvatureSign(unittest.TestCase):
    def setUp(self):
        box = Part.makeBox(20, 20, 20)
        hole = Part.makeCylinder(4, 20, App.Vector(10, 10, 0))
        boss = Part.makeCylinder(4, 10, App.Vector(10, 10, 20))
        self.part = box.cut(hole).fuse(boss)

    def test_hole_and_boss_differ_in_sign(self):
        signs = {}
        for f in cylinder_faces(self.part):
            u, v = mid(f)
            kmin, kmax = f.curvatureAt(u, v)
            # the larger magnitude belongs to the circular direction, 1/4
            k = kmin if abs(kmin) > abs(kmax) else kmax
            signs[f.Orientation] = k
        self.assertAlmostEqual(signs["Forward"], -0.25)  # boss: bends away from its outward normal
        self.assertAlmostEqual(signs["Reversed"], 0.25)  # hole: bends towards it

    def test_ball_and_cavity(self):
        ball = Part.makeSphere(5)
        cavity = Part.makeBox(20, 20, 20, App.Vector(-10, -10, -10)).cut(ball)
        fb = ball.Faces[0]
        fc = next(f for f in cavity.Faces if f.Surface.__class__.__name__ == "Sphere")
        self.assertEqual(fc.Orientation, "Reversed")
        for k in fb.curvatureAt(0.3, 0.2):
            self.assertAlmostEqual(k, -0.2)
        for k in fc.curvatureAt(0.3, 0.2):
            self.assertAlmostEqual(k, 0.2)

    def test_sign_agrees_with_normal_at(self):
        # move a little along normalAt(): on a surface that bends towards the normal the distance to
        # the axis changes the other way than on one that bends away
        for f in cylinder_faces(self.part):
            u, v = mid(f)
            p, n = f.valueAt(u, v), f.normalAt(u, v)
            q = p + n * 0.01
            axis_dist = lambda x: ((x.x - 10) ** 2 + (x.y - 10) ** 2) ** 0.5
            towards_axis = axis_dist(q) < axis_dist(p)
            kmin, kmax = f.curvatureAt(u, v)
            k = kmin if abs(kmin) > abs(kmax) else kmax
            self.assertEqual(k > 0, towards_axis)

    def test_min_not_greater_than_max_and_gauss_unchanged(self):
        torus = Part.makeTorus(10, 3)
        f = torus.Faces[0]
        g = Part.makeBox(40, 40, 20, App.Vector(-20, -20, -10)).cut(torus)
        fr = next(x for x in g.Faces if x.Surface.__class__.__name__ == "Toroid")
        for u, v in ((0.3, 0.2), (1.0, 2.5)):
            a = f.curvatureAt(u, v)
            b = fr.curvatureAt(u, v)
            self.assertLessEqual(b[0], b[1])
            self.assertAlmostEqual(a[0] * a[1], b[0] * b[1])


if __name__ == "__main__":
    unittest.main()
