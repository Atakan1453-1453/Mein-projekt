"""Strategiespiel-Kartenstil: baut aus Höhenmodell + Landnutzung drei Farbtexturen.

  base     unversehrte Landschaft (Sommerfarben; Jahreszeit/Schnee kommen beim Rendern dazu)
  damaged  Zerstörungsstufe 1: zerschossene Wälder (Stümpfe), umgepflügte Felder, Dorfruinen
  moon     Zerstörungsstufe 2: Trichterfeld („Mondlandschaft“)

Dazu Masken: forest (Wald 0..1), water, snow (wo Schnee liegen bleiben kann) und das Relief (shade).
Alle Texturen sind uint8-RGB im Raster der Karte (Web-Mercator, siehe geo.Grid).
"""
import math

import cv2
import numpy as np
from scipy import ndimage


def _noise(h, w, scale, rng, octaves=4):
    """Glattes Wertrauschen 0..1 (Summe mehrerer Oktaven)."""
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    s = scale
    for _ in range(octaves):
        gh, gw = max(2, int(h / s) + 2), max(2, int(w / s) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        out += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= 0.5
        s /= 2.0
    return np.clip(out / tot, 0, 1)


def hillshade(dem, res, z=2.2, az=315.0, alt=38.0):
    gy, gx = np.gradient(dem.astype(np.float32) * z, res)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    azr, altr = math.radians(az), math.radians(alt)
    hs = np.sin(altr) * np.cos(slope) + np.cos(altr) * np.sin(slope) * np.cos(azr - aspect - math.pi / 2)
    return np.clip(hs, 0, 1).astype(np.float32)


def _shade_height(hf, z=6.0):
    gy, gx = np.gradient(hf * z)
    n = np.sqrt(gx * gx + gy * gy + 1)
    # Licht von Nordwesten oben
    lx, ly, lz = -0.55, -0.55, 0.63
    return np.clip((-gx * lx - gy * ly + lz) / n, 0, 1).astype(np.float32)


def crown_tile(size, rng, density=0.010, rmin=2.2, rmax=4.6):
    """Kachel aus Baumkronen: Grünton (RGB float 0..1) und Schattierung."""
    hf = np.zeros((size, size), np.float32)
    col = np.zeros((size, size, 3), np.float32)
    n = int(size * size * density)
    yy, xx = np.mgrid[-8:9, -8:9].astype(np.float32)
    greens = np.array([[0.20, 0.33, 0.16], [0.24, 0.37, 0.18], [0.18, 0.30, 0.15], [0.28, 0.40, 0.20],
                       [0.22, 0.31, 0.13], [0.30, 0.36, 0.17]], np.float32)
    for _ in range(n):
        cx, cy = rng.integers(0, size), rng.integers(0, size)
        r = rng.uniform(rmin, rmax)
        bump = np.clip(1 - (xx * xx + yy * yy) / (r * r), 0, 1) ** 0.6 * r
        y0, x0 = cy - 8, cx - 8
        ys = (np.arange(17) + y0) % size
        xs = (np.arange(17) + x0) % size
        sub = hf[np.ix_(ys, xs)]
        upd = bump > sub
        sub = np.where(upd, bump, sub)
        hf[np.ix_(ys, xs)] = sub
        c = greens[rng.integers(0, len(greens))] * rng.uniform(0.9, 1.1)
        csub = col[np.ix_(ys, xs)]
        csub[upd] = c
        col[np.ix_(ys, xs)] = csub
    empty = hf <= 0
    col[empty] = (0.13, 0.20, 0.10)
    shade = _shade_height(hf, 1.6)
    return col, shade, hf


def crater_tile(size, rng, density=0.0045, rmin=2.0, rmax=9.0, water=0.08):
    """Kachel aus Granattrichtern: Höhenfeld, Schattierung, Wassermaske."""
    hf = _noise(size, size, 24, rng, 3) * 1.5
    wet = np.zeros((size, size), np.float32)
    n = int(size * size * density)
    for _ in range(n):
        cx, cy = rng.uniform(0, size), rng.uniform(0, size)
        r = rng.uniform(rmin, rmax) * (1.0 if rng.random() > 0.1 else 1.8)
        R_ = int(r * 1.8) + 2
        yy, xx = np.mgrid[-R_:R_ + 1, -R_:R_ + 1].astype(np.float32)
        d = np.sqrt((xx + (cx % 1)) ** 2 + (yy + (cy % 1)) ** 2) / r
        bowl = np.where(d < 1, -(1 - d * d) * r * 0.55, 0)
        rim = np.exp(-((d - 1.05) / 0.28) ** 2) * r * 0.22
        ys = (np.arange(-R_, R_ + 1) + int(cy)) % size
        xs = (np.arange(-R_, R_ + 1) + int(cx)) % size
        hf[np.ix_(ys, xs)] += bowl + rim
        if rng.random() < water and r > 3:
            wsub = wet[np.ix_(ys, xs)]
            wet[np.ix_(ys, xs)] = np.maximum(wsub, (d < 0.55).astype(np.float32))
    shade = _shade_height(hf, 0.9)
    return hf, shade, wet


def tile_to(tile, h, w, offset=(0, 0)):
    th, tw = tile.shape[:2]
    reps = (h // th + 2, w // tw + 2) + ((1,) if tile.ndim == 3 else ())
    big = np.tile(tile, reps)
    oy, ox = offset[0] % th, offset[1] % tw
    return big[oy:oy + h, ox:ox + w]


def _parcels(h, w, cell, rng):
    """Feld-Parzellen (Voronoi) in halber Auflösung -> Label-Bild."""
    hh, ww = h // 2 + 1, w // 2 + 1
    n = int(hh * ww / (cell * cell))
    seeds = np.zeros((hh, ww), np.int32)
    ys = rng.integers(0, hh, n)
    xs = rng.integers(0, ww, n)
    seeds[ys, xs] = np.arange(1, n + 1)
    # gestreckte Parzellen: x-Richtung stauchen
    idx = ndimage.distance_transform_edt(seeds == 0, return_distances=False, return_indices=True,
                                         sampling=(1.0, 0.65))
    lab = seeds[idx[0], idx[1]]
    lab = cv2.resize(lab.astype(np.float32), (w, h), interpolation=cv2.INTER_NEAREST).astype(np.int32)
    return lab, n


def draw_village(tex_base, tex_ruin, cx, cy, n_houses, rng, scale=1.0):
    """Zeichnet ein Dorf (Häuser mit Dächern + Schatten) in base und Ruinen in tex_ruin."""
    ang = rng.uniform(0, math.pi)
    streets = [ang, ang + rng.uniform(0.9, 2.2)]
    roofs = [(150, 70, 55), (132, 62, 50), (110, 100, 96), (160, 88, 66), (125, 112, 104)]
    for i in range(n_houses):
        a = streets[i % 2]
        t = rng.normal(0, 13 * scale)
        side = rng.choice([-1, 1]) * rng.uniform(3.5, 6.5) * scale
        hx = cx + math.cos(a) * t - math.sin(a) * side
        hy = cy + math.sin(a) * t + math.cos(a) * side
        L, W_ = rng.uniform(4.5, 8) * scale, rng.uniform(3, 4.5) * scale
        ca, sa = math.cos(a), math.sin(a)
        pts = np.array([[-L / 2, -W_ / 2], [L / 2, -W_ / 2], [L / 2, W_ / 2], [-L / 2, W_ / 2]])
        rot = np.array([[ca, -sa], [sa, ca]])
        poly = (pts @ rot.T) + [hx, hy]
        sh = poly + [2.0 * scale, 2.0 * scale]
        cv2.fillPoly(tex_base, [np.round(sh * 4).astype(np.int32)], (40, 46, 34), lineType=cv2.LINE_AA, shift=2)
        c = roofs[rng.integers(0, len(roofs))]
        cv2.fillPoly(tex_base, [np.round(poly * 4).astype(np.int32)], c, lineType=cv2.LINE_AA, shift=2)
        # Dachfirst: helle Hälfte
        half = np.array([poly[0], poly[1], (poly[1] + poly[2]) / 2, (poly[0] + poly[3]) / 2])
        cv2.fillPoly(tex_base, [np.round(half * 4).astype(np.int32)], tuple(min(255, int(v * 1.18)) for v in c),
                     lineType=cv2.LINE_AA, shift=2)
        # Ruine: Schutt-Fleck + Mauerreste
        cv2.fillPoly(tex_ruin, [np.round(poly * 4).astype(np.int32)], (118, 110, 100), lineType=cv2.LINE_AA, shift=2)
        for k in range(4):
            p0, p1 = poly[k], poly[(k + 1) % 4]
            if rng.random() < 0.55:
                cv2.line(tex_ruin, tuple(np.round(p0 * 4).astype(int)), tuple(np.round((p0 + (p1 - p0) * rng.uniform(0.3, 1)) * 4).astype(int)),
                         (170, 162, 150), 1, cv2.LINE_AA, shift=2)
        for k in range(3):
            q = poly.mean(0) + rng.normal(0, 3 * scale, 2)
            cv2.circle(tex_ruin, tuple(np.round(q * 4).astype(int)), int(4 * rng.uniform(1, 2.5) * scale), (88, 80, 70), -1,
                       cv2.LINE_AA, shift=2)


def draw_fort(tex, cx, cy, size, ruin=False):
    """Fort von oben: fünfeckiger Graben, Wall mit Gras, Betondecke."""
    pts = []
    for k in range(5):
        a = -math.pi / 2 + k * 2 * math.pi / 5
        rr = size * (1.0 if k % 2 == 0 else 0.92)
        pts.append([cx + math.cos(a) * rr * 1.25, cy + math.sin(a) * rr])
    pts = np.array(pts)
    s = 4
    P = lambda q: [np.round(q * s).astype(np.int32)]  # noqa: E731
    cen = pts.mean(0)
    outer = cen + (pts - cen) * 1.18
    cv2.fillPoly(tex, P(outer + 2), (52, 58, 44), cv2.LINE_AA, shift=2)                     # Schatten
    cv2.fillPoly(tex, P(outer), (96, 104, 74) if not ruin else (104, 96, 84), cv2.LINE_AA, shift=2)
    cv2.polylines(tex, P(cen + (pts - cen) * 1.08), True, (44, 48, 40), max(1, int(size * 0.10)), cv2.LINE_AA, shift=2)  # Graben
    cv2.fillPoly(tex, P(pts), (122, 134, 88) if not ruin else (128, 118, 102), cv2.LINE_AA, shift=2)                    # Wall
    inner = cen + (pts - cen) * 0.55
    cv2.fillPoly(tex, P(inner), (176, 174, 164) if not ruin else (150, 146, 138), cv2.LINE_AA, shift=2)                 # Beton
    cv2.polylines(tex, P(inner), True, (120, 118, 110), 1, cv2.LINE_AA, shift=2)


def build(dem, wc, res, villages, forts, verdun_px, clear_poly=None, seed=7, city_r=230):
    """villages: Liste (x, y, n_häuser); forts: Liste (x, y, size_px, gross?)."""
    rng = np.random.default_rng(seed)
    H, W = wc.shape
    f32 = np.float32

    # ---------------- Landnutzung 1916
    forest = ((wc == 10) | (wc == 20)).astype(f32)
    water = ((wc == 80) | (wc == 90)).astype(f32)
    yy, xx = np.ogrid[:H, :W]
    city = ((xx - verdun_px[0]) ** 2 + (yy - verdun_px[1]) ** 2) < city_r ** 2
    zone_hard = np.zeros((H, W), np.uint8)
    if clear_poly is not None:
        cv2.fillPoly(zone_hard, [np.round(np.array(clear_poly)).astype(np.int32)], 1)
    # moderne Orte: im Schlachtfeld entfernen (dort werden die Dörfer von 1916 gezeichnet),
    # außerhalb als Dorfflächen behalten; Straßen/Autobahn (dünne Linien) per Öffnung entfernen
    urb = ((wc == 50) & (city | (zone_hard == 0))).astype(np.uint8)
    urb = cv2.morphologyEx(urb, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    urban = urb.astype(f32)
    if clear_poly is not None:
        zone = cv2.GaussianBlur(zone_hard.astype(f32), (0, 0), 25)
        # Lichtungen um Dörfer/Forts: Distanzfeld, mit Rauschen verzerrt (keine Kreise)
        small = np.ones((H // 4 + 1, W // 4 + 1), np.uint8)
        for (vx, vy, n) in villages:
            cv2.circle(small, (int(vx / 4), int(vy / 4)), 2, 0, -1)
        for (fx, fy, s_, big) in forts:
            cv2.circle(small, (int(fx / 4), int(fy / 4)), 2, 0, -1)
        dist = cv2.distanceTransform(small, cv2.DIST_L2, 5) * 4
        dist = cv2.resize(dist, (W, H), interpolation=cv2.INTER_LINEAR)[:H, :W]
        warp = _noise(H, W, 180, rng, 4)
        clear = (dist < 110 + 230 * warp).astype(f32)
        nz = _noise(H, W, 300, rng, 4)
        clear = np.maximum(clear, (nz > 0.62).astype(f32))
        clear = cv2.GaussianBlur(clear, (0, 0), 3)
        forest = forest * (1 - np.clip(zone * clear * 1.6, 0, 1))
    # weiche, aber klare Waldkanten
    forest = cv2.GaussianBlur(forest, (0, 0), 1.2)
    forest = np.clip((forest - 0.35) * 3.0, 0, 1)
    water = cv2.GaussianBlur(water, (0, 0), 0.8)

    hs = hillshade(cv2.GaussianBlur(dem.astype(f32), (0, 0), 5.0), res, z=2.2)
    hs_s = cv2.GaussianBlur(hs, (0, 0), 1.0)
    elev = (dem - dem.min()) / max(1.0, dem.max() - dem.min())

    # ---------------- Felder
    lab, n = _parcels(H, W, 15, rng)
    pal = np.array([[0.47, 0.55, 0.29], [0.55, 0.59, 0.31], [0.62, 0.60, 0.37], [0.69, 0.64, 0.41],
                    [0.42, 0.50, 0.27], [0.59, 0.55, 0.34], [0.50, 0.47, 0.30], [0.66, 0.58, 0.36],
                    [0.45, 0.53, 0.33]], f32)
    pick = rng.integers(0, len(pal), n + 1)
    jitter = rng.uniform(0.93, 1.07, n + 1).astype(f32)
    field = pal[pick][lab] * jitter[lab][..., None]
    edges = (cv2.Laplacian(lab.astype(f32), cv2.CV_32F) != 0).astype(f32)
    field *= (1 - 0.12 * cv2.GaussianBlur(edges, (0, 0), 0.6))[..., None]
    # Feinstruktur (Furchen-Rauschen)
    fine = tile_to(_noise(512, 512, 6, rng, 2), H, W)
    field *= (0.92 + 0.16 * fine)[..., None]
    # Täler etwas grüner (Wiesen)
    meadow = np.array([0.40, 0.52, 0.28], f32)
    vmask = np.clip((0.25 - elev) * 4, 0, 1)[..., None]
    field = field * (1 - vmask * 0.6) + meadow * vmask * 0.6

    # ---------------- Wald
    ccol, cshade, _ = crown_tile(1024, rng)
    tcol = tile_to(ccol, H, W, (137, 291))
    tsh = tile_to(cshade, H, W, (137, 291))
    forest_col = tcol * (0.62 + 0.85 * tsh)[..., None]

    # ---------------- Zusammensetzen
    base = field.copy()
    fm = forest[..., None]
    # Schattenwurf der Waldkante nach Südosten
    fshadow = np.clip(cv2.GaussianBlur(np.roll(np.roll(forest, 3, 0), 3, 1), (0, 0), 2.0) - forest, 0, 1)
    base *= (1 - 0.45 * fshadow)[..., None]
    base = base * (1 - fm) + forest_col * fm
    roofs = tile_to((rng.random((256, 256)) < 0.5).astype(f32), H, W)
    roofs = cv2.GaussianBlur(cv2.resize(roofs[:H // 3 + 1, :W // 3 + 1], (W, H), interpolation=cv2.INTER_NEAREST), (0, 0), 0.6)
    urban_col = (np.array([0.58, 0.36, 0.30], f32) * roofs[..., None] + np.array([0.50, 0.48, 0.45], f32) * (1 - roofs[..., None])) \
        * (0.85 + 0.3 * fine)[..., None]
    um = cv2.GaussianBlur(urban, (0, 0), 1.0)[..., None]
    base = base * (1 - um) + urban_col * um
    water_col = np.array([0.27, 0.42, 0.52], f32)
    wm = water[..., None]
    shore = np.clip(cv2.GaussianBlur(water, (0, 0), 2.5) - water, 0, 1)[..., None]
    base = base * (1 - shore * 0.35) + np.array([0.55, 0.60, 0.50], f32) * shore * 0.35
    base = base * (1 - wm) + water_col * wm

    # Relief
    light = (0.50 + 0.72 * hs_s)[..., None]
    base_lit = base * light * (1 - wm * 0.5) + base * wm * 0.5 + 0.03 * elev[..., None]

    # ---------------- Zerstörung 1: Stümpfe, umgepflügt
    mud1 = np.array([0.45, 0.40, 0.29], f32)
    chf, csh, cwet = crater_tile(1024, rng, density=0.0016, rmin=1.6, rmax=5.5, water=0.03)
    csh1 = tile_to(csh, H, W, (511, 77))
    dmg = base * 0.45 + mud1 * 0.55
    stumps = tile_to((rng.random((512, 512)) < 0.035).astype(f32), H, W)
    stumps = cv2.GaussianBlur(stumps, (0, 0), 0.5) * forest
    dmg = dmg * (1 - np.clip(stumps * 3, 0, 0.8))[..., None]
    sparse = (tile_to(cshade, H, W, (700, 13)) > 0.75).astype(f32) * forest * 0.5
    dmg = dmg * (1 - sparse[..., None]) + forest_col * sparse[..., None]
    dmg *= (0.55 + 0.6 * csh1)[..., None]
    dmg = dmg * (1 - wm) + water_col * wm
    dmg_lit = dmg * light

    # ---------------- Zerstörung 2: Mondlandschaft
    mhf, msh, mwet = crater_tile(1024, rng, density=0.0060, rmin=2.0, rmax=9.5, water=0.10)
    msh_t = tile_to(msh, H, W, (233, 919))
    mwet_t = tile_to(mwet, H, W, (233, 919))
    mud2 = np.array([0.44, 0.39, 0.32], f32)
    var = tile_to(_noise(1024, 1024, 90, rng, 3), H, W)
    moon = mud2 * (0.85 + 0.3 * var)[..., None]
    moon = moon * (0.45 + 0.75 * msh_t)[..., None]
    puddle = np.array([0.30, 0.34, 0.33], f32)
    moon = moon * (1 - mwet_t[..., None] * 0.85) + puddle * mwet_t[..., None] * 0.85
    moon = moon * (1 - wm) + water_col * 0.8 * wm
    moon_lit = moon * (0.62 + 0.5 * hs_s)[..., None]

    to8 = lambda a: np.clip(a * 255, 0, 255).astype(np.uint8)  # noqa: E731
    base8, dmg8, moon8 = to8(base_lit), to8(dmg_lit), to8(moon_lit)

    # ---------------- Dörfer und Forts (Basis + Ruinen)
    for (vx, vy, nh) in villages:
        draw_village(base8, dmg8, vx, vy, nh, rng, scale=1.5)
        # in der Mondlandschaft nur noch Schuttflecken
        for k in range(nh // 3):
            q = (vx + rng.normal(0, 12), vy + rng.normal(0, 12))
            cv2.circle(moon8, (int(q[0]), int(q[1])), int(rng.uniform(1, 3)), (150, 142, 130), -1, cv2.LINE_AA)
    for (fx, fy, s, big) in forts:
        draw_fort(base8, fx, fy, s)
        draw_fort(dmg8, fx, fy, s, ruin=True)
        draw_fort(moon8, fx, fy, s, ruin=True)

    # Schnee-Maske (wo Schnee liegen bleibt: flach, weniger im Wald)
    gy, gx = np.gradient(cv2.GaussianBlur(dem.astype(f32), (0, 0), 5.0), res)
    slope = np.hypot(gx, gy)
    patch = tile_to(_noise(1024, 1024, 40, rng, 3), H, W)
    snow = np.clip(1.0 - slope * 2.5, 0.35, 1) * (1 - 0.45 * forest) * (0.55 + 0.35 * var + 0.35 * patch) * (0.85 + 0.15 * fine)
    snow = np.clip(snow, 0, 1) * (1 - water)
    return dict(base=base8, damaged=dmg8, moon=moon8, forest=to8(forest), water=to8(water), snow=to8(snow),
                shade=to8(hs_s))
