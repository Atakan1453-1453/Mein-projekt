"""Render-Engine: Kamera über Web-Mercator-Karten, Overlays (Flaggen-Zähler, Pfeile, Schiffe …), HUD.

Alle Positionen werden als (Breite, Länge) angegeben. Die Kamera kann geneigt werden
(Pitch, 2,5D-Luftaufnahme) und gedreht (Heading). Gezeichnet wird mit Skia (CPU).
"""
import json
import math
import os
import random

import numpy as np
import skia
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
CACHE = os.environ.get("CNK_CACHE", os.path.join(HERE, "cache"))

W, H = 1920, 1080
FPS = 30
R = 6378137.0
VFOV = math.radians(32)
FOCAL = (H / 2) / math.tan(VFOV / 2)

# Farben
TR_RED = skia.Color4f(0.89, 0.12, 0.13, 1)
AL_BLUE = skia.Color4f(0.22, 0.52, 0.92, 1)
GOLD = skia.Color4f(0.82, 0.68, 0.40, 1)
WHITE = skia.Color4f(1, 1, 1, 1)
INK = skia.Color4f(0.04, 0.055, 0.075, 1)
LOSS = skia.Color4f(1.0, 0.33, 0.27, 1)


def c4(c, a=1.0):
    return skia.Color4f(c.fR, c.fG, c.fB, c.fA * a)


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return skia.Color4f(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


# ------------------------------------------------------------------ Mathe
def merc(lat, lon):
    return R * math.radians(lon), R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease(x):
    """Weiches Ein- und Ausblenden (Sinus)."""
    x = clamp(x)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def fade(t, t0, t1, fin=0.6, fout=0.6):
    if t < t0 or t > t1:
        return 0.0
    a = 1.0
    if fin > 0:
        a = min(a, smooth((t - t0) / fin))
    if fout > 0:
        a = min(a, smooth((t1 - t) / fout))
    return a


def fmt(n):
    return f"{int(round(n)):,}".replace(",", ".")


# ------------------------------------------------------------------ Kamera
class Cam:
    __slots__ = ("lat", "lon", "width", "pitch", "heading")

    def __init__(self, lat, lon, width, pitch=0.0, heading=0.0):
        self.lat, self.lon, self.width, self.pitch, self.heading = lat, lon, width, pitch, heading

    def __repr__(self):
        return f"Cam({self.lat:.4f},{self.lon:.4f},{self.width:.1f}km,p{self.pitch:.0f},h{self.heading:.0f})"


def ground_km(a, b):
    dy = (b.lat - a.lat) * 111.2
    dx = (b.lon - a.lon) * 111.2 * math.cos(math.radians((a.lat + b.lat) / 2))
    return math.hypot(dx, dy)


def interp_cam(a, b, s):
    """Kamerafahrt a→b, s in [0,1] (bereits geglättet). Zoom logarithmisch, Position zoom-gekoppelt.
    Bei weiten Seitwärtsflügen steigt die Kamera in der Mitte etwas auf („Hop“)."""
    w = a.width * (b.width / a.width) ** s
    d = ground_km(a, b)
    m = max(a.width, b.width)
    if d > 0.6 * m:
        w *= 1 + min(2.5, 0.9 * (d / m - 0.6)) * math.sin(math.pi * s)
    w0 = a.width * (b.width / a.width) ** s
    if abs(b.width - a.width) / max(a.width, b.width) > 0.15:
        g = (w0 - a.width) / (b.width - a.width)
    else:
        g = s
    ax, ay = merc(a.lat, a.lon)
    bx, by = merc(b.lat, b.lon)
    x, y = ax + (bx - ax) * g, ay + (by - ay) * g
    lon = math.degrees(x / R)
    lat = math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)
    dh = (b.heading - a.heading + 180) % 360 - 180
    return Cam(lat, lon, w, a.pitch + (b.pitch - a.pitch) * s, a.heading + dh * s)


class CamPath:
    """Keyframes [(t, Cam, ease_kind)] – zwischen zwei Keyframes wird weich interpoliert."""

    def __init__(self, keys):
        self.keys = sorted(keys, key=lambda k: k[0])

    def at(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1]
        for (t0, c0, *_), (t1, c1, *e) in zip(ks, ks[1:]):
            if t <= t1:
                kind = e[0] if e else "ease"
                x = (t - t0) / max(1e-6, t1 - t0)
                s = {"ease": ease, "linear": clamp, "out": ease_out, "smooth": smooth}[kind](x)
                return interp_cam(c0, c1, s)
        return ks[-1][1]


class View:
    """Projektion Mercator → Bildschirm für eine Kamera."""

    def __init__(self, cam):
        self.cam = cam
        cx, cy = merc(cam.lat, cam.lon)
        k = 1.0 / math.cos(math.radians(cam.lat))
        self.width_m = cam.width * 1000.0 * k               # Mercator-Meter über die Bildbreite
        p = math.radians(cam.pitch)
        h = math.radians(cam.heading)
        D = FOCAL * self.width_m / W
        sp, cp = math.sin(p), math.cos(p)
        Hc = np.array([[FOCAL / D, (W / 2) * sp / D, W / 2],
                       [0.0, ((H / 2) * sp - FOCAL * cp) / D, H / 2],
                       [0.0, sp / D, 1.0]])
        ch, sh = math.cos(h), math.sin(h)
        L = np.array([[ch, -sh, -(cx * ch - cy * sh)],
                      [sh, ch, -(cx * sh + cy * ch)],
                      [0.0, 0.0, 1.0]])
        self.M = Hc @ L
        self.mpp = self.width_m / W                          # Mercator-Meter pro Pixel im Zentrum
        self.km_per_px = cam.width / W

    def skmatrix(self, A=None):
        M = self.M if A is None else self.M @ A
        # nicht durch M[2,2] teilen: das kann negativ sein (Ursprung hinter der Kamera) und kehrt das Vorzeichen um
        return skia.Matrix.MakeAll(*[float(v) for v in M.flatten()])

    def unproject(self, sx, sy):
        """Bildschirmpunkt → Mercator (auf dem Boden)."""
        if not hasattr(self, "Minv"):
            self.Minv = np.linalg.inv(self.M)
        X, Y, Z = self.Minv @ np.array([sx, sy, 1.0])
        return X / Z, Y / Z

    def covered_by(self, bounds, margin_px=0.0):
        """Liegt der ganze Bildausschnitt innerhalb der Mercator-Box (x0, y0, x1, y1)?"""
        x0, y0, x1, y1 = bounds
        m = margin_px * self.mpp
        for sx, sy in ((0, 0), (W, 0), (0, H), (W, H), (W / 2, 0)):
            X, Y = self.unproject(sx, sy)
            if not (x0 + m <= X <= x1 - m and y0 + m <= Y <= y1 - m):
                return False
        return True

    def proj_xy(self, x, y):
        M = self.M
        X = M[0, 0] * x + M[0, 1] * y + M[0, 2]
        Y = M[1, 0] * x + M[1, 1] * y + M[1, 2]
        Z = M[2, 0] * x + M[2, 1] * y + M[2, 2]
        if Z <= 1e-6:
            return None
        return X / Z, Y / Z

    def proj(self, lat, lon):
        return self.proj_xy(*merc(lat, lon))

    def depth_scale(self, lat, lon):
        """Wie stark ein Objekt an dieser Stelle perspektivisch verkleinert ist (1 = Bildmitte)."""
        x, y = merc(lat, lon)
        M = self.M
        Z = M[2, 0] * x + M[2, 1] * y + M[2, 2]
        return 1.0 / max(Z, 1e-6)


# ------------------------------------------------------------------ Ressourcen
_FONT_CACHE = {}


def typeface(name, weight=None):
    key = (name, weight)
    if key not in _FONT_CACHE:
        tf = skia.Typeface.MakeFromFile(os.path.join(ASSETS, "fonts", name))
        if weight is not None:
            VP = skia.FontArguments.VariationPosition
            fa = skia.FontArguments()
            fa.setVariationDesignPosition(VP(VP.Coordinates([VP.Coordinate(axis=0x77676874, value=weight)])))
            tf = tf.makeClone(fa)
        _FONT_CACHE[key] = tf
    return _FONT_CACHE[key]


def font(kind, size):
    tf = {
        "title": lambda: typeface("Cinzel[wght].ttf", 700),
        "title_r": lambda: typeface("Cinzel[wght].ttf", 500),
        "cond": lambda: typeface("BarlowCondensed-SemiBold.ttf"),
        "cond_b": lambda: typeface("BarlowCondensed-Bold.ttf"),
        "cond_m": lambda: typeface("BarlowCondensed-Medium.ttf"),
        "body": lambda: typeface("Barlow-Medium.ttf"),
        "body_r": lambda: typeface("Barlow-Regular.ttf"),
    }[kind]()
    f = skia.Font(tf, size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


_FLAG_CACHE = {}


def flag(code):
    if code not in _FLAG_CACHE:
        import cairosvg
        png = cairosvg.svg2png(url=os.path.join(ASSETS, "flags", code + ".svg"), output_width=160, output_height=120)
        img = Image.open(__import__("io").BytesIO(png)).convert("RGBA")
        _FLAG_CACHE[code] = skia.Image.fromarray(np.asarray(img).copy(), colorType=skia.kRGBA_8888_ColorType)
    return _FLAG_CACHE[code]


class MapLayer:
    def __init__(self, name, feather=0):
        meta = json.load(open(os.path.join(CACHE, name + ".json")))
        img = np.asarray(Image.open(os.path.join(CACHE, name + ".jpg")).convert("RGB"))
        h, w, _ = img.shape
        a = np.full((h, w, 1), 255, np.uint8)
        if feather:
            ramp = lambda n: np.clip(np.minimum(np.arange(n), np.arange(n)[::-1]) / feather, 0, 1)
            m = np.outer(ramp(h), ramp(w))
            a = (m * 255).astype(np.uint8)[..., None]
            img = (img.astype(np.float32) * m[..., None]).astype(np.uint8)   # vormultipliziert
        rgba = np.ascontiguousarray(np.concatenate([img, a], 2))
        self.image = skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType,
                                          alphaType=skia.kPremul_AlphaType).withDefaultMipmaps()
        self.A = np.array([[meta["res"], 0, meta["x0"]], [0, -meta["res"], meta["y1"]], [0, 0, 1.0]])
        self.res = meta["res"]
        self.bounds = (meta["x0"], meta["y1"] - meta["h"] * meta["res"], meta["x0"] + meta["w"] * meta["res"], meta["y1"])


