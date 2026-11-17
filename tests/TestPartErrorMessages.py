# SPDX-License-Identifier: LGPL-2.1-or-later
"""Error messages of Part operations should name the cause (for users and for scripts that repair themselves)."""

import unittest

import Part


class TestPartErrorMessages(unittest.TestCase):
    def setUp(self):
        self.box = Part.makeBox(60, 40, 20)

    def test_occ_error_names_the_exception_class(self):
        # typeid().name() gave a compiler-mangled prefix such as "15StdFail_NotDone"
        with self.assertRaises(Part.OCCError) as cm:
            self.box.makeFillet(30, self.box.Edges)
        self.assertTrue(str(cm.exception).startswith("StdFail_NotDone"), str(cm.exception))

    def test_fillet_failure_gives_the_radius(self):
        with self.assertRaises(Part.OCCError) as cm:
            self.box.makeFillet(25, self.box.Edges[:4])
        self.assertIn("radius 25", str(cm.exception))

    def test_chamfer_failure_gives_the_size(self):
        with self.assertRaises(Part.OCCError) as cm:
            self.box.makeChamfer(25, self.box.Edges[:4])
        self.assertIn("size 25", str(cm.exception))

    def test_fillet_without_edges_says_so(self):
        with self.assertRaises(Exception) as cm:
            self.box.makeFillet(1, [])
        self.assertIn("no edges", str(cm.exception))

    def test_chamfer_without_edges_says_so(self):
        with self.assertRaises(Exception) as cm:
            self.box.makeChamfer(1, [])
        self.assertIn("no edges", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
