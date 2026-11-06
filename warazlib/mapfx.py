"""Kartengrafik über dem Boden: Frontlinien (zwischen Ständen überblendet), Gebietsfärbung,
Angriffspfeile, Strecken, Wimpel, Maßstab. Alles in Geo-Koordinaten, projiziert mit dem Renderer.
"""
import math

import cv2
import numpy as np

f32 = np.float32
DE = (96, 100, 92)          # Feldgrau (dunkel, für Pfeile/Fläche)
DE_EDGE = (205, 205, 196)
FR = (62, 108, 178)         # Horizontblau (kräftig)
FR_EDGE = (190, 214, 245)
FRONT = (200, 56, 38)


def resample(pts, n=360):
    p = np.asarray(pts, np.float64)
    d = np.r_[0, np.cumsum(np.hypot(np.diff(p[:, 0]) * 1.0, np.diff(p[:, 1]) * 0.66))]
    s = np.linspace(0, d[-1], n)
    return np.stack([np.interp(s, d, p[:, 0]), np.interp(s, d, p[:, 1])], 1)


class Fronts:
    """Frontverlauf als Funktion des Schlachttags (lineare Überblendung zwischen Ständen)."""

    def __init__(self, fronts, days, west=None, south=None, ger_close=None, n=360):
        self.days = [d for _, d in days]
        self.lines = [resample(fronts[k], n) for k, _ in days]
        self.by_key = {k: resample(fronts[k], n) for k, _ in days}
        self.west = np.asarray(west or [], np.float64)
        self.south = np.asarray(south or [], np.float64)
        self.close = np.asarray(ger_close or [], np.float64)

    def at(self, day):
        ds = self.days
        if day <= ds[0]:
            return self.lines[0]
        if day >= ds[-1]:
            return self.lines[-1]
        i = np.searchsorted(ds, day) - 1
        k = (day - ds[i]) / max(1e-6, ds[i + 1] - ds[i])
        k = k * k * (3 - 2 * k)
        return self.lines[i] * (1 - k) + self.lines[i + 1] * k

    def full(self, day):
        parts = [p for p in (self.west, self.at(day), self.south) if len(p)]
        return np.concatenate(parts, 0)

    def german_poly(self, day):
        parts = [p for p in (self.west, self.at(day), self.south, self.close) if len(p)]
        return np.concatenate(parts, 0)


