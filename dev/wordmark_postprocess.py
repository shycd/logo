#!/usr/bin/env python3
"""Reshape the outlined wordmark of SHYCD.svg to match the 2012 lettering.

The only TypeWrong file available today is the "Smudged Bold" face, while the 2012 logo used a
lighter cut. Working on the outlined glyphs (already text-to-path), this script:

  1. enlarges the periods (the 2012 dots are bigger than the font's),
  2. narrows each letter along its own baseline,
  3. thins every glyph by eroding its outline,
  4. re-spaces letters and dots along the arc with a uniform gap, centered on the logo.

Defaults reproduce the approved 2026 wordmark. Requires shapely and numpy.
"""
import argparse, math, re, sys
import numpy as np
from lxml import etree
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

NUM = r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?'
TOK = re.compile(r'[MmLlHhVvCcSsQqTtAaZz]|' + NUM)
DOT_AREA = 15.0  # mm2: glyphs smaller than this are periods


def flatten(d, seg=14):
    """SVG path data -> list of closed polylines (curves sampled with `seg` segments)."""
    toks = TOK.findall(d); i = 0; rings = []; ring = []; cur = start = None; cmd = None; prev_ctrl = None

    def num():
        nonlocal i; v = float(toks[i]); i += 1; return v

    def close():
        nonlocal ring
        if len(ring) >= 3:
            rings.append(ring)
        ring = []

    while i < len(toks):
        if re.match(r'[A-Za-z]', toks[i]):
            cmd = toks[i]; i += 1
        rel = cmd.islower(); c = cmd.upper()
        if c == 'M':
            x, y = num(), num()
            if rel and cur is not None:
                x += cur[0]; y += cur[1]
            close(); cur = start = (x, y); ring = [cur]; prev_ctrl = None; cmd = 'l' if rel else 'L'
        elif c == 'L':
            x, y = num(), num()
            if rel:
                x += cur[0]; y += cur[1]
            cur = (x, y); ring.append(cur); prev_ctrl = None
        elif c == 'H':
            x = num(); cur = ((x + cur[0]) if rel else x, cur[1]); ring.append(cur); prev_ctrl = None
        elif c == 'V':
            y = num(); cur = (cur[0], (y + cur[1]) if rel else y); ring.append(cur); prev_ctrl = None
        elif c in 'QT':
            if c == 'Q':
                cx, cy = num(), num()
                if rel:
                    cx += cur[0]; cy += cur[1]
            else:
                cx, cy = (2 * cur[0] - prev_ctrl[0], 2 * cur[1] - prev_ctrl[1]) if prev_ctrl else cur
            x, y = num(), num()
            if rel:
                x += cur[0]; y += cur[1]
            p0 = cur
            for k in range(1, seg + 1):
                u = k / seg
                ring.append(((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * cx + u * u * x,
                             (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * cy + u * u * y))
            prev_ctrl = (cx, cy); cur = (x, y)
        elif c in 'CS':
            if c == 'C':
                c1x, c1y = num(), num()
                if rel:
                    c1x += cur[0]; c1y += cur[1]
            else:
                c1x, c1y = (2 * cur[0] - prev_ctrl[0], 2 * cur[1] - prev_ctrl[1]) if prev_ctrl else cur
            c2x, c2y = num(), num()
            if rel:
                c2x += cur[0]; c2y += cur[1]
            x, y = num(), num()
            if rel:
                x += cur[0]; y += cur[1]
            p0 = cur
            for k in range(1, seg + 1):
                u = k / seg; a = (1 - u) ** 3; b = 3 * (1 - u) ** 2 * u; cc = 3 * (1 - u) * u * u; dd = u ** 3
                ring.append((a * p0[0] + b * c1x + cc * c2x + dd * x, a * p0[1] + b * c1y + cc * c2y + dd * y))
            prev_ctrl = (c2x, c2y); cur = (x, y)
        elif c == 'Z':
            close(); cur = start; ring = [cur] if start else []; prev_ctrl = None
        else:
            sys.exit(f'unsupported path command {cmd}')
    close()
    return rings


def glyph_polys(rings):
    """Group rings into glyph polygons (outer contour minus its holes). Periods stay separate."""
    ps = sorted((Polygon(r).buffer(0) for r in rings), key=lambda q: -q.area)
    ps = [q for q in ps if q.area > 1e-6]
    glyphs = []  # [outer, holes]
    for q in ps:
        if q.area < DOT_AREA:
            glyphs.append([q, []]); continue
        for g in glyphs:
            if g[0].contains(q.representative_point()):
                g[1].append(q); break
        else:
            glyphs.append([q, []])
    out = []
    for outer, holes in glyphs:
        for h in holes:
            outer = outer.difference(h)
        out.append(outer)
    return out


def coords(g):
    gs = list(g.geoms) if g.geom_type == 'MultiPolygon' else [g]
    return np.array([(x, y) for gg in gs for x, y in gg.exterior.coords])


def to_path(geom, prec=3):
    polys = list(geom.geoms) if geom.geom_type == 'MultiPolygon' else [geom]
    parts = []
    for p in polys:
        for ring in [p.exterior] + list(p.interiors):
            pts = list(ring.coords)[:-1]
            parts.append('M' + ' '.join(f'{x:.{prec}f},{y:.{prec}f}' for x, y in pts) + 'Z')
    return ''.join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--id', default='shycd-wordmark', help='id of the wordmark path')
    ap.add_argument('--arc-center', default='92.549,90.896', help='center of the text arc, in SVG user units (mm)')
    ap.add_argument('--dot-scale', type=float, default=1.5, help='scale factor for the periods')
    ap.add_argument('--squeeze', type=float, default=0.86, help='horizontal scale of each letter along its baseline')
    ap.add_argument('--erode', type=float, default=0.5, help='outline inset in mm (thins the strokes)')
    ap.add_argument('--gap', type=float, default=0.5, help='uniform gap between glyphs along the arc, in mm')
    a = ap.parse_args()
    ax, ay = (float(v) for v in a.arc_center.split(','))

    tree = etree.parse(a.src)
    el = tree.getroot().xpath(f'//*[@id="{a.id}"]')[0]
    polys = glyph_polys(flatten(el.get('d')))

    # 1-3: per-glyph reshaping
    shaped = []
    for p in polys:
        c = p.centroid; isdot = p.area < DOT_AREA
        if isdot:
            q = affinity.scale(p, a.dot_scale, a.dot_scale, origin=(c.x, c.y))
        else:
            dx, dy = c.x - ax, c.y - ay; n = math.hypot(dx, dy); ux, uy = dx / n, dy / n
            tx, ty = -uy, ux; k = a.squeeze                      # tangent of the arc = baseline direction
            m11 = 1 + (k - 1) * tx * tx; m12 = (k - 1) * tx * ty; m22 = 1 + (k - 1) * ty * ty
            q = affinity.affine_transform(p, [m11, m12, m12, m22, c.x - (m11 * c.x + m12 * c.y), c.y - (m12 * c.x + m22 * c.y)])
        if a.erode:
            q = q.buffer(-a.erode, quad_segs=8, join_style='round')
        shaped.append((q, isdot))

    # 4: uniform spacing along the arc, symmetric about the top of the arc
    items = []
    for q, isdot in shaped:
        pts = coords(q)
        th = np.arctan2(pts[:, 0] - ax, -(pts[:, 1] - ay))   # angle from the top, positive to the right
        items.append([q, isdot, th.max() - th.min(), np.hypot(pts[:, 0] - ax, pts[:, 1] - ay).min(), (th.max() + th.min()) / 2])
    items.sort(key=lambda it: it[4])
    rb = np.mean([it[3] for it in items if it[1]] or [it[3] for it in items])
    gap_a = a.gap / rb
    total = sum(it[2] for it in items) + gap_a * (len(items) - 1)
    pos = -total / 2; placed = []
    for q, isdot, span, _, center in items:
        placed.append(affinity.rotate(q, math.degrees(pos + span / 2 - center), origin=(ax, ay)))
        pos += span + gap_a

    shape = unary_union(placed).simplify(0.008, preserve_topology=True)
    el.set('d', to_path(shape)); el.set('fill-rule', 'evenodd')
    tree.write(a.dst, xml_declaration=True, encoding='UTF-8')
    print(f'{a.dst}: {len(items)} glyphs, arc span {math.degrees(total):.1f} deg', file=sys.stderr)


if __name__ == '__main__':
    main()
