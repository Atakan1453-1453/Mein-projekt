"""Bereitet die Kartengrundlagen vor (einmalig, ca. 5-10 Minuten).

Erzeugt im Cache-Ordner (Standard: ./cache, per CNK_CACHE änderbar):
  sat_L3.jpg / sat_L3.json   Satellit + Relief, Schlachtfeld Amiens (Somme bis Montdidier), ~14 m/px (Web-Mercator)
  sat_L2.jpg / sat_L2.json   Satellit + Relief, Picardie von Abbeville bis Saint-Quentin, ~60 m/px
  europe.jpg / europe.json   stilisierte Reliefkarte Europa/Nahost (für die Bündniskarte)

Quellen (frei nutzbar):
  * Copernicus Sentinel-2 L2A (ESA), über AWS Open Data "sentinel-cogs"
  * Höhendaten: AWS Terrain Tiles (Terrarium, SRTM/GMTED/ETOPO, Mapzen)
"""
import json
import math
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import rasterio
from PIL import Image
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("CNK_DATA", os.path.join(HERE, "data"))
CACHE = os.environ.get("CNK_CACHE", os.path.join(HERE, "cache"))
os.makedirs(CACHE, exist_ok=True)
os.environ.setdefault("CURL_CA_BUNDLE", "/root/.ccr/ca-bundle.crt")

R = 6378137.0
S2 = "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/31"
TERRARIUM = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium"

# Wolkenfreie Aufnahmen vom 12. August 2025 (alle vier Kacheln am selben Tag – fast genau am Jahrestag der Schlacht)
SCENES_L2 = [
    ("U/DR", "2025/8/S2C_31UDR_20250812_0_L2A"),
    ("U/ER", "2025/8/S2C_31UER_20250812_0_L2A"),
    ("U/DQ", "2025/8/S2C_31UDQ_20250812_0_L2A"),
    ("U/EQ", "2025/8/S2C_31UEQ_20250812_0_L2A"),
]
SCENES_L3 = SCENES_L2
L3_BOX = (2.20, 3.00, 49.60, 50.03)
L2_BOX = (1.60, 3.60, 49.35, 50.25)


def merc(lon, lat):
    return R * math.radians(lon), R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def grid(lon0, lon1, lat0, lat1, res):
    x0, y0 = merc(lon0, lat0)
    x1, y1 = merc(lon1, lat1)
    w = int(round((x1 - x0) / res))
    h = int(round((y1 - y0) / res))
    return dict(x0=x0, y1=y1, res=res, w=w, h=h, transform=from_origin(x0, y1, res, res))


# ---------------------------------------------------------------- Höhendaten
def tile_xy(lon, lat, z):
    n = 2 ** z
    x = int((lon + 180) / 360 * n)
    r = math.radians(lat)
    y = int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n)
    return x, y


def fetch_tile(z, x, y):
    path = os.path.join(DATA, "dem", str(z), str(x), f"{y}.png")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        for attempt in range(6):
            r = subprocess.run(["curl", "-s", "--retry", "3", "--retry-all-errors", "-o", path, f"{TERRARIUM}/{z}/{x}/{y}.png"])
            if r.returncode == 0 and os.path.getsize(path) > 0:
                break
            import time
            time.sleep(2 + attempt * 2)
    return path


