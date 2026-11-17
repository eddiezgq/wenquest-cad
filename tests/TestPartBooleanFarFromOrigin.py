# SPDX-License-Identifier: LGPL-2.1-or-later
"""Boolean cuts of small round features far from the origin.

Point classification casts a ray and intersects it with the faces of the other solid. For cylinders,
spheres and cones the line is intersected with the implicit equation in global coordinates, whose
constant term carries the square of the distance from the origin; once that distance is about 1e8 times
the radius, the intersection points are lost and the face pieces inside the tool are kept. The result is
reported as done, is invalid or keeps the removed material, and the auto fuzzy value does not help.

Fixed in OCCT by solving the line - quadric intersection in a frame centred on the quadric
(patch "IntCurveSurface: intersect a line with a quadric in a local frame"). These tests fail with the
OCCT versions bundled up to FreeCAD 1.1.3 (OCCT 7.9.3).
"""

import math
import unittest

import FreeCAD as App
import Part

V = App.Vector


def check(case, shape, offset, volume):
    case.assertFalse(shape.isNull())
    case.assertTrue(shape.isValid())
    case.assertEqual(len(shape.Faces), 7)
    moved = shape.copy()
    moved.translate(V(-offset, -offset, -offset))  # measure near the origin (large coordinates cancel)
    case.assertAlmostEqual(moved.Volume / volume, 1.0, places=6)


class TestPartBooleanFarFromOrigin(unittest.TestCase):
    def test_through_hole_30_km_from_origin(self):
        # a 0.6 mm hole through a 1 mm block, 30 km from the origin: T / r = 1e8
        T, s = 3.0e7, 0.1
        box = Part.makeBox(10 * s, 10 * s, 10 * s, V(T, T, T))
        cyl = Part.makeCylinder(3 * s, 12 * s, V(T + 5 * s, T + 5 * s, T - s), V(0, 0, 1))
        check(self, box.cut(cyl), T, (1000 - 90 * math.pi) * s**3)

    def test_spherical_dent_50_km_from_origin(self):
        T, s = 5.0e7, 0.1
        box = Part.makeBox(10 * s, 10 * s, 10 * s, V(T, T, T))
        sph = Part.makeSphere(3 * s, V(T + 5 * s, T + 5 * s, T + 10 * s))
        check(self, box.cut(sph), T, (1000 - 18 * math.pi) * s**3)

    def test_same_cut_near_the_origin(self):
        # the same features 1 m from the origin work before and after the fix
        T, s = 1.0e3, 0.1
        box = Part.makeBox(10 * s, 10 * s, 10 * s, V(T, T, T))
        cyl = Part.makeCylinder(3 * s, 12 * s, V(T + 5 * s, T + 5 * s, T - s), V(0, 0, 1))
        check(self, box.cut(cyl), T, (1000 - 90 * math.pi) * s**3)


if __name__ == "__main__":
    unittest.main()
