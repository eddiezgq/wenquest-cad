# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tests for ReverseEngineering.sampleConsensus (input checks, inlier indices, distance threshold)."""

import math
import random
import unittest

import FreeCAD
import Points

try:
    import ReverseEngineering as Reen

    HAVE_SAC = hasattr(Reen, "sampleConsensus")
except ImportError:
    HAVE_SAC = False


def cylinder_points(n, radius=0.5, seed=0):
    rng = random.Random(seed)
    pts, nor = [], []
    for _ in range(n):
        t, z = rng.uniform(0, 2 * math.pi), rng.uniform(-1, 1)
        pts.append(FreeCAD.Vector(radius * math.cos(t), radius * math.sin(t), z))
        nor.append(FreeCAD.Vector(math.cos(t), math.sin(t), 0))
    return pts, nor


def plane_points(n, z=1.0, sigma=0.0, seed=1):
    rng = random.Random(seed)
    return [FreeCAD.Vector(rng.uniform(-1, 1), rng.uniform(-1, 1), z + rng.gauss(0, sigma) if sigma else z)
            for _ in range(n)]


def kernel(vectors):
    p = Points.Points()
    p.addPoints(vectors)
    return p


@unittest.skipUnless(HAVE_SAC, "ReverseEngineering built without PCL sample consensus")
class TestReenSampleConsensus(unittest.TestCase):
    def test_cylinder_without_normals_raises(self):
        # PCL's cylinder model reads one normal per point; without normals it used to read past the end and crash
        pts, _ = cylinder_points(200)
        with self.assertRaises(ValueError):
            Reen.sampleConsensus(SacModel="Cylinder", Points=kernel(pts))

    def test_normal_count_must_match_point_count(self):
        pts, nor = cylinder_points(200)
        with self.assertRaises(ValueError):
            Reen.sampleConsensus(SacModel="Cylinder", Points=kernel(pts), Normals=nor[:10])

    def test_inlier_indices_refer_to_the_input_points(self):
        # invalid (NaN) points are skipped internally; the returned indices must still index the input
        nan = FreeCAD.Vector(float("nan"), float("nan"), float("nan"))
        plane = plane_points(300)
        cyl, _ = cylinder_points(300)
        data = [nan] * 20 + plane + cyl
        res = Reen.sampleConsensus(SacModel="Plane", Points=kernel(data))
        model = res["Model"]
        self.assertGreaterEqual(len(model), 300)
        for i in model:
            self.assertTrue(abs(data[i].z - 1.0) < 0.01, f"index {i} is not on the plane z = 1")

    def test_distance_threshold(self):
        data = plane_points(500, sigma=0.02)
        default = Reen.sampleConsensus(SacModel="Plane", Points=kernel(data))
        wide = Reen.sampleConsensus(SacModel="Plane", Points=kernel(data), DistanceThreshold=0.1)
        self.assertLess(len(default["Model"]), 400)  # the default threshold 0.01 is half the noise
        self.assertGreaterEqual(len(wide["Model"]), 495)  # 0.1 is five standard deviations
        with self.assertRaises(ValueError):
            Reen.sampleConsensus(SacModel="Plane", Points=kernel(data), DistanceThreshold=0.0)


if __name__ == "__main__":
    unittest.main()
