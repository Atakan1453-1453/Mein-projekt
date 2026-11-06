"""Bild-Komposition: Story + Kartenebenen → fertiges Videobild zur Zeit t."""
import math
import os

import cv2
import numpy as np

from .render25d import Camera, Look, MapLayer, Renderer
from . import stage as ST, ui as UI, cards as CD, mapfx as MF
from .story import smooth

f32 = np.float32
MONTHS = ["JAN", "FEB", "MÄR", "APR", "MAI", "JUN", "JUL", "AUG", "SEP", "OKT", "NOV", "DEZ"]


def day_to_date(day):
    import datetime
    d = datetime.date(1916, 2, 21) + datetime.timedelta(days=int(round(day)) - 1)
    return f"{d.day:02d}. {MONTHS[d.month - 1]} {d.year}", int(round(day))


def season(day):
    """Schnee und Wintertönung je nach Tag der Schlacht."""
    if day < 1:
        return 0.0, 0.35
    pts_snow = [(1, 0.45), (12, 0.40), (26, 0.0), (276, 0.0), (296, 0.32), (303, 0.36)]
    pts_win = [(1, 1.0), (24, 0.9), (60, 0.25), (80, 0.0), (225, 0.0), (262, 0.45), (285, 0.85), (303, 0.9)]
    sn = float(np.interp(day, [p[0] for p in pts_snow], [p[1] for p in pts_snow]))
    wi = float(np.interp(day, [p[0] for p in pts_win], [p[1] for p in pts_win]))
    return sn, wi


class Layer:
    def __init__(self, folder, prefix, grid, W, H, z_exag=2.0):
        self.L = MapLayer(folder, prefix, grid, z_exag=z_exag)
        self.R = Renderer(self.L, W, H)
        self.g = grid
        self.paint = MF.Painter(self.R)

    def cam(self, gc):
        x, y = self.g.px(gc.lat, gc.lon)
        return Camera(x, y, gc.km * 1000.0 / self.g.ground_res, gc.pitch, gc.yaw, gc.fov)

    def proj(self, lat, lon, z_m=0.0):
        x, y = self.g.px(lat, lon)
        z = self.L.height_at(x, y) + z_m / self.g.ground_res
        return self.R.project(x, y, z)

    def px_per_m(self, s):
        return s / self.g.ground_res


