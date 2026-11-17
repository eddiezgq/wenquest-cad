# SPDX-License-Identifier: LGPL-2.1-or-later
"""BSplineSurface.approximate / interpolate / buildFromPolesMultsKnots must reject a point grid whose rows
differ in length."""

import unittest

import FreeCAD as App
import Part


def row(k, y):
    return [App.Vector(i / (k - 1), y, 0.1 * (i / (k - 1)) ** 2) for i in range(k)]


class TestBSplineSurfaceGrid(unittest.TestCase):
    def test_approximate_regular_grid(self):
        s = Part.BSplineSurface()
        s.approximate(Points=[row(8, j / 5) for j in range(6)], ParamType="ChordLength", Tolerance=1e-3)
        p = s.value(0.5, 0.5)
        self.assertAlmostEqual(p.y, 0.5, delta=0.05)

    def test_approximate_rejects_short_rows(self):
        # the missing points used to be taken as (0, 0, 0): no error, a wrong surface
        pts = [row(8, 0.0)] + [row(3, j / 5) for j in range(1, 6)]
        with self.assertRaises(Part.OCCError):
            Part.BSplineSurface().approximate(Points=pts, ParamType="ChordLength", Tolerance=1e-3)

    def test_approximate_rejects_long_rows(self):
        pts = [row(4, 0.0)] + [row(40, j / 5) for j in range(1, 6)]
        with self.assertRaises(Part.OCCError):
            Part.BSplineSurface().approximate(Points=pts, ParamType="ChordLength", Tolerance=1e-3)

    def test_interpolate_rejects_short_rows(self):
        pts = [row(6, 0.0)] + [row(3, j / 5) for j in range(1, 6)]
        with self.assertRaises(Part.OCCError):
            Part.BSplineSurface().interpolate(pts)

    def test_build_from_poles_rejects_short_rows(self):
        poles = [row(4, 0.0)] + [row(3, j / 3) for j in range(1, 4)]
        with self.assertRaises(Part.OCCError):
            Part.BSplineSurface().buildFromPolesMultsKnots(poles, [4, 4], [4, 4], [0, 1], [0, 1], False, False, 3, 3)


if __name__ == "__main__":
    unittest.main()
