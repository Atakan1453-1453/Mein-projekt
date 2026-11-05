"""Panzer, Flugzeuge, Wolken und Nebel für das Amiens-Video (ergänzt engine.py).

Panzer: jeder echte Panzer ist ein eigenes kleines Modell (Draufsicht, perspektivisch auf den Boden gelegt) mit
laufenden Ketten, Kettenspuren, Staub, Mündungsfeuer und brennenden Wracks.
Flugzeuge: Draufsicht-Silhouetten mit Schatten am Boden, Kurvenflug im Luftkampf, Leuchtspur, Absturz mit Rauchfahne.
Wolken: mehrere Schichten in verschiedenen Höhen. Beim Herunterzoomen wachsen sie, ziehen zur Seite oder fliegen durch
die Kamera; darunter liegt das Schlachtfeld. In den Nahszenen liegt die Kamera unter allen Wolkenschichten.
"""
import math

import numpy as np
import skia
from scipy import ndimage

import engine as E
from engine import H, W, Obj, Screen, clamp, fade, merc, smooth, soft_circle

R = 6378137.0


def _proj(v, X, Y):
    M = v.M
    Xs = M[0, 0] * X + M[0, 1] * Y + M[0, 2]
    Ys = M[1, 0] * X + M[1, 1] * Y + M[1, 2]
    Zs = M[2, 0] * X + M[2, 1] * Y + M[2, 2]
    ok = Zs > 1e-6
    Zs = np.where(ok, Zs, 1.0)
    return Xs / Zs, Ys / Zs, 1.0 / Zs, ok


def _merc_arr(lat, lon):
    return R * np.radians(lon), R * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))


def _img(a):
    a = np.ascontiguousarray(a)
    return skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType).withDefaultMipmaps()


def _quad_draw(c, img, pts, alpha=1.0, p=None):
    """Bild auf ein Viereck (Bildschirmpunkte im Uhrzeigersinn ab vorne-links) abbilden."""
    w, h = img.width(), img.height()
    src = [skia.Point(0, 0), skia.Point(w, 0), skia.Point(w, h), skia.Point(0, h)]
    dst = [skia.Point(float(x), float(y)) for x, y in pts]
    m = skia.Matrix()
    if not m.setPolyToPoly(src, dst):
        return
    c.save()
    c.concat(m)
    pp = p or skia.Paint(AntiAlias=True)
    pp.setAlphaf(clamp(alpha))
    c.drawImage(img, 0, 0, E.SAMPLING, pp)
    c.restore()


# ====================================================================== Panzer-Modelle (Draufsicht, Bug oben)
TANK_DIM = {  # Länge, Breite in m (Breite mit Seitenkasematten)
    "mk5": (8.05, 4.1), "mk5s": (9.9, 4.1), "mk4": (8.05, 4.1), "supply": (8.05, 3.3), "whippet": (6.1, 2.6),
    "a7v": (7.34, 3.06), "ft": (5.0, 1.74),
}
KHAKI = (112, 106, 64)
DE_GREY = (108, 112, 100)
FR_BLUE = (104, 118, 120)


def _shade(a, x0, y0, x1, y1, col, alpha=255):
    a[y0:y1, x0:x1, :3] = col
    a[y0:y1, x0:x1, 3] = alpha