SAMPLING = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


# ------------------------------------------------------------------ Zeichenhilfen
def paint(color, style="fill", width=1.0, aa=True, blend=None, blur=0.0):
    p = skia.Paint(Color4f=color, AntiAlias=aa)
    if style == "stroke":
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(width)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blend is not None:
        p.setBlendMode(blend)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def text_width(f, s):
    return f.measureText(s)


def draw_text(c, s, x, y, f, color, align="left", halo=0.0, halo_color=None, spacing=0.0, shadow=True):
    if not s:
        return 0
    if spacing:
        glyph_w = [f.measureText(ch) + spacing for ch in s]
        tw = sum(glyph_w) - spacing
    else:
        tw = f.measureText(s)
    if align == "center":
        x -= tw / 2
    elif align == "right":
        x -= tw

    def _draw(p):
        if spacing:
            xx = x
            for ch, gw in zip(s, glyph_w):
                c.drawString(ch, xx, y, f, p)
                xx += gw
        else:
            c.drawString(s, x, y, f, p)

    if shadow:
        _draw(paint(skia.Color4f(0, 0, 0, 0.55 * color.fA), blur=max(2.0, f.getSize() * 0.08)))
    if halo > 0:
        _draw(paint(halo_color or skia.Color4f(0, 0, 0, 0.75 * color.fA), "stroke", halo))
    _draw(paint(color))
    return tw


def rrect(c, x, y, w, h, r, fill=None, stroke=None, sw=1.5, shadow=0.0):
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
    if shadow > 0:
        c.drawRRect(rr.makeOffset(0, shadow * 0.4), paint(skia.Color4f(0, 0, 0, 0.5 * (fill.fA if fill else 1)), blur=shadow))
    if fill is not None:
        c.drawRRect(rr, paint(fill))
    if stroke is not None:
        c.drawRRect(rr, paint(stroke, "stroke", sw))


def draw_flag(c, code, x, y, w, alpha=1.0):
    h = w * 0.75
    img = flag(code)
    c.save()
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), 3, 3)
    c.clipRRect(rr, True)
    p = skia.Paint(AntiAlias=True)
    p.setAlphaf(alpha)
    c.drawImageRect(img, skia.Rect.MakeXYWH(x, y, w, h), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kNone), p)
    c.restore()
    c.drawRRect(rr, paint(skia.Color4f(1, 1, 1, 0.35 * alpha), "stroke", 1.0))


def catmull(points, n=12):
    """Glatte Kurve durch Bildschirmpunkte."""
    if len(points) < 3:
        if len(points) == 2:
            (x0, y0), (x1, y1) = points
            return [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]
        return points
    pts = [points[0]] + points + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    out.append(points[-1])
    return out


def trim_polyline(pts, frac):
    if frac >= 1:
        return pts
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    total = sum(seg)
    target = total * max(0.0, frac)
    out = [pts[0]]
    acc = 0.0
    for (a, b), L in zip(zip(pts, pts[1:]), seg):
        if acc + L >= target:
            r = (target - acc) / L if L > 0 else 0
            out.append((a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r))
            return out
        out.append(b)
        acc += L
    return out


def path_from(pts):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    return p


# ------------------------------------------------------------------ Overlays
class Obj:
    t0 = 0.0
    t1 = 1e9
    z = 0

    def alpha(self, t):
        return fade(t, self.t0, self.t1, getattr(self, "fin", 0.6), getattr(self, "fout", 0.6))

    def active(self, t):
        return self.t0 <= t <= self.t1


class Label(Obj):
    """Ortsname mit Punkt, Haupttext + Untertitel."""
    z = 5

    def __init__(self, lat, lon, text, sub=None, t0=0, t1=1e9, dx=12, dy=-10, size=26, dot=True, color=None,
                 align="left", style="place"):
        self.lat, self.lon, self.text, self.sub = lat, lon, text, sub
        self.t0, self.t1, self.dx, self.dy, self.size, self.dot = t0, t1, dx, dy, size, dot
        self.color = color or WHITE
        self.align, self.style = align, style

    def draw(self, c, v, t):
        a = self.alpha(t)
        p = v.proj(self.lat, self.lon)
        if a <= 0 or p is None:
            return
        x, y = p
        if self.style == "sea":
            f = font("cond_m", self.size)
            draw_text(c, self.text.upper(), x, y, f, skia.Color4f(0.62, 0.78, 0.86, 0.75 * a), "center", spacing=self.size * 0.25, shadow=False)
            return
        if self.style == "country":
            f = font("title_r", self.size)
            draw_text(c, self.text.upper(), x, y, f, c4(self.color, 0.92 * a), "center", spacing=self.size * 0.12, halo=3, halo_color=skia.Color4f(0, 0, 0, 0.45 * a))
            if self.sub:
                draw_text(c, self.sub, x, y + self.size * 0.95, font("cond_m", self.size * 0.62), skia.Color4f(0.85, 0.85, 0.85, 0.8 * a), "center", halo=2)
            return
        if self.dot:
            c.drawCircle(x, y, 5.5, paint(skia.Color4f(0, 0, 0, 0.6 * a)))
            c.drawCircle(x, y, 4.0, paint(c4(self.color, a)))
        f = font("cond", self.size)
        tx = x + self.dx
        draw_text(c, self.text, tx, y + self.dy, f, c4(self.color, a), self.align, halo=3.5)
        if self.sub:
            fs = font("cond_m", self.size * 0.68)
            draw_text(c, self.sub, tx, y + self.dy + self.size * 0.82, fs, skia.Color4f(0.86, 0.84, 0.78, 0.9 * a), self.align, halo=3)


class Token(Obj):
    """Truppen-Marker: Flagge(n) + Zahl, die bei Kämpfen sinkt (oder steigt)."""
    z = 20

    def __init__(self, lat, lon, flags, keys, label=None, side="tr", t0=0, t1=1e9, dx=0, dy=-70, unit="",
                 show_loss=True, loss_only=False, size=1.0, note=None):
        self.lat, self.lon, self.flags = lat, lon, flags
        self.keys = sorted(keys)  # [(t, value)] – Zahl ändert sich zwischen aufeinanderfolgenden Keys
        self.label, self.side, self.t0, self.t1 = label, side, t0, t1
        self.dx, self.dy, self.unit, self.show_loss, self.loss_only, self.size, self.note = dx, dy, unit, show_loss, loss_only, size, note

    def value(self, t):
        ks = self.keys
        cur, flash, loss = ks[0][1], 0.0, None
        for i in range(1, len(ks)):
            tb, vb = ks[i]
            if t < tb:
                break
            va = ks[i - 1][1]
            x = (t - tb) / 2.2
            cur = va + (vb - va) * ease_out(min(1.0, x * 1.1)) if x < 1 else vb
            if vb < va and x < 1:
                flash = 1 - x
            if vb != va and t - tb < 3.2:
                loss = (va - vb, t - tb)
        return cur, flash, loss

    def draw(self, c, v, t):
        a = self.alpha(t)
        p = v.proj(self.lat, self.lon)
        if a <= 0 or p is None:
            return
        side_c = TR_RED if self.side == "tr" else AL_BLUE
        x, y = p
        s = self.size * (0.92 + 0.08 * ease_out((t - self.t0) / 0.5))
        val, flash, loss = self.value(t)
        # Bodenmarker + Puls
        pulse = (t * 0.8) % 1.0
        c.drawCircle(x, y, 7 + 22 * pulse, paint(c4(side_c, 0.45 * (1 - pulse) * a), "stroke", 2.0))
        c.drawCircle(x, y, 7.5, paint(skia.Color4f(0, 0, 0, 0.6 * a)))
        c.drawCircle(x, y, 6.0, paint(c4(side_c, a)))
        c.drawCircle(x, y, 2.4, paint(skia.Color4f(1, 1, 1, a)))
        # Box
        fw = 46 * s
        gap = 5 * s
        fnum = font("cond_b", 36 * s)
        txt = "" if self.loss_only else (fmt(val) + self.unit)
        tw = fnum.measureText(txt) if txt else -gap
        bw = 12 * s + len(self.flags) * (fw + gap) + tw + 14 * s
        bh = 50 * s
        bx = x + self.dx * s - bw / 2
        by = y + self.dy * s - bh / 2
        # Stiel
        sy = by + bh if by + bh / 2 < y else by
        c.drawLine(x, y - 7 if sy < y else y + 7, x + self.dx * s, sy, paint(skia.Color4f(1, 1, 1, 0.7 * a), "stroke", 1.6))
        bg = skia.Color4f(0.035, 0.05, 0.07, 0.86 * a)
        rrect(c, bx, by, bw, bh, 7 * s, fill=bg, stroke=c4(side_c, 0.95 * a), sw=2.2 * s, shadow=10)
        c.drawRect(skia.Rect.MakeXYWH(bx + 1.5 * s, by + 8 * s, 4 * s, bh - 16 * s), paint(c4(side_c, a)))
        fx = bx + 12 * s
        for code in self.flags:
            draw_flag(c, code, fx, by + (bh - fw * 0.75) / 2, fw, a)
            fx += fw + gap
        if txt:
            col = skia.Color4f(1, 1 - 0.55 * flash, 1 - 0.6 * flash, a)
            draw_text(c, txt, fx + 2 * s, by + bh / 2 + 13 * s, fnum, col, shadow=False)
        if self.label:
            fl = font("cond", 19 * s)
            draw_text(c, self.label.upper(), bx + bw / 2, by - 8 * s, fl, skia.Color4f(0.95, 0.92, 0.84, 0.95 * a), "center", spacing=1.2 * s, halo=3)
        if self.note:
            fl = font("cond_m", 18 * s)
            draw_text(c, self.note, bx + bw / 2, by + bh + 22 * s, fl, skia.Color4f(0.9, 0.9, 0.9, 0.85 * a), "center", halo=3)
        if loss and self.show_loss:
            d, age = loss
            la = a * (1 - smooth((age - 2.2) / 1.0)) * smooth(age / 0.25)
            ff = font("cond_b", 34 * s)
            sign = "−" if d > 0 else "+"
            col = LOSS if d > 0 else skia.Color4f(0.55, 0.95, 0.55, 1)
            draw_text(c, sign + fmt(abs(d)), bx + bw + 10 * s, by + bh / 2 + 12 * s - age * 14 * s, ff, c4(col, la), halo=3)


