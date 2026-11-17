# SPDX-License-Identifier: LGPL-2.1-or-later
"""Memory accounting of shapes and of the undo stack
("FreeCAD kernel: decode, verify, correct", chapter 35)."""
import unittest

import FreeCAD as App
import Part


def meshed_sphere(r):
    s = Part.makeSphere(r)
    s.tessellate(0.01)
    return s


class TestUndoMemSize(unittest.TestCase):
    def setUp(self):
        self.doc = App.newDocument("TestUndoMemSize")
        self.doc.UndoMode = 1

    def tearDown(self):
        App.closeDocument(self.doc.Name)

    def test_shape_mem_size_counts_triangulation(self):
        plain = Part.makeSphere(10)
        before = plain.MemSize
        plain.tessellate(0.01)
        self.assertGreater(plain.MemSize, before)

    def test_undo_redo_mem_size_grows_with_transactions(self):
        f = self.doc.addObject("Part::Feature", "F")
        sizes = []
        for k in range(3):
            self.doc.openTransaction(f"t{k}")
            f.Shape = meshed_sphere(10 + k)
            self.doc.commitTransaction()
            sizes.append(self.doc.UndoRedoMemSize)
        self.assertGreater(sizes[0], 0)
        self.assertLess(sizes[0], sizes[-1])
        self.doc.clearUndos()
        self.assertEqual(self.doc.UndoRedoMemSize, 0)

    def test_document_mem_size_includes_undo(self):
        f = self.doc.addObject("Part::Feature", "F")
        self.doc.openTransaction("t")
        f.Shape = meshed_sphere(10)
        self.doc.commitTransaction()
        self.doc.openTransaction("t2")
        f.Shape = meshed_sphere(11)
        self.doc.commitTransaction()
        with_undo = self.doc.MemSize
        self.doc.clearUndos()
        self.assertGreater(with_undo, self.doc.MemSize)
