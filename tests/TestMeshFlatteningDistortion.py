# SPDX-License-Identifier: LGPL-2.1-or-later
"""flatmesh.FaceUnwrapper.getDistortion() reports how far a flattening is from an isometry.

The flattener scales its result to the 3D area, so equal areas say nothing about length errors; before
this method a script had no way to learn that a flattened 60 degree spherical cap has edges stretched by
more than 10 %.
"""

import math
import unittest

import flatmesh
import numpy as np


def grid(fn, nu, nv):
    P = np.array([fn(i / nu, j / nv) for i in range(nu + 1) for j in range(nv + 1)], float)
    T = []
    for i in range(nu):
        for j in range(nv):
            a, b = i * (nv + 1) + j, (i + 1) * (nv + 1) + j
            T += [[a, b, b + 1], [a, b + 1, a + 1]]
    return P, np.array(T, dtype=np.int64)


def cylinder():
    return grid(lambda x, y: (10 * math.cos(2 * x), 10 * math.sin(2 * x), 20 * y), 24, 8)


def cap(deg):
    a = math.radians(deg)
    return grid(lambda x, y: (10 * math.sin(a * (0.05 + 0.95 * x)) * math.cos(math.pi * y),
                              10 * math.sin(a * (0.05 + 0.95 * x)) * math.sin(math.pi * y),
                              10 * math.cos(a * (0.05 + 0.95 * x))), 12, 24)


def direct(P, T, Q):
    s = []
    for t in T:
        for i, j in ((0, 1), (1, 2), (2, 0)):
            s.append(np.linalg.norm(Q[t[i]] - Q[t[j]]) / np.linalg.norm(P[t[i]] - P[t[j]]) - 1)
    s = np.array(s)
    return np.abs(s).max(), math.sqrt((s ** 2).mean())


class TestMeshFlatteningDistortion(unittest.TestCase):
    def flatten(self, P, T):
        fu = flatmesh.FaceUnwrapper(P, T)
        fu.findFlatNodes(5, 0.95)
        return fu

    def test_flat_nodes_of_a_cylinder_are_isometric(self):
        P, T = cylinder()
        fu = self.flatten(P, T)
        mx, _ = direct(P, T, np.array(fu.ze_nodes))
        self.assertLess(mx, 1e-9)

    def test_cylinder_reports_no_distortion(self):
        P, T = cylinder()
        d = self.flatten(P, T).getDistortion()
        self.assertLess(d["max_edge_strain"], 1e-9)
        self.assertEqual(d["flipped_triangles"], 0)

    def test_sphere_cap_distortion_is_reported_although_areas_agree(self):
        P, T = cap(60)
        d = self.flatten(P, T).getDistortion()
        self.assertGreater(d["max_edge_strain"], 0.05)
        self.assertLess(abs(d["flat_area"] / d["area"] - 1), 0.01)

    def test_values_match_direct_computation(self):
        P, T = cap(30)
        fu = self.flatten(P, T)
        d = fu.getDistortion()
        mx, rms = direct(P, T, np.array(fu.ze_nodes))
        self.assertAlmostEqual(d["max_edge_strain"], mx, places=12)
        self.assertAlmostEqual(d["rms_edge_strain"], rms, places=12)

    def test_requires_flat_nodes(self):
        P, T = cylinder()
        fu = flatmesh.FaceUnwrapper(P, T)
        with self.assertRaises(RuntimeError):
            fu.getDistortion()


if __name__ == "__main__":
    unittest.main()
