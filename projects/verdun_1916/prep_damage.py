"""Zerstörungs-Verlauf: an welchem Tag der Schlacht wird jeder Kartenpunkt zerschossen / zum Trichterfeld?

Grundlage sind die Frontverläufe aus vgeo.FRONTS. Je länger die Front in der Nähe eines Punktes
liegt, desto mehr „Beschuss“ sammelt sich dort an. Überschreitet die Summe Schwellen, beginnt
Stufe 1 (zerschossen) bzw. Stufe 2 (Trichterfeld). Ergebnis (Viertel-Auflösung, uint16 = Tag):
  assets/ww1/maps/verdun/L3_onset1.png, L3_onset2.png
"""
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from warazlib.geo import Grid  # noqa: E402
from warazlib.mapstyle import _noise  # noqa: E402
import vgeo  # noqa: E402

OUT = os.path.join(ROOT, "assets", "ww1", "maps", "verdun")
DAYS = [("feb21", 1), ("feb24", 4), ("feb25", 5), ("feb26", 6), ("apr15", 55), ("may31", 101), ("jun07", 108),
        ("jun23", 124), ("jul12", 143), ("sep01", 194), ("oct24", 247), ("nov02", 256), ("dec18", 302)]
Q = 4  # Viertel-Auflösung


def main():
    g = Grid.load(os.path.join(OUT, "L3_grid.json"))
    w, h = g.w // Q + 1, g.h // Q + 1
    px_km = g.px_per_km() / Q
    dists = []
    for key, day in DAYS:
        img = np.full((h, w), 255, np.uint8)
        pts = np.array([g.px(la, lo) for (la, lo) in vgeo.FRONTS[key]], np.float32) / Q
        cv2.polylines(img, [np.round(pts).astype(np.int32)], False, 0, 2)
        dists.append(cv2.distanceTransform(img, cv2.DIST_L2, 5) / px_km)    # km
    rng = np.random.default_rng(3)
    nz = _noise(h, w, 18, rng, 5)
    E = np.zeros((h, w), np.float32)
    on1 = np.full((h, w), 9999, np.float32)
    on2 = np.full((h, w), 9999, np.float32)
    thr1 = 3.0 * (0.5 + nz)
    thr2 = 46.0 * (0.55 + 0.9 * nz)
    for i in range(len(DAYS)):
        d0 = DAYS[i][1]
        d1 = DAYS[i + 1][1] if i + 1 < len(DAYS) else 302
        dk = dists[i]
        rate = np.exp(-(dk / 0.95) ** 2) + 0.07 * np.exp(-(dk / 2.6) ** 2)
        if d0 < 6:
            rate = rate * 4.0          # Trommelfeuer der ersten Tage
        for day in range(d0, max(d0 + 1, d1)):
            E += rate
            on1 = np.where((on1 > 9000) & (E >= thr1), day, on1)
            on2 = np.where((on2 > 9000) & (E >= thr2), day, on2)
    on1 = cv2.GaussianBlur(on1.clip(0, 9999), (0, 0), 3.0)
    on2 = cv2.GaussianBlur(on2.clip(0, 9999), (0, 0), 3.0)
    cv2.imwrite(os.path.join(OUT, "L3_onset1.png"), on1.clip(0, 65535).astype(np.uint16))
    cv2.imwrite(os.path.join(OUT, "L3_onset2.png"), on2.clip(0, 65535).astype(np.uint16))
    for day in (5, 101, 143, 302):
        s = (np.clip((day - on1) / 7, 0, 1) * 120 + np.clip((day - on2) / 25, 0, 1) * 135).astype(np.uint8)
        cv2.imwrite(os.path.join(ROOT, "work", "stilprobe", f"damage_day{day}.jpg"), s)
    print("ok", (on1 < 400).mean(), (on2 < 400).mean())


if __name__ == "__main__":
    main()
