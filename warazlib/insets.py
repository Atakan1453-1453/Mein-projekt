"""Übersichtskarten (2D) mit den Grenzen von 1914 – als Einblendung oben rechts oder bildfüllend.

Daten: historical-basemaps (A. Ourednik), world_1914.geojson (assets/ww1/maps/europe1914).
"""
import json
import math
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

from . import ui as UI

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = os.path.join(ROOT, "assets", "ww1", "maps", "europe1914", "world_1914.geojson")

COL = {
    "France": (196, 204, 222), "German Empire": (168, 170, 160), "Belgium": (214, 208, 186),
    "Luxembourg": (200, 196, 176), "Netherlands": (206, 206, 192), "Switzerland": (214, 206, 196),
    "United Kingdom of Great Britain and Ireland": (210, 196, 190), "Kingdom of Italy": (206, 202, 186),
    "Austro-Hungarian Empire": (178, 172, 160), "Russian Empire": (196, 190, 176),
}
SEA = (112, 132, 150)
LAND = (196, 190, 172)


def _merc(lon, lat):
    lat = max(-85.0, min(85.0, lat))
    return lon, math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


class Inset:
    def __init__(self, lon0, lat0, lon1, lat1, W=560, H=420):
        self.lon0, self.lat0, self.lon1, self.lat1, self.W, self.H = lon0, lat0, lon1, lat1, W, H
        self.mx0, self.my0 = _merc(lon0, lat0)
        self.mx1, self.my1 = _merc(lon1, lat1)
        self.img = self._base()

    def xy(self, lat, lon):
        mx, my = _merc(lon, lat)
        return ((mx - self.mx0) / (self.mx1 - self.mx0) * self.W, (self.my1 - my) / (self.my1 - self.my0) * self.H)

    def _base(self):
        im = Image.new("RGB", (self.W * 2, self.H * 2), SEA)
        d = ImageDraw.Draw(im)
        data = json.load(open(GEO))
        for f in data["features"]:
            name = f["properties"].get("NAME") or ""
            geom = f["geometry"]
            polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
            col = COL.get(name, LAND)
            for poly in polys:
                ring = poly[0]
                lons = [c[0] for c in ring]
                lats = [c[1] for c in ring]
                if max(lons) < self.lon0 - 5 or min(lons) > self.lon1 + 5 or max(lats) < self.lat0 - 5 or min(lats) > self.lat1 + 5:
                    continue
                pts = [tuple(2 * v for v in self.xy(lat, lon)) for lon, lat in ring]
                if len(pts) > 2:
                    d.polygon(pts, fill=col, outline=(90, 90, 86))
        im = im.resize((self.W, self.H), Image.LANCZOS)
        a = np.asarray(im).astype(np.float32)
        # leichte Papierstruktur
        rng = np.random.default_rng(1)
        n = cv2.GaussianBlur(rng.normal(0, 1, (self.H, self.W)).astype(np.float32), (0, 0), 1.2)
        a *= (1 + 0.035 * n[..., None])
        return np.clip(a, 0, 255).astype(np.uint8)

    def render(self, draw_fn=None, t=0.0):
        """draw_fn(d, inset) zeichnet dynamische Marker auf ein PIL-Bild."""
        im = Image.fromarray(self.img.copy()).convert("RGBA")
        if draw_fn:
            d = ImageDraw.Draw(im)
            draw_fn(d, self, t)
        return im

    # ------------------------------------------------------------ Bausteine
    def pin(self, d, lat, lon, label=None, t=0.0, color=UI.STYLE["accent"]):
        x, y = self.xy(lat, lon)
        r = 7 + 3 * (0.5 + 0.5 * math.sin(t * 5))
        d.ellipse((x - r * 2, y - r * 2, x + r * 2, y + r * 2), outline=color + (120,), width=3)
        d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color + (255,), outline=(255, 255, 255, 255), width=2)
        if label:
            UI.spaced(d, (x + 14, y - 16), label, UI.font("bold", 26), (20, 20, 22, 255), 1.5)

    def line(self, d, latlon, color, width=4, dashed=False):
        pts = [self.xy(la, lo) for la, lo in latlon]
        if dashed:
            for i in range(0, len(pts) - 1, 2):
                d.line([pts[i], pts[i + 1]], fill=color, width=width)
        else:
            d.line(pts, fill=color, width=width, joint="curve")

    def arrow(self, d, a, b, color, width=10, progress=1.0):
        (x0, y0), (x1, y1) = self.xy(*a), self.xy(*b)
        x1 = x0 + (x1 - x0) * progress
        y1 = y0 + (y1 - y0) * progress
        d.line([(x0, y0), (x1, y1)], fill=color, width=width)
        ang = math.atan2(y1 - y0, x1 - x0)
        hl = width * 2.2
        p1 = (x1 + math.cos(ang) * hl * 0.6, y1 + math.sin(ang) * hl * 0.6)
        p2 = (x1 + math.cos(ang + 2.5) * hl, y1 + math.sin(ang + 2.5) * hl)
        p3 = (x1 + math.cos(ang - 2.5) * hl, y1 + math.sin(ang - 2.5) * hl)
        d.polygon([p1, p2, p3], fill=color)


def place_inset(ov, im, k, x=None, y=None, title=None):
    """Legt eine Inset-Karte (PIL RGBA) mit Rahmen auf das Overlay. k = Sichtbarkeit."""
    if k <= 0:
        return
    W, H = im.size
    x = ov.W - W - 60 if x is None else x
    y = 60 if y is None else y
    y = y + (1 - UI.ease_out(k)) * -30
    d = ov.d
    UI.plate(d, (x - 12, y - (52 if title else 12), x + W + 12, y + H + 12), k, cut=14, accent=True)
    a = Image.new("L", im.size, int(255 * k))
    ov.img.paste(im.convert("RGB"), (int(x), int(y)), a)
    d.rectangle((x - 1, y - 1, x + W, y + H), outline=(230, 226, 216, int(200 * k)), width=2)
    if title:
        UI.spaced(d, (x + 6, y - 46), title, UI.font("bold", 30), UI.STYLE["text"] + (int(255 * k),), 2.5)
