"""Bühne über der Karte: Figuren (Billboards), Effekte, Trichter, Schneefall, Kamerawackeln.

Alle Objekte stehen auf Kartenkoordinaten und werden mit der Kamera des Renderers projiziert.
Figuren sind absichtlich größer als maßstabsgerecht (Spielfiguren-Look).
"""
import math
import os
from functools import lru_cache

import cv2
import numpy as np

f32 = np.float32
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "assets", "ww1", "figures")


@lru_cache(maxsize=None)
def figure(name):
    im = cv2.imread(os.path.join(FIG, name + ".png"), cv2.IMREAD_UNCHANGED)
    return cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)


_scaled = {}


def scaled(key, img, h, flip=False):
    h = max(2, int(round(h)))
    k = (key, h, flip)
    if k not in _scaled:
        w = max(2, int(round(img.shape[1] * h / img.shape[0])))
        s = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA if h < img.shape[0] else cv2.INTER_LINEAR)
        if flip:
            s = s[:, ::-1].copy()
        _scaled[k] = s.astype(f32)
        if len(_scaled) > 4000:
            _scaled.clear()
    return _scaled[k]


def blit(frame, spr, x, y, alpha=1.0, add=False):
    """spr: float32 RGBA; (x, y) = linke obere Ecke (Bildpunkte)."""
    H, W = frame.shape[:2]
    h, w = spr.shape[:2]
    x0, y0 = int(round(x)), int(round(y))
    x1, y1 = x0 + w, y0 + h
    if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H:
        return
    sx0, sy0 = max(0, -x0), max(0, -y0)
    sx1, sy1 = w - max(0, x1 - W), h - max(0, y1 - H)
    fx0, fy0 = max(0, x0), max(0, y0)
    sub = spr[sy0:sy1, sx0:sx1]
    a = sub[..., 3:4] * (alpha / 255.0)
    dst = frame[fy0:fy0 + sub.shape[0], fx0:fx0 + sub.shape[1]]
    if add:
        dst += sub[..., :3] * a
    else:
        dst *= (1 - a)
        dst += sub[..., :3] * a


def shadow(frame, cx, cy, rw, rh, strength=0.45):
    H, W = frame.shape[:2]
    x0, x1 = int(max(0, cx - rw)), int(min(W, cx + rw + 1))
    y0, y1 = int(max(0, cy - rh)), int(min(H, cy + rh + 1))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.ogrid[y0:y1, x0:x1]
    d = ((xx - cx) / max(rw, 1)) ** 2 + ((yy - cy) / max(rh, 1)) ** 2
    a = np.clip(1 - d, 0, 1) ** 0.8 * strength
    frame[y0:y1, x0:x1] *= (1 - a)[..., None]


class Figure:
    """Spielfigur auf der Karte. path: Liste (t, x, y) in Sekunden/Kartenpixeln (linear interpoliert)."""

    def __init__(self, sprite, path, size=46.0, flip=False, t0=-1e9, t1=1e9, z=0.0, bob=0.0, seed=0):
        self.sprite, self.path, self.size, self.flip = sprite, path, size, flip
        self.t0, self.t1, self.z, self.bob = t0, t1, z, bob
        self.ph = (seed * 0.731) % 1.0

    def pos(self, t):
        p = self.path
        if t <= p[0][0]:
            return p[0][1], p[0][2]
        for (ta, xa, ya), (tb, xb, yb) in zip(p, p[1:]):
            if t <= tb:
                k = (t - ta) / max(1e-6, tb - ta)
                k = k * k * (3 - 2 * k)
                return xa + (xb - xa) * k, ya + (yb - ya) * k
        return p[-1][1], p[-1][2]

    def visible(self, t):
        return self.t0 <= t <= self.t1


class Explosion:
    def __init__(self, t0, x, y, size=95.0, crater=True):
        self.t0, self.x, self.y, self.size, self.crater = t0, x, y, size, crater