def dem_for_grid(g, z):
    """Terrarium-Kacheln mosaikieren und auf das Zielraster bringen (Meter)."""
    lon0 = math.degrees(g["x0"] / R)
    lon1 = math.degrees((g["x0"] + g["w"] * g["res"]) / R)
    lat1 = math.degrees(2 * math.atan(math.exp(g["y1"] / R)) - math.pi / 2)
    lat0 = math.degrees(2 * math.atan(math.exp((g["y1"] - g["h"] * g["res"]) / R)) - math.pi / 2)
    tx0, ty0 = tile_xy(lon0, lat1, z)
    tx1, ty1 = tile_xy(lon1, lat0, z)
    jobs = [(z, x, y) for x in range(tx0, tx1 + 1) for y in range(ty0, ty1 + 1)]
    with ThreadPoolExecutor(16) as ex:
        list(ex.map(lambda a: fetch_tile(*a), jobs))
    nx, ny = tx1 - tx0 + 1, ty1 - ty0 + 1
    mosaic = np.zeros((ny * 256, nx * 256), np.float32)
    for (zz, x, y) in jobs:
        try:
            a = np.asarray(Image.open(os.path.join(DATA, "dem", str(z), str(x), f"{y}.png")).convert("RGB")).astype(np.float32)
        except Exception:
            print("  Höhenkachel fehlt:", z, x, y, flush=True)
            continue
        e = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
        mosaic[(y - ty0) * 256:(y - ty0 + 1) * 256, (x - tx0) * 256:(x - tx0 + 1) * 256] = e
    world = 2 * math.pi * R
    tres = world / (256 * 2 ** z)
    src_tr = from_origin(-world / 2 + tx0 * 256 * tres, world / 2 - ty0 * 256 * tres, tres, tres)
    out = np.zeros((g["h"], g["w"]), np.float32)
    reproject(mosaic, out, src_transform=src_tr, src_crs="EPSG:3857", dst_transform=g["transform"],
              dst_crs="EPSG:3857", resampling=Resampling.cubic)
    return out


def hillshade(dem, res_ground, az=315.0, alt=40.0, zf=1.0):
    gy, gx = np.gradient(dem * zf, res_ground)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    azr, altr = math.radians(az), math.radians(alt)
    hs = np.sin(altr) * np.cos(slope) + np.cos(altr) * np.sin(slope) * np.cos(azr - aspect - math.pi / 2)
    return np.clip(hs, 0, 1)


# ---------------------------------------------------------------- Satellit
def read_sat(g, scenes, overview=None):
    out = np.zeros((3, g["h"], g["w"]), np.uint8)
    for tile, key in scenes:
        local = os.path.join(DATA, "s2", f"{key.split('/')[-1]}_TCI.tif")
        url = local if os.path.exists(local) else f"/vsicurl/{S2}/{tile}/{key}/TCI.tif"
        kw = {} if overview is None else {"overview_level": overview}
        print("  lese", tile, key.split("/")[-1], "ov", overview, flush=True)
        with rasterio.open(url, **kw) as src:
            data = src.read()
            tmp = np.zeros_like(out)
            reproject(data, tmp, src_transform=src.transform, src_crs=src.crs, src_nodata=0,
                      dst_transform=g["transform"], dst_crs="EPSG:3857", dst_nodata=0,
                      resampling=Resampling.average if overview is not None else Resampling.bilinear)
        hole = out.sum(0) == 0
        for b in range(3):
            out[b][hole] = tmp[b][hole]
    return out


WATER_DEEP = np.array([0.030, 0.062, 0.088], np.float32)
WATER_SHALLOW = np.array([0.060, 0.135, 0.150], np.float32)


def water_mask(sat, dem, res_ground, refine):
    """Wasser = 1, Land = 0. Grundlage Höhenmodell; nahe der Küste optional per Satellitenfarbe verfeinert."""
    land_dem = dem > 0.5
    if not refine:
        m = ndimage.gaussian_filter((~land_dem).astype(np.float32), 0.8)
        return m
    rgb = sat.astype(np.float32)
    r, g, b = rgb[0], rgb[1], rgb[2]
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    looks_water = (b >= r) & (b >= g * 0.95) & (luma < 70)
    band = int(round(180 / res_ground))          # ±180 m um die DEM-Küste
    near = ndimage.binary_dilation(land_dem, iterations=band) & ndimage.binary_dilation(~land_dem, iterations=band)
    water = np.where(near, looks_water, ~land_dem)
    water = ndimage.binary_opening(water, iterations=1)
    water = ndimage.binary_closing(water, iterations=2)
    # kleine Inseln/Flecken entfernen
    lab, n = ndimage.label(water)
    if n:
        sizes = ndimage.sum(water, lab, range(1, n + 1))
        water = np.isin(lab, np.nonzero(sizes > 400)[0] + 1)
    return ndimage.gaussian_filter(water.astype(np.float32), 0.9)


