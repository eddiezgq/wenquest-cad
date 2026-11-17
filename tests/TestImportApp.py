# SPDX-License-Identifier: LGPL-2.1-or-later
"""Import module tests that run without the GUI ("FreeCAD kernel: decode, verify, correct", chapter 33)."""
import os
import tempfile
import unittest

import FreeCAD as App
import Import
import Part


class ExportColorsTests(unittest.TestCase):
    def setUp(self):
        self.doc = App.newDocument("ExportColors")
        self.asm = self.doc.addObject("App::Part", "Assembly")
        self.parts = []
        for i in range(2):
            f = self.doc.addObject("Part::Feature", f"Box{i}")
            f.Shape = Part.makeBox(10, 10, 10, App.Vector(20 * i, 0, 0))
            self.asm.addObject(f)
            self.parts.append(f)
        self.doc.recompute()
        self.path = os.path.join(tempfile.mkdtemp(), "colors.step")

    def tearDown(self):
        App.closeDocument(self.doc.Name)

    def reimported_features(self):
        doc = App.newDocument("ExportColorsBack")
        try:
            Import.insert(self.path, doc.Name)
            return [o for o in doc.Objects if o.TypeId == "Part::Feature"]
        finally:
            App.closeDocument(doc.Name)

    def test_colors_of_parts_inside_an_assembly_do_not_duplicate_them(self):
        colors = [(1.0, 0.0, 0.0, 1.0)] * 6
        Import.export([self.asm] + [(p, colors) for p in self.parts], self.path)
        self.assertEqual(len(self.reimported_features()), len(self.parts))

    def test_tuples_alone_still_export_their_objects(self):
        colors = [(0.0, 0.0, 1.0, 1.0)] * 6
        Import.export([(p, colors) for p in self.parts], self.path)
        self.assertEqual(len(self.reimported_features()), len(self.parts))