class LossBadge(Obj):
    """Nur Verluste anzeigen (wenn Stärke unbekannt): Flagge + rotes −Zahl."""
    z = 21

    def __init__(self, lat, lon, flags, loss, t0, t1=1e9, label=None, dx=0, dy=-70, side="tr"):
        self.lat, self.lon, self.flags, self.loss, self.t0, self.t1 = lat, lon, flags, loss, t0, t1
        self.label, self.dx, self.dy, self.side = label, dx, dy, side

    def draw(self, c, v, t):
        a = self.alpha(t)
        p = v.proj(self.lat, self.lon)
        if a <= 0 or p is None:
            return
        x, y = p
        side_c = TR_RED if self.side == "tr" else AL_BLUE
        val = self.loss * ease_out((t - self.t0) / 2.0)
        f = font("cond_b", 34)
        txt = "−" + fmt(val)
        tw = f.measureText(txt)
        bw = 12 + len(self.flags) * 51 + tw + 14
        bx, by = x + self.dx - bw / 2, y + self.dy - 25
        c.drawCircle(x, y, 6.0, paint(c4(side_c, a)))
        sy = by + 50 if by + 25 < y else by
        c.drawLine(x, y - 6 if sy < y else y + 6, x + self.dx, sy, paint(skia.Color4f(1, 1, 1, 0.7 * a), "stroke", 1.6))
        rrect(c, bx, by, bw, 50, 7, fill=skia.Color4f(0.035, 0.05, 0.07, 0.86 * a), stroke=c4(LOSS, a), sw=2.2, shadow=10)
        fx = bx + 12
        for code in self.flags:
            draw_flag(c, code, fx, by + 25 - 17.25, 46, a)
            fx += 51
        draw_text(c, txt, fx + 2, by + 38, f, c4(LOSS, a), shadow=False)
        if self.label:
            draw_text(c, self.label.upper(), bx + bw / 2, by - 8, font("cond", 19), skia.Color4f(0.95, 0.92, 0.84, 0.95 * a), "center", spacing=1.2, halo=3)


class Arrow(Obj):
    """Angriffs-/Bewegungspfeil entlang (lat, lon)-Punkten, wächst ab t0 über `grow` Sekunden."""
    z = 10

    def __init__(self, pts, side="al", t0=0, grow=2.5, t1=1e9, width=16, head=1.0, dashed=False, color=None):
        self.pts, self.side, self.t0, self.grow, self.t1 = pts, side, t0, grow, t1
        self.width, self.head, self.dashed = width, head, dashed
        self.color = color or (TR_RED if side == "tr" else AL_BLUE)
        self.fin = 0.3

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        sp = [v.proj(la, lo) for la, lo in self.pts]
        if any(p is None for p in sp):
            return
        curve = catmull(sp, 16)
        g = ease_out((t - self.t0) / self.grow) if self.grow > 0 else 1
        pts = trim_polyline(curve, g)
        if len(pts) < 2:
            return
        w = self.width
        # Pfeilspitze
        (x1, y1), (x0, y0) = pts[-1], pts[-2] if len(pts) > 1 else pts[-1]
        k = len(pts) - 2
        while k > 0 and math.hypot(x1 - pts[k][0], y1 - pts[k][1]) < w * 1.6:
            k -= 1
        x0, y0 = pts[k]
        ang = math.atan2(y1 - y0, x1 - x0)
        hl, hw = w * 2.0 * self.head, w * 1.55 * self.head
        base = (x1 - math.cos(ang) * hl * 0.9, y1 - math.sin(ang) * hl * 0.9)
        body = trim_polyline(pts, 1.0)
        body = body[:-1] + [base]
        path = path_from(body)
        head = skia.Path()
        head.moveTo(x1 + math.cos(ang) * hl * 0.1, y1 + math.sin(ang) * hl * 0.1)
        head.lineTo(base[0] + math.cos(ang + math.pi / 2) * hw, base[1] + math.sin(ang + math.pi / 2) * hw)
        head.lineTo(base[0] - math.cos(ang) * hl * 0.15, base[1] - math.sin(ang) * hl * 0.15)
        head.lineTo(base[0] - math.cos(ang + math.pi / 2) * hw, base[1] - math.sin(ang + math.pi / 2) * hw)
        head.close()
        col = self.color
        # Schatten/Kontur
        c.drawPath(path, paint(skia.Color4f(0, 0, 0, 0.45 * a), "stroke", w + 6))
        c.drawPath(head, paint(skia.Color4f(0, 0, 0, 0.45 * a), "stroke", 6))
        pb = paint(c4(col, 0.88 * a), "stroke", w)
        if self.dashed:
            pb.setPathEffect(skia.DashPathEffect.Make([w * 1.4, w * 0.9], -t * 40))
            pb.setStrokeCap(skia.Paint.kButt_Cap)
        c.drawPath(path, pb)
        c.drawPath(path, paint(skia.Color4f(1, 1, 1, 0.22 * a), "stroke", max(1.5, w * 0.18)))
        c.drawPath(head, paint(c4(col, 0.95 * a)))


class Polyline(Obj):
    """Frontlinie / Route / Minenreihe als Linie."""
    z = 8

    def __init__(self, pts, color, t0=0, t1=1e9, width=4, grow=0.0, dash=None, glow=False, smooth_n=8, closed=False, fill=None):
        self.pts, self.color, self.t0, self.t1, self.width, self.grow = pts, color, t0, t1, width, grow
        self.dash, self.glow, self.smooth_n, self.closed, self.fill = dash, glow, smooth_n, closed, fill

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        sp = [v.proj(la, lo) for la, lo in self.pts]
        if any(p is None for p in sp):
            return
        pts = catmull(sp, self.smooth_n) if self.smooth_n > 1 else sp
        if self.grow > 0:
            pts = trim_polyline(pts, ease_out((t - self.t0) / self.grow))
        if len(pts) < 2:
            return
        path = path_from(pts)
        if self.closed:
            path.close()
        if self.fill is not None:
            c.drawPath(path, paint(c4(self.fill, a)))
        if self.glow:
            c.drawPath(path, paint(c4(self.color, 0.35 * a), "stroke", self.width * 3.5, blur=6))
        c.drawPath(path, paint(skia.Color4f(0, 0, 0, 0.5 * a), "stroke", self.width + 3))
        p = paint(c4(self.color, a), "stroke", self.width)
        if self.dash:
            p.setPathEffect(skia.DashPathEffect.Make(list(self.dash), -t * 30))
            p.setStrokeCap(skia.Paint.kButt_Cap)
        c.drawPath(path, p)


class Area(Obj):
    """Gefülltes Gebiet (z. B. Brückenkopf) in Lat/Lon."""
    z = 6

    def __init__(self, pts, color, t0=0, t1=1e9, alpha=0.35, outline=True, grow=0.0):
        self.pts, self.color, self.t0, self.t1, self.al, self.outline, self.grow = pts, color, t0, t1, alpha, outline, grow

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        sp = [v.proj(la, lo) for la, lo in self.pts]
        if any(p is None for p in sp):
            return
        g = ease_out((t - self.t0) / self.grow) if self.grow > 0 else 1.0
        if g < 1:
            cx = sum(p[0] for p in sp) / len(sp)
            cy = sum(p[1] for p in sp) / len(sp)
            sp = [(cx + (p[0] - cx) * g, cy + (p[1] - cy) * g) for p in sp]
        path = path_from(catmull(sp + [sp[0]], 6))
        path.close()
        dark = skia.Color4f(self.color.fR * 0.55, self.color.fG * 0.55, self.color.fB * 0.7, 1)
        c.drawPath(path, paint(c4(dark, self.al * a)))
        if self.outline:
            p = paint(c4(self.color, 0.9 * a), "stroke", 2.5)
            p.setPathEffect(skia.DashPathEffect.Make([10, 6], 0))
            c.drawPath(path, p)


def ship_path(L):
    p = skia.Path()
    p.moveTo(L * 0.5, 0)
    p.cubicTo(L * 0.35, -L * 0.12, -L * 0.3, -L * 0.11, -L * 0.5, -L * 0.07)
    p.lineTo(-L * 0.5, L * 0.07)
    p.cubicTo(-L * 0.3, L * 0.11, L * 0.35, L * 0.12, L * 0.5, 0)
    p.close()
    return p


