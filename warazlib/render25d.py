"""2.5D-Kartenrenderer: geneigte Kamera über einer Reliefkarte mit zeitabhängiger Zerstörung.

Welt-Koordinaten: x = Kartenpixel nach Osten, y = −Kartenpixel (Norden positiv), z = Höhe in Kartenpixeln.
Die Kamera schaut auf einen Zielpunkt (Kartenpixel), aus `dist` Abstand, `pitch` Grad aus der Senkrechten
gekippt, `yaw` Grad gedreht (0 = Norden oben).

Zerstörung: onset1/onset2 sind Karten (Tag der Schlacht), ab denen ein Pixel zerschossen (Stufe 1)
bzw. Trichterfeld (Stufe 2) wird. Der Renderer blendet zum Tag `day` weich über.
"""
import math
import os

import cv2
import numpy as np

f32 = np.float32


class Camera:
    def __init__(self, x, y, view_w, pitch=40.0, yaw=0.0, fov=34.0):
        self.x, self.y = float(x), float(y)       # Zielpunkt (Kartenpixel)
        self.view_w = float(view_w)               # sichtbare Breite am Zielpunkt (Kartenpixel)
        self.pitch, self.yaw, self.fov = float(pitch), float(yaw), float(fov)

    def lerp(self, o, t):
        a = 1 - t
        return Camera(self.x * a + o.x * t, self.y * a + o.y * t,
                      math.exp(math.log(self.view_w) * a + math.log(o.view_w) * t),
                      self.pitch * a + o.pitch * t, self.yaw * a + o.yaw * t, self.fov * a + o.fov * t)