class Stage:
    def __init__(self, renderer, fxlib, fps=30):
        self.R = renderer
        self.fx = fxlib
        self.fps = fps
        self.figures = []
        self.explosions = []
        self.muzzles = []          # (t, figure, dx, dy)
        self.smokes = []           # (t0, x, y, size, dur)
        self.crater_spr = fxlib["crater"].astype(f32)
        self.flash = fxlib["flash"].astype(f32)
        self.muzzle = fxlib["muzzle"].astype(f32)
        self.smoke = fxlib["smoke"].astype(f32)
        self.expl = [f.astype(f32) for f in fxlib["explosion"]]

    # ------------------------------------------------------------ Zeichnen
    def draw(self, frame, t):
        R = self.R
        items = []
        # Trichter (am Boden, zuerst)
        for e in self.explosions:
            if e.crater and t >= e.t0 + 0.12:
                pr = R.project(e.x, e.y)
                if pr is None:
                    continue
                sx, sy, s, zc = pr
                w = e.size * 0.42 * s
                hgt = w * max(0.35, math.cos(math.radians(R.cam.pitch)))
                k = min(1.0, (t - e.t0 - 0.12) / 0.25)
                spr = cv2.resize(self.crater_spr, (max(2, int(w)), max(2, int(hgt))), interpolation=cv2.INTER_AREA)
                blit(frame, spr, sx - w / 2, sy - hgt / 2, alpha=0.55 * k)
        for f in self.figures:
            if not f.visible(t):
                continue
            x, y = f.pos(t)
            pr = R.project(x, y, R.L.height_at(x, y) + f.z)
            if pr is None:
                continue
            items.append((pr[3], "fig", f, pr))
        for e in self.explosions:
            age = t - e.t0
            if 0 <= age < len(self.expl) / self.fps:
                pr = R.project(e.x, e.y)
                if pr is not None:
                    items.append((pr[3] - 0.5, "exp", e, pr))
        for (t0, x, y, size, dur) in self.smokes:
            age = t - t0
            if 0 <= age < dur:
                pr = R.project(x, y)
                if pr is not None:
                    items.append((pr[3] - 0.4, "smk", (age, size, dur), pr))
        items.sort(key=lambda it: -it[0])
        for zc, kind, obj, (sx, sy, s, _) in items:
            if kind == "fig":
                f = obj
                h = f.size * s
                spr = figure(f.sprite)
                bob = math.sin((t + f.ph) * 9.0) * f.bob * h if f.bob else 0.0
                img = scaled(f.sprite, spr, h, f.flip)
                if f.z <= 0:
                    shadow(frame, sx + h * 0.05, sy - h * 0.02, img.shape[1] * 0.42, h * 0.10)
                else:
                    gp = R.project(*f.pos(t))
                    if gp:
                        shadow(frame, gp[0], gp[1], img.shape[1] * 0.25, h * 0.05, 0.25)
                blit(frame, img, sx - img.shape[1] / 2, sy - img.shape[0] + h * 0.04 + bob)
            elif kind == "exp":
                e = obj
                age = t - e.t0
                i = int(age * self.fps)
                fr = self.expl[min(i, len(self.expl) - 1)]
                h = e.size * s * 1.25
                w = h * fr.shape[1] / fr.shape[0]
                img = cv2.resize(fr, (max(2, int(w)), max(2, int(h))), interpolation=cv2.INTER_AREA)
                blit(frame, img, sx - w / 2, sy - h * 0.90)
                if age < 0.18:
                    k = 1 - age / 0.18
                    g = e.size * s * 2.4
                    fl = cv2.resize(self.flash, (max(2, int(g)), max(2, int(g * 0.7))))
                    blit(frame, fl, sx - g / 2, sy - g * 0.45, alpha=1.3 * k, add=True)
            elif kind == "smk":
                age, size, dur = obj
                k = age / dur
                g = size * s * (0.6 + 1.6 * k)
                img = cv2.resize(self.smoke, (max(2, int(g)), max(2, int(g))), interpolation=cv2.INTER_AREA)
                blit(frame, img, sx - g / 2 + k * size * s * 0.8, sy - g * 0.8 - k * size * s * 1.6,
                     alpha=0.75 * math.sin(math.pi * min(1, k * 1.15)))
        # Mündungsfeuer (additiv, obenauf)
        for (tm, f, dx, dy) in self.muzzles:
            age = t - tm
            if 0 <= age < 0.12 and f.visible(t):
                x, y = f.pos(t)
                pr = R.project(x, y)
                if pr is None:
                    continue
                sx, sy, s, _ = pr
                h = f.size * s
                k = 1 - age / 0.12
                g = h * 1.1
                img = cv2.resize(self.muzzle, (max(2, int(g * 2)), max(2, int(g))))
                if not f.flip:
                    bx = sx + dx * h
                else:
                    img = img[:, ::-1].copy()
                    bx = sx - dx * h - img.shape[1]
                blit(frame, img, bx, sy - h + dy * h - g / 2, alpha=1.4 * k, add=True)
                fl = cv2.resize(self.flash, (max(2, int(g * 2.5)), max(2, int(g * 1.6))))
                blit(frame, fl, sx - g * 1.25, sy - h * 0.8 - g * 0.8, alpha=0.6 * k, add=True)
        return frame

    def flash_amount(self, t):
        """Globale Aufhellung durch Einschläge/Mündungsfeuer."""
        a = 0.0
        for e in self.explosions:
            age = t - e.t0
            if 0 <= age < 0.25:
                a += 0.10 * (1 - age / 0.25)
        for (tm, f, dx, dy) in self.muzzles:
            age = t - tm
            if 0 <= age < 0.1:
                a += 0.05 * (1 - age / 0.1)
        return min(a, 0.35)

    def shake(self, t):
        s = 0.0
        for e in self.explosions:
            age = t - e.t0
            if 0 <= age < 0.5:
                s += 2.5 * (1 - age / 0.5)
        s = min(s, 9.0)
        return (math.sin(t * 91.0) * s, math.cos(t * 77.0) * s * 0.7)


class Snowfall:
    def __init__(self, n=900, W=1920, H=1080, seed=11):
        rng = np.random.default_rng(seed)
        self.x = rng.uniform(0, W, n)
        self.y = rng.uniform(0, H, n)
        self.z = rng.uniform(0.25, 1.0, n)        # Nähe: 1 = nah (groß, schnell)
        self.ph = rng.uniform(0, 6.28, n)
        self.W, self.H = W, H

    def draw(self, frame, t, amount=1.0, wind=40.0):
        if amount <= 0:
            return frame
        W, H = self.W, self.H
        layer = np.zeros((H, W), np.uint8)
        sp = 60 + 140 * self.z
        ys = (self.y + t * sp) % (H + 20) - 10
        xs = (self.x + t * wind * self.z + 14 * np.sin(t * 1.3 + self.ph)) % (W + 20) - 10
        rs = (1.0 + 2.4 * self.z)
        n = int(len(self.x) * min(1.0, amount))
        for i in range(n):
            cv2.circle(layer, (int(xs[i]), int(ys[i])), int(rs[i]), int(150 + 105 * self.z[i]), -1, cv2.LINE_AA)
        a = cv2.GaussianBlur(layer, (0, 0), 0.8).astype(f32)[..., None] / 255.0 * 0.85
        frame *= (1 - a)
        frame += 245 * a
        return frame
