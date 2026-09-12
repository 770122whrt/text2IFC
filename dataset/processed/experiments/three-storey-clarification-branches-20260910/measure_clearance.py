"""Read-only axis-aligned flight sampling, not a building-code compliance gate."""
import hashlib
import json
from pathlib import Path
import sys

import ifcopenshell
import ifcopenshell.geom
import numpy as np


def vertical_hits(triangles, x, y):
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    u, v = b - a, c - a
    denominator = u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]
    usable = np.abs(denominator) > 1e-12
    a, u, v, denominator = a[usable], u[usable], v[usable], denominator[usable]
    dx, dy = x - a[:, 0], y - a[:, 1]
    s = (dx * v[:, 1] - dy * v[:, 0]) / denominator
    t = (u[:, 0] * dy - u[:, 1] * dx) / denominator
    inside = (s >= -1e-9) & (t >= -1e-9) & (s + t <= 1 + 1e-9)
    return sorted(set(np.round((a[:, 2] + s * u[:, 2] + t * v[:, 2])[inside], 9)))


def main():
    source, output = map(Path, sys.argv[1:3])
    model = ifcopenshell.open(str(source))
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    items = [e for kind in ('IfcStairFlight', 'IfcSlab', 'IfcRoof', 'IfcBeam') for e in model.by_type(kind) if e.Representation]
    meshes = {}
    for item in items:
        shape = ifcopenshell.geom.create_shape(settings, item)
        verts = np.array(shape.geometry.verts).reshape(-1, 3)
        faces = np.array(shape.geometry.faces).reshape(-1, 3)
        meshes[item.id()] = (verts, verts[faces])
    samples = []
    for flight in model.by_type('IfcStairFlight'):
        verts, triangles = meshes[flight.id()]
        lo, hi = verts.min(axis=0), verts.max(axis=0)
        # This fixture contract has north/south straight flights only.
        count = int(flight.NumberOfTreads)
        for i in range(count):
            y = lo[1] + (hi[1] - lo[1]) * (i + 0.5) / count
            for fraction in (0.25, 0.5, 0.75):
                x = lo[0] + (hi[0] - lo[0]) * fraction
                walking = vertical_hits(triangles, x, y)
                if not walking:
                    raise ValueError('No walk surface at a frozen sample; do not claim clearance.')
                z = max(walking)
                overhead = []
                for other in items:
                    if other.id() == flight.id():
                        continue
                    hits = vertical_hits(meshes[other.id()][1], x, y)
                    for h in hits:
                        if h >= z - 1e-7:
                            overhead.append((max(0.0, h - z), other.GlobalId))
                    # Closed-solid ray intervals detect a walking point inside another solid.
                    if len(hits) % 2 == 0:
                        for bottom, top in zip(hits[::2], hits[1::2]):
                            if bottom - 1e-7 <= z <= top + 1e-7:
                                overhead.append((0.0, other.GlobalId))
                nearest = min(overhead) if overhead else None
                samples.append({'flight': flight.GlobalId, 'point_m': [float(x), float(y), float(z)],
                                'gap_m': float(nearest[0]) if nearest else None,
                                'overhead': nearest[1] if nearest else None})
    finite = [s['gap_m'] for s in samples if s['gap_m'] is not None]
    report = {
        'evidence_class': 'offline native IFC mesh sampling',
        'ifc_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'scope': 'axis-aligned north/south flights; sampled vertical rays to flights/slabs/roof/beams only; no code threshold, lateral circulation or railing review',
        'samples': samples, 'sample_count': len(samples),
        'minimum_sampled_gap_m': min(finite) if finite else None,
        'zero_gap_count': sum(s['gap_m'] is not None and s['gap_m'] <= 1e-7 for s in samples),
        'unbounded_sample_count': sum(s['gap_m'] is None for s in samples),
    }
    with output.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps({k: report[k] for k in ('sample_count', 'minimum_sampled_gap_m', 'zero_gap_count')}))


if __name__ == '__main__':
    main()
