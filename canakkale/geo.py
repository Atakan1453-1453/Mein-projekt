"""Geländeabfragen (Höhe, Land/Wasser) auf Basis des Höhenmodells der Halbinsel – zum Platzieren von Objekten."""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("CNK_CACHE", os.path.join(HERE, "cache"))
R = 6378137.0
_dem = None
_meta = None


def _load():
    global _dem, _meta
    if _dem is None:
        _dem = np.load(os.path.join(CACHE, "dem_L3.npy")).astype(np.float32)
        _meta = json.load(open(os.path.join(CACHE, "sat_L3.json")))
    return _dem, _meta


def elev(lat, lon):
    dem, m = _load()
    x = R * math.radians(lon)
    y = R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    c = int((x - m["x0"]) / m["res"])
    r = int((m["y1"] - y) / m["res"])
    if 0 <= r < dem.shape[0] and 0 <= c < dem.shape[1]:
        return float(dem[r, c])
    return float("nan")


def shore_scan(lat, lon0, lon1, step=0.0005):
    """Liefert Übergänge Land/Wasser entlang eines Breitengrads."""
    out = []
    prev = None
    lon = lon0
    while lon <= lon1:
        w = elev(lat, lon) <= 0.5
        if prev is not None and w != prev:
            out.append((round(lon, 4), "water" if w else "land"))
        prev = w
        lon += step
    return out