class Painter:
    """Zeichnet Kartengrafik für einen Renderer (Layer + Kamera bereits gesetzt)."""

    def __init__(self, renderer):
        self.R = renderer
        self.g = renderer.L.grid

    def to_px(self, latlon):
        ll = np.asarray(latlon, np.float64)
        xs, ys = [], []
        for la, lo in ll:
            x, y = self.g.px(la, lo)
            xs.append(x)
            ys.append(y)
        return np.array(xs), np.array(ys)

    def screen(self, latlon):
        xs, ys = self.to_px(latlon)
        return self.R.project_many(xs, ys)

    # ---------------------------------------------------------------- Gebiet
    def territory(self, frame, poly_latlon, alpha):
        if alpha <= 0:
            return
        L = self.R.L
        q = 8
        h, w = L.H // q + 1, L.W // q + 1
        m = np.zeros((h, w), np.uint8)
        xs, ys = self.to_px(poly_latlon)
        pts = np.stack([xs / q, ys / q], 1)
        cv2.fillPoly(m, [np.round(pts * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
        m = cv2.GaussianBlur(m, (0, 0), 1.5)
        mx, my = self.R.mx / q, self.R.my / q
        s = cv2.remap(m, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(f32) / 255.0
        de = s[..., None] * 0.20 * alpha
        fr = (1 - s[..., None]) * 0.12 * alpha
        frame *= (1 - de - fr)
        frame += np.array(DE, f32) * de + np.array(FR, f32) * fr

    # ---------------------------------------------------------------- Linien
    def polyline(self, frame, latlon, color, width, alpha=1.0, outline=None, dashed=False, glow=False):
        sx, sy, ok = self.screen(latlon)
        pts = np.stack([sx, sy], 1)
        segs = []
        cur = []
        for p, o in zip(pts, ok):
            if o and abs(p[0]) < 6000 and abs(p[1]) < 6000:
                cur.append(p)
            elif cur:
                segs.append(cur)
                cur = []
        if cur:
            segs.append(cur)
        if not segs:
            return
        H, W = frame.shape[:2]
        layer = np.zeros((H, W, 3), np.uint8)
        mask = np.zeros((H, W), np.uint8)
        for s in segs:
            arr = np.round(np.array(s) * 4).astype(np.int32)
            if dashed:
                L = np.r_[0, np.cumsum(np.hypot(*np.diff(np.array(s), axis=0).T))]
                on = (L // 22) % 2 == 0
                for i in range(len(s) - 1):
                    if on[i]:
                        cv2.line(mask, tuple(arr[i]), tuple(arr[i + 1]), 255, int(width), cv2.LINE_AA, shift=2)
                        cv2.line(layer, tuple(arr[i]), tuple(arr[i + 1]), color, int(width), cv2.LINE_AA, shift=2)
                continue
            if outline is not None:
                cv2.polylines(mask, [arr], False, 255, int(width + 4), cv2.LINE_AA, shift=2)
                cv2.polylines(layer, [arr], False, outline, int(width + 4), cv2.LINE_AA, shift=2)
            if glow:
                g = np.zeros((H, W), np.uint8)
                cv2.polylines(g, [arr], False, 255, int(width * 3), cv2.LINE_AA, shift=2)
                g = cv2.GaussianBlur(g, (0, 0), width * 1.5).astype(f32)[..., None] / 255.0 * 0.5 * alpha
                frame += np.array(color, f32) * g
            cv2.polylines(mask, [arr], False, 255, int(width), cv2.LINE_AA, shift=2)
            cv2.polylines(layer, [arr], False, color, int(width), cv2.LINE_AA, shift=2)
        a = mask.astype(f32)[..., None] / 255.0 * alpha
        ys, xs = np.nonzero(mask)
        if len(ys) == 0:
            return
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        fa = a[y0:y1, x0:x1]
        frame[y0:y1, x0:x1] = frame[y0:y1, x0:x1] * (1 - fa) + layer[y0:y1, x0:x1].astype(f32) * fa

    def front(self, frame, latlon, alpha=1.0, color=FRONT, width=None):
        if alpha <= 0:
            return
        w = width or max(3, int(5 * (1.0 if self.R.cam.view_w < 4000 else 0.8)))
        self.polyline(frame, latlon, color, w, alpha, outline=(30, 26, 24))

    # ---------------------------------------------------------------- Pfeile
    def arrow(self, frame, path_latlon, side, width_km, progress, alpha=1.0):
        if progress <= 0 or alpha <= 0:
            return
        p = resample(path_latlon, 80)
        n = max(2, int(len(p) * min(1.0, progress)))
        p = p[:n]
        sx, sy, ok = self.screen(p)
        if not ok.all():
            return
        pts = np.stack([sx, sy], 1)
        # Breite in Bildpunkten (über Maßstab am Mittelpunkt)
        mid = p[len(p) // 2]
        x, y = self.g.px(*mid)
        pr = self.R.project(x, y)
        if pr is None:
            return
        wpx = max(10.0, width_km * 1000 / self.g.ground_res * pr[2])
        d = np.gradient(pts, axis=0)
        d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-6)
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        t = np.linspace(0, 1, len(pts))
        half = wpx * (0.35 + 0.15 * t)[:, None] / 2
        L0 = float(np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1)))
        head_len = min(wpx * 1.1, L0 * 0.35)
        L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
        body = L < L[-1] - head_len
        if body.sum() < 2:
            body[:2] = True
        left = pts[body] + nrm[body] * half[body]
        right = pts[body] - nrm[body] * half[body]
        tip = pts[-1]
        base = pts[body][-1]
        dn = nrm[body][-1]
        hw = min(wpx * 0.52, head_len * 0.75)
        poly = np.concatenate([left, [base + dn * hw, tip, base - dn * hw], right[::-1]], 0)
        col = DE if side == "de" else FR
        edge = DE_EDGE if side == "de" else FR_EDGE
        H, W = frame.shape[:2]
        mask = np.zeros((H, W), np.uint8)
        cv2.fillPoly(mask, [np.round(poly * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
        edgem = np.zeros((H, W), np.uint8)
        cv2.polylines(edgem, [np.round(poly * 4).astype(np.int32)], True, 255, 3, cv2.LINE_AA, shift=2)
        ys, xs = np.nonzero(mask | edgem)
        if len(ys) == 0:
            return
        y0, y1, x0, x1 = max(0, ys.min() - 2), min(H, ys.max() + 3), max(0, xs.min() - 2), min(W, xs.max() + 3)
        sub = frame[y0:y1, x0:x1]
        a = mask[y0:y1, x0:x1].astype(f32)[..., None] / 255.0 * 0.78 * alpha
        # leichter Schatten
        sh = cv2.GaussianBlur(np.roll(np.roll(mask, 5, 0), 4, 1)[y0:y1, x0:x1], (0, 0), 4).astype(f32)[..., None] / 255.0
        sub *= (1 - 0.30 * sh * alpha)
        sub[:] = sub * (1 - a) + np.array(col, f32) * a
        e = edgem[y0:y1, x0:x1].astype(f32)[..., None] / 255.0 * alpha
        sub[:] = sub * (1 - e) + np.array(edge, f32) * e

    # ---------------------------------------------------------------- Wimpel
    def pennant(self, frame, lat, lon, side, scale=1.0, t=0.0):
        x, y = self.g.px(lat, lon)
        pr = self.R.project(x, y)
        if pr is None:
            return None
        sx, sy, s, _ = pr
        h = max(14.0, min(80.0, 80 * scale))
        col = (150, 154, 144) if side == "de" else FR
        top = (sx, sy - h)
        cv2.line(frame, (int(sx), int(sy)), (int(sx), int(sy - h)), (40, 34, 28), 3, cv2.LINE_AA)
        wv = math.sin(t * 6.0) * 0.12
        pts = np.array([[sx + 1, sy - h], [sx + 1 + h * 0.62, sy - h + h * (0.18 + wv)], [sx + 1, sy - h + h * 0.40]])
        cv2.fillPoly(frame, [np.round(pts * 4).astype(np.int32)], tuple(float(c) for c in col), cv2.LINE_AA, shift=2)
        cv2.polylines(frame, [np.round(pts * 4).astype(np.int32)], True, (235, 232, 224), 2, cv2.LINE_AA, shift=2)
        return top

    def ruler(self, frame, lat0, lon0, lat1, lon1, text, ov, alpha=1.0):
        (sx, sy, ok) = self.screen([(lat0, lon0), (lat1, lon1)])
        if not ok.all() or alpha <= 0:
            return
        p0, p1 = (sx[0], sy[0]), (sx[1], sy[1])
        col = (245, 240, 230)
        a = alpha
        lay = frame.copy()
        cv2.line(lay, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), col, 3, cv2.LINE_AA)
        for p in (p0, p1):
            cv2.circle(lay, (int(p[0]), int(p[1])), 6, col, -1, cv2.LINE_AA)
        frame[:] = frame * (1 - a) + lay * a
        ov.place(text, (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, a, side=1)
