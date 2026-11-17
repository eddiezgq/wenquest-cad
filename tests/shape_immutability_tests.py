# SPDX-License-Identifier: LGPL-2.1-or-later
"""The Shape of a document object must not be changed through the Python objects
FreeCAD hands out for it ("FreeCAD kernel: decode, verify, correct", chapter 31).

obj.Shape returns an immutable TopoShape whose TShapes are shared with the object's
stored shape. Changing tolerances through it, through its sub-shapes or through a
shape derived from it (translated) used to change the stored shape silently.
"""
import unittest

import FreeCAD as App
import Part  # noqa: F401

V = App.Vector


class ShapeImmutabilityTests(unittest.TestCase):
    def setUp(self):
        self.doc = App.newDocument("ShapeImmutability")
        self.box = self.doc.addObject("Part::Box", "Box")
        self.doc.recompute()

    def tearDown(self):
        App.closeDocument(self.doc.Name)

    def stored_tolerance(self):
        return max(v.Tolerance for v in self.box.Shape.Vertexes)

    def test_fix_tolerance_on_object_shape_is_refused(self):
        with self.assertRaises(ReferenceError):
            self.box.Shape.fixTolerance(0.05)
        self.assertLess(self.stored_tolerance(), 1e-6)

    def test_sub_shape_tolerance_on_object_shape_is_refused(self):
        with self.assertRaises(ReferenceError):
            self.box.Shape.Vertexes[0].Tolerance = 0.05
        with self.assertRaises(ReferenceError):
            self.box.Shape.Edges[0].fixTolerance(0.05)
        self.assertLess(self.stored_tolerance(), 1e-6)

    def test_derived_shape_is_copied_on_write(self):
        s = self.box.Shape.translated(V(10, 0, 0))
        s.fixTolerance(0.05)
        self.assertAlmostEqual(max(v.Tolerance for v in s.Vertexes), 0.05)
        self.assertLess(self.stored_tolerance(), 1e-6)

    def test_copy_can_be_changed(self):
        s = self.box.Shape.copy()
        s.Vertexes[0].Tolerance = 0.05
        s.fixTolerance(0.05)
        self.assertAlmostEqual(max(v.Tolerance for v in s.Vertexes), 0.05)
        self.assertLess(self.stored_tolerance(), 1e-6)