class Ship(Obj):
    """Kriegsschiff, fährt eine Route ab ([(t, lat, lon)]), kann sinken (sink=t) oder beschädigt werden."""
    z = 12

    def __init__(self, route, code="gb", t0=0, t1=1e9, sink=None, damaged=None, name=None, size=30, fire=None, target=None):
        self.code, self.t0, self.t1, self.sink, self.damaged, self.name, self.size = code, t0, t1, sink, damaged, name, size
        self.fire = fire or []   # Zeitfenster [(ta, tb)] mit Mündungsfeuer
        self.target = target     # (lat, lon) – Ziel der Geschütze (Leuchtspur + Einschläge)
        # Route: [(t, lat, lon)]; t=None → Durchfahrtspunkt zwischen zwei Zeitpunkten (gleichmäßige Fahrt)
        self.legs = []
        pend = []
        prev = None
        for (tt, la, lo) in route:
            if tt is None:
                pend.append((la, lo))
                continue
            if prev is not None:
                self.legs.append((prev[0], tt, [(prev[1], prev[2])] + pend + [(la, lo)]))
            pend = []
            prev = (tt, la, lo)
        self.route = [(tt, la, lo) for (tt, la, lo) in route if tt is not None]

    def pos(self, t):
        for (ta, tb, pts) in self.legs:
            if ta <= t <= tb and len(pts) > 2:
                s = ease((t - ta) / max(1e-6, tb - ta))
                seg = [math.hypot(b[0] - a[0], (b[1] - a[1]) * 0.77) for a, b in zip(pts, pts[1:])]
                tot = sum(seg) or 1e-9
                d = s * tot
                for (a, b), L in zip(zip(pts, pts[1:]), seg):
                    if d <= L or (a, b) == (pts[-2], pts[-1]):
                        f = d / L if L > 0 else 0
                        return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, (b[0] - a[0], b[1] - a[1])
                    d -= L
        r = self.route
        if t <= r[0][0]:
            return r[0][1], r[0][2], None
        for (ta, la, lo), (tb, lb, lob) in zip(r, r[1:]):
            if t <= tb:
                s = ease((t - ta) / max(1e-6, tb - ta))
                return la + (lb - la) * s, lo + (lob - lo) * s, (lb - la, lob - lo)
        return r[-1][1], r[-1][2], (r[-1][1] - r[-2][1], r[-1][2] - r[-2][2]) if len(r) > 1 else None

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        lat, lon, d = self.pos(t)
        p = v.proj(lat, lon)
        if p is None:
            return
        x, y = p
        if d is None or (abs(d[0]) + abs(d[1])) < 1e-9:
            d = self.route[-1][1] - self.route[0][1], self.route[-1][2] - self.route[0][2]
            if abs(d[0]) + abs(d[1]) < 1e-9:
                d = (1, 0)
        q = v.proj(lat + d[0] * 0.01, lon + d[1] * 0.01)
        ang = math.atan2(q[1] - y, q[0] - x) if q else 0
        sinking = 0.0
        if self.sink is not None and t >= self.sink:
            sinking = clamp((t - self.sink) / 4.0)
            # Wellenringe
            for k in range(3):
                ph = ((t - self.sink) * 0.6 + k / 3) % 1
                if t - self.sink < 9:
                    c.drawCircle(x, y, 6 + 40 * ph, paint(skia.Color4f(1, 1, 1, 0.5 * (1 - ph) * a), "stroke", 1.6))
            if t - self.sink < 1.2:
                fl = 1 - (t - self.sink) / 1.2
                c.drawCircle(x, y, 30 + 30 * (1 - fl), paint(skia.Color4f(1, 0.75, 0.35, 0.8 * fl * a), blend=skia.BlendMode.kPlus, blur=14))
        alpha = a * (1 - sinking)
        if alpha <= 0.01:
            return
        moving = self.route[-1][0] > t > self.route[0][0]
        c.save()
        c.translate(x, y)
        c.rotate(math.degrees(ang) + sinking * 25)
        L = self.size * (1 - 0.3 * sinking)
        if moving:
            wake = skia.Path()
            wake.moveTo(-L * 0.5, 0)
            wake.lineTo(-L * 2.6, -L * 0.25)
            wake.lineTo(-L * 2.6, L * 0.25)
            wake.close()
            c.drawPath(wake, paint(skia.Color4f(1, 1, 1, 0.18 * alpha), blur=3))
        hull = ship_path(L)
        c.drawPath(hull, paint(skia.Color4f(0, 0, 0, 0.6 * alpha), "stroke", 3.5))
        col = AL_BLUE if self.code != "tr" else TR_RED
        c.drawPath(hull, paint(skia.Color4f(0.78, 0.82, 0.86, alpha)))
        c.drawRect(skia.Rect.MakeXYWH(-L * 0.18, -L * 0.05, L * 0.36, L * 0.1), paint(c4(col, alpha)))
        c.restore()
        for ta, tb in self.fire:
            if ta <= t <= tb and sinking == 0:
                rnd = random.Random(int(t * 7) * 131 + int(self.route[0][2] * 1e4) % 977)
                if rnd.random() < 0.45:
                    c.drawCircle(x + math.cos(ang) * L * 0.4, y + math.sin(ang) * L * 0.4, 10 + rnd.random() * 8,
                                 paint(skia.Color4f(1, 0.85, 0.5, 0.85 * alpha), blend=skia.BlendMode.kPlus, blur=6))
                    if self.target is not None:
                        q2 = v.proj(self.target[0] + rnd.uniform(-0.002, 0.002), self.target[1] + rnd.uniform(-0.003, 0.003))
                        if q2 is not None:
                            pl = paint(skia.Color4f(1, 0.9, 0.6, 0.55 * alpha), "stroke", 1.6, blend=skia.BlendMode.kPlus)
                            c.drawLine(x, y, q2[0], q2[1], pl)
                            c.drawCircle(q2[0], q2[1], 9 + rnd.random() * 10, paint(skia.Color4f(1, 0.6, 0.25, 0.8 * alpha), blend=skia.BlendMode.kPlus, blur=6))
        if self.damaged is not None and t >= self.damaged and sinking == 0:
            rnd = random.Random(int(t * 12))
            for k in range(3):
                ph = ((t * 0.5 + k / 3) % 1)
                c.drawCircle(x - 4 + k * 3 - ph * 6, y - 6 - ph * 26, 5 + ph * 10, paint(skia.Color4f(0.2, 0.2, 0.2, 0.55 * (1 - ph) * alpha), blur=4))
            c.drawCircle(x, y, 6 + rnd.random() * 3, paint(skia.Color4f(1, 0.55, 0.15, 0.7 * alpha), blend=skia.BlendMode.kPlus, blur=4))
        draw_flag(c, self.code, x - 9, y - self.size * 0.55 - 15, 18, alpha)
        if self.name:
            draw_text(c, self.name, x, y + self.size * 0.55 + 18, font("cond", 17), skia.Color4f(1, 1, 1, 0.92 * alpha), "center", halo=3)


class Mines(Obj):
    z = 9

    def __init__(self, pts, t0, t1=1e9, color=None, size=5.0, stagger=0.0, highlight=False):
        self.pts, self.t0, self.t1, self.size, self.stagger, self.highlight = pts, t0, t1, size, stagger, highlight
        self.color = color or skia.Color4f(0.08, 0.08, 0.09, 1)

    def draw(self, c, v, t):
        a0 = self.alpha(t)
        if a0 <= 0:
            return
        n = len(self.pts)
        for i, (la, lo) in enumerate(self.pts):
            a = a0 * smooth((t - self.t0 - i * self.stagger) / 0.4)
            if a <= 0:
                continue
            p = v.proj(la, lo)
            if p is None:
                continue
            x, y = p
            s = self.size
            if self.highlight:
                c.drawCircle(x, y, s * 2.6, paint(skia.Color4f(1, 0.3, 0.2, 0.35 * a), blur=4))
            pk = paint(skia.Color4f(0.9, 0.9, 0.9, 0.8 * a), "stroke", 1.2)
            for k in range(4):
                an = k * math.pi / 4
                c.drawLine(x - math.cos(an) * s * 1.6, y - math.sin(an) * s * 1.6, x + math.cos(an) * s * 1.6, y + math.sin(an) * s * 1.6, pk)
            c.drawCircle(x, y, s, paint(c4(self.color, a)))
            c.drawCircle(x, y, s, paint(skia.Color4f(0.9, 0.9, 0.9, 0.8 * a), "stroke", 1.2))


class Fort(Obj):
    z = 15

    def __init__(self, lat, lon, name, t0=0, t1=1e9, dx=14, dy=-12, sub=None, align="left", fire=None):
        self.lat, self.lon, self.name, self.t0, self.t1, self.dx, self.dy, self.sub, self.align = lat, lon, name, t0, t1, dx, dy, sub, align
        self.fire = fire or []

    def draw(self, c, v, t):
        a = self.alpha(t)
        p = v.proj(self.lat, self.lon)
        if a <= 0 or p is None:
            return
        x, y = p
        s = 11
        star = skia.Path()
        for k in range(5):
            an = -math.pi / 2 + k * 2 * math.pi / 5
            px, py = x + math.cos(an) * s, y + math.sin(an) * s
            star.moveTo(px, py) if k == 0 else star.lineTo(px, py)
        star.close()
        c.drawPath(star, paint(skia.Color4f(0, 0, 0, 0.6 * a), "stroke", 4))
        c.drawPath(star, paint(c4(TR_RED, a)))
        c.drawPath(star, paint(skia.Color4f(1, 1, 1, 0.9 * a), "stroke", 1.6))
        for ta, tb in self.fire:
            if ta <= t <= tb:
                rnd = random.Random(int(t * 6) * 31 + int(self.lat * 1000))
                if rnd.random() < 0.5:
                    c.drawCircle(x + rnd.uniform(-6, 6), y + rnd.uniform(-6, 6), 12 + rnd.random() * 10,
                                 paint(skia.Color4f(1, 0.8, 0.45, 0.9 * a), blend=skia.BlendMode.kPlus, blur=7))
        if self.name:
            draw_text(c, self.name, x + self.dx, y + self.dy, font("cond", 23), skia.Color4f(1, 0.93, 0.88, a), self.align, halo=3)
            if self.sub:
                draw_text(c, self.sub, x + self.dx, y + self.dy + 19, font("cond_m", 16), skia.Color4f(0.86, 0.84, 0.78, 0.9 * a), self.align, halo=3)


class Battle(Obj):
    """Gefechtseffekt: Mündungsfeuer, Einschläge, Rauch rund um einen Punkt."""
    z = 7

    def __init__(self, lat, lon, radius_km, t0, t1, rate=6.0, intensity=1.0, seed=0):
        self.lat, self.lon, self.r, self.t0, self.t1, self.rate, self.intensity, self.seed = lat, lon, radius_km, t0, t1, rate, intensity, seed
        self.fin, self.fout = 1.0, 1.5

    def draw(self, c, v, t):
        a = self.alpha(t) * self.intensity
        p = v.proj(self.lat, self.lon)
        if a <= 0 or p is None:
            return
        cx, cy = p
        rpx = self.r / v.km_per_px * v.depth_scale(self.lat, self.lon) * 1.0
        rpx = max(18, rpx)
        # Rauchschleier
        c.drawCircle(cx, cy, rpx * 1.1, paint(skia.Color4f(0.55, 0.52, 0.48, 0.10 * a), blur=rpx * 0.5))
        life = 0.9
        k0 = int((t - life) * self.rate)
        k1 = int(t * self.rate)
        for k in range(k0, k1 + 1):
            rnd = random.Random(k * 7919 + self.seed * 104729)
            tb = k / self.rate + rnd.random() / self.rate
            age = t - tb
            if age < 0 or age > life:
                continue
            ang = rnd.random() * 2 * math.pi
            dist = math.sqrt(rnd.random()) * rpx
            x, y = cx + math.cos(ang) * dist, cy + math.sin(ang) * dist * 0.75
            f = age / life
            big = rnd.random() < 0.25
            rr = (10 if big else 5) + 26 * f * (1.6 if big else 1)
            c.drawCircle(x, y, rr, paint(skia.Color4f(1, 0.72, 0.35, 0.75 * (1 - f) ** 2 * a), blend=skia.BlendMode.kPlus, blur=6))
            c.drawCircle(x, y, 3 + 4 * (1 - f), paint(skia.Color4f(1, 0.95, 0.8, (1 - f) * a), blend=skia.BlendMode.kPlus))
            c.drawCircle(x - 6 * f, y - 18 * f, 6 + 18 * f, paint(skia.Color4f(0.25, 0.24, 0.23, 0.35 * (1 - f) * a), blur=5))


