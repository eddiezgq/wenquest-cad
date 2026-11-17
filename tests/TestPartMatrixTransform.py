# SPDX-License-Identifier: LGPL-2.1-or-later
"""A matrix that gp_Trsf cannot hold must not be silently changed into one it can.

gp_Trsf::SetValues() divides a matrix by the cube root of its determinant and orthogonalizes it, so a
non-uniform scaling became a uniform one and a shear was dropped; Shape.Matrix = m with a scaling gave a
shape that BRepCheck rejects, with a mirror a solid with negative volume.
"""

import unittest

import FreeCAD as App
import Part


def matrix(rows):
    m = App.Matrix()
    m.A11, m.A12, m.A13 = rows[0]
    m.A21, m.A22, m.A23 = rows[1]
    m.A31, m.A32, m.A33 = rows[2]
    return m


SCALE_2_1_1 = matrix([[2, 0, 0], [0, 1, 0], [0, 0, 1]])
SHEAR = matrix([[1, 0.5, 0], [0, 1, 0], [0, 0, 1]])
UNIFORM_2 = matrix([[2, 0, 0], [0, 2, 0], [0, 0, 2]])
MIRROR_X = matrix([[-1, 0, 0], [0, 1, 0], [0, 0, 1]])


class TestPartMatrixTransform(unittest.TestCase):
    def test_transform_shape_rejects_non_uniform_scaling(self):
        # was: a cube of edge 2**(1/3) instead of a 2 x 1 x 1 box, no error
        box = Part.makeBox(1, 1, 1)
        with self.assertRaises((ValueError, Part.OCCError)):
            box.transformShape(SCALE_2_1_1)

    def test_transform_shape_rejects_shear(self):
        # was: the shear was dropped, the cube came back unchanged
        box = Part.makeBox(1, 1, 1)
        with self.assertRaises((ValueError, Part.OCCError)):
            box.transformShape(SHEAR)

    def test_matrix_property_rejects_scaling_and_mirror(self):
        # was: scaling -> BRepCheck invalid; mirror -> solid with negative volume
        for m in (UNIFORM_2, MIRROR_X):
            box = Part.makeBox(1, 1, 1)
            with self.assertRaises((ValueError, Part.OCCError)):
                box.Matrix = m

    def test_valid_paths_are_unchanged(self):
        box = Part.makeBox(1, 1, 1)
        s = box.copy()
        s.transformShape(SCALE_2_1_1, False, True)
        self.assertAlmostEqual(s.BoundBox.XLength, 2.0)
        self.assertAlmostEqual(s.BoundBox.YLength, 1.0)
        for m, vol in ((UNIFORM_2, 8.0), (MIRROR_X, 1.0)):
            s = box.copy()
            s.transformShape(m)
            self.assertTrue(s.isValid())
            self.assertAlmostEqual(s.Volume, vol)
        p = App.Placement(App.Vector(1, 2, 3), App.Rotation(App.Vector(1, 1, 0), 33))
        s = box.copy()
        s.Placement = p
        self.assertTrue(s.Placement.isSame(p, 1e-12))
        s = box.copy()
        s.Matrix = p.toMatrix()
        self.assertTrue(s.isValid())
        g = box.transformGeometry(SHEAR)
        self.assertAlmostEqual(g.BoundBox.XLength, 1.5)


if __name__ == "__main__":
    unittest.main()