def grade(sat, dem, res_ground, hs_strength=0.55, refine=False):
    """Satellitenbild + Relief, gedeckter Doku-Look, einheitliches Wasser."""
    rgb = sat.transpose(1, 2, 0).astype(np.float32) / 255.0
    empty = rgb.sum(2) == 0
    rgb = np.clip((rgb - 0.02) * 1.30, 0, 1) ** 0.95
    lum = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    rgb = lum[..., None] + (rgb - lum[..., None]) * 0.78
    hs = hillshade(dem, res_ground, zf=1.6)
    hs = ndimage.gaussian_filter(hs, 0.6)
    shade = 1.0 + hs_strength * (hs - 0.62) * 1.6
    rgb = rgb * shade[..., None]
    lum = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    rgb += (np.array([0.035, 0.015, -0.02]) * lum[..., None] + np.array([-0.01, 0.0, 0.015]) * (1 - lum[..., None]))
    rgb = np.clip(rgb, 0, 1)
    if empty.any():
        fill = relief_style(dem, res_ground)
        e = ndimage.gaussian_filter(empty.astype(np.float32), 3)
        rgb = rgb * (1 - e[..., None]) + fill * e[..., None]
    # Wasser: einheitlich, flaches Küstenwasser etwas heller
    wm = water_mask(sat, dem, res_ground, refine)
    dist = ndimage.distance_transform_edt(wm > 0.5) * res_ground
    shallow = np.exp(-dist / 350.0)[..., None]
    rng = np.random.default_rng(1)
    noise = ndimage.gaussian_filter(rng.standard_normal(dem.shape).astype(np.float32), 3.0)[..., None] * 0.04
    wcol = WATER_DEEP * (1 - shallow) + WATER_SHALLOW * shallow
    wcol = wcol * (1 + noise)
    if refine:   # bei der Detailkarte etwas echte Wasserstruktur behalten
        orig = sat.transpose(1, 2, 0).astype(np.float32) / 255.0
        ol = orig @ np.array([0.299, 0.587, 0.114], np.float32)
        wcol = wcol * (0.75 + 0.25 * np.clip(ol / 0.12, 0, 2)[..., None])
    w = wm[..., None]
    rgb = rgb * (1 - w) + wcol * w
    return (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)


def relief_style(dem, res_ground, dark=False):
    hs = hillshade(dem, res_ground, zf=2.5 if res_ground > 500 else 1.6)
    h = np.clip(dem, 0, 3000) / 3000.0
    if dark:
        land = np.stack([0.20 + 0.18 * h, 0.21 + 0.13 * h, 0.19 + 0.08 * h], -1)
        sea = np.array([0.055, 0.085, 0.115], np.float32)
    else:
        land = np.stack([0.42 + 0.25 * h, 0.44 + 0.15 * h, 0.30 + 0.12 * h], -1)
        sea = np.array([0.05, 0.11, 0.15], np.float32)
    shade = (0.55 + 0.75 * hs)[..., None]
    depth = np.clip(-dem / 3000.0, 0, 1)[..., None]
    seac = sea * (1 - 0.45 * depth)
    m = ndimage.gaussian_filter((dem > 0.5).astype(np.float32), 1.0)[..., None]
    return np.clip(land * shade * m + seac * (1 - m), 0, 1).astype(np.float32)


def save(name, img, g, quality=93):
    Image.fromarray(img).save(os.path.join(CACHE, name + ".jpg"), quality=quality, subsampling=0)
    meta = dict(x0=g["x0"], y1=g["y1"], res=g["res"], w=g["w"], h=g["h"])
    json.dump(meta, open(os.path.join(CACHE, name + ".json"), "w"))
    print("gespeichert", name, img.shape, flush=True)


