"""Baut die Karte „Verdun“ (Detailkarte L3) für die Asset-Bibliothek.

  python3 projects/verdun_1916/prep_map.py
→ assets/ww1/maps/verdun/L3_{base,damaged,moon}.jpg, L3_{forest,water,snow,shade}.png, L3_dem.npy, L3_grid.json
"""
import os
import sys
import time

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from warazlib.geo import Grid  # noqa: E402
from warazlib import terrain_data, mapstyle  # noqa: E402
import vgeo  # noqa: E402

CACHE = os.path.join(ROOT, "cache")
OUT = os.path.join(ROOT, "assets", "ww1", "maps", "verdun")
os.makedirs(OUT, exist_ok=True)

GRID = Grid(49.08, 5.05, 49.36, 5.62, 6.0)
GRID_L2 = Grid(48.70, 4.85, 49.45, 5.85, 30.0)

# Dörfer 1916 (Name im vgeo.P, ungefähre Häuserzahl für die Darstellung)
VILLAGES = [("douaumont_dorf", 34), ("fleury", 40), ("vaux_dorf", 26), ("damloup", 24), ("louvemont", 26),
            ("bezonvaux", 30), ("ornes", 44), ("beaumont", 30), ("haumont", 26), ("samogneux", 30), ("brabant", 26),
            ("champneuville", 24), ("vacherauville", 26), ("bras", 40), ("eix", 26), ("moulainville", 26),
            ("flabas", 26), ("ville", 26), ("consenvoye", 32), ("cumieres", 30), ("chattancourt", 26),
            ("bethincourt", 24), ("malancourt", 28), ("avocourt", 28), ("esnes", 30), ("forges", 26),
            ("montfaucon", 40)]
# weitere Dörfer (nicht in vgeo): Charny, Thierville, Belleville, Fromeréville, Marre, Haudainville, Belrupt
EXTRA_VILLAGES = [((49.1985, 5.3600), 30), ((49.1620, 5.3530), 34), ((49.1790, 5.3870), 30), ((49.1680, 5.3060), 26),
                  ((49.2080, 5.3150), 22), ((49.1180, 5.4180), 26), ((49.1480, 5.4410), 22)]


def build_L2():
    """Regionalkarte (30 m/px): Maas, Argonnen, Woëvre, Bar-le-Duc, Souilly."""
    g = GRID_L2
    dem = terrain_data.dem(g, 10, CACHE)
    wc = terrain_data.worldcover(g, CACHE)
    forts = []
    for (name, la, lo, big) in vgeo.FORTS:
        x, y = g.px(la, lo)
        forts.append((x, y, 7 if name == "Douaumont" else 5, big))
    pts = np.array([g.px(la, lo) for z in vgeo.ZONES.values() for (la, lo) in z], np.float32)
    hull = cv2.convexHull(pts)[:, 0, :]
    c = hull.mean(0)
    hull = c + (hull - c) * 1.12
    vx, vy = g.px(*vgeo.P["verdun"])
    vill = [(x, y, n) for (x, y, n) in [(*g.px(*vgeo.P[k]), 6) for k, _ in VILLAGES]]
    tex = mapstyle.build(dem, wc, g.ground_res, [], forts, (vx, vy), clear_poly=hull, city_r=60)
    for k in ("base", "damaged", "moon"):
        cv2.imwrite(os.path.join(OUT, f"L2_{k}.jpg"), tex[k][..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
    for k in ("forest", "water"):
        cv2.imwrite(os.path.join(OUT, f"L2_{k}.png"), tex[k])
    cv2.imwrite(os.path.join(OUT, "L2_snow.jpg"), tex["snow"], [cv2.IMWRITE_JPEG_QUALITY, 90])
    half = cv2.resize(dem, (g.w // 2, g.h // 2), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(OUT, "L2_dem16.png"), np.clip((half - 100) * 100, 0, 65535).astype(np.uint16))
    g.save(os.path.join(OUT, "L2_grid.json"))
    print("L2 fertig", g.w, g.h)


def main():
    if "L2" in sys.argv:
        return build_L2()
    t = time.time()
    dem = terrain_data.dem(GRID, 12, CACHE)
    wc = terrain_data.worldcover(GRID, CACHE)
    print("Daten", round(time.time() - t, 1), "s", flush=True)
    vill = []
    for name, n in VILLAGES:
        x, y = GRID.px(*vgeo.P[name])
        vill.append((x, y, n))
    for (ll, n) in EXTRA_VILLAGES:
        x, y = GRID.px(*ll)
        vill.append((x, y, n))
    forts = []
    for (name, la, lo, big) in vgeo.FORTS:
        x, y = GRID.px(la, lo)
        if 0 <= x < GRID.w and 0 <= y < GRID.h:
            forts.append((x, y, 34 if name == "Douaumont" else (26 if big else 18), big))
    # Lichtungs-Zone: das spätere Schlachtfeld (Hüllpolygon der Trichterzonen, etwas größer)
    pts = np.array([GRID.px(la, lo) for z in vgeo.ZONES.values() for (la, lo) in z], np.float32)
    hull = cv2.convexHull(pts)[:, 0, :]
    c = hull.mean(0)
    hull = c + (hull - c) * 1.12
    vx, vy = GRID.px(*vgeo.P["verdun"])
    t = time.time()
    tex = mapstyle.build(dem, wc, GRID.res * 0 + GRID.ground_res, vill, forts, (vx, vy), clear_poly=hull)
    print("Textur", round(time.time() - t, 1), "s", flush=True)
    for k in ("base", "damaged", "moon"):
        cv2.imwrite(os.path.join(OUT, f"L3_{k}.jpg"), tex[k][..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
    for k in ("forest", "water"):
        cv2.imwrite(os.path.join(OUT, f"L3_{k}.png"), tex[k])
    cv2.imwrite(os.path.join(OUT, "L3_snow.jpg"), tex["snow"], [cv2.IMWRITE_JPEG_QUALITY, 90])
    np.save(os.path.join(CACHE, "verdun_L3_dem.npy"), dem.astype(np.float32))
    half = cv2.resize(dem, (GRID.w // 2, GRID.h // 2), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(OUT, "L3_dem16.png"), np.clip((half - 100) * 100, 0, 65535).astype(np.uint16))
    GRID.save(os.path.join(OUT, "L3_grid.json"))
    print("fertig", OUT)


if __name__ == "__main__":
    main()
