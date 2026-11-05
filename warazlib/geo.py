"""Geo-Hilfen: Web-Mercator-Raster, Umrechnung Breite/Länge <-> Kartenpixel.

Alle WarAZ-Karten sind Web-Mercator-Raster (EPSG:3857). Ein Raster wird durch seine
Grenzen (lat0, lon0, lat1, lon1) und die Bodenauflösung (Meter pro Pixel in Kartenmitte) festgelegt.
"""
import json
import math

R = 6378137.0


def merc(lon, lat):
    return R * math.radians(lon), R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def unmerc(x, y):
    return math.degrees(x / R), math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)


class Grid:
    def __init__(self, lat0, lon0, lat1, lon1, ground_res):
        self.lat0, self.lon0, self.lat1, self.lon1 = lat0, lon0, lat1, lon1
        self.ground_res = ground_res
        latc = (lat0 + lat1) / 2
        self.res = ground_res / math.cos(math.radians(latc))     # Mercator-Meter pro Pixel
        self.x0, self.y0 = merc(lon0, lat0)
        self.x1, self.y1 = merc(lon1, lat1)
        self.w = int(round((self.x1 - self.x0) / self.res))
        self.h = int(round((self.y1 - self.y0) / self.res))
        self.m_per_px = ground_res

    # Breite/Länge -> Pixel (x nach Osten, y nach Süden)
    def px(self, lat, lon):
        x, y = merc(lon, lat)
        return (x - self.x0) / self.res, (self.y1 - y) / self.res

    def latlon(self, px, py):
        lon, lat = unmerc(self.x0 + px * self.res, self.y1 - py * self.res)
        return lat, lon

    def km(self, px_dist):
        return px_dist * self.ground_res / 1000.0

    def px_per_km(self):
        return 1000.0 / self.ground_res

    def to_json(self):
        return dict(lat0=self.lat0, lon0=self.lon0, lat1=self.lat1, lon1=self.lon1, ground_res=self.ground_res,
                    w=self.w, h=self.h)

    @staticmethod
    def from_json(d):
        return Grid(d["lat0"], d["lon0"], d["lat1"], d["lon1"], d["ground_res"])

    def save(self, path):
        with open(path, "w") as f:
            json.dump(self.to_json(), f, indent=1)

    @staticmethod
    def load(path):
        with open(path) as f:
            return Grid.from_json(json.load(f))
