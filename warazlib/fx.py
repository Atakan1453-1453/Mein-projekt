"""Prozedurale Effekte (per Code erzeugt, als Bildfolgen in assets/ww1/fx gespeichert).

  explosion   Granateinschlag: Blitz, Feuerball, Erdfontäne, Rauch (Flipbook, RGBA)
  smoke       weicher Rauchballen (einzeln, zum Aufsteigen/Treiben)
  muzzle      Mündungsfeuer
  crater      Trichter-Abziehbild (von oben)
  gas         gelbgrüne Gasschwade
  fire        Flammen-Flipbook
"""
import math
import os

import cv2
import numpy as np

f32 = np.float32


def _blob_noise(h, w, rng, scale=8.0):
    g = rng.random((int(h / scale) + 3, int(w / scale) + 3)).astype(f32)
    n = cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
    g2 = rng.random((int(h / scale * 2) + 3, int(w / scale * 2) + 3)).astype(f32)
    n += 0.5 * cv2.resize(g2, (w, h), interpolation=cv2.INTER_CUBIC)
    return n / 1.5


def _puff(canvas_a, canvas_c, cx, cy, r, color, alpha, noise):
    h, w = canvas_a.shape
    yy, xx = np.ogrid[:h, :w]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(r, 1e-3)
    a = np.clip(1.12 - d - 0.22 * (noise - 0.5), 0, 1) ** 1.2 * alpha
    # Licht von oben links
    shade = np.clip(1.08 - 0.22 * ((xx - cx) + (yy - cy)) / max(r, 1e-3), 0.65, 1.2)
    c = np.array(color, f32)[None, None, :] * shade[..., None]
    na = a + canvas_a * (1 - a)
    canvas_c[:] = (c * a[..., None] + canvas_c * (canvas_a * (1 - a))[..., None]) / np.maximum(na, 1e-4)[..., None]
    canvas_a[:] = na


def explosion_frames(n=48, W=320, H=400, seed=1):
    """Flipbook eines Granateinschlags (Boden bei y = H - 40)."""
    rng = np.random.default_rng(seed)
    gy = H - 40
    cx = W / 2
    noise = _blob_noise(H, W, rng, 16)
    dirt = [(rng.normal(0, 0.22), rng.uniform(0.6, 1.0), rng.uniform(9, 20)) for _ in range(40)]
    smoke = [(rng.normal(0, 0.35), rng.uniform(0.35, 1.0), rng.uniform(30, 52), rng.uniform(0.6, 1.0)) for _ in range(18)]
    frames = []
    for i in range(n):
        t = i / (n - 1)
        A = np.zeros((H, W), f32)
        Cc = np.zeros((H, W, 3), f32)
        nz = np.roll(noise, i * 2, 0)
        for (dx, sp, rr, gray) in smoke:
            tt = max(0.0, t - 0.04)
            if tt <= 0:
                continue
            rise = 230 * sp * (1 - math.exp(-tt * 2.6))
            x = cx + dx * 70 * (0.4 + tt) + 26 * tt
            y = gy - 30 - rise
            r = rr * (0.45 + 1.25 * tt)
            al = 0.80 * math.exp(-max(0, tt - 0.45) * 2.8) * min(1, tt * 10)
            g = 40 + 52 * gray * tt
            _puff(A, Cc, x, y, r, (g * 1.02, g * 0.97, g * 0.9), al, nz)
        if t < 0.7:
            tt = t / 0.7
            for (dx, sp, rr) in dirt:
                x = cx + dx * 150 * tt
                y = gy - (430 * sp * tt - 460 * tt * tt)
                if y > gy + 4:
                    continue
                r = rr * (1 + 0.8 * tt)
                al = 0.97 * (1 - tt ** 2.5)
                _puff(A, Cc, x, y, r, (70, 55, 38), al, nz)
        if t < 0.30:
            tt = t / 0.30
            r = 34 + 62 * tt ** 0.5
            al = (1 - tt) ** 1.1
            _puff(A, Cc, cx, gy - 24 - 34 * tt, r, (255, 170 - 80 * tt, 50 - 40 * tt), al, nz)
            _puff(A, Cc, cx, gy - 20 - 28 * tt, r * 0.6, (255, 240, 190), al * (1 - tt) ** 0.7, nz)
        frames.append(np.dstack([np.clip(Cc, 0, 255), np.clip(A * 255, 0, 255)]).astype(np.uint8))
    return frames


def flash_sprite(size=256):
    yy, xx = np.mgrid[:size, :size].astype(f32) - size / 2
    d = np.sqrt(xx * xx + yy * yy) / (size / 2)
    a = np.clip(1 - d, 0, 1) ** 2.2
    c = np.dstack([np.full_like(a, 255), 220 - 40 * d, 150 - 80 * d])
    return np.dstack([np.clip(c, 0, 255), a * 255]).astype(np.uint8)