def build_L3():
    g = grid(*L3_BOX, 14.0)
    print("L3", g["w"], g["h"], flush=True)
    dem = dem_for_grid(g, 13)
    sat = read_sat(g, SCENES_L3)
    res_ground = g["res"] * math.cos(math.radians(49.8))
    save("sat_L3", grade(sat, dem, res_ground, refine=True), g)
    np.save(os.path.join(CACHE, "dem_L3.npy"), dem.astype(np.float16))


def build_L2():
    g = grid(*L2_BOX, 60.0)
    print("L2", g["w"], g["h"], flush=True)
    dem = dem_for_grid(g, 11)
    sat = read_sat(g, SCENES_L2, overview=1)
    res_ground = g["res"] * math.cos(math.radians(49.8))
    save("sat_L2", grade(sat, dem, res_ground, hs_strength=0.75), g)


def build_europe():
    g = grid(-16.0, 58.0, 22.0, 67.0, 2400.0)
    print("Europa", g["w"], g["h"], flush=True)
    dem = dem_for_grid(g, 6)
    img = relief_style(dem, g["res"] * 0.7, dark=True)
    save("europe", (img * 255 + 0.5).astype(np.uint8), g)
    np.save(os.path.join(CACHE, "dem_europe.npy"), dem.astype(np.float16))