def _cross(a, cx, cy, s, white=True):
    """Eisernes Kreuz (Tatzenkreuz, 1918 Balkenkreuz) als Kennzeichen."""
    t = max(2, s // 4)
    if white:
        _shade(a, cx - s - 2, cy - t - 2, cx + s + 2, cy + t + 2, (240, 240, 240))
        _shade(a, cx - t - 2, cy - s - 2, cx + t + 2, cy + s + 2, (240, 240, 240))
    _shade(a, cx - s, cy - t, cx + s, cy + t, (20, 20, 20))
    _shade(a, cx - t, cy - s, cx + t, cy + s, (20, 20, 20))


def _tank_sprite(kind, nation, frame):
    """RGBA-Draufsicht 64×(Breite) Pixel: Kettenlaufwerk, Rumpf, Aufbauten; frame bewegt das Kettenmuster."""
    L, B = TANK_DIM[kind]
    h = 96
    w = max(24, int(round(h * B / L)))
    a = np.zeros((h, w, 4), np.uint8)
    body = DE_GREY if nation == "de" else (FR_BLUE if nation == "fr" else KHAKI)
    dark = tuple(int(c * 0.55) for c in body)
    light = tuple(min(255, int(c * 1.22)) for c in body)
    track = (58, 52, 44)
    tw = max(5, int(w * (0.24 if kind in ("mk5", "mk5s", "mk4", "supply") else 0.28)))
    if kind == "a7v":
        # A7V: großer Kastenaufbau über dem Fahrwerk, Ketten kaum sichtbar
        _shade(a, 1, 4, w - 1, h - 4, track)
        _shade(a, 3, 2, w - 3, h - 2, body)
        _shade(a, 3, 2, w - 3, 8, light)                      # Bugplatte
        _shade(a, w // 2 - 7, h // 2 - 12, w // 2 + 7, h // 2 + 8, dark)   # Kommandantenstand
        _shade(a, w // 2 - 5, h // 2 - 10, w // 2 + 5, h // 2 + 6, light)
        _shade(a, w // 2 - 2, 0, w // 2 + 2, 6, (40, 40, 38))   # Bugkanone
        _cross(a, w // 2, int(h * 0.74), 7)
        for y in range(10, h - 6, 9):                         # Nietenreihen
            a[y, 4:w - 4, :3] = dark
    else:
        # Kettenbänder links und rechts, Glieder laufen mit frame
        for x0 in (0, w - tw):
            _shade(a, x0, 0, x0 + tw, h, track)
            for y in range((frame * 2) % 6, h, 6):
                a[y:y + 2, x0 + 1:x0 + tw - 1, :3] = (92, 84, 70)
        hx0, hx1 = tw, w - tw
        if kind == "whippet":
            _shade(a, hx0 - 1, 6, hx1 + 1, h - 4, body)
            _shade(a, hx0, 8, hx1, int(h * 0.42), dark)       # Motorraum vorne
            for y in range(10, int(h * 0.40), 5):
                a[y, hx0 + 2:hx1 - 2, :3] = light
            _shade(a, hx0 - 2, int(h * 0.55), hx1 + 2, h - 6, light)   # Kampfraum hinten
            _shade(a, hx0 + 2, int(h * 0.58), hx1 - 2, h - 9, body)
        else:
            _shade(a, hx0, 3, hx1, h - 3, body)
            _shade(a, hx0, 3, hx1, 10, light)
            # Seitenkasematten (Male: 6-Pfünder) ragen über die Ketten hinaus
            if kind != "supply":
                sy0, sy1 = int(h * 0.36), int(h * 0.56)
                _shade(a, 0, sy0, tw + 2, sy1, light)
                _shade(a, w - tw - 2, sy0, w, sy1, light)
                a[sy0 + 3:sy1 - 3, 0:2, :3] = (35, 35, 32)
                a[sy0 + 3:sy1 - 3, w - 2:w, :3] = (35, 35, 32)
            # Kommandantenstand / Kabine vorne, Auspuff hinten
            _shade(a, w // 2 - 6, 12, w // 2 + 6, 26, dark)
            _shade(a, w // 2 - 4, 14, w // 2 + 4, 24, light)
            if kind in ("mk5", "mk5s", "supply"):
                _shade(a, w // 2 - 7, int(h * 0.72), w // 2 + 7, int(h * 0.84), dark)   # hintere Kabine
            _shade(a, w // 2 - 2, h - 10, w // 2 + 2, h - 4, (30, 30, 28))
            if kind == "supply":
                for y in range(int(h * 0.32), int(h * 0.68), 9):
                    _shade(a, hx0 + 2, y, hx1 - 2, y + 7, (150, 118, 70))
                    a[y + 3, hx0 + 2:hx1 - 2, :3] = (110, 85, 50)
        # weiß-rot-weiße Erkennungsstreifen am Bug (britische Panzer 1918)
        if nation != "fr":
            for i, col in enumerate(((235, 235, 230), (200, 30, 30), (235, 235, 230))):
                a[4 + i * 2:6 + i * 2, 0:tw, :3] = col
                a[4 + i * 2:6 + i * 2, w - tw:w, :3] = col
    # weiche Kante + leichte Lichtkante
    alpha = a[..., 3].astype(np.float32)
    alpha = ndimage.gaussian_filter(alpha, 0.6)
    a[..., 3] = np.clip(alpha, 0, 255).astype(np.uint8)
    return _img(a)


_TANK_CACHE = {}


def tank_sprite(kind, nation, frame=0, wreck=False):
    key = (kind, nation, frame, wreck)
    if key not in _TANK_CACHE:
        img = _tank_sprite(kind, nation, frame)
        if wreck:
            arr = img.toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType).copy()
            arr[..., :3] = (arr[..., :3].astype(np.float32) * np.array([0.42, 0.38, 0.34])).astype(np.uint8)
            img = _img(arr)
        _TANK_CACHE[key] = img
    return _TANK_CACHE[key]


class TankGroup:
    """n Panzer in Linie: keys [(t, lat, lon)] für die Gruppenmitte; Verluste (abgeschossen, brennt) und Ausfälle."""

    def __init__(self, nation, kind, n, keys, facing=None, spacing=55.0, rows=1, row_gap=70.0, losses=None, breakdowns=None,
                 fire=None, seed=0, t0=None, t1=1e9, lag=1.6):
        self.nation, self.kind, self.n = nation, kind, int(n)
        self.keys = sorted(keys)
        self.t0 = self.keys[0][0] if t0 is None else t0
        self.t1 = t1
        self.fire = fire or []
        rng = np.random.default_rng(seed + 31 * self.n)
        per_row = math.ceil(self.n / rows)
        ox, oy = [], []
        for i in range(self.n):
            r, j = divmod(i, per_row)
            ox.append((j - (per_row - 1) / 2) * spacing + rng.normal(0, spacing * 0.18))
            oy.append(-r * row_gap + rng.normal(0, spacing * 0.25))
        self.off = np.stack([ox, oy], 1)
        self.lag = rng.random(self.n) * lag
        self.wob = rng.random(self.n) * 10
        self.ko = np.full(self.n, np.inf)        # abgeschossen (brennt)
        self.stop = np.full(self.n, np.inf)      # liegengeblieben (ohne Feuer)
        order = rng.permutation(self.n)
        idx = 0
        for (tl, k) in sorted(losses or []):
            k = int(min(k, self.n - idx))
            self.ko[order[idx:idx + k]] = tl + rng.random(k) * 2.5
            idx += k
        for (tl, k) in sorted(breakdowns or []):
            k = int(min(k, self.n - idx))
            self.stop[order[idx:idx + k]] = tl + rng.random(k) * 4.0
            idx += k
        self.halt = np.minimum(self.ko, self.stop)
        if facing is None:
            (_, a1, o1), (_, a2, o2) = self.keys[0], self.keys[-1]
            facing = math.degrees(math.atan2((o2 - o1) * math.cos(math.radians(a1)), a2 - a1)) % 360 if len(self.keys) > 1 else 90.0
        self.facing = facing
        # Richtung je Abschnitt (für stehende Panzer: letzte Fahrtrichtung)
        self.seg_dir = []
        for (ta, a1, o1), (tb, a2, o2) in zip(self.keys, self.keys[1:]):
            if abs(a2 - a1) + abs(o2 - o1) > 1e-7:
                self.seg_dir.append((tb, math.degrees(math.atan2((o2 - o1) * math.cos(math.radians(a1)), a2 - a1)) % 360))

    def center(self, t):
        ks = self.keys
        tt = np.atleast_1d(np.asarray(t, dtype=np.float64))
        la = np.full(tt.shape, ks[0][1])
        lo = np.full(tt.shape, ks[0][2])
        for (ta, a1, o1), (tb, a2, o2) in zip(ks, ks[1:]):
            m = (tt >= ta) & (tt <= tb)
            if m.any():
                s = (tt[m] - ta) / max(1e-6, tb - ta)
                s = s * s * (3 - 2 * s) * 0.25 + s * 0.75        # fast gleichmäßige Fahrt
                la[m] = a1 + (a2 - a1) * s
                lo[m] = o1 + (o2 - o1) * s
        last = tt > ks[-1][0]
        la[last], lo[last] = ks[-1][1], ks[-1][2]
        return la, lo

    def heading_at(self, t):
        h = self.facing
        for tb, d in self.seg_dir:
            if t >= tb - 1e9:
                pass
        # Richtung des zuletzt begonnenen Abschnitts
        for (ta, *_), (tb, d) in zip(self.keys, self.seg_dir):
            if t >= ta:
                h = d
        return h

    def state(self, t):
        """Positionen (Mercator), Fahrtrichtung, fährt?, Wrack? je Panzer."""
        te = np.minimum(t - self.lag, self.halt)
        la, lo = self.center(te)
        la2, lo2 = self.center(te + 0.5)
        la1, lo1 = self.center(te - 0.5)
        k = np.cos(np.radians(la))
        dy, dx = la2 - la1, (lo2 - lo1) * k
        moving = (np.hypot(dx, dy) > 2e-7) & (te < self.halt - 1e-6) & (t - self.lag < self.halt)
        hd = np.where(np.hypot(dx, dy) > 1e-9, np.degrees(np.arctan2(dx, dy)), self.heading_at(t))
        # Formation dreht mit der Fahrtrichtung
        h = np.radians(np.full(self.n, self.heading_at(t)))
        cx, cy = _merc_arr(la, lo)
        km = 1.0 / np.cos(np.radians(la))
        ox, oy = self.off[:, 0], self.off[:, 1]
        X = cx + (ox * np.cos(h) + oy * np.sin(h)) * km
        Y = cy + (-ox * np.sin(h) + oy * np.cos(h)) * km
        return X, Y, np.radians(hd), moving, la


class Tanks(Obj):
    """Zeichnet Panzergruppen (1 Modell = 1 Panzer)."""
    z = 19

    def __init__(self, groups, t0, t1, max_width=60.0):
        self.groups, self.t0, self.t1, self.max_width = groups, t0, t1, max_width
        self.fin, self.fout = 0.8, 1.0

    def draw(self, c, v, t):
        a = self.alpha(t) * clamp((self.max_width - v.cam.width) / (self.max_width * 0.35))
        if a <= 0:
            return
        gm = v.cam.width * 1000.0 / W
        wrecks, movers = [], []
        for g in self.groups:
            if not (g.t0 <= t <= g.t1):
                continue
            ga = a * fade(t, g.t0, g.t1, 0.8, 1.0)
            L, B = TANK_DIM[g.kind]
            Lpx = clamp(L / gm * 3.4, 6.0, 30.0)
            sc = Lpx * gm / L                                   # Vergrößerung gegenüber Echtmaß
            X, Y, hd, moving, la = g.state(t)
            km = 1.0 / np.cos(np.radians(la))
            fx, fy = np.sin(hd), np.cos(hd)
            rx, ry = np.cos(hd), -np.sin(hd)
            hl, hb = L * sc / 2 * km, B * sc / 2 * km
            sx, sy, dz, ok = _proj(v, X, Y)
            vis = ok & (sx > -60) & (sx < W + 60) & (sy > -60) & (sy < H + 60)
            if not vis.any():
                continue
            # Kettenspuren (letzte Sekunden) und Staub
            for i in np.nonzero(vis & moving)[0]:
                pass
            idx = np.nonzero(vis)[0]
            trail_t = np.array([0.0, 1.5, 3.0, 4.5, 6.0])
            if (moving[idx]).any():
                tp = c
                path = skia.Path()
                for i in idx[moving[idx]]:
                    te = min(t - g.lag[i], g.halt[i])
                    pts = []
                    for dt in trail_t:
                        lam, lom = g.center(np.array([te - dt]))
                        hh = math.radians(g.heading_at(te - dt))
                        cx, cy = _merc_arr(lam[0], lom[0])
                        kk = 1.0 / math.cos(math.radians(lam[0]))
                        ox, oy = g.off[i]
                        pts.append((cx + (ox * math.cos(hh) + oy * math.sin(hh)) * kk, cy + (-ox * math.sin(hh) + oy * math.cos(hh)) * kk))
                    P = np.array(pts)
                    px, py, _, pok = _proj(v, P[:, 0], P[:, 1])
                    if not pok.all():
                        continue
                    path.moveTo(px[0], py[0])
                    for xx, yy in zip(px[1:], py[1:]):
                        path.lineTo(xx, yy)
                c.drawPath(path, E.paint(skia.Color4f(0.20, 0.16, 0.11, 0.30 * ga), "stroke", max(1.0, Lpx * 0.22)))
            frame = int(t * 8) % 3
            for i in idx:
                cxs = [X[i] + (fx[i] * hl[i] * s1 + rx[i] * hb[i] * s2) for s1, s2 in ((1, -1), (1, 1), (-1, 1), (-1, -1))]
                cys = [Y[i] + (fy[i] * hl[i] * s1 + ry[i] * hb[i] * s2) for s1, s2 in ((1, -1), (1, 1), (-1, 1), (-1, -1))]
                qx, qy, _, qok = _proj(v, np.array(cxs), np.array(cys))
                if not qok.all():
                    continue
                wreck = t >= g.ko[i]
                halted = t >= g.stop[i]
                if moving[i]:
                    # Staub hinter dem Panzer
                    bx, by = (qx[2] + qx[3]) / 2, (qy[2] + qy[3]) / 2
                    soft_circle(c, bx, by, Lpx * 0.9, skia.Color4f(0.55, 0.47, 0.36, 0.22 * ga))
                img = tank_sprite(g.kind, g.nation, 0 if (wreck or halted or not moving[i]) else (frame + int(g.wob[i] * 3)) % 3, wreck)
                # Schatten
                sh = skia.Paint(AntiAlias=True)
                sh.setColorFilter(skia.ColorFilters.Blend(skia.Color4f(0, 0, 0, 1).toColor(), skia.BlendMode.kSrcIn))
                off = Lpx * 0.12
                _quad_draw(c, img, [(qx[k] + off, qy[k] + off) for k in range(4)], 0.35 * ga, sh)
                _quad_draw(c, img, list(zip(qx, qy)), ga)
                if wreck:
                    wrecks.append((sx[i], sy[i], Lpx, t - g.ko[i], ga, g.wob[i]))
                elif any(ta <= t <= tb for ta, tb in g.fire) and ((int(t * 10) + i * 7) % 23 == 0):
                    mx, my = (qx[0] + qx[1]) / 2, (qy[0] + qy[1]) / 2
                    soft_circle(c, mx, my, Lpx * 0.6, skia.Color4f(1, 0.85, 0.45, 0.85 * ga), skia.BlendMode.kPlus)
                    ex, ey = mx + (mx - sx[i]) * 6, my + (my - sy[i]) * 6
                    c.drawLine(mx, my, ex, ey, E.paint(skia.Color4f(1, 0.9, 0.5, 0.55 * ga), "stroke", 1.2))
        for x, y, Lpx, age, ga, ph in wrecks:
            fa = ga * (1 - smooth((age - 40) / 20))
            if fa <= 0.02:
                continue
            fl = 0.75 + 0.25 * math.sin(t * 9 + ph * 3)
            if age < 1.0:
                soft_circle(c, x, y, Lpx * 2.2 * (1 + age), skia.Color4f(1, 0.75, 0.3, 0.9 * (1 - age) * ga), skia.BlendMode.kPlus)
            soft_circle(c, x, y, Lpx * 0.8, skia.Color4f(1, 0.45, 0.1, 0.55 * fa * fl), skia.BlendMode.kPlus)
            for j in range(3):
                p = (t * 0.25 + ph + j / 3) % 1.0
                soft_circle(c, x + p * Lpx * 1.5, y - p * Lpx * 5, Lpx * (0.6 + 1.6 * p), skia.Color4f(0.08, 0.07, 0.07, 0.45 * fa * (1 - p)))


# ====================================================================== Flugzeuge
PLANE_DIM = {"camel": 8.5, "se5": 8.1, "spad": 8.1, "dh9": 12.9, "breguet": 14.4, "fokker": 8.9, "dr1": 7.2, "rumpler": 12.2}


def _roundel(img_a, cx, cy, r, nation):
    yy, xx = np.mgrid[0:img_a.shape[0], 0:img_a.shape[1]]
    d = np.hypot(xx - cx, yy - cy)
    if nation in ("gb", "au", "ca"):
        rings = [(r, (30, 50, 140)), (r * 0.66, (240, 240, 240)), (r * 0.36, (200, 30, 35))]
    elif nation == "fr":
        rings = [(r, (200, 30, 35)), (r * 0.66, (240, 240, 240)), (r * 0.36, (30, 60, 160))]
    else:
        rings = [(r, (40, 60, 150)), (r * 0.66, (240, 240, 240)), (r * 0.36, (200, 30, 35))]
    for rr, col in rings:
        m = d <= rr
        img_a[m, :3] = col
        img_a[m, 3] = 255


def _plane_sprite(kind, nation):
    """Draufsicht 128×128, Nase oben."""
    s = 128
    a = np.zeros((s, s, 4), np.uint8)
    if nation == "de":
        top = (178, 30, 30) if kind == "dr1" else (92, 98, 70)
        alt = (140, 22, 22) if kind == "dr1" else (110, 80, 110)
    else:
        top = (104, 98, 60) if nation != "fr" else (150, 140, 110)
        alt = (86, 82, 52) if nation != "fr" else (120, 125, 105)
    span = {"dh9": 124, "breguet": 126, "rumpler": 122}.get(kind, 118)
    chord = 22 if kind not in ("dh9", "breguet", "rumpler") else 26
    cx = s // 2
    wy = 38
    # Oberflügel (beim Dreidecker etwas schmaler) mit runden Enden
    _shade(a, cx - span // 2 + 4, wy, cx + span // 2 - 4, wy + chord, top)
    for side in (-1, 1):
        x0 = cx + side * (span // 2 - 4)
        yy, xx = np.mgrid[wy:wy + chord, min(x0, x0 + side * 4) - 1:max(x0, x0 + side * 4) + 1]
        m = ((xx - x0) / 5.0) ** 2 + ((yy - (wy + chord / 2)) / (chord / 2)) ** 2 <= 1
        sub = a[wy:wy + chord, min(x0, x0 + side * 4) - 1:max(x0, x0 + side * 4) + 1]
        sub[m] = list(top) + [255]
    # Rippen/Tarnmuster
    rng = np.random.default_rng(len(kind) * 7 + (nation == "de"))
    for _ in range(14):
        x = int(rng.integers(cx - span // 2 + 6, cx + span // 2 - 10))
        _shade(a, x, wy + 1, x + int(rng.integers(4, 9)), wy + chord - 1, alt)
    # Rumpf, Leitwerk
    fw = 12 if kind not in ("dh9", "breguet", "rumpler") else 14
    _shade(a, cx - fw // 2, 10, cx + fw // 2, 112, top)
    _shade(a, cx - fw // 2 + 2, 14, cx + fw // 2 - 2, 26, (60, 55, 40))          # Motorhaube
    _shade(a, cx - 3, wy + chord + 2, cx + 3, wy + chord + 10, (40, 35, 30))        # Cockpit
    if kind in ("dh9", "breguet", "rumpler"):
        _shade(a, cx - 3, wy + chord + 16, cx + 3, wy + chord + 24, (40, 35, 30))   # Beobachter
    _shade(a, cx - 24, 100, cx + 24, 114, top)                                        # Höhenleitwerk
    if nation == "de":
        for x in (cx - span // 2 + 18, cx + span // 2 - 18):
            _cross(a, x, wy + chord // 2, 8)
        _cross(a, cx, 107, 4, white=True)
    else:
        for x in (cx - span // 2 + 18, cx + span // 2 - 18):
            _roundel(a, x, wy + chord // 2, 9, nation)
        a[104:114, cx - 2:cx + 2, :3] = (200, 30, 35)
    alpha = ndimage.gaussian_filter(a[..., 3].astype(np.float32), 0.7)
    a[..., 3] = np.clip(alpha, 0, 255).astype(np.uint8)
    return _img(a)


_PLANE_CACHE = {}


def plane_sprite(kind, nation):
    key = (kind, nation)
    if key not in _PLANE_CACHE:
        _PLANE_CACHE[key] = _plane_sprite(kind, nation)
    return _PLANE_CACHE[key]


class Plane:
    """Ein Flugzeug: Flugweg keys [(t, lat, lon, alt_m)], Kurbelkreise circles [(t0, t1, lat, lon, r_m, period_s)],
    Abschuss shot=t (stürzt mit Rauchfahne ab), Bomben drops=[(t, lat, lon)]."""

    def __init__(self, kind, nation, keys, circles=None, shot=None, drops=None, seed=0, t1=None, phase=None):
        self.kind, self.nation = kind, nation
        self.keys = sorted(keys)
        self.circles = circles or []
        self.shot = shot
        self.drops = drops or []
        rng = np.random.default_rng(seed)
        self.phase = rng.random() * 2 * math.pi if phase is None else phase
        self.dirn = 1 if rng.random() < 0.5 else -1
        self.t0 = self.keys[0][0]
        self.t1 = t1 if t1 is not None else (self.shot + 9.0 if self.shot is not None else self.keys[-1][0])
        self.rng = rng

    def _path(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1], ks[0][2], ks[0][3]
        for (ta, a1, o1, h1), (tb, a2, o2, h2) in zip(ks, ks[1:]):
            if t <= tb:
                s = (t - ta) / max(1e-6, tb - ta)
                return a1 + (a2 - a1) * s, o1 + (o2 - o1) * s, h1 + (h2 - h1) * s
        return ks[-1][1], ks[-1][2], ks[-1][3]

    def pos(self, t):
        la, lo, alt = self._path(t)
        for (c0, c1, cla, clo, r, per) in self.circles:
            if c0 - 2 <= t <= c1 + 2:
                b = smooth((t - (c0 - 2)) / 2.0) * (1 - smooth((t - c1) / 2.0))
                ang = self.phase + self.dirn * 2 * math.pi * (t - c0) / per
                k = math.cos(math.radians(cla))
                pla = cla + (r * math.cos(ang)) / 111320.0
                plo = clo + (r * math.sin(ang)) / (111320.0 * k)
                la, lo = la + (pla - la) * b, lo + (plo - lo) * b
        return la, lo, alt

    def at(self, t):
        """(lat, lon, alt, heading_deg, bank, falling_age)."""
        tt = t
        fall = None
        if self.shot is not None and t > self.shot:
            fall = t - self.shot
            tt = self.shot + (1 - math.exp(-fall / 2.5)) * 2.5      # bremst ab
        la, lo, alt = self.pos(tt)
        la2, lo2, _ = self.pos(tt + 0.2)
        k = math.cos(math.radians(la))
        hd = math.degrees(math.atan2((lo2 - lo) * k, la2 - la)) % 360
        bank = 0.0
        if any(c0 - 1 <= tt <= c1 + 1 for c0, c1, *_ in self.circles):
            bank = 0.55 * self.dirn
        if fall is not None:
            alt = alt * max(0.0, 1 - (fall / 5.5) ** 1.6)
            hd = (hd + fall * 160 * self.dirn) % 360
            bank = 0.9
        return la, lo, alt, hd, bank, fall


class AirWar(Obj):
    """Zeichnet Flugzeuge (Silhouette + Schatten), Leuchtspur im Luftkampf, Rauchfahnen, Abstürze, Bomben."""
    z = 26

    def __init__(self, planes, t0, t1, fights=None, max_width=140.0, size=1.0):
        self.planes, self.t0, self.t1 = planes, t0, t1
        self.fights = fights or []        # [(t0, t1)] Zeitfenster mit Leuchtspur
        self.max_width, self.size = max_width, size
        self.fin, self.fout = 0.8, 1.0

    def _screen(self, v, la, lo, alt):
        p = v.proj(la, lo)
        if p is None:
            return None
        ds = v.depth_scale(la, lo)
        gm = v.cam.width * 1000.0 / W
        up = alt / gm * ds * (0.25 + 0.75 * math.sin(math.radians(max(5.0, v.cam.pitch)))) * 0.9
        return p[0], p[1] - up, ds, p

    def draw(self, c, v, t):
        a = self.alpha(t) * clamp((self.max_width - v.cam.width) / (self.max_width * 0.4))
        if a <= 0:
            return
        gm = v.cam.width * 1000.0 / W
        fighting = any(f0 <= t <= f1 for f0, f1 in self.fights)
        shown = []
        for i, pl in enumerate(self.planes):
            if not (pl.t0 - 0.5 <= t <= pl.t1):
                continue
            pa = a * fade(t, pl.t0, pl.t1, 0.6, 0.8)
            la, lo, alt, hd, bank, fall = pl.at(t)
            s = self._screen(v, la, lo, alt)
            if s is None:
                continue
            x, y, ds, (gx, gy) = s
            if not (-200 < x < W + 200 and -200 < y < H + 200):
                continue
            span = PLANE_DIM[pl.kind]
            px = clamp(span / gm * 2.6 * ds, 10.0, 44.0) * self.size * (1 + alt / max(1.0, v.cam.width * 1000.0) * 0.8)
            # Bildschirm-Richtung aus einem Punkt vor dem Flugzeug
            k = math.cos(math.radians(la))
            ahead = v.proj(la + math.cos(math.radians(hd)) * 0.002, lo + math.sin(math.radians(hd)) * 0.002 / k)
            if ahead is None:
                continue
            ang = math.degrees(math.atan2(ahead[0] - gx, -(ahead[1] - gy)))
            # Rauchfahne beim Absturz
            if fall is not None:
                for j in range(10):
                    tb = t - j * 0.35
                    if tb < pl.shot:
                        break
                    l2, o2, a2, *_ = pl.at(tb)
                    s2 = self._screen(v, l2, o2, a2)
                    if s2 is None:
                        continue
                    soft_circle(c, s2[0], s2[1], px * (0.35 + j * 0.12), skia.Color4f(0.12, 0.11, 0.10, 0.45 * pa * (1 - j / 10)))
                if alt <= 1.0:
                    age = fall - 5.5
                    if age < 1.5:
                        soft_circle(c, gx, gy, px * (1.5 + age * 2), skia.Color4f(1, 0.7, 0.3, 0.9 * pa * (1 - age / 1.5)), skia.BlendMode.kPlus)
                    soft_circle(c, gx, gy, px * 0.5, skia.Color4f(1, 0.45, 0.1, 0.5 * pa * (1 - smooth((age - 8) / 4))), skia.BlendMode.kPlus)
                    for j in range(3):
                        p = (t * 0.3 + j / 3) % 1.0
                        soft_circle(c, gx + p * px, gy - p * px * 3, px * (0.5 + p), skia.Color4f(0.1, 0.09, 0.08, 0.4 * pa * (1 - p)))
                    continue
            # Schatten am Boden
            img = plane_sprite(pl.kind, pl.nation)
            shp = skia.Paint(AntiAlias=True)
            shp.setColorFilter(skia.ColorFilters.Blend(skia.Color4f(0, 0, 0, 1).toColor(), skia.BlendMode.kSrcIn))
            shp.setImageFilter(skia.ImageFilters.Blur(2.0, 2.0))
            spx = px * 0.85
            c.save()
            c.translate(gx, gy)
            c.rotate(ang)
            c.scale(1.0, 0.8)
            shp.setAlphaf(0.30 * pa)
            c.drawImageRect(img, skia.Rect.MakeXYWH(-spx / 2, -spx / 2, spx, spx), E.SAMPLING, shp)
            c.restore()
            # Flugzeug
            c.save()
            c.translate(x, y)
            c.rotate(ang)
            c.scale(max(0.35, math.cos(bank)), 1.0)
            pp = skia.Paint(AntiAlias=True)
            pp.setAlphaf(pa)
            c.drawImageRect(img, skia.Rect.MakeXYWH(-px / 2, -px / 2, px, px), E.SAMPLING, pp)
            # Propellerkreis
            c.drawCircle(0, -px * 0.44, px * 0.16, E.paint(skia.Color4f(0.85, 0.85, 0.8, 0.25 * pa)))
            c.restore()
            shown.append((i, x, y, ang, px, pl, pa))
            for (td, dla, dlo) in pl.drops:
                if td <= t <= td + 2.2:
                    f = (t - td) / 2.2
                    dp = v.proj(dla, dlo)
                    if dp:
                        bx, by = x + (dp[0] - x) * f, y + (dp[1] - y) * f * f
                        c.drawCircle(bx, by, max(1.5, px * 0.06), E.paint(skia.Color4f(0.1, 0.1, 0.1, pa)))
        if fighting and len(shown) > 1:
            rng = np.random.default_rng(int(t * 30) * 977)
            for (i, x, y, ang, px, pl, pa) in shown:
                if pl.shot is not None and t > pl.shot:
                    continue
                if rng.random() < 0.18:
                    # Leuchtspur auf den nächsten Gegner
                    opp = [s for s in shown if (s[5].nation == "de") != (pl.nation == "de")]
                    if not opp:
                        continue
                    j = min(opp, key=lambda s: (s[1] - x) ** 2 + (s[2] - y) ** 2)
                    ex, ey = x + (j[1] - x) * 0.8, y + (j[2] - y) * 0.8
                    c.drawLine(x, y, ex, ey, E.paint(skia.Color4f(1, 0.85, 0.4, 0.75 * pa), "stroke", 1.4))
                    soft_circle(c, x, y, px * 0.25, skia.Color4f(1, 0.9, 0.5, 0.8 * pa), skia.BlendMode.kPlus)


class Parachutes(Obj):
    """Munitionsabwurf an Fallschirmen (Le Hamel): Schirm sinkt von alt_m auf den Boden."""
    z = 25

    def __init__(self, drops, alt=300.0, fall=9.0):
        self.drops, self.alt, self.fall = drops, alt, fall     # [(t, lat, lon)]
        self.t0 = min(d[0] for d in drops)
        self.t1 = max(d[0] for d in drops) + fall + 4
        self.fin, self.fout = 0.3, 0.8

    def draw(self, c, v, t):
        a = self.alpha(t) * clamp((40 - v.cam.width) / 15)
        if a <= 0:
            return
        gm = v.cam.width * 1000.0 / W
        for (td, la, lo) in self.drops:
            f = (t - td) / self.fall
            if f < 0 or f > 1.35:
                continue
            p = v.proj(la, lo)
            if p is None:
                continue
            ds = v.depth_scale(la, lo)
            alt = self.alt * max(0.0, 1 - f)
            up = alt / gm * ds * 0.8
            sway = math.sin(t * 2.2 + td) * 4
            x, y = p[0] + sway, p[1] - up
            r = clamp(9 / gm * 3.0 * ds, 4, 14)
            fa = a * (1 - smooth((f - 1.0) / 0.35))
            if f < 1.0:
                c.drawLine(x, y, x, y + r * 1.6, E.paint(skia.Color4f(0.9, 0.9, 0.9, 0.7 * fa), "stroke", 0.8))
                oval = skia.Rect.MakeXYWH(x - r, y - r * 0.7, 2 * r, 1.4 * r)
                pth = skia.Path()
                pth.addArc(oval, 180, 180)
                pth.close()
                c.drawPath(pth, E.paint(skia.Color4f(0.96, 0.95, 0.9, 0.95 * fa)))
            c.drawRect(skia.Rect.MakeXYWH(x - r * 0.3, y + r * 1.5, r * 0.6, r * 0.5), E.paint(skia.Color4f(0.45, 0.35, 0.2, fa)))


# ====================================================================== Wolken
def _cloud_texture(seed, w=384, h=256):
    rng = np.random.default_rng(seed)
    n = np.zeros((h, w), np.float32)
    for sc, amp in ((40, 1.0), (18, 0.55), (8, 0.3), (3, 0.15)):
        n += ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), sc) * amp * sc
    n = (n - n.mean()) / (n.std() + 1e-6)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # mehrere Kugeln bilden die Grundform
    base = np.zeros((h, w), np.float32)
    for _ in range(int(rng.integers(4, 8))):
        bx, by = rng.uniform(0.25, 0.75) * w, rng.uniform(0.35, 0.65) * h
        br = rng.uniform(0.12, 0.26) * w
        base = np.maximum(base, np.exp(-(((xx - bx) / br) ** 2 + ((yy - by) / (br * 0.75)) ** 2)))
    d = base * 1.25 + n * 0.22 - 0.45
    alpha = np.clip(d * 2.2, 0, 1)
    alpha = ndimage.gaussian_filter(alpha, 2.0)
    # Licht von oben links, Unterseite etwas grauer
    gy, gx = np.gradient(ndimage.gaussian_filter(d, 6))
    lit = np.clip(0.88 + (gy * -2.5 + gx * -1.5) * 8, 0.72, 1.0)
    col = np.stack([lit * 0.98, lit * 0.99, lit * 1.0], -1)
    a = np.zeros((h, w, 4), np.uint8)
    a[..., :3] = np.clip(col * 255, 0, 255).astype(np.uint8)
    a[..., 3] = (alpha * 255).astype(np.uint8)
    return _img(a)


class Clouds(Obj):
    """Wolkenschichten in mehreren Höhen über einem Gebiet. Kamerahöhe ≈ Bildbreite × 0,62.
    Liegt die Kamera über einer Schicht, wird diese perspektivisch vergrößert (Faktor A/(A−h)) – beim Herabzoomen
    wachsen die Wolken, laufen nach außen aus dem Bild oder ziehen durch die Kamera. Schatten der Wolken auf dem Boden."""
    z = 45

    def __init__(self, box, layers, t0, t1, campath=None, seed=7, wind=(0.0, 0.035), shadows=True):
        lat0, lon0, lat1, lon1 = box
        rng = np.random.default_rng(seed)
        self.tex = [_cloud_texture(seed * 13 + i) for i in range(8)]
        self.layers = []
        for (h_km, n, smin, smax, alpha) in layers:
            la = rng.uniform(lat0, lat1, n)
            lo = rng.uniform(lon0, lon1, n)
            size = rng.uniform(smin, smax, n)
            tex = rng.integers(0, len(self.tex), n)
            al = alpha * rng.uniform(0.6, 1.0, n)
            flip = rng.random(n) < 0.5
            self.layers.append((h_km, la, lo, size, tex, al, flip))
        self.box = box
        self.t0, self.t1, self.campath = t0, t1, campath
        self.wind = wind                 # km/s nach Norden, Osten
        self.shadows = shadows
        self.fin, self.fout = 1.0, 1.0

    def activity(self, t):
        if self.campath is None:
            return 1.0
        w0 = self.campath(t - 0.6).width
        w1 = self.campath(t + 0.6).width
        z = abs(math.log(max(w1, 1e-3) / max(w0, 1e-3))) / 1.2
        return smooth(z / 0.18)

    def draw(self, c, v, t):
        a0 = self.alpha(t)
        if a0 <= 0:
            return
        A = v.cam.width * 0.62
        act = self.activity(t)
        lat0, lon0, lat1, lon1 = self.box
        cxs, cys = W / 2, H * 0.46
        gm_km = v.cam.width / W
        for (h_km, la, lo, size, tex, al, flip) in sorted(self.layers, key=lambda L: -L[0]):
            if A <= h_km * 1.02:
                continue
            r = A / h_km
            la_ = lat0 + (la - lat0 + self.wind[0] * t / 111.0) % (lat1 - lat0)
            lo_ = lon0 + (lo - lon0 + self.wind[1] * t / (111.0 * math.cos(math.radians(la.mean())))) % (lon1 - lon0)
            # Sichtbarkeit: weit oben dünn, beim Durchflug (r → 1) weg
            vis = smooth((r - 1.05) / 0.45) * (1 - smooth((r - 9.0) / 9.0))
            if vis <= 0.01:
                continue
            f = A / (A - h_km)
            X, Y = _merc_arr(la_, lo_)
            sx, sy, dz, ok = _proj(v, X, Y)
            # Schatten auf dem Boden (ohne Vergrößerung)
            if self.shadows and a0 * vis > 0.05:
                sp = skia.Paint(AntiAlias=True)
                sp.setColorFilter(skia.ColorFilters.Blend(skia.Color4f(0.02, 0.03, 0.05, 1).toColor(), skia.BlendMode.kSrcIn))
                for i in np.nonzero(ok)[0]:
                    s = size[i] / gm_km * dz[i]
                    x, y = sx[i] + s * 0.25, sy[i] + s * 0.35
                    if x + s < 0 or x - s > W or y + s < 0 or y - s > H or s < 3:
                        continue
                    sp.setAlphaf(0.16 * al[i] * a0 * vis)
                    c.drawImageRect(self.tex[tex[i]], skia.Rect.MakeXYWH(x - s / 2, y - s / 3, s, s * 0.66), E.SAMPLING, sp)
            ca = a0 * vis * (0.30 + 0.70 * act)
            if ca <= 0.01:
                continue
            for i in np.nonzero(ok)[0]:
                x = cxs + (sx[i] - cxs) * f
                y = cys + (sy[i] - cys) * f
                s = size[i] / gm_km * dz[i] * f
                if x + s < 0 or x - s > W or y + s < 0 or y - s > H or s < 4:
                    continue
                p = skia.Paint(AntiAlias=True)
                # sehr große Wolken (direkt vor der Kamera) werden durchsichtiger
                p.setAlphaf(clamp(ca * al[i] * (1 - smooth((s - W * 0.9) / (W * 1.4)))))
                c.save()
                c.translate(x, y)
                if flip[i]:
                    c.scale(-1, 1)
                c.drawImageRect(self.tex[tex[i]], skia.Rect.MakeXYWH(-s / 2, -s / 3, s, s * 0.66), E.SAMPLING, p)
                c.restore()


class Fog(Screen):
    """Bodennebel (Morgen des 8. August): treibende Schleier über dem ganzen Bild."""
    z = 41

    def __init__(self, t0, t1, strength=0.55, fin=2.0, fout=4.0):
        self.t0, self.t1, self.strength = t0, t1, strength
        self.fin, self.fout = fin, fout
        rng = np.random.default_rng(818)
        h, w = 288, 512
        n = np.zeros((h, w), np.float32)
        for sc, amp in ((30, 1.0), (12, 0.5), (5, 0.25)):
            n += ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), sc, mode="wrap") * amp * sc
        n = (n - n.min()) / (n.max() - n.min())
        a = np.zeros((h, w, 4), np.uint8)
        a[..., :3] = (226, 230, 232)
        a[..., 3] = (np.clip(n * 1.3 - 0.15, 0, 1) * 255).astype(np.uint8)
        self.tex = _img(a)

    def draw(self, c, v, t):
        a = self.alpha(t) * self.strength
        if a <= 0:
            return
        c.drawRect(skia.Rect.MakeWH(W, H), E.paint(skia.Color4f(0.82, 0.85, 0.86, 0.35 * a)))
        for k, (spd, sc, al) in enumerate(((14.0, 2.6, 0.75), (-9.0, 3.4, 0.55))):
            tw, th = W * sc / 2.2, H * sc / 2.2
            ox = (t * spd) % tw
            p = skia.Paint()
            p.setAlphaf(clamp(a * al))
            y = -th * 0.3 + k * 60
            x = -ox
            while x < W:
                c.drawImageRect(self.tex, skia.Rect.MakeXYWH(x, y, tw, th), E.SAMPLING, p)
                x += tw


class NightTint(Screen):
    """Nacht: dunkelblau, leicht entsättigt."""
    z = 31

    def __init__(self, t0, t1, strength=0.55, fin=2.0, fout=2.0):
        self.t0, self.t1, self.strength, self.fin, self.fout = t0, t1, strength, fin, fout

    def draw(self, c, v, t):
        a = self.alpha(t) * self.strength
        if a <= 0:
            return
        c.drawRect(skia.Rect.MakeWH(W, H), E.paint(skia.Color4f(0.02, 0.04, 0.10, 0.75 * a)))


# ====================================================================== Westfront 1918 (für Flaggen-Gebiete)
class WFront:
    """Gesamte Westfront zu mehreren Zeitpunkten; line_at(t) liefert die (gemorphte) Linie Nordsee → Schweiz."""

    def __init__(self, states, n=420):
        # states: [(t_start, t_end, pts)] – Übergang zum neuen Verlauf zwischen t_start und t_end
        self.states = [(a, b, E.resample(np.array(p, float), n)) for a, b, p in states]

    def line_at(self, t):
        cur = self.states[0][2]
        key = (0, 1.0)
        for i, (ta, tb, pts) in enumerate(self.states[1:], 1):
            if t >= tb:
                cur, key = pts, (i, 1.0)
            elif t > ta:
                f = E.ease((t - ta) / max(1e-6, tb - ta))
                cur, key = cur + (pts - cur) * f, (i, round(f, 3))
                break
            else:
                break
        return cur, key
