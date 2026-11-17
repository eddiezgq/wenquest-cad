# SPDX-License-Identifier: LGPL-2.1-or-later
"""Mesh booleans of two boxes that are almost aligned.

The facets cut by the other mesh are re-triangulated by MeshCore::DelaunayTriangulator (Wm4 Delaunay2
with 64-bit integer predicates). The points are first truncated to a 2^16 grid over their bounding box,
so intersection points that lie closer than 1/65536 of a facet's size share integer coordinates and the
new triangles fold over: the union reports self-intersections and inconsistently oriented facets. With
exact (rational) predicates the same unions are clean.
"""

import unittest

import FreeCAD as App
import Mesh


def union(rz, rx, x, y, z):
    a = Mesh.createBox(10, 10, 10)
    b = Mesh.createBox(10, 10, 10)
    m = App.Matrix()
    m.rotateZ(rz)
    m.rotateX(rx)
    m.move(App.Vector(x, y, z))
    b.transform(m)
    return a.unite(b)


class TestMeshBooleanNearCoincident(unittest.TestCase):
    def check(self, r):
        self.assertFalse(r.hasSelfIntersections())
        self.assertFalse(r.hasNonUniformOrientedFacets())
        self.assertFalse(r.hasNonManifolds())
        self.assertTrue(r.isSolid())
        self.assertAlmostEqual(r.Volume / 1875.0, 1.0, places=5)

    def test_union_rotated_by_3e_6(self):
        self.check(union(-3.031084379490322e-06, 6.349018431426328e-06,
                         5.0000140872122625, 5.000012794016027, 5.000001257693694))

    def test_union_rotated_by_6e_6(self):
        self.check(union(5.650525101955883e-06, 5.426424051259354e-06,
                         4.999996019588627, 5.000002984046341, 5.000002527598264))

    def test_union_of_offset_boxes(self):
        # no rotation: the cut facets are re-triangulated without near-coincident points
        r = union(0.0, 0.0, 5.0, 5.0, 5.0)
        self.assertFalse(r.hasSelfIntersections())
        self.assertAlmostEqual(r.Volume / 1875.0, 1.0, places=9)


if __name__ == "__main__":
    unittest.main()