def smoke_sprite(size=128, seed=2):
    rng = np.random.default_rng(seed)
    A = np.zeros((size, size), f32)
    C = np.zeros((size, size, 3), f32)
    n = _blob_noise(size, size, rng, 8)
    for k in range(7):
        _puff(A, C, size / 2 + rng.normal(0, size * 0.1), size / 2 + rng.normal(0, size * 0.1),
              size * rng.uniform(0.22, 0.34), (150, 148, 144), 0.6, n)
    return np.dstack([np.clip(C, 0, 255), A * 255]).astype(np.uint8)


def muzzle_sprite(W=128, H=64):
    yy, xx = np.mgrid[:H, :W].astype(f32)
    cx, cy = 18, H / 2
    d = np.sqrt(((xx - cx) / 2.6) ** 2 + (yy - cy) ** 2) / (H / 2)
    a = np.clip(1 - d, 0, 1) ** 1.6 * (xx > cx - 8)
    c = np.dstack([np.full_like(a, 255), 236 - 60 * d, 170 - 120 * d])
    return np.dstack([np.clip(c, 0, 255), np.clip(a * 255, 0, 255)]).astype(np.uint8)


def crater_decal(size=96, seed=3):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[:size, :size].astype(f32) - size / 2
    d = np.sqrt(xx * xx + yy * yy) / (size / 2)
    n = _blob_noise(size, size, rng, 6)
    n = cv2.GaussianBlur(n, (0, 0), 3)
    d = d + 0.10 * (n - 0.5)
    bowl = np.clip(1 - d / 0.70, 0, 1)
    rim = np.exp(-((d - 0.78) / 0.12) ** 2)
    spray = np.clip(1 - d, 0, 1) ** 0.8 * np.clip((n - 0.45) * 4, 0, 1) * 0.6
    a = np.clip(bowl * 0.95 + rim * 0.9 + spray * 0.5, 0, 1)
    light = np.clip(0.5 - 0.5 * (xx + yy) / size * 2, 0, 1)
    col = np.dstack([58 + 70 * rim * light + 20 * spray, 48 + 60 * rim * light + 16 * spray, 38 + 50 * rim * light + 12 * spray])
    col = col * (1 - bowl[..., None] * 0.35)
    return np.dstack([np.clip(col, 0, 255), np.clip(a * 255, 0, 255)]).astype(np.uint8)


def gas_sprite(size=256, seed=4):
    rng = np.random.default_rng(seed)
    A = np.zeros((size, size), f32)
    C = np.zeros((size, size, 3), f32)
    n = _blob_noise(size, size, rng, 12)
    for k in range(10):
        _puff(A, C, size / 2 + rng.normal(0, size * 0.14), size / 2 + rng.normal(0, size * 0.08),
              size * rng.uniform(0.16, 0.28), (196, 204, 96), 0.45, n)
    return np.dstack([np.clip(C, 0, 255), A * 200]).astype(np.uint8)


def fire_frames(n=24, W=96, H=128, seed=5):
    rng = np.random.default_rng(seed)
    frames = []
    for i in range(n):
        A = np.zeros((H, W), f32)
        C = np.zeros((H, W, 3), f32)
        nn = _blob_noise(H, W, np.random.default_rng(seed * 100 + i), 6)
        for k in range(9):
            ph = (i / n + k / 9) % 1.0
            y = H - 14 - ph * 80
            x = W / 2 + math.sin(ph * 6 + k) * 8
            r = 16 * (1 - ph) + 4
            col = (255, 220 - 150 * ph, 90 - 80 * ph)
            _puff(A, C, x, y, r, col, 0.9 * (1 - ph), nn)
        frames.append(np.dstack([np.clip(C, 0, 255), np.clip(A * 255, 0, 255)]).astype(np.uint8))
    return frames


def build_library(folder):
    os.makedirs(folder, exist_ok=True)
    for name, frames in (("explosion", explosion_frames()), ("fire", fire_frames())):
        d = os.path.join(folder, name)
        os.makedirs(d, exist_ok=True)
        for i, fr in enumerate(frames):
            cv2.imwrite(os.path.join(d, f"{i:03d}.png"), cv2.cvtColor(fr, cv2.COLOR_RGBA2BGRA))
    for name, img in (("flash", flash_sprite()), ("smoke", smoke_sprite()), ("muzzle", muzzle_sprite()),
                      ("crater", crater_decal()), ("gas", gas_sprite())):
        cv2.imwrite(os.path.join(folder, name + ".png"), cv2.cvtColor(img, cv2.COLOR_RGBA2BGRA))


def load_library(folder):
    def rd(p):
        return cv2.cvtColor(cv2.imread(p, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
    lib = {}
    for name in ("explosion", "fire"):
        d = os.path.join(folder, name)
        lib[name] = [rd(os.path.join(d, f)) for f in sorted(os.listdir(d))]
    for name in ("flash", "smoke", "muzzle", "crater", "gas"):
        lib[name] = rd(os.path.join(folder, name + ".png"))
    return lib