def _half(a):
    """Halbiert ein Mehrkanal-uint8-Bild (2x2-Mittel)."""
    h, w = a.shape[:2]
    if h % 2 or w % 2:
        a = np.pad(a, ((0, h % 2), (0, w % 2), (0, 0)), mode="edge")
    s = a[0::2, 0::2].astype(np.uint16) + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]
    return ((s + 2) // 4).astype(np.uint8)


class MapLayer:
    """Texturen einer Karte, gepackt in ein 13-Kanal-Bild (+ Mip-Pyramide):
    0-2 base, 3-5 damaged, 6-8 moon (RGB), 9 onset1, 10 onset2 (Tag/1.25; 255 = nie), 11 snow, 12 forest."""

    ONSET_SCALE = 1.25

    def __init__(self, folder, prefix, grid, z_exag=2.0, levels=6):
        self.grid = grid
        self.z_exag = z_exag
        rd = lambda n: cv2.imread(os.path.join(folder, f"{prefix}_{n}"), cv2.IMREAD_UNCHANGED)  # noqa: E731
        base = rd("base.jpg")
        H, W = base.shape[:2]
        pack = np.empty((H, W, 13), np.uint8)
        pack[..., 0:3] = base[..., ::-1]
        del base
        pack[..., 3:6] = rd("damaged.jpg")[..., ::-1]
        pack[..., 6:9] = rd("moon.jpg")[..., ::-1]
        for ch, name in ((9, "onset1.png"), (10, "onset2.png")):
            o = rd(name)
            if o is None:
                pack[..., ch] = 255
            else:
                o = cv2.resize(o.astype(f32), (W, H), interpolation=cv2.INTER_LINEAR)
                pack[..., ch] = np.clip(o / self.ONSET_SCALE, 0, 255).astype(np.uint8)
        sn = rd("snow.jpg")
        pack[..., 11] = sn if sn.ndim == 2 else sn[..., 0]
        pack[..., 12] = rd("forest.png")
        self.pyr = [pack]
        for _ in range(levels - 1):
            self.pyr.append(_half(self.pyr[-1]))
        dem = rd("dem16.png").astype(f32) / 100.0 + 100.0
        dem = cv2.resize(dem, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        self.height_half = dem / grid.ground_res * z_exag                    # in Kartenpixeln, halbe Auflösung
        self.W, self.H = W, H
        self.levels = levels

    def height_at(self, x, y):
        xi = min(max(int(x / 2), 0), self.height_half.shape[1] - 1)
        yi = min(max(int(y / 2), 0), self.height_half.shape[0] - 1)
        return float(self.height_half[yi, xi])


class Look:
    """Bildstimmung pro Bild: Jahreszeit, Schnee, Tageszeit, Nebel."""

    def __init__(self, day=1, snow=0.0, winter=0.0, night=0.0, dawn=0.0, fog=0.15, regrow=0.0, gas=0.0, sat=1.0):
        self.day, self.snow, self.winter, self.night, self.dawn = day, snow, winter, night, dawn
        self.fog, self.regrow, self.gas, self.sat = fog, regrow, gas, sat


class Renderer:
    def __init__(self, layer, W=1920, H=1080):
        self.L = layer
        self.W, self.H = W, H
        xs = (np.arange(W, dtype=f32) - W / 2 + 0.5)
        ys = (np.arange(H, dtype=f32) - H / 2 + 0.5)
        self.sx, self.sy = np.meshgrid(xs, ys)

    # ---------------------------------------------------------------- Kamera-Geometrie
    def setup(self, cam):
        L = self.L
        p, yw = math.radians(cam.pitch), math.radians(cam.yaw)
        F = (self.W / 2) / math.tan(math.radians(cam.fov) / 2)
        dist = cam.view_w / 2 / math.tan(math.radians(cam.fov) / 2)
        tz = L.height_at(cam.x, cam.y)
        T = np.array([cam.x, -cam.y, tz], f32)
        h = np.array([-math.sin(yw), -math.cos(yw), 0], f32)        # vom Ziel zur Kamera (waagrecht)
        C = T + dist * (math.cos(p) * np.array([0, 0, 1], f32) + math.sin(p) * h)
        fwd = (T - C) / np.linalg.norm(T - C)
        right = np.array([math.cos(yw), -math.sin(yw), 0], f32)
        up = np.cross(right, fwd)
        self.cam = cam
        self.F, self.C, self.f, self.r, self.u, self.tz = F, C, fwd, right, up, tz
        return F

    def project(self, x, y, z=None):
        """Kartenpixel (x, y[, z]) → Bildschirm (sx, sy, Skalierung px pro Kartenpixel, Tiefe)."""
        if z is None:
            z = self.L.height_at(x, y)
        P = np.array([x, -y, z], f32) - self.C
        zc = float(P @ self.f)
        if zc <= 1e-3:
            return None
        s = self.F / zc
        return self.W / 2 + float(P @ self.r) * s, self.H / 2 - float(P @ self.u) * s, s, zc

    def ground_maps(self):
        """Pro Bildpunkt: Kartenkoordinaten (mx, my), Abstand (für Nebel)."""
        F, C, fw, r, u = self.F, self.C, self.f, self.r, self.u
        dx = fw[0] + (self.sx / F) * r[0] - (self.sy / F) * u[0]
        dy = fw[1] + (self.sx / F) * r[1] - (self.sy / F) * u[1]
        dz = fw[2] + (self.sx / F) * r[2] - (self.sy / F) * u[2]
        dz = np.minimum(dz, -1e-4)
        zt = self.tz
        t = (zt - C[2]) / dz
        hmap = self.L.height_half
        for it in range(3):
            gx = C[0] + t * dx
            gy = C[1] + t * dy
            hz = cv2.remap(hmap, gx * 0.5, -gy * 0.5, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            t_new = (hz - C[2]) / dz
            t = t + (t_new - t) * (0.85 if it < 2 else 1.0)
        mx = (C[0] + t * dx).astype(f32)
        my = (-(C[1] + t * dy)).astype(f32)
        depth = t * np.sqrt(dx * dx + dy * dy + dz * dz)
        return mx, my, depth

    # ---------------------------------------------------------------- Bodentextur
    def sample(self):
        """13-Kanal-Werte pro Bildpunkt (trilinear über die Mip-Stufen)."""
        L = self.L
        mx, my, depth = self.ground_maps()
        gxm = np.abs(np.diff(mx, axis=1, append=mx[:, -1:])) + np.abs(np.diff(my, axis=1, append=my[:, -1:]))
        gym = np.abs(np.diff(mx, axis=0, append=mx[-1:, :])) + np.abs(np.diff(my, axis=0, append=my[-1:, :]))
        foot = np.maximum(gxm, gym) * 0.8
        lod = np.log2(np.maximum(foot, 1e-3)).clip(0, L.levels - 1.001)
        lod = cv2.blur(lod, (15, 15))
        l_lo = int(math.floor(float(lod.min())))
        l_hi = min(int(math.floor(float(lod.max()))) + 1, L.levels - 1)
        acc = None
        wsum = np.zeros((self.H, self.W), f32)
        for lvl in range(l_lo, l_hi + 1):
            w = np.clip(1 - np.abs(lod - lvl), 0, 1)
            if lvl == l_lo:
                w = np.where(lod < lvl, 1.0, w)
            if lvl == l_hi:
                w = np.where(lod > lvl, 1.0, w)
            if float(w.max()) <= 1e-3:
                continue
            sc = 1.0 / (2.0 ** lvl)
            smp = cv2.remap(L.pyr[lvl], (mx * sc - 0.5 + 0.5 * sc).astype(f32), (my * sc - 0.5 + 0.5 * sc).astype(f32),
                            cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(f32)
            acc = smp * w[..., None] if acc is None else acc + smp * w[..., None]
            wsum += w
        acc /= np.maximum(wsum, 1e-4)[..., None]
        self.mx, self.my, self.depth = mx, my, depth
        return acc

    def ground(self, look):
        L = self.L
        s = self.sample()
        b, d, m = s[..., 0:3], s[..., 3:6], s[..., 6:9]
        o1 = s[..., 9] * L.ONSET_SCALE
        o2 = s[..., 10] * L.ONSET_SCALE
        never1 = s[..., 9] > 250
        never2 = s[..., 10] > 250
        s1 = np.where(never1, 0, np.clip((look.day - o1) / 7.0, 0, 1))[..., None]
        s2 = np.where(never2, 0, np.clip((look.day - o2) / 25.0, 0, 1))[..., None]
        fo = (s[..., 12] / 255.0)[..., None]
        if look.winter > 0:
            lum = b @ np.array([0.30, 0.55, 0.15], f32)
            wf = np.stack([lum * 1.06, lum * 0.97, lum * 0.80], -1) * 0.92 + b * 0.18
            wfo = b * np.array([0.92, 0.90, 0.86], f32) + np.array([14, 8, 4], f32)
            wcol = wf * (1 - fo) + wfo * fo
            b = b * (1 - look.winter) + wcol * look.winter
        col = b * (1 - s1) + d * s1
        col = col * (1 - s2) + m * s2
        if look.regrow > 0:
            reg = np.clip(s1 * 1.5, 0, 1) * look.regrow
            col = col * (1 - reg) + (b * fo + np.array([60, 92, 50], f32) * (1 - fo)) * reg
        if look.snow > 0:
            sn = (s[..., 11] / 255.0)[..., None]
            k = np.clip((sn - (1.0 - look.snow)) * 2.0, 0, 0.78) * (1 - 0.55 * s2) * (1 - 0.45 * fo)
            lumc = col.mean(-1, keepdims=True)
            snowc = np.array([214, 222, 234], f32) * (0.70 + 0.30 * np.clip(lumc / 120.0, 0, 1.4))
            col = col * (1 - k) + snowc * k
        mx, my, depth = self.mx, self.my, self.depth
        outside = (mx < 0) | (my < 0) | (mx > L.W) | (my > L.H)
        dn = depth / max(1.0, float(np.median(depth)))
        fogk = np.clip((dn - 0.8) * 0.9, 0, 1) * min(1.0, look.fog * 3)
        fogc = np.array([196, 202, 206], f32) * (1 - look.night * 0.8)
        fogc = fogc * (1 - look.dawn) + np.array([150, 140, 150], f32) * look.dawn
        col = col * (1 - fogk[..., None]) + fogc * fogk[..., None]
        col[outside] = fogc
        return col

    def grade(self, img, look):
        """Farbstimmung: Nacht, Morgendämmerung, Sättigung, Vignette."""
        if look.sat != 1.0:
            g = img.mean(-1, keepdims=True)
            img = g + (img - g) * look.sat
        if look.dawn > 0:
            dn = look.dawn
            lum = img.mean(-1, keepdims=True)
            cool = img * np.array([0.86, 0.92, 1.10], f32)
            warm = np.clip((lum - 150) / 80, 0, 1) * np.array([30, 10, -10], f32)
            img = img * (1 - dn) + (cool * 0.88 + warm + np.array([12, 8, 22], f32)) * dn
        if look.night > 0:
            n = look.night
            g = img.mean(-1, keepdims=True)
            img = img * (1 - n) + (g * np.array([0.45, 0.55, 0.85], f32) * 0.55) * n
        if look.gas > 0:
            img = img * (1 - 0.25 * look.gas) + np.array([150, 170, 60], f32) * 0.25 * look.gas
        # Vignette
        r = (self.sx / (self.W / 2)) ** 2 + (self.sy / (self.H / 2)) ** 2
        v = 1 - 0.28 * np.clip(r - 0.35, 0, 1)
        return img * v[..., None]
