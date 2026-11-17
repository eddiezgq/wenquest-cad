# SPDX-License-Identifier: LGPL-2.1-or-later
"""Path.Area.makeOffset must use the parameters set on the Area, as getShape does
("FreeCAD kernel: decode, verify, correct", chapter 34)."""
import unittest

import FreeCAD as App
import Part
import Path


def circles(shape):
    return sum(1 for e in shape.Edges if isinstance(e.Curve, Part.Circle))


class TestPathAreaOffset(unittest.TestCase):
    def setUp(self):
        self.face = Part.Face(Part.Wire(Part.makeCircle(10, App.Vector(0, 0, 0), App.Vector(0, 0, 1))))

    def area(self, **params):
        a = Path.Area()
        a.setParams(**params)
        a.add(self.face)
        return a

    def test_fit_arcs_off_gives_no_arcs(self):
        shape = self.area(FitArcs=False, Accuracy=0.01).makeOffset(offset=3.0)
        self.assertEqual(circles(shape), 0)

    def test_make_offset_matches_get_shape(self):
        for fit in (True, False):
            by_offset = self.area(FitArcs=fit, Accuracy=0.01).makeOffset(offset=3.0)
            by_shape = self.area(FitArcs=fit, Accuracy=0.01, Offset=3.0).getShape()
            self.assertEqual(len(by_offset.Edges), len(by_shape.Edges))
            self.assertEqual(circles(by_offset), circles(by_shape))