class Countries(Obj):
    """Bündniskarte 1914/15 (historische Grenzen)."""
    z = 1

    def __init__(self, groups, t0=0, t1=1e9, borders=True):
        self.t0, self.t1, self.borders = t0, t1, borders
        self.groups = []   # (Path in Mercator, Color4f, Stil, t_on)
        for g in groups:
            self.groups.append(g)

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        c.save()
        c.concat(v.skmatrix())
        if LAND_PATH[0] is None:
            LAND_PATH[0] = load_land()
        c.clipPath(LAND_PATH[0], skia.ClipOp.kIntersect, True)
        for path, color, t_on, t_off in self.groups:
            aa = a * fade(t, t_on, t_off, 1.0, 1.0)
            if aa <= 0:
                continue
            c.drawPath(path, paint(c4(color, aa)))
            if self.borders:
                c.drawPath(path, paint(skia.Color4f(1, 1, 1, 0.35 * aa), "stroke", v.mpp * 1.3))
        c.restore()


LAND_PATH = [None]


def load_land():
    data = json.load(open(os.path.join(os.environ.get("CNK_DATA", os.path.join(HERE, "data")), "geo", "ne_50m_land.geojson")))
    p = skia.Path()
    for f in data["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            for ring in poly:
                for i, (lon, lat) in enumerate(ring):
                    x, y = merc(max(-85, min(85, lat)), lon)
                    p.moveTo(x, y) if i == 0 else p.lineTo(x, y)
                p.close()
    return p


def load_countries():
    data = json.load(open(os.path.join(os.environ.get("CNK_DATA", os.path.join(HERE, "data")), "geo", "world_1914.geojson")))
    paths = {}
    for f in data["features"]:
        name = f["properties"].get("NAME") or ""
        geom = f["geometry"]
        if geom is None:
            continue
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        p = paths.setdefault(name, skia.Path())
        for poly in polys:
            for ring in poly:
                first = True
                for lon, lat in ring:
                    lat = max(-85, min(85, lat))
                    x, y = merc(lat, lon)
                    if first:
                        p.moveTo(x, y)
                        first = False
                    else:
                        p.lineTo(x, y)
                p.close()
    return paths


# ------------------------------------------------------------------ Bildschirm-Elemente (HUD)
class Screen(Obj):
    """Basisklasse für Elemente im Bildschirmraum."""
    z = 50


class DateStamp(Screen):
    def __init__(self, date, place, t0, t1, sub=None):
        self.date, self.place, self.t0, self.t1, self.sub = date, place, t0, t1, sub
        self.fin, self.fout = 0.8, 0.8

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        x, y = 70, 92
        slide = (1 - ease_out((t - self.t0) / 0.9)) * -30
        c.drawRect(skia.Rect.MakeXYWH(x + slide, y - 44, 4, 92 if self.sub else 70), paint(c4(GOLD, a)))
        draw_text(c, self.date.upper(), x + 22 + slide, y, font("title", 40), c4(WHITE, a), spacing=2, halo=0)
        draw_text(c, self.place.upper(), x + 24 + slide, y + 34, font("cond", 25), skia.Color4f(0.86, 0.80, 0.66, a), spacing=3)
        if self.sub:
            draw_text(c, self.sub, x + 24 + slide, y + 62, font("cond_m", 21), skia.Color4f(0.85, 0.85, 0.85, 0.85 * a))


class Caption(Screen):
    """Untere Infozeile / Fakten-Einblendung."""

    def __init__(self, lines, t0, t1, pos="br", width=520, title=None, flags=None):
        self.lines, self.t0, self.t1, self.pos, self.width, self.title, self.flags = lines, t0, t1, pos, width, title, flags
        self.fin, self.fout = 0.6, 0.6

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        lh = 34
        h = 30 + (44 if self.title else 0) + lh * len(self.lines)
        w = self.width
        x = W - w - 70 if self.pos.endswith("r") else 70
        y = H - h - 80 if self.pos.startswith("b") else 170
        x += (1 - ease_out((t - self.t0) / 0.7)) * (40 if self.pos.endswith("r") else -40)
        rrect(c, x, y, w, h, 10, fill=skia.Color4f(0.03, 0.045, 0.06, 0.84 * a), stroke=skia.Color4f(1, 1, 1, 0.14 * a), shadow=16)
        c.drawRect(skia.Rect.MakeXYWH(x, y + 14, 4, h - 28), paint(c4(GOLD, a)))
        yy = y + 22
        if self.title:
            draw_text(c, self.title.upper(), x + 26, yy + 26, font("cond_b", 27), c4(GOLD, a), spacing=1.5, shadow=False)
            yy += 44
        for ln in self.lines:
            fl = None
            if isinstance(ln, tuple):
                fl, ln = ln
            xx = x + 26
            if fl:
                for code in fl:
                    draw_flag(c, code, xx, yy + 6, 30, a)
                    xx += 36
                xx += 4
            draw_text(c, ln, xx, yy + 26, font("cond_m", 26), skia.Color4f(0.94, 0.93, 0.9, a), shadow=False)
            yy += lh


class ChapterCard(Screen):
    z = 60

    def __init__(self, num, title, sub, t0, dur=4.0):
        self.num, self.title, self.sub, self.t0, self.t1 = num, title, sub, t0, t0 + dur
        self.fin, self.fout = 0.8, 0.9

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        c.drawRect(skia.Rect.MakeWH(W, H), paint(skia.Color4f(0, 0, 0, 0.45 * a)))
        cy = H / 2
        prog = ease_out((t - self.t0) / 1.6)
        lw = 520 * prog
        c.drawRect(skia.Rect.MakeXYWH(W / 2 - lw / 2, cy + 40, lw, 2), paint(c4(GOLD, a)))
        draw_text(c, f"KAPITEL {self.num}", W / 2, cy - 78, font("cond", 30), c4(GOLD, a), "center", spacing=8)
        draw_text(c, self.title.upper(), W / 2, cy + 18, font("title", 76), c4(WHITE, a), "center", spacing=4 + 3 * (1 - prog))
        if self.sub:
            draw_text(c, self.sub, W / 2, cy + 92, font("cond_m", 32), skia.Color4f(0.88, 0.86, 0.8, a), "center", spacing=2)


class TitleCard(Screen):
    z = 60

    def __init__(self, t0, dur):
        self.t0, self.t1 = t0, t0 + dur
        self.fin, self.fout = 1.5, 1.5

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        c.drawRect(skia.Rect.MakeWH(W, H), paint(skia.Color4f(0, 0, 0, 0.35 * a)))
        prog = ease_out((t - self.t0) / 3.0)
        cy = H / 2 - 10
        draw_text(c, "ÇANAKKALE", W / 2, cy, font("title", 150), c4(WHITE, a), "center", spacing=14 + 10 * (1 - prog))
        lw = 760 * prog
        c.drawRect(skia.Rect.MakeXYWH(W / 2 - lw / 2, cy + 38, lw, 2.5), paint(c4(GOLD, a)))
        draw_text(c, "1915", W / 2, cy + 110, font("title", 64), c4(GOLD, a), "center", spacing=18)
        draw_text(c, "DIE SCHLACHT UM DIE DARDANELLEN", W / 2, cy + 168, font("cond", 34), skia.Color4f(0.9, 0.88, 0.82, a), "center", spacing=9)


class Quote(Screen):
    z = 58

    def __init__(self, lines, author, t0, t1, size=50):
        self.lines, self.author, self.t0, self.t1, self.size = lines, author, t0, t1, size
        self.fin, self.fout = 1.0, 1.0

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        c.drawRect(skia.Rect.MakeWH(W, H), paint(skia.Color4f(0, 0, 0, 0.55 * a)))
        n = len(self.lines)
        lh = self.size * 1.32
        y0 = H / 2 - (n * lh) / 2 + self.size * 0.5
        fl = font("body", self.size)
        x_left = W / 2 - max(fl.measureText(ln) for ln in self.lines) / 2
        draw_text(c, "„", x_left - self.size * 0.9, y0 + self.size * 0.9, font("title", self.size * 2.2), c4(GOLD, 0.9 * a), "center", shadow=False)
        for i, ln in enumerate(self.lines):
            la = a * smooth((t - self.t0 - 0.35 * i) / 0.8)
            draw_text(c, ln, W / 2, y0 + i * lh + self.size * 0.6, font("body", self.size), c4(WHITE, la), "center")
        if self.author:
            draw_text(c, self.author, W / 2, y0 + n * lh + self.size * 1.15, font("cond", 30), c4(GOLD, a), "center", spacing=4)


class Vignette:
    def __init__(self):
        self.k = (H / W) * 1.35
        sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * 0.62,
                                            [skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 0.32), skia.Color4f(0, 0, 0, 0.75)],
                                            [0.0, 0.50, 0.80, 1.0])
        self.p = skia.Paint()
        self.p.setShader(sh)

    def draw(self, c, strength=1.0):
        c.save()
        c.translate(W / 2, H / 2)
        c.scale(1.0, self.k)
        c.translate(-W / 2, -H / 2)
        self.p.setAlphaf(strength)
        hh = H / self.k
        c.drawRect(skia.Rect.MakeXYWH(0, H / 2 - hh / 2, W, hh), self.p)
        c.restore()


# ------------------------------------------------------------------ weitere Effekte
class Explosion(Obj):
    z = 14

    def __init__(self, lat, lon, t, size=1.0):
        self.lat, self.lon, self.t0, self.t1, self.size = lat, lon, t, t + 6, size
        self.fin, self.fout = 0, 0

    def draw(self, c, v, t):
        p = v.proj(self.lat, self.lon)
        if p is None or not (self.t0 <= t <= self.t1):
            return
        x, y = p
        age = t - self.t0
        s = self.size
        if age < 1.2:
            f = age / 1.2
            c.drawCircle(x, y, (40 + 120 * f) * s, paint(skia.Color4f(1, 0.75, 0.4, 0.9 * (1 - f)), blend=skia.BlendMode.kPlus, blur=25 * s))
            c.drawCircle(x, y, (14 + 30 * f) * s, paint(skia.Color4f(1, 0.97, 0.85, 1 - f), blend=skia.BlendMode.kPlus, blur=6))
        if age < 2.0:
            f = age / 2.0
            c.drawCircle(x, y, (20 + 220 * f) * s, paint(skia.Color4f(1, 1, 1, 0.5 * (1 - f)), "stroke", 3))
        for k in range(7):
            rnd = random.Random(k * 97 + int(self.lat * 1e4))
            ang = rnd.random() * 2 * math.pi
            sp = (30 + rnd.random() * 50) * s
            f = clamp(age / 6.0)
            r = (18 + 40 * f) * s
            c.drawCircle(x + math.cos(ang) * sp * f, y + math.sin(ang) * sp * f * 0.6 - 60 * f * s, r,
                         paint(skia.Color4f(0.18, 0.17, 0.16, 0.55 * (1 - f)), blur=10 * s))


