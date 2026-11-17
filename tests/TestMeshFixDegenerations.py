# SPDX-License-Identifier: LGPL-2.1-or-later
"""Mesh.fixDegenerations on a mesh with many degenerate facets
("FreeCAD kernel: decode, verify, correct", chapter 38).

The mesh is a marching-tetrahedra surface of a cube with a hole, sampled on a grid whose planes contain the
cube's faces (so many samples are exactly zero) and with those zeros pushed off by 1e-6 of the grid spacing:
it has hundreds of needle facets. On FreeCAD 1.1.3 fixDegenerations() crashes on the 11^3 version of this mesh
(out-of-bounds write in MeshTopoAlgorithm::RemoveDegeneratedFacet when a neighbour does not refer back) and
never returns on the 21^3 version (MeshFixDegeneratedFacets::Fixup swaps the same edge back and forth)."""
import os
import struct
import tempfile
import unittest

import Mesh
import numpy as np

_CORNERS = np.array([[(c >> 0) & 1, (c >> 1) & 1, (c >> 2) & 1] for c in range(8)])
_TETS = [(0, 1, 3, 7), (0, 3, 2, 7), (0, 2, 6, 7), (0, 6, 4, 7), (0, 4, 5, 7), (0, 5, 1, 7)]


def _field(n, lo):
    """Signed distance of the cube [-1, 1]^3 with a hole of radius 0.5 along z (exact zero set), on the grid."""
    t = np.linspace(lo, -lo, n)
    X, Y, Z = np.meshgrid(t, t, t, indexing="ij")
    p = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    q = np.abs(p) - 1.0
    d_box = np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0)
    return np.maximum(d_box, 0.5 - np.hypot(p[:, 0], p[:, 1])).reshape(n, n, n), t[1] - t[0]


def needle_mesh_triangles(n=11, lo=-1.25):
    F, h = _field(n, lo)
    eps = 1e-6 * h
    small = np.abs(F) < eps
    F[small] = np.where(F[small] < 0, -eps, eps)
    nj, nk = F.shape[1], F.shape[2]
    verts, vid, tris = [], {}, []

    def gid(c):
        return (c[0] * nj + c[1]) * nk + c[2]

    def vert(a, b):
        key = (min(gid(a), gid(b)), max(gid(a), gid(b)))
        if key not in vid:
            t = F[a] / (F[a] - F[b])
            vid[key] = len(verts)
            verts.append(lo + h * (np.array(a) + t * (np.array(b) - np.array(a))))
        return vid[key]

    def orient(tri, ins, outs):
        pa, pb, pc = (verts[t] for t in tri)
        nrm = np.cross(pb - pa, pc - pa)
        q = [np.array(x, dtype=float) for x in ins + outs]
        M = np.array([q[1] - q[0], q[2] - q[0], q[3] - q[0]])
        rhs = np.array([F[tuple(int(v) for v in x)] - F[tuple(int(v) for v in q[0])] for x in q[1:]])
        g = np.linalg.solve(M, rhs)
        return tri if np.dot(nrm, g) >= 0 else [tri[0], tri[2], tri[1]]

    for i in range(n - 1):
        for j in range(n - 1):
            for k in range(n - 1):
                cube = F[i:i + 2, j:j + 2, k:k + 2]
                if (cube < 0).all() or (cube >= 0).all():
                    continue
                cs = [(i + c[0], j + c[1], k + c[2]) for c in _CORNERS]
                for tet in _TETS:
                    p = [cs[t] for t in tet]
                    inside = [F[c] < 0 for c in p]
                    ins = [c for c, s in zip(p, inside) if s]
                    outs = [c for c, s in zip(p, inside) if not s]
                    if len(ins) in (0, 4):
                        continue
                    if len(ins) == 1:
                        tris.append(orient([vert(ins[0], o) for o in outs], ins, outs))
                    elif len(ins) == 3:
                        tris.append(orient([vert(a, outs[0]) for a in ins], ins, outs))
                    else:
                        quad = [vert(ins[0], outs[0]), vert(ins[0], outs[1]), vert(ins[1], outs[1]),
                                vert(ins[1], outs[0])]
                        tris.append(orient([quad[0], quad[1], quad[2]], ins, outs))
                        tris.append(orient([quad[0], quad[2], quad[3]], ins, outs))
    return [tuple(tuple(float(v) for v in verts[t]) for t in tri) for tri in tris]


def load_needle_mesh(n):
    """Write the triangles as a binary STL and read it back (the path a user's file takes)."""
    tris = needle_mesh_triangles(n)
    fd, path = tempfile.mkstemp(suffix=".stl")
    with os.fdopen(fd, "wb") as f:
        f.write(b" " * 80)
        f.write(struct.pack("<I", len(tris)))
        for t in tris:
            f.write(struct.pack("<12fH", 0.0, 0.0, 0.0, *t[0], *t[1], *t[2], 0))
    try:
        return Mesh.Mesh(path)
    finally:
        os.remove(path)


class TestMeshFixDegenerations(unittest.TestCase):
    def test_fix_degenerations_does_not_crash(self):
        mesh = load_needle_mesh(11)
        mesh.fixDegenerations(1e-9)  # crashes on FreeCAD 1.1.3
        self.assertGreater(mesh.CountFacets, 0)
        self.assertFalse(mesh.hasInvalidNeighbourhood())

    def test_fix_degenerations_terminates(self):
        mesh = load_needle_mesh(21)
        mesh.fixDegenerations(1e-9)  # never returns on FreeCAD 1.1.3
        self.assertGreater(mesh.CountFacets, 0)
        self.assertFalse(mesh.hasInvalidNeighbourhood())