def build_craters():
    """Trichterwüste als Textur (RGBA, Mercator, 8 m/px): Alpha = Vereinigung der Trichterzonen (weicher Rand)."""
    import vgeo
    from PIL import ImageDraw
    from scipy.signal import fftconvolve
    lat0, lon0, lat1, lon1 = vgeo.CRATER_BOX
    res = 8.0
    x0, y0 = merc(lon0, lat0)
    x1, y1 = merc(lon1, lat1)
    w, h = int((x1 - x0) / res), int((y1 - y0) / res)
    print("Trichter", w, h, flush=True)
    rng = np.random.default_rng(1916)
    hgt = np.zeros((h, w), np.float32)
    for r, per in ((3, 110), (4, 230), (6, 650), (9, 2300), (13, 9000)):
        n = int(w * h / per)
        imp = np.zeros((h, w), np.float32)
        np.add.at(imp, (rng.integers(0, h, n), rng.integers(0, w, n)), 1.0)
        R_ = int(r * 1.8) + 1
        yy, xx = np.mgrid[-R_:R_ + 1, -R_:R_ + 1].astype(np.float32)
        d = np.hypot(xx, yy) / r
        k = np.where(d < 1, -(1 - d ** 2), 0) + 0.35 * np.exp(-((d - 1.0) / 0.35) ** 2)
        hgt += fftconvolve(imp, (k * r).astype(np.float32), mode="same").astype(np.float32)
        print("  r", r, n, flush=True)
    gy, gx = np.gradient(hgt)
    shade = np.clip(0.55 + (-gx - gy) * 0.09, 0.0, 1.2)
    low = ndimage.gaussian_filter(rng.standard_normal((h // 8 + 1, w // 8 + 1)).astype(np.float32), 3)
    low = np.kron(low, np.ones((8, 8), np.float32))[:h, :w]
    low /= (np.abs(low).max() + 1e-6)
    hi = rng.standard_normal((h, w)).astype(np.float32) * 0.025
    base = np.array([0.40, 0.335, 0.27], np.float32)
    rgb = base[None, None, :] * (1 + 0.16 * low[..., None]) + hi[..., None]
    depth = np.clip(-hgt / (np.percentile(-hgt, 99) + 1e-6), -1, 1)
    rgb = rgb * (0.62 + 0.55 * shade[..., None]) * (1 - 0.22 * np.clip(depth, 0, 1)[..., None])
    puddle = (depth > 0.72) & (ndimage.gaussian_filter(rng.random((h, w)).astype(np.float32), 6) > 0.505)
    rgb[puddle] = rgb[puddle] * 0.35 + np.array([0.16, 0.20, 0.22], np.float32) * 0.65
    stumps = rng.random((h, w)) < 0.0015
    rgb[stumps] = np.array([0.13, 0.11, 0.09], np.float32)
    # Alpha: Zonen
    mask = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(mask)
    for pts in vgeo.ZONES.values():
        poly = []
        for la, lo in pts:
            X, Y = merc(lo, la)
            poly.append(((X - x0) / res, (y1 - Y) / res))
        dr.polygon(poly, fill=255)
    m = ndimage.gaussian_filter(np.asarray(mask, np.float32) / 255.0, 22)
    rag = ndimage.gaussian_filter(rng.random((h, w)).astype(np.float32), 10)
    rag = (rag - rag.mean()) / (rag.std() + 1e-6)
    alpha = np.clip((m - 0.25 + 0.10 * rag) * 2.2, 0, 1) * (0.88 + 0.12 * np.clip(shade, 0, 1))
    out = np.dstack([np.clip(rgb, 0, 1) * 255, alpha * 255]).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(os.path.join(CACHE, "craters.png"), compress_level=3)
    json.dump(dict(x0=x0, y1=y1, res=res, w=w, h=h), open(os.path.join(CACHE, "craters.json"), "w"))
    print("gespeichert craters", out.shape, flush=True)


# ---------------------------------------------------------------- Landbedeckung (ESA WorldCover) für Übersichtskarten
WC = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{ns}{lat:02d}{ew}{lon:03d}_Map.tif"
WC_CLASSES = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]


def wc_for_grid(g, lon0, lon1, lat0, lat1, level):
    """WorldCover-Klassen (uint8) auf das Mercator-Raster g bringen; fehlende Kacheln (Meer) = 0."""
    out = np.zeros((g["h"], g["w"]), np.uint8)
    tiles = [(la, lo) for la in range(int(math.floor(lat0 / 3) * 3), int(math.ceil(lat1 / 3) * 3), 3)
             for lo in range(int(math.floor(lon0 / 3) * 3), int(math.ceil(lon1 / 3) * 3), 3)]

    def one(tile):
        la, lo = tile
        url = WC.format(ns="N" if la >= 0 else "S", lat=abs(la), ew="E" if lo >= 0 else "W", lon=abs(lo))
        try:
            with rasterio.open("/vsicurl/" + url, overview_level=level) as src:
                return tile, src.read(1), src.transform, src.crs
        except Exception:
            return tile, None, None, None
    with ThreadPoolExecutor(16) as ex:
        res = list(ex.map(one, tiles))
    n_ok = 0
    for tile, data, tr, crs in res:
        if data is None:
            continue
        n_ok += 1
        tmp = np.zeros_like(out)
        reproject(data, tmp, src_transform=tr, src_crs=crs, src_nodata=0, dst_transform=g["transform"], dst_crs="EPSG:3857",
                  dst_nodata=0, resampling=Resampling.mode)
        m = (out == 0) & (tmp != 0)
        out[m] = tmp[m]
    print("  WorldCover-Kacheln", n_ok, "von", len(tiles), flush=True)
    return out


def wc_palette():
    """Mittlere Farbe des (gradierten) Satellitenbilds je Landbedeckungsklasse – damit Übersichtskarte und Satellit zusammenpassen."""
    meta = json.load(open(os.path.join(CACHE, "sat_L2.json")))
    g = dict(x0=meta["x0"], y1=meta["y1"], res=meta["res"], w=meta["w"], h=meta["h"],
             transform=from_origin(meta["x0"], meta["y1"], meta["res"], meta["res"]))
    cls = wc_for_grid(g, *L2_BOX, 3)
    sat = np.asarray(Image.open(os.path.join(CACHE, "sat_L2.jpg")).convert("RGB")).astype(np.float32) / 255
    pal = {}
    for c in WC_CLASSES:
        m = cls == c
        if m.sum() > 200:
            pal[c] = sat[m].mean(0)
    # Felder: helle (abgeerntete) und grüne Anteile getrennt, für ein Flickenmuster
    m = cls == 40
    crop = sat[m]
    lum = crop @ np.array([0.299, 0.587, 0.114], np.float32)
    green = (crop[:, 1] > crop[:, 0] * 1.02)
    pal["crop_gold"] = crop[~green & (lum > np.median(lum))].mean(0)
    pal["crop_green"] = crop[green].mean(0) if green.sum() > 100 else pal[40]
    fallback = {20: pal.get(30, pal[10]), 60: np.array([0.55, 0.52, 0.47], np.float32), 70: np.array([0.9, 0.92, 0.95], np.float32),
                80: WATER_DEEP, 90: pal.get(30, pal[10]), 95: pal[10], 100: pal.get(30, pal[10])}
    for c, v in fallback.items():
        pal.setdefault(c, v)
    print("  Palette:", {k: np.round(v, 2).tolist() for k, v in pal.items()}, flush=True)
    return pal


def colorize_wc(cls, dem, res_ground, pal, seed, hs_strength=0.6, zf=1.6, patch_px=1.0):
    h, w = cls.shape
    rng = np.random.default_rng(seed)
    rgb = np.zeros((h, w, 3), np.float32)
    for c in WC_CLASSES:
        m = cls == c
        if m.any():
            rgb[m] = pal[c]
    # Feldflicken: gold/grün gemischt
    m = cls == 40
    if m.any():
        noise = rng.random((h, w)).astype(np.float32)
        if patch_px > 1:
            noise = ndimage.gaussian_filter(noise, patch_px * 0.5)
            noise = (noise - noise.mean()) / (noise.std() + 1e-6) * 0.29 + 0.5
        f = np.clip((noise - 0.35) * 3.0, 0, 1)[..., None]
        mix = pal["crop_green"] * (1 - f) + pal["crop_gold"] * f
        rgb[m] = mix[m]
    land_dem = dem > 0.5
    nodata = cls == 0
    sea = nodata & ~land_dem
    rel = relief_style(dem, res_ground)            # Ersatz, wo keine Klasse vorliegt (außerhalb der Kacheln)
    rgb[nodata & land_dem] = rel[nodata & land_dem]
    hs = hillshade(dem, res_ground, zf=zf)
    shade = 1.0 + hs_strength * (hs - 0.62) * 1.6
    tex = 1 + ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), 1.2)[..., None] * 0.05
    rgb = rgb * shade[..., None] * tex
    water = sea | (cls == 80)
    wm = ndimage.gaussian_filter(water.astype(np.float32), 0.7)[..., None]
    dist = ndimage.distance_transform_edt(water) * res_ground
    shallow = np.exp(-dist / 6000.0)[..., None]
    wcol = WATER_DEEP * (1 - shallow) + WATER_SHALLOW * shallow
    rgb = rgb * (1 - wm) + wcol * wm
    return (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)