class Fire(Obj):
    """Brennendes Buschland / Feuerzone."""
    z = 7

    def __init__(self, lat, lon, radius_km, t0, t1):
        self.lat, self.lon, self.r, self.t0, self.t1 = lat, lon, radius_km, t0, t1
        self.fin, self.fout = 2.0, 2.0

    def draw(self, c, v, t):
        a = self.alpha(t)
        p = v.proj(self.lat, self.lon)
        if a <= 0 or p is None:
            return
        cx, cy = p
        rpx = max(20, self.r / v.km_per_px * v.depth_scale(self.lat, self.lon))
        for k in range(14):
            rnd = random.Random(k * 31 + 7)
            ang = rnd.random() * 2 * math.pi
            d = math.sqrt(rnd.random()) * rpx
            fl = 0.6 + 0.4 * math.sin(t * (3 + rnd.random() * 4) + k)
            x, y = cx + math.cos(ang) * d, cy + math.sin(ang) * d * 0.7
            c.drawCircle(x, y, rpx * 0.22 * fl, paint(skia.Color4f(1, 0.45, 0.1, 0.35 * a * fl), blend=skia.BlendMode.kPlus, blur=rpx * 0.12))
            ph = (t * 0.25 + rnd.random()) % 1
            c.drawCircle(x - ph * rpx * 0.2, y - ph * rpx * 0.9, rpx * (0.12 + 0.25 * ph), paint(skia.Color4f(0.2, 0.19, 0.18, 0.35 * a * (1 - ph)), blur=rpx * 0.1))


class Searchlight(Obj):
    z = 4

    def __init__(self, lat, lon, t0, t1, base_deg, sweep=35, speed=0.3, length_km=6.0):
        self.lat, self.lon, self.t0, self.t1, self.base, self.sweep, self.speed, self.len = lat, lon, t0, t1, base_deg, sweep, speed, length_km
        self.fin, self.fout = 1.0, 1.0

    def draw(self, c, v, t):
        a = self.alpha(t)
        p = v.proj(self.lat, self.lon)
        if a <= 0 or p is None:
            return
        ang = math.radians(self.base + self.sweep * math.sin(t * self.speed * 2 * math.pi + self.lat * 100))
        dlat = self.len / 111.0 * math.cos(ang)
        dlon = self.len / (111.0 * math.cos(math.radians(self.lat))) * math.sin(ang)
        q = v.proj(self.lat + dlat, self.lon + dlon)
        if q is None:
            return
        x0, y0 = p
        x1, y1 = q
        L = math.hypot(x1 - x0, y1 - y0)
        wdt = L * 0.13
        nx, ny = -(y1 - y0) / max(L, 1), (x1 - x0) / max(L, 1)
        path = skia.Path()
        path.moveTo(x0, y0)
        path.lineTo(x1 + nx * wdt, y1 + ny * wdt)
        path.lineTo(x1 - nx * wdt, y1 - ny * wdt)
        path.close()
        sh = skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)],
                                           [skia.Color4f(1, 0.97, 0.85, 0.45 * a), skia.Color4f(1, 0.97, 0.85, 0)])
        pp = skia.Paint(AntiAlias=True)
        pp.setShader(sh)
        pp.setBlendMode(skia.BlendMode.kPlus)
        c.drawPath(path, pp)
        c.drawCircle(x0, y0, 6, paint(skia.Color4f(1, 1, 0.9, 0.9 * a), blend=skia.BlendMode.kPlus, blur=4))


class MeasureLine(Obj):
    z = 16

    def __init__(self, a, b, text, t0, t1, grow=1.2, offset=(0, -16)):
        self.a, self.b, self.text, self.t0, self.t1, self.grow, self.offset = a, b, text, t0, t1, grow, offset

    def draw(self, c, v, t):
        al = self.alpha(t)
        pa, pb = v.proj(*self.a), v.proj(*self.b)
        if al <= 0 or pa is None or pb is None:
            return
        g = ease_out((t - self.t0) / self.grow)
        mx, my = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
        xa, ya = mx + (pa[0] - mx) * g, my + (pa[1] - my) * g
        xb, yb = mx + (pb[0] - mx) * g, my + (pb[1] - my) * g
        c.drawLine(xa, ya, xb, yb, paint(skia.Color4f(0, 0, 0, 0.5 * al), "stroke", 5))
        c.drawLine(xa, ya, xb, yb, paint(c4(GOLD, al), "stroke", 2.5))
        L = max(1, math.hypot(xb - xa, yb - ya))
        nx, ny = -(yb - ya) / L * 9, (xb - xa) / L * 9
        for x, y in ((xa, ya), (xb, yb)):
            c.drawLine(x - nx, y - ny, x + nx, y + ny, paint(c4(GOLD, al), "stroke", 2.5))
        draw_text(c, self.text, mx + self.offset[0], my + self.offset[1], font("cond_b", 30), c4(WHITE, al), "center", halo=4)


class Snow(Screen):
    z = 40

    def __init__(self, t0, t1, n=320):
        self.t0, self.t1, self.n = t0, t1, n
        self.fin, self.fout = 2.0, 2.0

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        c.drawRect(skia.Rect.MakeWH(W, H), paint(skia.Color4f(0.55, 0.65, 0.8, 0.16 * a)))
        for i in range(self.n):
            rnd = random.Random(i)
            sp = 60 + rnd.random() * 140
            x = (rnd.random() * W + t * (90 + rnd.random() * 80) + math.sin(t * 1.3 + i) * 20) % W
            y = (rnd.random() * H + t * sp) % H
            r = 1.2 + rnd.random() * 2.6
            c.drawCircle(x, y, r, paint(skia.Color4f(1, 1, 1, (0.45 + 0.4 * rnd.random()) * a), blur=0.8))


class Tint(Screen):
    """Farbstimmung über der Karte (Nacht, Morgengrauen …)."""
    z = 30

    def __init__(self, color, t0, t1, fin=1.5, fout=1.5):
        self.color, self.t0, self.t1, self.fin, self.fout = color, t0, t1, fin, fout

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a > 0:
            c.drawRect(skia.Rect.MakeWH(W, H), paint(c4(self.color, a)))


class BattleMarker(Obj):
    """Schlachtmarker für die Übersichtskarte: gekreuzte Schwerter, Name, Datum/Ergebnis, Flaggen beider Seiten."""
    z = 22

    def __init__(self, lat, lon, name, date, flags_tr, flags_al, t0, t1=1e9, dx=0, dy=-62, result=None):
        self.lat, self.lon, self.name, self.date, self.t0, self.t1, self.dx, self.dy = lat, lon, name, date, t0, t1, dx, dy
        self.flags_tr, self.flags_al, self.result = flags_tr, flags_al, result

    def draw(self, c, v, t):
        a = self.alpha(t)
        p = v.proj(self.lat, self.lon)
        if a <= 0 or p is None:
            return
        x, y = p
        s = 0.85 + 0.15 * ease_out((t - self.t0) / 0.4)
        c.drawCircle(x, y, 15 * s, paint(skia.Color4f(0.03, 0.04, 0.06, 0.85 * a)))
        c.drawCircle(x, y, 15 * s, paint(c4(GOLD, a), "stroke", 2))
        ps = paint(skia.Color4f(1, 1, 1, a), "stroke", 2.4)
        c.drawLine(x - 8 * s, y - 8 * s, x + 8 * s, y + 8 * s, ps)
        c.drawLine(x + 8 * s, y - 8 * s, x - 8 * s, y + 8 * s, ps)
        f1 = font("cond_b", 21)
        f2 = font("cond_m", 17)
        fw = 26
        nflags = len(self.flags_tr) + len(self.flags_al)
        flags_w = nflags * (fw + 3) + 14
        sub = self.date + (" · " + self.result if self.result else "")
        tw = max(f1.measureText(self.name), f2.measureText(sub)) + flags_w + 26
        bh = 50
        bx, by = x + self.dx - tw / 2, y + self.dy - bh / 2
        sy = by + bh if by + bh / 2 < y else by
        c.drawLine(x, y - 15 if sy < y else y + 15, x + self.dx, sy, paint(skia.Color4f(1, 1, 1, 0.5 * a), "stroke", 1.3))
        rrect(c, bx, by, tw, bh, 6, fill=skia.Color4f(0.03, 0.045, 0.06, 0.86 * a), stroke=skia.Color4f(1, 1, 1, 0.18 * a), shadow=8)
        fx = bx + 10
        for code in self.flags_tr:
            draw_flag(c, code, fx, by + 8, fw, a)
            fx += fw + 3
        fx += 8
        for code in self.flags_al:
            draw_flag(c, code, fx, by + 8, fw, a)
            fx += fw + 3
        tx = bx + flags_w + 14
        draw_text(c, self.name, tx, by + 22, f1, c4(WHITE, a), shadow=False)
        draw_text(c, sub, tx, by + 42, f2, skia.Color4f(0.85, 0.80, 0.68, a), shadow=False)


class BilanzPanel(Screen):
    """Abschlusstafel: eingesetzte Soldaten und Gefallene je Nation, Zahlen zählen hoch."""
    z = 55

    def __init__(self, t0, t1, rows, head=None):
        self.t0, self.t1, self.rows, self.head = t0, t1, rows, head
        self.fin, self.fout = 0.8, 1.0

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        w = 700
        x = W - w - 60
        n = len(self.rows)
        h = 110 + n * 64
        y = (H - h) / 2 + 20
        rrect(c, x, y, w, h, 12, fill=skia.Color4f(0.025, 0.035, 0.05, 0.9 * a), stroke=skia.Color4f(1, 1, 1, 0.15 * a), shadow=20)
        draw_text(c, (self.head or "GEFALLENE 1915/16").upper(), x + 32, y + 52, font("cond_b", 30), c4(GOLD, a), spacing=3, shadow=False)
        c.drawRect(skia.Rect.MakeXYWH(x + 32, y + 70, w - 64, 1.5), paint(skia.Color4f(1, 1, 1, 0.2 * a)))
        yy = y + 96
        for (codes, name, value, note, tv) in self.rows:
            ra = a * smooth((t - tv) / 0.6)
            if ra > 0:
                xx = x + 32
                for code in codes:
                    draw_flag(c, code, xx, yy + 4, 44, ra)
                    xx += 50
                draw_text(c, name, x + 150, yy + 26, font("cond", 28), c4(WHITE, ra), shadow=False)
                if note:
                    draw_text(c, note, x + 150, yy + 50, font("cond_m", 19), skia.Color4f(0.8, 0.78, 0.72, ra), shadow=False)
                val = value * ease_out((t - tv) / 2.0)
                draw_text(c, fmt(val), x + w - 32, yy + 34, font("cond_b", 40), c4(WHITE if codes[0] != "tr" else skia.Color4f(1, 0.82, 0.8, 1), ra), "right", shadow=False)
            yy += 64


