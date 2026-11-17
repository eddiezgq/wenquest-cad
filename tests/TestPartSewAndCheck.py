# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shape.sewShape(tolerance) must use the tolerance; Shape.check() must say what is wrong with an invalid shape."""

import unittest

import Part


def box_faces_with_gaps(gap):
    """The six faces of a 10 mm box, each moved outwards along its normal by gap (a gap of about gap at every edge)."""
    box = Part.makeBox(10, 10, 10)
    return [f.translated(f.normalAt(0, 0) * gap) for f in box.Faces]


def box_with_one_face_reversed():
    # Shell.add() keeps the faces as given (it sews an invalid shell but then stores the unsewn one);
    # building it with Part.Shell(list) or replaceShape() gives a valid solid instead
    box = Part.makeBox(10, 10, 10)
    shell = Part.Shell()
    for i, f in enumerate(box.Faces):
        shell.add(f.reversed() if i == 0 else f)
    return Part.Solid(shell)


class TestPartSewAndCheck(unittest.TestCase):
    def test_sew_shape_uses_the_given_tolerance(self):
        # the tolerance was parsed and then ignored (sewShape() was called with its default 1e-6)
        c = Part.Compound(box_faces_with_gaps(0.01))
        c.sewShape(0.1)
        self.assertEqual(len(c.Shells), 1)
        self.assertTrue(c.Shells[0].isClosed())

    def test_sew_shape_default_tolerance_does_not_close_large_gaps(self):
        c = Part.Compound(box_faces_with_gaps(0.01))
        c.sewShape()
        self.assertFalse(any(s.isClosed() for s in c.Shells))

    def test_check_names_the_bad_orientation(self):
        # the status is recorded for the shell in the context of the solid; check() printed only
        # the statuses each sub-shape has on its own and raised "No error"
        s = box_with_one_face_reversed()
        self.assertFalse(s.isValid())
        with self.assertRaises(ValueError) as cm:
            s.check()
        msg = str(cm.exception)
        self.assertNotIn("No error", msg)
        self.assertIn("orientation", msg.lower())


if __name__ == "__main__":
    unittest.main()