def build_L1_europe():
    pal = wc_palette()
    # Westeuropa, ~320 m/px
    g = grid(-2.0, 14.0, 44.0, 54.0, 320.0)
    print("L1", g["w"], g["h"], flush=True)
    dem = dem_for_grid(g, 9)
    cls = wc_for_grid(g, -2.0, 14.0, 44.0, 54.0, 4)
    save("sat_L1", colorize_wc(cls, dem, g["res"] * math.cos(math.radians(49)), pal, 1, hs_strength=0.75, zf=2.0), g)
    # Europa, 2,4 km/px
    g = grid(-16.0, 58.0, 22.0, 67.0, 2400.0)
    print("Europa", g["w"], g["h"], flush=True)
    dem = np.load(os.path.join(CACHE, "dem_europe.npy")).astype(np.float32)
    cls = wc_for_grid(g, -16.0, 58.0, 22.0, 67.0, 5)
    save("europe", colorize_wc(cls, dem, g["res"] * 0.7, pal, 2, hs_strength=0.8, zf=2.5), g)


if __name__ == "__main__":
    which = sys.argv[1:] or ["europe", "L2", "L3", "craters"]
    if "europe" in which:
        build_europe()
    if "L2" in which:
        build_L2()
    if "L3" in which:
        build_L3()
    if "craters" in which:
        build_craters()
    if "worldcover" in which:
        build_L1_europe()
