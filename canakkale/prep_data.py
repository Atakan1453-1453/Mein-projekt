"""Bereitet die Kartengrundlagen vor (einmalig, ca. 5-10 Minuten).

Erzeugt im Cache-Ordner (Standard: ./cache, per CNK_CACHE änderbar):
  sat_L3.jpg / sat_L3.json   Satellit + Relief, Halbinsel Gelibolu, ~12 m/px (Web-Mercator)
  sat_L2.jpg / sat_L2.json   Satellit + Relief, Dardanellen-Region, ~60 m/px
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
S2 = "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/35"
TERRARIUM = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium"

# Klare Aufnahmen vom Juni 2024 (Wolkenanteil < 0,5 %)
SCENES_L2 = [
    ("T/NF", "2024/6/S2B_35TNF_20240620_0_L2A"),
    ("T/LF", "2024/6/S2B_35TLF_20240623_0_L2A"),
    ("T/MF", "2024/6/S2A_35TMF_20240608_0_L2A"),
    ("T/MF", "2024/6/S2B_35TMF_20240620_0_L2A"),
    ("T/NE", "2024/6/S2A_35TNE_20240605_0_L2A"),
    ("T/LE", "2024/6/S2A_35TLE_20240608_0_L2A"),
    ("T/ME", "2024/6/S2A_35TME_20240605_0_L2A"),
    ("S/LD", "2024/6/S2A_35SLD_20240608_0_L2A"),
    ("S/MD", "2024/6/S2A_35SMD_20240605_0_L2A"),
    ("S/ND", "2024/6/S2A_35SND_20240605_0_L2A"),
]
SCENE_L3 = ("T/ME", "2024/6/S2A_35TME_20240605_0_L2A")


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
        subprocess.run(["curl", "-s", "--retry", "3", "-o", path, f"{TERRARIUM}/{z}/{x}/{y}.png"], check=True)
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
        a = np.asarray(Image.open(os.path.join(DATA, "dem", str(z), str(x), f"{y}.png")).convert("RGB")).astype(np.float32)
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
        local = os.path.join(DATA, "s2", f"{tile[2:]}_TCI.tif")
        url = f"/vsicurl/{S2}/{tile}/{key}/TCI.tif"
        if tile in ("T/ME", "T/LE") and os.path.exists(local):
            url = local
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
    g = grid(25.95, 26.85, 39.88, 40.58, 12.0)
    print("L3", g["w"], g["h"], flush=True)
    dem = dem_for_grid(g, 13)
    sat = read_sat(g, [SCENE_L3])
    res_ground = g["res"] * math.cos(math.radians(40.2))
    save("sat_L3", grade(sat, dem, res_ground, refine=True), g)
    np.save(os.path.join(CACHE, "dem_L3.npy"), dem.astype(np.float16))


def build_L2():
    g = grid(24.45, 28.45, 39.25, 41.55, 60.0)
    print("L2", g["w"], g["h"], flush=True)
    dem = dem_for_grid(g, 11)
    sat = read_sat(g, SCENES_L2, overview=1)
    res_ground = g["res"] * math.cos(math.radians(40.3))
    save("sat_L2", grade(sat, dem, res_ground, hs_strength=0.75), g)


def build_europe():
    g = grid(-16.0, 58.0, 22.0, 67.0, 2400.0)
    print("Europa", g["w"], g["h"], flush=True)
    dem = dem_for_grid(g, 6)
    img = relief_style(dem, g["res"] * 0.7, dark=True)
    save("europe", (img * 255 + 0.5).astype(np.uint8), g)
    np.save(os.path.join(CACHE, "dem_europe.npy"), dem.astype(np.float16))


if __name__ == "__main__":
    which = sys.argv[1:] or ["europe", "L2", "L3"]
    if "europe" in which:
        build_europe()
    if "L2" in which:
        build_L2()
    if "L3" in which:
        build_L3()