class Credits(Screen):
    z = 70

    def __init__(self, t0, t1, lines):
        self.t0, self.t1, self.lines = t0, t1, lines
        self.fin, self.fout = 1.5, 2.0

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        c.drawRect(skia.Rect.MakeWH(W, H), paint(skia.Color4f(0.01, 0.012, 0.016, 0.88 * a)))
        draw_text(c, "ÇANAKKALE 1915", W / 2, 300, font("title", 84), c4(WHITE, a), "center", spacing=8)
        c.drawRect(skia.Rect.MakeXYWH(W / 2 - 220, 336, 440, 2), paint(c4(GOLD, a)))
        draw_text(c, "Im Gedenken an alle Gefallenen beider Seiten", W / 2, 392, font("cond_m", 34), skia.Color4f(0.9, 0.88, 0.82, a), "center", spacing=1.5)
        y = 500
        for ln in self.lines:
            draw_text(c, ln, W / 2, y, font("cond_m", 23), skia.Color4f(0.75, 0.74, 0.70, a), "center", shadow=False)
            y += 36


# ------------------------------------------------------------------ Flaggenkarte (Länder mit ihrer Flagge gefüllt)
_FLAGIMG = {}


def _svg_image(path, w=1600, h=1200):
    import cairosvg
    png = cairosvg.svg2png(url=path, output_width=w, output_height=h)
    img = Image.open(__import__("io").BytesIO(png)).convert("RGBA")
    return np.asarray(img).copy()


