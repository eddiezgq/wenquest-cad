# SPDX-License-Identifier: LGPL-2.1-or-later
"""Curve.parameterAtDistance() must find the point at the given arc length.

Without a tolerance GCPnts_AbscissaPoint integrated the arc length with one fixed 10-point Gauss rule over
the whole range; on an ellipse with axes 10 and 1 the returned point was more than half a millimetre away
(along the curve) from where it should be, while Edge.getParameterByLength() on the same ellipse was right.
"""

import unittest

import FreeCAD as App
import Part


class TestPartParameterAtDistance(unittest.TestCase):
    def setUp(self):
        self.ellipse = Part.Ellipse(App.Vector(0, 0, 0), 10.0, 1.0)
        self.length = self.ellipse.length()

    def test_point_is_at_the_given_arc_length(self):
        for k in range(1, 20):
            s = self.length * k / 20
            u = self.ellipse.parameterAtDistance(s, 0.0)
            # Curve.length(u0, u1, tol) integrates with error control
            self.assertAlmostEqual(self.ellipse.length(0.0, u, 1e-9), s, delta=1e-6)

    def test_agrees_with_edge_get_parameter_by_length(self):
        edge = self.ellipse.toShape()
        for k in range(1, 20):
            s = self.length * k / 20
            self.assertAlmostEqual(self.ellipse.parameterAtDistance(s, 0.0), edge.getParameterByLength(s),
                                   delta=1e-7)

    def test_2d_curve(self):
        e2 = Part.Geom2d.Ellipse2d(App.Base.Vector2d(0, 0), 10.0, 1.0)
        length = e2.length()
        for k in range(1, 20):
            s = length * k / 20
            u = e2.parameterAtDistance(s, 0.0)
            self.assertAlmostEqual(e2.length(0.0, u, 1e-9), s, delta=1e-6)

    def test_circle_and_line_unchanged(self):
        c = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 5.0)
        self.assertAlmostEqual(c.parameterAtDistance(5.0, 0.0), 1.0, places=12)
        line = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(3, 4, 0))
        self.assertAlmostEqual(line.parameterAtDistance(2.5, 0.0), 2.5, places=12)


if __name__ == "__main__":
    unittest.main()