class Composer:
    def __init__(self, story, layers, fxlib, fronts, W=1920, H=1080, fps=30, clips_dir=None):
        self.S = story
        self.layers = layers          # {"L3": Layer, "L2": Layer}
        self.fx = fxlib
        self.fronts = fronts
        self.W, self.H, self.fps = W, H, fps
        self.snow = ST.Snowfall(W=W, H=H)
        self.rain = ST.Snowfall(n=700, W=W, H=H, seed=5)
        self.ov = UI.Overlay(W, H)
        self.expl = [f.astype(f32) for f in fxlib["explosion"]]
        self.firefr = [f.astype(f32) for f in fxlib["fire"]]
        self.crater = fxlib["crater"].astype(f32)
        self.flash = fxlib["flash"].astype(f32)
        self.smoke = fxlib["smoke"].astype(f32)
        self.gas = fxlib["gas"].astype(f32)
        self.muzzle = fxlib["muzzle"].astype(f32)
        self.caps = {}
        rng = np.random.default_rng(7)
        n = rng.normal(0, 1, (H // 4, W // 4)).astype(f32)
        self.grain = [cv2.resize(np.roll(n, (i * 37, i * 53), (0, 1)), (W, H)) for i in range(8)]
        fog = cv2.GaussianBlur(rng.random((H // 8, W // 4)).astype(f32), (0, 0), 6)
        self.fogtex = cv2.resize((fog - fog.min()) / (fog.max() - fog.min() + 1e-6), (W * 2, H))

    # ---------------------------------------------------------------- Zustand
    def look(self, t):
        S = self.S
        day = S.day(t)
        sn, wi = season(day)
        if S.snow.keys:
            sn = S.snow(t)
        if S.winter.keys:
            wi = S.winter(t)
        return Look(day=day, snow=sn, winter=wi, night=S.night(t), dawn=S.dawn(t), fog=S.fog(t), regrow=S.regrow(t),
                    gas=S.gas(t), sat=S.sat(t))

    # ---------------------------------------------------------------- Karte einer Ebene
    def map_layer(self, lay, gc, lk, t):
        R = lay.R
        R.setup(lay.cam(gc))
        img = R.ground(lk)
        S = self.S
        ta = S.terr_a(t)
        if ta > 0:
            lay.paint.territory(img, self.fronts.german_poly(lk.day), ta)
        for (t0, t1, key, style) in S.static_fronts:
            k = UI.fade(t, t0, t1, 0.6, 0.6)
            if k > 0:
                if style == "dashed":
                    lay.paint.polyline(img, self.fronts.by_key[key], (240, 236, 228), 4, k, dashed=True)
                else:
                    lay.paint.front(img, self.fronts.by_key[key], k)
        fa = S.front_a(t)
        if fa > 0:
            lay.paint.front(img, self.fronts.full(lk.day), fa)
        for ar in S.arrows:
            if ar.t0 <= t <= ar.t1:
                prog = smooth((t - ar.t0) / max(0.05, ar.grow))
                k = min(1.0, (ar.t1 - t) / 0.5)
                lay.paint.arrow(img, ar.path, ar.side, ar.width_km, prog, k)
        for (t0, t1, fn) in [(a, b, f) for (a, b, f) in S.ground_fx]:
            if t0 <= t <= t1:
                fn(img, t, lay)
        self.draw_objects(img, lay, t)
        # Wimpel an Forts
        km_view = R.cam.view_w * lay.g.ground_res / 1000.0
        for (la, lo, hist) in (S.flags if km_view < 26 else []):
            side = None
            for (tf, sd) in hist:
                if t >= tf:
                    side = sd
            if side:
                lay.paint.pennant(img, la, lo, side, scale=min(1.0, max(0.18, 3.0 / max(1.0, km_view))), t=t)
        img = R.grade(img, lk)
        return img

    def draw_objects(self, frame, lay, t):
        S = self.S
        R = lay.R
        items = []
        res = lay.g.ground_res
        # Trichter am Boden
        for b in S.booms:
            if b.crater and b.t + 0.12 <= t <= b.t + 40:
                pr = lay.proj(b.lat, b.lon)
                if pr is None:
                    continue
                sx, sy, s, _ = pr
                w = b.size_m * 0.30 / res * s
                if w < 3 or not (-200 < sx < self.W + 200 and -200 < sy < self.H + 200):
                    continue
                hgt = w * max(0.35, math.cos(math.radians(R.cam.pitch)))
                k = min(1.0, (t - b.t - 0.12) / 0.25) * min(1.0, (b.t + 40 - t) / 6)
                spr = cv2.resize(self.crater, (max(2, int(w)), max(2, int(hgt))), interpolation=cv2.INTER_AREA)
                ST.blit(frame, spr, sx - w / 2, sy - hgt / 2, alpha=0.5 * k)
        for f in S.figs:
            a = f.alpha(t)
            if a <= 0:
                continue
            la, lo = f.pos(t)
            pr = lay.proj(la, lo, f.z_m)
            if pr is None or not (-400 < pr[0] < self.W + 400 and -400 < pr[1] < self.H + 600):
                continue
            items.append((pr[3], 0, f, pr, a))
        for b in S.booms:
            age = t - b.t
            if 0 <= age < len(self.expl) / 30.0:
                pr = lay.proj(b.lat, b.lon)
                if pr is not None and -400 < pr[0] < self.W + 400 and -400 < pr[1] < self.H + 800:
                    items.append((pr[3] - 0.5, 1, b, pr, 1.0))
        for sm in S.smokes:
            age = t - sm.t
            if 0 <= age < sm.dur:
                pr = lay.proj(sm.lat, sm.lon)
                if pr is not None and -300 < pr[0] < self.W + 300 and -300 < pr[1] < self.H + 600:
                    items.append((pr[3] - 0.4, 2, sm, pr, 1.0))
        for g in S.gases:
            if g.t0 <= t <= g.t1:
                age = t - g.t0
                for j in range(7):
                    ang = j / 7 * 2 * math.pi + 0.3 * j
                    rr = g.radius_m * (0.25 + 0.5 * ((j * 0.37) % 1)) * min(1.0, 0.3 + age / 6)
                    la = g.lat + g.drift[0] * age + math.sin(ang) * rr / 111000
                    lo = g.lon + g.drift[1] * age + math.cos(ang) * rr / 72900
                    pr = lay.proj(la, lo)
                    if pr is not None:
                        k = min(1.0, age / 2.0, (g.t1 - t) / 2.0)
                        items.append((pr[3] - 0.3, 3, (g, j, k), pr, 1.0))
        for fi in S.fires:
            if fi.t0 <= t <= fi.t1:
                pr = lay.proj(fi.lat, fi.lon)
                if pr is not None:
                    items.append((pr[3] - 0.2, 4, fi, pr, min(1.0, (t - fi.t0) / 0.8, (fi.t1 - t) / 0.8)))
        items.sort(key=lambda it: -it[0])
        for zc, kind, obj, (sx, sy, s, _), a in items:
            if kind == 0:
                f = obj
                h = f.size_m / res * s
                h = min(max(h, f.min_px), 260.0)
                name = f.sprite_at(t)
                spr = ST.figure(name)
                flip = f.flip
                img = ST.scaled(name, spr, h, flip)
                bob = math.sin(t * 9.0 + hash(f.tag) % 7) * f.bob * h if f.bob else 0.0
                if f.z_m <= 0:
                    ST.shadow(frame, sx + h * 0.05, sy - h * 0.02, img.shape[1] * 0.42, h * 0.10, 0.4 * a)
                ST.blit(frame, img, sx - img.shape[1] / 2, sy - img.shape[0] + h * 0.04 + bob, alpha=a)
            elif kind == 1:
                b = obj
                age = t - b.t
                i = int(age * 30)
                fr = self.expl[min(i, len(self.expl) - 1)]
                h = min(700.0, max(30.0, b.size_m / res * s))
                w = h * fr.shape[1] / fr.shape[0]
                img = cv2.resize(fr, (max(2, int(w)), max(2, int(h))), interpolation=cv2.INTER_AREA)
                ST.blit(frame, img, sx - w / 2, sy - h * 0.90)
                if age < 0.18:
                    k = 1 - age / 0.18
                    gsz = h * 1.9
                    fl = cv2.resize(self.flash, (max(2, int(gsz)), max(2, int(gsz * 0.7))))
                    ST.blit(frame, fl, sx - gsz / 2, sy - gsz * 0.45, alpha=1.3 * k, add=True)
            elif kind == 2:
                sm = obj
                age = t - sm.t
                k = age / sm.dur
                gsz = min(500.0, max(10.0, sm.size_m / res * s)) * (0.6 + 1.6 * k)
                img = cv2.resize(self.smoke, (max(2, int(gsz)), max(2, int(gsz))), interpolation=cv2.INTER_AREA)
                if sm.dark:
                    img = img.copy()
                    img[..., :3] *= 0.45
                ST.blit(frame, img, sx - gsz / 2 + k * gsz * 0.4, sy - gsz * 0.8 - k * gsz * 0.9,
                        alpha=0.75 * math.sin(math.pi * min(1, k * 1.15)))
            elif kind == 3:
                g, j, k = obj
                gsz = min(900.0, max(30.0, g.radius_m * 0.9 / res * s))
                img = cv2.resize(self.gas, (max(2, int(gsz)), max(2, int(gsz * 0.6))), interpolation=cv2.INTER_AREA)
                ST.blit(frame, img, sx - gsz / 2, sy - gsz * 0.42, alpha=0.75 * k)
            elif kind == 4:
                fi = obj
                fr = self.firefr[int(t * 24) % len(self.firefr)]
                h = min(260.0, max(16.0, fi.size_m / res * s))
                w = h * fr.shape[1] / fr.shape[0]
                img = cv2.resize(fr, (max(2, int(w)), max(2, int(h))), interpolation=cv2.INTER_AREA)
                ST.blit(frame, img, sx - w / 2, sy - h * 0.92, alpha=a)
                gl = cv2.resize(self.flash, (max(2, int(h * 1.6)), max(2, int(h))))
                ST.blit(frame, gl, sx - h * 0.8, sy - h * 0.7, alpha=0.35 * a, add=True)
        # Mündungsfeuer
        for m in S.muzzles:
            age = t - m.t
            if 0 <= age < 0.12 and m.fig.alpha(t) > 0:
                la, lo = m.fig.pos(t)
                pr = lay.proj(la, lo)
                if pr is None:
                    continue
                sx, sy, s, _ = pr
                h = min(max(m.fig.size_m / res * s, m.fig.min_px), 260.0)
                k = 1 - age / 0.12
                gsz = h * 1.1
                img = cv2.resize(self.muzzle, (max(2, int(gsz * 2)), max(2, int(gsz))))
                if m.fig.flip:
                    img = img[:, ::-1].copy()
                    bx = sx - 0.42 * h - img.shape[1]
                else:
                    bx = sx + 0.42 * h
                ST.blit(frame, img, bx, sy - h + 0.30 * h - gsz / 2, alpha=1.4 * k, add=True)
                fl = cv2.resize(self.flash, (max(2, int(gsz * 2.5)), max(2, int(gsz * 1.6))))
                ST.blit(frame, fl, sx - gsz * 1.25, sy - h * 0.8 - gsz * 0.8, alpha=0.6 * k, add=True)

    # ---------------------------------------------------------------- Bildschirm-Effekte
    def flash_amount(self, t):
        a = 0.0
        for b in self.S.booms:
            age = t - b.t
            if 0 <= age < 0.25:
                a += 0.06 * b.loud * (1 - age / 0.25)
        for m in self.S.muzzles:
            age = t - m.t
            if 0 <= age < 0.1:
                a += 0.03
        return min(a, 0.3)

    def shake(self, t):
        s = 0.0
        for b in self.S.booms:
            age = t - b.t
            if 0 <= age < 0.45:
                s += 2.0 * b.loud * (1 - age / 0.45)
        s = min(s, 8.0)
        return math.sin(t * 91.0) * s, math.cos(t * 77.0) * s * 0.7

    # ---------------------------------------------------------------- KI-Clips
    def clip_frame(self, c, t):
        st = self.caps.get(c.path)
        if st is None:
            cap = cv2.VideoCapture(c.path)
            st = {"cap": cap, "pos": -1, "frame": None, "n": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                  "fps": cap.get(cv2.CAP_PROP_FPS) or 24}
            self.caps[c.path] = st
        idx = int(min(st["n"] - 1, max(0, (t - c.t0) * st["fps"] * c.speed)))
        if idx < st["pos"] or idx > st["pos"] + 3:
            st["cap"].set(cv2.CAP_PROP_POS_FRAMES, idx)
            st["pos"] = idx - 1
        while st["pos"] < idx:
            ok, f = st["cap"].read()
            if not ok:
                break
            st["pos"] += 1
            st["frame"] = f
        fr = st["frame"]
        if fr is None:
            return None
        h2 = int(round(fr.shape[0] * self.W / fr.shape[1]))
        fr = cv2.resize(fr, (self.W, max(self.H, h2)), interpolation=cv2.INTER_LANCZOS4)
        y0 = (fr.shape[0] - self.H) // 2
        fr = fr[y0:y0 + self.H, :, ::-1].astype(f32)
        # Filmlook: leicht entsättigt, Körnung, Vignette
        g = fr.mean(-1, keepdims=True)
        fr = g + (fr - g) * 0.88
        fr = (fr - 128) * 1.06 + 124
        fr += self.grain[int(t * 24) % 8][..., None] * 7.0
        return fr

    # ---------------------------------------------------------------- Bild
    def frame(self, t):
        S = self.S
        self.ov.clear()
        gc = S.cam(t)
        lk = self.look(t)
        mix = S.mapmix(t)
        img = None
        if mix < 0.999:
            img = self.map_layer(self.layers["L3"], gc, lk, t)
        if mix > 0.001:
            im2 = self.map_layer(self.layers["L2"], gc, lk, t)
            img = im2 if img is None else img * (1 - mix) + im2 * mix
        img *= 1.0 + self.flash_amount(t)
        sf = S.snowfall(t)
        if sf > 0:
            img = self.snow.draw(img, t, amount=sf)
        rn = S.rain(t)
        if rn > 0:
            img = self.rain_draw(img, t, rn)
        fs = S.fogscreen(t)
        if fs > 0:
            off = int((t * 40) % self.W)
            fogl = self.fogtex[:, off:off + self.W][..., None]
            k = np.clip(fogl * 1.3 - 0.15, 0, 1) * fs
            img = img * (1 - k * 0.8) + 200 * k * 0.8
        dx, dy = self.shake(t)
        if abs(dx) + abs(dy) > 0.05:
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            img = cv2.warpAffine(img, M, (self.W, self.H), borderMode=cv2.BORDER_REFLECT)
        # KI-Clips
        clip_k = 0.0
        for c in S.clips:
            if c.t0 - 0.35 <= t <= c.t1 + 0.4:
                k = min(smooth((t - (c.t0 - 0.35)) / 0.35), smooth(((c.t1 + 0.4) - t) / 0.4))
                fr = self.clip_frame(c, min(max(t, c.t0), c.t1))
                if fr is not None:
                    # Eintauchen: Blitz + Unschärfe am Übergang
                    if k < 1:
                        img = cv2.GaussianBlur(img, (0, 0), 1 + 6 * k)
                    img = img * (1 - k) + fr * k
                    img += 60 * math.sin(math.pi * k) * (1 if k < 1 else 0)
                    clip_k = max(clip_k, k)
        # Einblendungen
        ov = self.ov
        lay = self.layers["L2"] if mix > 0.5 else self.layers["L3"]
        ca = S.counter_a(t) * (1 - clip_k)
        if ca > 0:
            date, day = day_to_date(lk.day)
            ov.counter(date, max(1, day), ca)
        for lb in S.labels:
            k = UI.fade(t, lb.t0, lb.t1, 0.9, 0.4)
            if k > 0 and clip_k < 0.5:
                pr = lay.proj(lb.lat, lb.lon)
                if pr:
                    ov.place(lb.text, pr[0], pr[1], k, side=lb.side, sub=lb.sub)
        for (t0, t1, fig, text) in S.highlight:
            k = UI.fade(t, t0, t1, 0.5, 0.5) * (1 - clip_k)
            if k > 0 and fig.alpha(t) > 0:
                la, lo = fig.pos(t)
                pr = lay.proj(la, lo)
                if pr:
                    r = 60 + 6 * math.sin(t * 4)
                    ov.d.ellipse((pr[0] - r, pr[1] - r * 0.45, pr[0] + r, pr[1] + r * 0.45),
                                 outline=UI.STYLE["warn"] + (int(230 * k),), width=4)
                    ov.place(text, pr[0], pr[1] - 70, k, side=1)
        for (t0, t1, fn, fin, fout) in S.overlays:
            k = UI.fade(t, t0, t1, fin, fout)
            if k > 0:
                fn(ov, t, k, lay)
        if clip_k > 0.5:
            CD.ai_tag(ov, clip_k)
        img = UI.composite(img, ov.rgba())
        # Ein-/Ausblende des ganzen Videos
        k = min(smooth(t / 1.0), smooth((S.duration - t) / 1.0))
        img *= k
        return np.clip(img, 0, 255).astype(np.uint8)

    def rain_draw(self, img, t, amount):
        H, W = self.H, self.W
        lay = np.zeros((H, W), np.uint8)
        r = self.rain
        ys = (r.y + t * 900 * (0.6 + r.z)) % (H + 40) - 20
        xs = (r.x + t * 120 * r.z) % (W + 20) - 10
        n = int(len(r.x) * min(1.0, amount))
        for i in range(n):
            L = 10 + 18 * r.z[i]
            cv2.line(lay, (int(xs[i]), int(ys[i])), (int(xs[i] - L * 0.15), int(ys[i] - L)), int(120 + 100 * r.z[i]), 1,
                     cv2.LINE_AA)
        a = lay.astype(f32)[..., None] / 255.0 * 0.45
        return img * (1 - a) + 215 * a