def _stripes(colors, w=1600, h=1200, vertical=False):
    a = np.zeros((h, w, 4), np.uint8)
    n = len(colors)
    for i, c in enumerate(colors):
        c = [int(c[k:k + 2], 16) for k in (1, 3, 5)] + [255]
        if vertical:
            a[:, i * w // n:(i + 1) * w // n] = c
        else:
            a[i * h // n:(i + 1) * h // n] = c
    return a


def flag_texture(key):
    """Flaggenbild (skia.Image) für die Bündniskarte 1914/15."""
    if key in _FLAGIMG:
        return _FLAGIMG[key]
    F = os.path.join(ASSETS, "flags")
    if key == "de1871":
        a = _stripes(["#000000", "#ffffff", "#dd0000"])
    elif key == "ah1869":
        a = np.asarray(Image.open(os.path.join(ASSETS, "emblems", "ah_flag.png")).convert("RGBA").resize((1460, 860), Image.LANCZOS)).copy()
    elif key == "ru1914":
        # Nationalflagge weiß-blau-rot mit gelbem Kanton und Zarenadler (1914–1917)
        w, h = 1800, 1200
        a = _stripes(["#ffffff", "#0039a6", "#d52b1e"], w, h)
        cw, ch = int(w * 0.40), int(h * 0.62)
        a[:ch, :cw] = [255, 204, 51, 255]
        eagle = Image.open(os.path.join(ASSETS, "emblems", "russia_eagle.png")).convert("RGBA")
        ew = int(ch * 0.94 * eagle.size[0] / eagle.size[1])
        eagle = eagle.resize((ew, int(ch * 0.94)), Image.LANCZOS)
        img = Image.fromarray(a)
        img.paste(eagle, ((cw - ew) // 2, int(ch * 0.03)), eagle)
        a = np.asarray(img).copy()
    else:
        a = _svg_image(os.path.join(F, key + ".svg"))
    img = skia.Image.fromarray(np.ascontiguousarray(a), colorType=skia.kRGBA_8888_ColorType).withDefaultMipmaps()
    _FLAGIMG[key] = img
    return img


class FlagCountries(Obj):
    """Bündniskarte im Stil einer Flaggenkarte: Länder mit ihrer Flagge gefüllt, Rand in Bündnisfarbe."""
    z = 1

    def __init__(self, entries, t0=0, t1=1e9, alpha=0.9):
        # entries: dict(path, flag|None, rect=(lat0, lon0, lat1, lon1)|None, base=Color4f|None, side, t_on, t_off)
        self.entries, self.t0, self.t1, self.al = entries, t0, t1, alpha
        self.fin, self.fout = 1.0, 1.0

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        if LAND_PATH[0] is None:
            LAND_PATH[0] = load_land()
        c.save()
        c.concat(v.skmatrix())
        for e in self.entries:
            aa = a * fade(t, e["t_on"], e.get("t_off", 1e9), 1.0, 1.0)
            if aa <= 0:
                continue
            c.save()
            c.clipPath(LAND_PATH[0], skia.ClipOp.kIntersect, True)
            c.clipPath(e["path"], skia.ClipOp.kIntersect, True)
            if e.get("base") is not None:
                c.drawPath(e["path"], paint(c4(e["base"], self.al * aa)))
            if e.get("flag"):
                img = flag_texture(e["flag"])
                if e.get("rect"):
                    la0, lo0, la1, lo1 = e["rect"]
                    x0, y0 = merc(la0, lo0)
                    x1, y1 = merc(la1, lo1)
                    rect = skia.Rect.MakeLTRB(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
                else:
                    rect = e["path"].getBounds()
                p = skia.Paint(AntiAlias=True)
                p.setAlphaf(self.al * aa)
                # Mercator-y zeigt nach oben → Bild vertikal spiegeln
                c.save()
                c.translate(0, rect.top() + rect.bottom())
                c.scale(1, -1)
                c.drawImageRect(img, skia.Rect.MakeWH(img.width(), img.height()), rect, SAMPLING, p)
                c.restore()
            c.restore()
            col = TR_RED if e.get("side") == "cp" else AL_BLUE if e.get("side") == "en" else skia.Color4f(0.8, 0.8, 0.8, 1)
            c.drawPath(e["path"], paint(skia.Color4f(0, 0, 0, 0.75 * aa), "stroke", v.mpp * 3.2))
            if e.get("side") in ("cp", "en"):
                c.drawPath(e["path"], paint(c4(col, 0.9 * aa), "stroke", v.mpp * 1.6))
        c.restore()


def thrace_path():
    """Osmanisches Ostthrakien 1913–1915 (fehlt im Grenzdatensatz): Maritza von Enez bis nördlich Edirne,
    dann entlang der Grenze zum Schwarzen Meer; Küsten werden über die Landmaske beschnitten."""
    pts = [(40.72, 26.03), (40.86, 26.02), (41.10, 26.32), (41.33, 26.49), (41.60, 26.58), (41.71, 26.36), (41.80, 26.44),
           (41.88, 26.75), (41.95, 27.05), (41.98, 27.50), (42.02, 27.85), (41.99, 28.05), (41.70, 28.40), (41.30, 29.15),
           (40.95, 29.05), (40.62, 28.10), (40.38, 27.20), (40.30, 26.80), (40.10, 26.42), (39.95, 26.14), (40.15, 25.95),
           (40.45, 25.95), (40.72, 26.03)]
    p = skia.Path()
    for i, (la, lo) in enumerate(pts):
        x, y = merc(la, lo)
        p.moveTo(x, y) if i == 0 else p.lineTo(x, y)
    p.close()
    return p


# ------------------------------------------------------------------ Gebietskontrolle (leicht eingefärbt)
_LANDMASK = {}


def landmask_layer():
    """Landmaske der Halbinsel-Karte als Bild (weiß, Alpha = Land), passend zum L3-Raster."""
    if "img" in _LANDMASK:
        return _LANDMASK["img"], _LANDMASK["A"]
    meta = json.load(open(os.path.join(CACHE, "sat_L3.json")))
    dem = np.load(os.path.join(CACHE, "dem_L3.npy")).astype(np.float32)
    k = 4
    h, w = dem.shape[0] // k, dem.shape[1] // k
    land = (dem[:h * k, :w * k] > 1.0).reshape(h, k, w, k).mean((1, 3))
    from scipy import ndimage
    land = ndimage.gaussian_filter(land, 0.8)
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = np.clip(land * 255, 0, 255).astype(np.uint8)
    img = skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType).withDefaultMipmaps()
    A = np.array([[meta["res"] * k, 0, meta["x0"]], [0, -meta["res"] * k, meta["y1"]], [0, 0, 1.0]])
    _LANDMASK["img"], _LANDMASK["A"] = img, A
    return img, A


class ControlMap(Obj):
    """Osmanisch gehaltenes Land ganz leicht rot, alliierte Brückenköpfe ganz leicht blau."""
    z = 3

    def __init__(self, t0, t1, areas, strength=0.20):
        self.t0, self.t1, self.areas, self.strength = t0, t1, areas, strength   # areas: [(pts, t_on, t_off)]
        self.fin, self.fout = 2.0, 2.0
        self._paths = None

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0 or v.cam.width > 400:
            return
        img, A = landmask_layer()
        lp = skia.Paint()
        lp.setAlphaf(self.strength * a)
        c.saveLayer(None, lp)
        p = skia.Paint()
        p.setColorFilter(skia.ColorFilters.Blend(skia.Color4f(0.93, 0.16, 0.14, 1).toColor(), skia.BlendMode.kSrcIn))
        c.save()
        c.concat(v.skmatrix(A))
        c.drawImage(img, 0, 0, SAMPLING, p)
        c.restore()
        for pts, t_on, t_off in self.areas:
            aa = fade(t, t_on, t_off, 1.5, 1.5)
            if aa <= 0:
                continue
            sp = [v.proj(la, lo) for la, lo in pts]
            if any(q is None for q in sp):
                continue
            path = path_from(catmull(sp + [sp[0]], 6))
            path.close()
            bp = paint(skia.Color4f(0.25, 0.55, 1.0, aa), blend=skia.BlendMode.kSrcATop)
            c.drawPath(path, bp)
        c.restore()


# ------------------------------------------------------------------ Truppen als Figuren (1 Figur = 1 Soldat)
class Unit:
    """Ein Verband: n Figuren in Formation, bewegt sich entlang keys [(t, lat, lon)], verliert Figuren bei losses [(t, k)]."""

    def __init__(self, side, n, keys, facing=0.0, area=55.0, aspect=2.5, losses=None, fire=None, nation=None, t0=None, t1=1e9, seed=0,
                 arrive=None):
        self.side, self.n, self.keys, self.facing = side, int(n), sorted(keys), facing
        self.losses, self.fire, self.nation = losses or [], fire or [], nation
        self.t0 = self.keys[0][0] if t0 is None else t0
        self.t1 = t1
        self.arrive = arrive          # Figuren erscheinen gestaffelt über so viele Sekunden (Nachschub/Landung)
        rng = np.random.default_rng(seed + 17 * self.n)
        W = math.sqrt(self.n * area * aspect)
        D = self.n * area / W
        u = rng.random((self.n, 2))
        # Formation: Reihen mit leichtem Versatz und Zufall
        self.off = np.stack([(u[:, 0] - 0.5) * W, (u[:, 1] - 0.5) * D], 1)
        self.off += rng.normal(0, 2.0, self.off.shape)
        self.var = rng.random(self.n)
        self.appear = rng.random(self.n)
        # Fallzeitpunkte: Verluste verteilen sich über 2,4 s ab dem jeweiligen Zeitpunkt
        self.tfall = np.full(self.n, np.inf)
        order = rng.permutation(self.n)
        # vordere Reihen fallen zuerst
        front = np.argsort(-self.off[:, 1] + rng.normal(0, D * 0.25, self.n))
        idx = 0
        for (tl, k) in sorted(self.losses):
            k = int(min(k, self.n - idx))
            sel = front[idx:idx + k]
            self.tfall[sel] = tl + rng.random(k) ** 0.8 * 2.4
            idx += k

    def center(self, t):
        ks = self.keys
        tt = np.atleast_1d(np.asarray(t, dtype=np.float64))
        la = np.full(tt.shape, ks[0][1])
        lo = np.full(tt.shape, ks[0][2])
        for (ta, a1, o1), (tb, a2, o2) in zip(ks, ks[1:]):
            m = (tt >= ta) & (tt <= tb)
            if m.any():
                s = (tt[m] - ta) / max(1e-6, tb - ta)
                s = s * s * (3 - 2 * s)
                la[m] = a1 + (a2 - a1) * s
                lo[m] = o1 + (o2 - o1) * s
        last = tt > ks[-1][0]
        la[last], lo[last] = ks[-1][1], ks[-1][2]
        return la, lo

    def merc_positions(self, lat, lon):
        """Formation um Mittelpunkt(e) – lat/lon Skalar oder Arrays je Figur."""
        cx = R * np.radians(lon)
        cy = R * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
        k = 1.0 / np.cos(np.radians(np.mean(lat)))
        h = math.radians(self.facing)
        ox, oy = self.off[:, 0], self.off[:, 1]
        # facing = Marschrichtung (0 = Nord); x quer, y nach vorn
        ex, ey = math.cos(h), -math.sin(h)
        fx, fy = math.sin(h), math.cos(h)
        return cx + (ox * ex + oy * fx) * k, cy + (ox * ey + oy * fy) * k


_TROOP_STAMPS = {
    # (dx, dy, Helligkeitsfaktor) – kleine Soldatenfigur: Kopf + Körper
    1: [(0, 0, 1.0), (0, -1, 1.15)],
    2: [(0, 0, 1.0), (0, -1, 1.0), (0, -2, 1.25), (1, 0, 0.75)],
    3: [(0, 0, 1.0), (0, -1, 1.0), (0, -2, 1.0), (0, -3, 1.3), (1, -1, 0.8), (-1, -1, 0.8), (1, 0, 0.7)],
    4: [(0, 0, 1.0), (1, 0, 0.8), (0, -1, 1.0), (1, -1, 0.85), (0, -2, 1.0), (1, -2, 0.85), (0, -3, 1.0), (-1, -2, 0.8),
        (2, -2, 0.8), (0, -4, 1.3), (1, -4, 1.2), (0, -5, 1.25)],
}
_FALLEN = [(0, 0, 1.0), (1, 0, 1.0), (2, 0, 0.9), (-1, 0, 0.9)]

SIDE_RGB = {"tr": (225, 38, 36), "gb": (60, 125, 235), "fr": (120, 165, 255), "au": (60, 175, 225), "nz": (40, 150, 200)}


class Troops(Obj):
    """Zeichnet alle Verbände einer Szene als Figuren; Mündungsfeuer, Leuchtspuren zwischen Gegnern."""
    z = 18

    def __init__(self, units, t0, t1, enemies=None):
        self.units, self.t0, self.t1 = units, t0, t1
        self.enemies = enemies or []   # Paare (i, j) von Verbänden, die sich beschießen
        self.fin, self.fout = 0.8, 1.2
        self.buf = np.zeros((H, W, 4), np.uint8)

    def _project(self, v, X, Y):
        M = v.M
        Xs = M[0, 0] * X + M[0, 1] * Y + M[0, 2]
        Ys = M[1, 0] * X + M[1, 1] * Y + M[1, 2]
        Zs = M[2, 0] * X + M[2, 1] * Y + M[2, 2]
        ok = Zs > 1e-6
        Zs = np.where(ok, Zs, 1.0)
        return Xs / Zs, Ys / Zs, 1.0 / Zs, ok

    def _splat(self, xs, ys, cls, rgb, alpha, stamps):
        buf = self.buf
        xi = np.round(xs).astype(np.int32)
        yi = np.round(ys).astype(np.int32)
        for (dx, dy, f) in stamps:
            px, py = xi + dx, yi + dy
            m = (px >= 0) & (px < W) & (py >= 0) & (py < H)
            if not m.any():
                continue
            col = np.clip(np.array(rgb, np.float32) * f, 0, 255)
            buf[py[m], px[m], 0] = col[0]
            buf[py[m], px[m], 1] = col[1]
            buf[py[m], px[m], 2] = col[2]
            buf[py[m], px[m], 3] = int(255 * alpha)

    def draw(self, c, v, t):
        a = self.alpha(t)
        if a <= 0:
            return
        buf = self.buf
        buf[:] = 0
        gm = (v.cam.width * 1000.0) / W          # Boden-Meter pro Pixel (Bildmitte)
        flashes = []
        stand_xy = {}
        for ui, u in enumerate(self.units):
            if not (u.t0 <= t <= u.t1):
                continue
            ua = a * fade(t, u.t0, u.t1, 0.8, 1.0)
            vis = np.ones(u.n, bool)
            if u.arrive:
                vis = u.appear * u.arrive <= (t - u.t0)
            standing = (u.tfall > t) & vis
            fallen = (u.tfall <= t) & vis
            lat, lon = u.center(t)
            X, Y = u.merc_positions(lat[0], lon[0])
            xs, ys, dz, ok = self._project(v, X, Y)
            size = 7.5 / gm * dz
            rgb = SIDE_RGB.get(u.nation or u.side, (200, 200, 200))
            for cls, lo_, hi_ in ((1, 0, 2.2), (2, 2.2, 3.6), (3, 3.6, 5.5), (4, 5.5, 99)):
                m = standing & ok & (size >= lo_) & (size < hi_)
                if m.any():
                    # leichtes Wippen beim Vormarsch
                    bob = np.sin(t * 9 + u.var[m] * 20) * 0.4
                    self._splat(xs[m], ys[m] + bob, cls, rgb, ua, _TROOP_STAMPS[cls])
            if fallen.any():
                lf, of = u.center(u.tfall[fallen])
                k = 1.0 / math.cos(math.radians(float(lat[0])))
                fx = R * np.radians(of)
                fy = R * np.log(np.tan(np.pi / 4 + np.radians(lf) / 2))
                h = math.radians(u.facing)
                ox, oy = u.off[fallen, 0], u.off[fallen, 1]
                FX = fx + (ox * math.cos(h) + oy * math.sin(h)) * k
                FY = fy + (-ox * math.sin(h) + oy * math.cos(h)) * k
                fxs, fys, _, fok = self._project(v, FX, FY)
                dark = tuple(int(cc * 0.42) for cc in rgb)
                self._splat(fxs[fok], fys[fok], 1, dark, ua * 0.95, _FALLEN)
            if any(ta <= t <= tb for ta, tb in u.fire):
                idx = np.nonzero(standing & ok)[0]
                if len(idx):
                    rnd = np.random.default_rng(int(t * 30) * 7919 + ui)
                    nf = max(3, int(len(idx) * 0.004))
                    pick = rnd.choice(idx, size=min(nf, len(idx)), replace=False)
                    flashes.append((xs[pick], ys[pick] - size[pick] * 0.6, ua))
                    stand_xy[ui] = (xs[idx], ys[idx] - size[idx] * 0.5)
        img = skia.Image.fromarray(buf, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
        c.drawImage(img, 0, 0)
        for fxs, fys, fa in flashes:
            for x, y in zip(fxs[:60], fys[:60]):
                c.drawCircle(float(x), float(y), 3.2, paint(skia.Color4f(1, 0.85, 0.45, 0.9 * fa), blend=skia.BlendMode.kPlus, blur=2.5))
            for x, y in zip(fxs[60:], fys[60:]):
                c.drawCircle(float(x), float(y), 1.6, paint(skia.Color4f(1, 0.95, 0.7, fa), blend=skia.BlendMode.kPlus))
        # Leuchtspuren zwischen Gegnern
        for (i, j) in self.enemies:
            if i in stand_xy and j in stand_xy:
                rnd = np.random.default_rng(int(t * 30) * 31 + i * 7 + j)
                ax, ay = stand_xy[i]
                bx, by = stand_xy[j]
                for _ in range(18):
                    p = rnd.integers(len(ax))
                    q = rnd.integers(len(bx))
                    x0, y0, x1, y1 = float(ax[p]), float(ay[p]), float(bx[q]), float(by[q])
                    if rnd.random() < 0.5:
                        x0, y0, x1, y1 = x1, y1, x0, y0
                    f0 = rnd.random() * 0.6
                    f1 = min(1.0, f0 + 0.12 + rnd.random() * 0.15)
                    c.drawLine(x0 + (x1 - x0) * f0, y0 + (y1 - y0) * f0, x0 + (x1 - x0) * f1, y0 + (y1 - y0) * f1,
                               paint(skia.Color4f(1, 0.9, 0.55, 0.55 * a), "stroke", 1.3, blend=skia.BlendMode.kPlus))
