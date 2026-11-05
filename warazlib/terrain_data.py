"""Lädt Rohdaten für eine Karte: Höhenmodell (AWS Terrain Tiles) und Landnutzung (ESA WorldCover 2021).

Beide Quellen sind frei nutzbar:
  * Höhen: AWS Terrain Tiles (Terrarium-Format; SRTM, GMTED, ETOPO1), https://registry.opendata.aws/terrain-tiles/
  * Landnutzung: ESA WorldCover 10 m 2021 v200 (CC BY 4.0), https://esa-worldcover.org
"""
import math
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image

from .geo import R

TERRARIUM = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium"
WORLDCOVER = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
os.environ.setdefault("CURL_CA_BUNDLE", "/root/.ccr/ca-bundle.crt")


def _tile_xy(lon, lat, z):
    n = 2 ** z
    x = int((lon + 180) / 360 * n)
    r = math.radians(lat)
    y = int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n)
    return x, y


def _fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for attempt in range(6):
        r = subprocess.run(["curl", "-sf", "--retry", "3", "-o", path, url])
        if r.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 0:
            return path
        time.sleep(2 + 2 * attempt)
    raise RuntimeError("Download fehlgeschlagen: " + url)


def dem(grid, z, cache):
    """Höhen in Metern auf dem Raster `grid` (float32, h x w)."""
    import cv2
    lat_top, lon_left = grid.lat1, grid.lon0
    lat_bot, lon_right = grid.lat0, grid.lon1
    tx0, ty0 = _tile_xy(lon_left, lat_top, z)
    tx1, ty1 = _tile_xy(lon_right, lat_bot, z)
    jobs = [(x, y) for x in range(tx0, tx1 + 1) for y in range(ty0, ty1 + 1)]

    def get(xy):
        x, y = xy
        return _fetch(f"{TERRARIUM}/{z}/{x}/{y}.png", os.path.join(cache, "dem", str(z), str(x), f"{y}.png"))

    with ThreadPoolExecutor(16) as ex:
        list(ex.map(get, jobs))
    nx, ny = tx1 - tx0 + 1, ty1 - ty0 + 1
    mosaic = np.zeros((ny * 256, nx * 256), np.float32)
    for (x, y) in jobs:
        a = np.asarray(Image.open(os.path.join(cache, "dem", str(z), str(x), f"{y}.png")).convert("RGB")).astype(np.float32)
        mosaic[(y - ty0) * 256:(y - ty0 + 1) * 256, (x - tx0) * 256:(x - tx0 + 1) * 256] = \
            a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    world = 2 * math.pi * R
    tres = world / (256 * 2 ** z)
    ox = -world / 2 + tx0 * 256 * tres          # Mercator-x der linken Mosaikkante
    oy = world / 2 - ty0 * 256 * tres           # Mercator-y der oberen Mosaikkante
    # Zielpixel -> Mosaikpixel
    xs = (grid.x0 + (np.arange(grid.w) + 0.5) * grid.res - ox) / tres - 0.5
    ys = (oy - (grid.y1 - (np.arange(grid.h) + 0.5) * grid.res)) / tres - 0.5
    mx, my = np.meshgrid(xs.astype(np.float32), ys.astype(np.float32))
    return cv2.remap(mosaic, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def worldcover(grid, cache):
    """WorldCover-Klassen (uint8) auf dem Raster `grid` (nächster Nachbar)."""
    import rasterio
    from rasterio.warp import Resampling, reproject
    from rasterio.transform import from_origin
    out = np.zeros((grid.h, grid.w), np.uint8)
    lat_tiles = range(int(math.floor(grid.lat0 / 3)) * 3, int(math.floor(grid.lat1 / 3)) * 3 + 1, 3)
    lon_tiles = range(int(math.floor(grid.lon0 / 3)) * 3, int(math.floor(grid.lon1 / 3)) * 3 + 1, 3)
    dst_tr = from_origin(grid.x0, grid.y1, grid.res, grid.res)
    for la in lat_tiles:
        for lo in lon_tiles:
            name = f"{'N' if la >= 0 else 'S'}{abs(la):02d}{'E' if lo >= 0 else 'W'}{abs(lo):03d}"
            url = "/vsicurl/" + WORLDCOVER.format(tile=name)
            with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
                with rasterio.open(url) as src:
                    # Fenster in Grad (mit Rand)
                    win = src.window(grid.lon0 - 0.01, grid.lat0 - 0.01, grid.lon1 + 0.01, grid.lat1 + 0.01)
                    win = win.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
                    data = src.read(1, window=win)
                    tr = src.window_transform(win)
                    tmp = np.zeros_like(out)
                    reproject(data, tmp, src_transform=tr, src_crs=src.crs, dst_transform=dst_tr,
                              dst_crs="EPSG:3857", resampling=Resampling.nearest)
                    out = np.where(tmp > 0, tmp, out)
    return out
