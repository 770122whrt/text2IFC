"""Static views from the exact mesh payload used by the offline viewer."""
import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('html', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--selection', default='all')
parser.add_argument('--yaw', type=float, default=-.72)
parser.add_argument('--pitch', type=float, default=.52)
args = parser.parse_args()
page = args.html.read_text(encoding='utf-8')
data = json.loads(page)
products = [p for p in data['products'] if args.selection == 'all' or p['id'] == args.selection
            or args.selection == 'fillings' and p['kind'] in {'IfcDoor', 'IfcWindow'}]
def project(x, y, z):
    u = x * math.cos(args.yaw) - y * math.sin(args.yaw)
    d = x * math.sin(args.yaw) + y * math.cos(args.yaw)
    return u, d * math.sin(args.pitch) + z * math.cos(args.pitch), d * math.cos(args.pitch) - z * math.sin(args.pitch)
triangles, points = [], []
for p in products:
    vertices = [project(*p['verts'][i:i + 3]) for i in range(0, len(p['verts']), 3)]
    points.extend(vertices)
    for i in range(0, len(p['faces']), 3):
        vs = [vertices[n] for n in p['faces'][i:i + 3]]
        index = p['material_ids'][i // 3]
        material = p['materials'][index] if 0 <= index < len(p['materials']) else [.72, .74, .73, 1]
        triangles.append((sum(v[2] for v in vs) / 3, vs, material))
low = [min(v[k] for v in points) for k in range(2)]
high = [max(v[k] for v in points) for k in range(2)]
width, height = 1600, 1000
scale = min((width - 140) / (high[0] - low[0] or 1), (height - 140) / (high[1] - low[1] or 1))
pixels = np.full((height, width, 3), [243., 244., 240.])
depth = np.full((height, width), np.inf)
ordered = [t for t in triangles if t[2][3] >= .999] + sorted(
    [t for t in triangles if t[2][3] < .999], key=lambda t: t[0], reverse=True)
for _, vs, material in ordered:
    coords = np.array([((v[0] - (high[0] + low[0]) / 2) * scale + width / 2,
                       height / 2 - (v[1] - (high[1] + low[1]) / 2) * scale) for v in vs])
    xmin, ymin = np.maximum(np.floor(coords.min(axis=0)).astype(int), [0, 0])
    xmax, ymax = np.minimum(np.ceil(coords.max(axis=0)).astype(int), [width - 1, height - 1])
    if xmax < xmin or ymax < ymin:
        continue
    (x0, y0), (x1, y1), (x2, y2) = coords
    denominator = (y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
    if abs(denominator) < 1e-10:
        continue
    yy, xx = np.mgrid[ymin:ymax+1, xmin:xmax+1]
    a = ((y1-y2)*(xx+.5-x2)+(x2-x1)*(yy+.5-y2))/denominator
    b = ((y2-y0)*(xx+.5-x2)+(x0-x2)*(yy+.5-y2))/denominator
    c = 1-a-b
    z = a*vs[0][2]+b*vs[1][2]+c*vs[2][2]
    current = depth[ymin:ymax+1, xmin:xmax+1]
    mask = (a >= 0) & (b >= 0) & (c >= 0) & (z <= current + 1e-8)
    normal = np.cross(np.array(vs[1])-vs[0], np.array(vs[2])-vs[0])
    light = .76+.24*abs(normal @ [.3, .7, -.64] / (np.linalg.norm(normal) or 1))
    color = np.array(material[:3])*255*light
    region = pixels[ymin:ymax+1, xmin:xmax+1]
    opacity = max(0, min(1, material[3]))
    region[mask] = region[mask]*(1-opacity)+color*opacity
    if opacity >= .999:
        current[mask] = z[mask]
canvas = Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))
assert not args.output.exists()
canvas.save(args.output)
print(args.output)
