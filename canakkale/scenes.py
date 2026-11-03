"""Drehbuch als Zeitleiste: Kamerafahrten, Flaggen-Zähler, Pfeile und Einblendungen.

Zeiten in Kommentaren wie  # „Bouvet“ 3.8  beziehen sich auf die Wortzeit in der
jeweiligen Sprachaufnahme (per Spracherkennung ermittelt).
Alle Truppenstärken/Verluste sind gerundete Werte aus der Literatur (siehe README).
"""
import json
import math
import os

import skia

import engine as E
from engine import (Arrow, Area, Battle, BattleMarker, BilanzPanel, Cam, Caption, ChapterCard, Countries, Credits,
                    DateStamp, Explosion, Fire, Fort, Label, LossBadge, MeasureLine, Mines, Polyline, Quote,
                    Searchlight, Ship, Snow, Tint, TitleCard, Token)
from narration import SEGMENTS

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- Orte (Breite, Länge)
P = dict(
    canakkale=(40.1467, 26.4086), kilitbahir=(40.1500, 26.3780), eceabat=(40.1840, 26.3570),
    gelibolu=(40.4100, 26.6700), bolayir=(40.5160, 26.7650), lapseki=(40.3440, 26.6850),
    seddulbahir=(40.0475, 26.1880), helles=(40.0440, 26.1760), vbeach=(40.0443, 26.1840),
    wbeach=(40.0490, 26.1705), xbeach=(40.0640, 26.1775), ybeach=(40.0905, 26.1990), sbeach=(40.0545, 26.2160),
    krithia=(40.0870, 26.2290), achibaba=(40.0980, 26.2544), kumkale=(40.0040, 26.2010), gully=(40.0800, 26.2000),
    kereves=(40.0700, 26.2480),
    anzac=(40.2405, 26.2805), ariburnu=(40.2445, 26.2815), kabatepe=(40.2045, 26.2700),
    lonepine=(40.2310, 26.2890), nek=(40.2470, 26.2905), chunuk=(40.2537, 26.3085), hill971=(40.2610, 26.3215),
    battleship=(40.2460, 26.2997), plateau400=(40.2335, 26.2930), quinns=(40.2400, 26.2925),
    suvla=(40.3000, 26.2380), nibrunesi=(40.2740, 26.2420), saltlake=(40.2950, 26.2620), scimitar=(40.2855, 26.2900),
    hill60=(40.2735, 26.2770), anafarta=(40.2820, 26.3530), kiretch=(40.3330, 26.2900), bigali=(40.2290, 26.3530),
    rumeli_mec=(40.1380, 26.3700), hamidiye=(40.1300, 26.4090), cimenlik=(40.1478, 26.4022), kepez=(40.1050, 26.3960),
    erenkoy=(40.0700, 26.3720), mudros=(39.8700, 25.2700), imbros=(40.1700, 25.8500), tenedos=(39.8300, 26.0500),
    istanbul=(41.0100, 28.9800),
)

TR, AL = "tr", "al"
RED = E.TR_RED
BLUE = E.AL_BLUE


def mine_rows():
    """10 Minenreihen quer durch die Meerenge zwischen Kepez und Engstelle (aus Höhenmodell ermittelt)."""
    import geo
    rows = []
    for k in range(10):
        lat = 40.106 + k * 0.0037
        trans = geo.shore_scan(lat, 26.30, 26.43, 0.0004)
        w0 = next((lo for lo, kind in trans if kind == "water"), None)
        w1 = next((lo for lo, kind in trans if kind == "land" and w0 and lo > w0 + 0.005), None)
        if w0 is None or w1 is None:
            continue
        n = int((w1 - w0) / 0.0036)
        rows.append([(lat + 0.0006 * math.sin(i), w0 + 0.002 + (w1 - w0 - 0.004) * i / max(1, n - 1)) for i in range(n)])
    return rows


ANZAC_AREA = [(40.2312, 26.2818), (40.2328, 26.2880), (40.2380, 26.2918), (40.2440, 26.2930), (40.2492, 26.2902),
              (40.2503, 26.2848), (40.2470, 26.2826), (40.2405, 26.2806)]
NUSRET_MINES = [(40.066 + 0.034 * i / 25, 26.3445 + 0.0125 * i / 25) for i in range(26)]


class Timeline:
    def __init__(self):
        dur = json.load(open(os.path.join(HERE, "voice_durations.json")))
        self.vdur = {k: d for (k, _), d in zip(SEGMENTS, dur)}
        self.vstart = {}
        self.t = 0.0
        self.objects = []
        self.cam_keys = []
        self.dim_keys = [(0.0, 0.0)]
        self.marks = []       # (Start, Dauer, Name) – für Kontaktbogen
        self.music = []       # (Zeit, Stimmung)
        self.duration = 0.0
        self._campath = None

    # --- Zeitsteuerung
    def say(self, key, pre=0.0, post=1.4):
        self.t += pre
        self.vstart[key] = self.t
        self.marks.append((self.t, self.vdur[key], key))
        self.t += self.vdur[key] + post
        return self.vstart[key]

    def w(self, key, sec):
        """Absolute Zeit eines Worts in einer Sprachaufnahme."""
        return self.vstart[key] + sec

    def end(self, key):
        return self.vstart[key] + self.vdur[key]

    def wait(self, sec):
        self.t += sec
        return self.t

    def add(self, *objs):
        self.objects.extend(objs)
        return objs[0] if len(objs) == 1 else objs

    def mood(self, t, name):
        self.music.append((t, name))

    # --- Abfragen für den Renderer
    def finalize(self):
        """Zwischen zwei Kamerazielen hält die Kamera (mit leichtem Drift) und fliegt erst kurz vorher los."""
        ks = sorted(self.cam_keys, key=lambda k: k[0])
        out = [ks[0]]
        for (t0, c0, *_), (t1, c1, *e) in zip(ks, ks[1:]):
            kind = e[0] if e else "ease"
            if kind == "ease":
                zoom = abs(math.log2(c1.width / c0.width))
                dist = E.ground_km(c0, c1) / max(c0.width, c1.width)
                mv = max(2.6, min(6.0, 2.4 + 0.75 * zoom + 1.2 * min(2.0, dist)))
                if t1 - t0 > mv + 0.5:
                    el = t1 - mv - t0
                    hold = Cam(c0.lat, c0.lon, c0.width * (1 - min(0.08, 0.004 * el)), c0.pitch, c0.heading + min(6.0, 0.12 * el))
                    out.append((t1 - mv, hold, "linear"))
            out.append((t1, c1, kind))
        self.cam_keys = out
        self._campath = E.CamPath(self.cam_keys)
        self.dim_keys.sort()
        self.duration = self.t

    def camera(self, t):
        return self._campath.at(t)

    def cam(self, t, cam=None, kind="ease"):
        """Mit Kamera: Keyframe setzen. Ohne: Kamera zur Zeit t abfragen."""
        if cam is None:
            return self._campath.at(t)
        self.cam_keys.append((t, cam, kind))

    def dim(self, t, value=None):
        """Mit Wert: Abdunklungs-Keyframe setzen. Ohne: Abdunklung zur Zeit t."""
        if value is not None:
            self.dim_keys.append((t, value))
            return
        ks = self.dim_keys
        if t <= ks[0][0]:
            return ks[0][1]
        for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
            if t <= t1:
                return v0 + (v1 - v0) * E.ease((t - t0) / max(1e-6, t1 - t0))
        return ks[-1][1]

    def global_fade(self, t):
        return E.smooth(t / 2.5) * E.smooth((self.duration - t) / 3.0)

    def scene_starts(self):
        return [(s, d) for s, d, _ in self.marks]


def countries_layer(tl, t0, t1, central_on, entente_on, ottoman_on, bulgaria_on=None):
    """Bündniskarte als Flaggenkarte (Länder mit ihrer Flagge von 1914 gefüllt)."""
    paths = E.load_countries()
    thrace = E.thrace_path()
    gray = E.hexc("#8a8a80", 0.10)
    red = E.hexc("#e30a17")
    blue_ru = E.hexc("#0039a6")
    spec = {
        "German Empire": dict(flag="de1871", side="cp", on=central_on),
        "Austro-Hungarian Empire": dict(flag="ah1869", side="cp", on=central_on),
        "Ottoman Empire": dict(flag="tr", base=red, rect=(33.0, 27.0, 43.6, 46.0), side="cp", on=ottoman_on),
        "United Kingdom of Great Britain and Ireland": dict(flag="gb", rect=(49.9, -10.6, 58.7, 1.8), side="en", on=entente_on),
        "France": dict(flag="fr", side="en", on=entente_on),
        "Russian Empire": dict(flag="ru1914", base=blue_ru, rect=(44.0, 20.0, 60.0, 60.0), side="en", on=entente_on),
        "Grand Duchy of Finland": dict(flag="ru1914", base=blue_ru, rect=(44.0, 20.0, 60.0, 60.0), side="en", on=entente_on),
        "Georgia": dict(base=blue_ru, side="en", on=entente_on),
        "Armenia": dict(base=blue_ru, side="en", on=entente_on),
        "Azerbaijan": dict(base=blue_ru, side="en", on=entente_on),
        "Serbia": dict(flag="rs", side="en", on=entente_on),
        "Montenegro": dict(flag="me", side="en", on=entente_on),
        "Belgium": dict(flag="be", side="en", on=entente_on),
    }
    entries = []
    for name, path in paths.items():
        if name == "Bulgaria":
            p = skia.Op(path, thrace, skia.PathOp.kDifference_PathOp) or path
            entries.append(dict(path=p, base=gray, t_on=t0))
            if bulgaria_on:
                entries.append(dict(path=p, flag="bg", side="cp", t_on=bulgaria_on))
            continue
        sp = spec.get(name)
        if sp is None:
            entries.append(dict(path=path, base=gray, t_on=t0))
            continue
        entries.append(dict(path=path, flag=sp.get("flag"), base=sp.get("base"), rect=sp.get("rect"), side=sp["side"], t_on=sp["on"]))
    o = spec["Ottoman Empire"]
    entries.append(dict(path=thrace, flag="tr", base=red, rect=o["rect"], side="cp", t_on=ottoman_on))
    return E.FlagCountries(entries, t0, t1)


def bearing(a, b):
    dy = b[0] - a[0]
    dx = (b[1] - a[1]) * math.cos(math.radians(a[0]))
    return math.degrees(math.atan2(dx, dy)) % 360


def add_battles(T):
    """Schlachtfelder: Figuren (1 Figur = 1 Soldat), Kämpfe, Gebietskontrolle."""
    U = E.Unit
    w = T.w

    # ---------------- Gebietskontrolle ab der Landung (ganz leicht rot = osmanisch, blau = alliiert)
    helles_small = [(40.0440, 26.163), (40.0565, 26.166), (40.0560, 26.186), (40.0515, 26.198), (40.0470, 26.200), (40.0430, 26.186)]
    helles_may = [(40.073, 26.172), (40.0715, 26.200), (40.0665, 26.221), (40.0625, 26.240), (40.0585, 26.252), (40.050, 26.236),
                  (40.044, 26.200), (40.040, 26.178), (40.050, 26.160), (40.062, 26.166)]
    helles_jul = [(40.086, 26.186), (40.082, 26.205), (40.074, 26.225), (40.068, 26.245), (40.061, 26.256), (40.050, 26.236),
                  (40.044, 26.200), (40.040, 26.178), (40.050, 26.160), (40.068, 26.168)]
    anzac_aug = [(40.231, 26.281), (40.234, 26.291), (40.245, 26.296), (40.255, 26.296), (40.264, 26.291), (40.274, 26.281),
                 (40.286, 26.286), (40.300, 26.292), (40.316, 26.290), (40.332, 26.282), (40.338, 26.262), (40.330, 26.222),
                 (40.300, 26.222), (40.270, 26.232), (40.250, 26.262), (40.240, 26.276)]
    suvla_init = [(40.270, 26.238), (40.288, 26.256), (40.310, 26.258), (40.326, 26.242), (40.312, 26.220), (40.282, 26.222)]
    kumkale_fr = [(39.996, 26.190), (40.009, 26.193), (40.011, 26.214), (39.999, 26.216)]
    t_land = T.vstart["helles"] - 0.5
    t_end = T.end("rueckzug") + 1.5
    areas = [
        (helles_small, t_land + 30, w("kirte", 7.6)),
        (helles_may, w("kirte", 7.6), w("kirte3", 13.0)),
        (helles_jul, w("kirte3", 13.0), w("rueckzug", 23.0)),
        (ANZAC_AREA, w("anzac", 26.0), w("conk", 1.0)),
        (anzac_aug, w("conk", 1.0), w("rueckzug", 8.4)),
        (suvla_init, w("suvla", 6.0), w("anafarta", 1.0)),
        (kumkale_fr, w("kumkale", 3.0), w("kumkale", 11.5)),
    ]
    T.add(E.ControlMap(t_land, t_end, areas))

    def troops(units, t0, t1, enemies):
        T.add(E.Troops(units, t0, t1, enemies))

    # ---------------- 25. April · Seddülbahir / Kap Helles
    k = "helles"
    beaches = {"S": (P["sbeach"], (40.035, 26.235), 1500, 200), "V": (P["vbeach"], (40.028, 26.180), 3000, 1300),
               "W": (P["wbeach"], (40.040, 26.150), 3000, 900), "X": (P["xbeach"], (40.064, 26.150), 2000, 250),
               "Y": (P["ybeach"], (40.092, 26.170), 2500, 350)}
    units, gb_idx = [], {}
    for i, (name, (dst, src, n, loss)) in enumerate(beaches.items()):
        f = bearing(src, dst)
        inland = (dst[0] + (dst[0] - src[0]) * 0.12, dst[1] + (dst[1] - src[1]) * 0.12)
        gb_idx[name] = len(units)
        units.append(U("al", n, [(w(k, 6.4), *src), (w(k, 11.8) + i * 0.3, *dst), (w(k, 34.0), *inland)], facing=f, area=40,
                       losses=[(w(k, 28.4), loss)], fire=[(w(k, 12.4), T.end(k) + 1)], nation="gb", t1=T.end(k) + 1, seed=i))
    tv = len(units); units.append(U("tr", 300, [(w(k, 6.0), 40.0475, 26.1888)], facing=215, area=45, losses=[(w(k, 31.4), 200)],
                                    fire=[(w(k, 12.4), T.end(k) + 1)], t1=T.end(k) + 1, seed=11))
    tw = len(units); units.append(U("tr", 300, [(w(k, 6.0), 40.0528, 26.1772)], facing=250, area=45, losses=[(w(k, 31.4), 200)],
                                    fire=[(w(k, 13.8), T.end(k) + 1)], t1=T.end(k) + 1, seed=12))
    tres = len(units); units.append(U("tr", 3900, [(w(k, 16.0), 40.0700, 26.2060), (w(k, 24.0), 40.0625, 26.1980)], facing=215, area=60,
                                      losses=[(w(k, 31.4), 1500)], fire=[(w(k, 20.0), T.end(k) + 1)], t1=T.end(k) + 1, seed=13, arrive=5.0))
    troops(units, w(k, 6.0), T.end(k) + 1.2,
           [(gb_idx["V"], tv), (gb_idx["W"], tw), (gb_idx["X"], tres), (gb_idx["Y"], tres), (gb_idx["S"], tres)])

    # ---------------- 25. April · Arıburnu
    k, k2 = "anzac", "kemal"
    cove = P["anzac"]
    units = [
        U("al", 6000, [(w(k, 1.4), 40.2290, 26.2610), (w(k, 8.0), *cove), (w(k, 18.0), *P["plateau400"])], facing=70, area=35,
          losses=[(w(k2, 21.0), 800)], fire=[(w(k, 14.8), T.end(k2) + 1)], nation="au", t1=T.end(k2) + 1, seed=21, arrive=6.0),
        U("al", 5000, [(w(k, 2.0), 40.2310, 26.2620), (w(k, 8.6), 40.2420, 26.2815), (w(k, 18.5), *P["battleship"])], facing=65, area=35,
          losses=[(w(k2, 21.0), 600)], fire=[(w(k, 14.8), T.end(k2) + 1)], nation="au", t1=T.end(k2) + 1, seed=22, arrive=6.0),
        U("al", 5000, [(w(k, 2.6), 40.2335, 26.2640), (w(k, 9.2), 40.2445, 26.2820), (w(k, 19.0), 40.2505, 26.2990)], facing=55, area=35,
          losses=[(w(k2, 21.0), 600)], fire=[(w(k, 14.8), T.end(k2) + 1)], nation="nz", t1=T.end(k2) + 1, seed=23, arrive=6.0),
        U("tr", 2000, [(w(k, 10.0), 40.2405, 26.3035)], facing=270, area=50, losses=[(w(k2, 21.2), 800)],
          fire=[(w(k, 12.0), T.end(k2) + 1)], t1=T.end(k2) + 1, seed=24),
        U("tr", 8000, [(w(k, 22.4), *P["bigali"]), (w(k, 27.0), 40.2500, 26.3110)], facing=280, area=45, losses=[(w(k2, 21.2), 1200)],
          fire=[(w(k, 27.0), T.end(k2) + 1)], t1=T.end(k2) + 1, seed=25, arrive=4.0),
    ]
    troops(units, w(k, 1.4), T.end(k2) + 1.2, [(0, 3), (1, 3), (2, 4), (1, 4)])

    # ---------------- Kumkale
    k = "kumkale"
    units = [U("al", 3000, [(w(k, 0.6), 39.9900, 26.1500), (w(k, 2.4), 40.0035, 26.1960), (w(k, 6.0), 40.0050, 26.2080),
                            (w(k, 10.6), 40.0040, 26.2000), (w(k, 12.0), 39.9930, 26.1560)], facing=70, area=40,
               losses=[(w(k, 9.4), 786)], fire=[(w(k, 4.0), w(k, 10.6))], nation="fr", t1=w(k, 12.0), seed=31),
             U("tr", 2600, [(w(k, 3.0), 40.0110, 26.2300)], facing=250, area=50, losses=[(w(k, 9.6), 1735)],
               fire=[(w(k, 4.0), w(k, 10.8))], t1=w(k, 12.0), seed=32)]
    troops(units, w(k, 0.6), w(k, 12.2), [(0, 1)])

    # ---------------- Kirte I und II
    k = "kirte"
    units = [U("al", 10000, [(w(k, 9.5), 40.0625, 26.1950), (w(k, 14.0), 40.0730, 26.2040)], facing=20, area=45,
               losses=[(w(k, 14.5), 2000)], fire=[(w(k, 10.5), w(k, 15.6))], nation="gb", t1=w(k, 15.8), seed=41),
             U("al", 4000, [(w(k, 10.0), 40.0595, 26.2330), (w(k, 14.0), 40.0670, 26.2400)], facing=20, area=45,
               losses=[(w(k, 14.6), 1000)], fire=[(w(k, 10.5), w(k, 15.6))], nation="fr", t1=w(k, 15.8), seed=42),
             U("tr", 7000, [(w(k, 9.0), 40.0850, 26.2160)], facing=200, area=55, losses=[(w(k, 14.8), 2400)],
               fire=[(w(k, 10.5), w(k, 15.6))], t1=w(k, 15.8), seed=43)]
    troops(units, w(k, 9.0), w(k, 16.0), [(0, 2), (1, 2)])
    units = [U("al", 13000, [(w(k, 17.6), 40.0640, 26.1990), (w(k, 26.0), 40.0715, 26.2070)], facing=20, area=42,
               losses=[(w(k, 26.9), 3000)], fire=[(w(k, 19.5), w(k, 29.0))], nation="gb", t1=T.end(k) + 0.5, seed=44),
             U("al", 7000, [(w(k, 17.6), 40.0600, 26.2360), (w(k, 26.0), 40.0665, 26.2420)], facing=20, area=42,
               losses=[(w(k, 26.9), 2000)], fire=[(w(k, 19.5), w(k, 29.0))], nation="fr", t1=T.end(k) + 0.5, seed=45),
             U("al", 5000, [(w(k, 18.6), 40.0655, 26.2180), (w(k, 26.0), 40.0735, 26.2220)], facing=20, area=42,
               losses=[(w(k, 26.9), 1500)], fire=[(w(k, 19.5), w(k, 29.0))], nation="au", t1=T.end(k) + 0.5, seed=46),
             U("tr", 20000, [(w(k, 17.6), 40.0840, 26.2210)], facing=200, area=50, aspect=4.0, losses=[(w(k, 27.4), 2000)],
               fire=[(w(k, 19.5), w(k, 29.0))], t1=T.end(k) + 0.5, seed=47)]
    troops(units, w(k, 17.6), T.end(k) + 0.6, [(0, 3), (1, 3), (2, 3)])

    # ---------------- Kirte III und Zığındere
    k = "kirte3"
    units = [U("al", 20000, [(w(k, 2.6), 40.0650, 26.2040), (w(k, 8.6), 40.0760, 26.2110), (w(k, 11.6), 40.0700, 26.2070)], facing=20,
               area=40, losses=[(w(k, 10.0), 4500)], fire=[(w(k, 4.8), w(k, 11.8))], nation="gb", t1=w(k, 12.2), seed=51),
             U("al", 10000, [(w(k, 4.2), 40.0605, 26.2380), (w(k, 8.6), 40.0680, 26.2430)], facing=20, area=40,
               losses=[(w(k, 10.2), 2000)], fire=[(w(k, 4.8), w(k, 11.8))], nation="fr", t1=w(k, 12.2), seed=52),
             U("tr", 25000, [(w(k, 5.6), 40.0840, 26.2220), (w(k, 9.6), 40.0840, 26.2220), (w(k, 11.6), 40.0790, 26.2170)], facing=200,
               area=45, aspect=4.0, losses=[(w(k, 11.0), 3000)], fire=[(w(k, 4.8), w(k, 11.8))], t1=w(k, 12.2), seed=53)]
    troops(units, w(k, 2.6), w(k, 12.4), [(0, 2), (1, 2)])
    units = [U("al", 8000, [(w(k, 12.2), 40.0770, 26.1990), (w(k, 16.0), 40.0830, 26.2020)], facing=15, area=40,
               losses=[(w(k, 19.2), 3800)], fire=[(w(k, 14.0), w(k, 22.5))], nation="gb", t1=T.end(k) + 1, seed=54),
             U("tr", 20000, [(w(k, 12.6), 40.0930, 26.2130), (w(k, 18.0), 40.0870, 26.2070)], facing=200, area=45,
               losses=[(w(k, 18.4), 14000)], fire=[(w(k, 14.0), w(k, 22.5))], t1=T.end(k) + 1, seed=55)]
    troops(units, w(k, 12.2), T.end(k) + 1.2, [(0, 1)])

    # ---------------- 19. Mai · Arıburnu
    k = "mai19"
    units = [U("tr", 42000, [(w(k, 6.5), 40.2440, 26.3150), (w(k, 16.0), 40.2425, 26.3040)], facing=265, area=40, aspect=3.0,
               losses=[(w(k, 20.0), 10000)], fire=[(w(k, 8.0), w(k, 23.5))], t1=T.end(k) + 1, seed=61, arrive=4.0),
             U("al", 12300, [(w(k, 12.0), 40.2400, 26.2870)], facing=80, area=28, losses=[(w(k, 25.8), 470)],
               fire=[(w(k, 8.0), w(k, 23.5))], nation="au", t1=T.end(k) + 1, seed=62),
             U("al", 5000, [(w(k, 12.0), 40.2470, 26.2895)], facing=80, area=28, losses=[(w(k, 25.8), 170)],
               fire=[(w(k, 8.0), w(k, 23.5))], nation="nz", t1=T.end(k) + 1, seed=63)]
    troops(units, w(k, 6.5), T.end(k) + 1.2, [(1, 0), (2, 0)])

    # ---------------- August · Kanlısırt / Lone Pine
    k = "lonepine"
    units = [U("al", 4600, [(w(k, 4.5), 40.2290, 26.2840), (w(k, 9.5), 40.2310, 26.2895)], facing=80, area=22,
               losses=[(w(k, 21.2), 2277)], fire=[(w(k, 6.5), w(k, 26.0))], nation="au", t1=T.end(k) + 1, seed=71),
             U("tr", 9000, [(w(k, 4.0), 40.2325, 26.2950), (w(k, 12.0), 40.2318, 26.2925)], facing=260, area=24,
               losses=[(w(k, 24.4), 6000)], fire=[(w(k, 6.5), w(k, 26.0))], t1=T.end(k) + 1, seed=72, arrive=6.0)]
    troops(units, w(k, 4.0), T.end(k) + 1.2, [(0, 1)])

    # ---------------- The Nek (600 Leichte Reiter, vier Wellen)
    k = "nek"
    waves = []
    for i in range(4):
        waves.append(U("al", 150, [(w(k, 2.0), 40.2458 + 0.00008 * i, 26.2880 - 0.0002 * i),
                                   (w(k, 8.8) + i * 0.6, 40.2458 + 0.00008 * i, 26.2880 - 0.0002 * i),
                                   (w(k, 11.0) + i * 0.6, 40.2466, 26.2902)], facing=75, area=8, aspect=6.0,
                       losses=[(w(k, 14.2), 93)], fire=[(w(k, 9.0), w(k, 13.5))], nation="au", t1=T.end(k) + 1, seed=80 + i))
    waves.append(U("tr", 300, [(w(k, 2.0), 40.2474, 26.2925)], facing=255, area=10, aspect=4.0, fire=[(w(k, 8.8), w(k, 14.0))],
                   t1=T.end(k) + 1, seed=85))
    troops(waves, w(k, 2.0), T.end(k) + 1.2, [(0, 4), (1, 4), (2, 4), (3, 4)])

    # ---------------- Conkbayırı · 8. und 10. August
    k = "conk"
    units = [U("al", 760, [(w(k, 3.4), 40.2620, 26.2900), (w(k, 14.7), 40.2545, 26.3070)], facing=120, area=18,
               losses=[(w(k, 23.6), 690)], fire=[(w(k, 15.8), T.end(k))], nation="nz", t1=T.end(k) + 1, seed=91),
             U("al", 3000, [(w(k, 3.4), 40.2680, 26.2760), (w(k, 16.0), 40.2600, 26.3120)], facing=110, area=30,
               fire=[(w(k, 16.0), T.end(k))], nation="gb", t1=T.end(k) + 1, seed=92),
             U("tr", 3000, [(w(k, 12.0), 40.2575, 26.3170)], facing=240, area=30, fire=[(w(k, 15.8), T.end(k))], t1=T.end(k) + 1, seed=93)]
    troops(units, w(k, 3.4), T.end(k) + 1.2, [(0, 2), (1, 2)])
    k = "kemal_conk"
    units = [U("al", 1500, [(w(k, 6.0), 40.2540, 26.3082)], facing=90, area=22, losses=[(w(k, 16.0), 1200)],
               fire=[(w(k, 10.0), w(k, 18.5))], nation="gb", t1=w(k, 19.0), seed=94),
             U("tr", 6000, [(w(k, 9.4), 40.2560, 26.3300), (w(k, 17.3), 40.2548, 26.3110)], facing=270, area=30, losses=[(w(k, 15.0), 1500)],
               fire=[(w(k, 11.0), w(k, 18.5))], t1=T.end(k) + 1, seed=95, arrive=3.0)]
    troops(units, w(k, 6.0), T.end(k) + 1.2, [(0, 1)])

    # ---------------- Suvla / Anafartalar
    k = "suvla"
    land = [((40.290, 26.190), (40.293, 26.236), 7000), ((40.305, 26.185), (40.305, 26.226), 7000), ((40.272, 26.205), (40.275, 26.240), 6000)]
    units = []
    for i, (src, dst, n) in enumerate(land):
        units.append(U("al", n, [(w(k, 1.8) + i * 0.3, *src), (w(k, 6.5) + i * 0.3, *dst)], facing=bearing(src, dst), area=40,
                       nation="gb", t1=T.end(k) + 1, seed=101 + i))
    units.append(U("tr", 1500, [(w(k, 8.4), 40.3000, 26.3000)], facing=260, area=40, fire=[(w(k, 10.0), T.end(k))], t1=T.end(k) + 1, seed=104))
    troops(units, w(k, 1.8), T.end(k) + 1.2, [])
    k = "anafarta"
    units = [U("al", 20000, [(w(k, 0.0), 40.2950, 26.2480), (w(k, 9.0), 40.2920, 26.2720)], facing=95, area=40, losses=[(w(k, 11.0), 2500)],
               fire=[(w(k, 9.0), w(k, 13.2))], nation="gb", t1=w(k, 14.0), seed=111),
             U("tr", 10000, [(w(k, 3.4), 40.2950, 26.3500), (w(k, 9.0), 40.2950, 26.3050)], facing=265, area=45, losses=[(w(k, 11.5), 1500)],
               fire=[(w(k, 9.0), w(k, 13.2))], t1=w(k, 14.0), seed=112, arrive=4.0),
             U("al", 14300, [(w(k, 16.6), 40.2830, 26.2660), (w(k, 22.5), 40.2850, 26.2840)], facing=80, area=32,
               losses=[(w(k, 25.4), 5300)], fire=[(w(k, 17.0), T.end(k))], nation="gb", t1=T.end(k) + 1, seed=113),
             U("tr", 8000, [(w(k, 15.0), 40.2885, 26.2970)], facing=255, area=35, losses=[(w(k, 26.0), 2600)],
               fire=[(w(k, 17.0), T.end(k))], t1=T.end(k) + 1, seed=114)]
    troops(units, w(k, 0.0), T.end(k) + 1.2, [(0, 1), (2, 3)])


# ======================================================================= Aufbau
def build():
    tl = Timeline()
    T = tl

    # ------------------------------------------------------------ 0 · Luftaufnahme & Titel
    T.mood(0, "intro")
    T.cam(0.0, Cam(39.93, 26.02, 150, 52, 52))
    s = T.say("intro", pre=6.0, post=1.0)
    # „Tschanakkale“ 0.0
    T.add(Label(*P["canakkale"], "Çanakkale", t0=T.w("intro", 0.2), t1=T.w("intro", 9.0), size=34))
    T.cam(T.w("intro", 4.0), Cam(40.12, 26.36, 38, 48, 40))
    T.cam(T.w("intro", 8.8), Cam(40.15, 26.40, 52, 44, 36))
    # „Europa von Asien“ 5.8
    T.add(Label(40.30, 26.20, "EUROPA", t0=T.w("intro", 5.6), t1=T.w("intro", 15.0), size=34, style="sea", dot=False))
    T.add(Label(40.02, 26.52, "ASIEN", t0=T.w("intro", 6.4), t1=T.w("intro", 15.0), size=34, style="sea", dot=False))
    T.add(Label(40.11, 26.355, "Dardanellen", "Çanakkale Boğazı", t0=T.w("intro", 7.9), t1=T.w("intro", 15.0), size=32, dot=False, dx=0, dy=0, align="center"))
    # „Rund 60 Kilometer“ 9.5 → Kamera weiter, Messlinie entlang der Meerenge
    T.cam(T.w("intro", 10.6), Cam(40.20, 26.45, 80, 40, 34))
    strait = [(40.012, 26.225), (40.060, 26.300), (40.100, 26.335), (40.135, 26.378), (40.150, 26.390), (40.170, 26.392),
              (40.210, 26.425), (40.260, 26.495), (40.320, 26.570), (40.380, 26.650), (40.405, 26.690)]
    T.add(Polyline(strait, E.GOLD, t0=T.w("intro", 9.4), t1=T.w("intro", 12.4), width=3.5, grow=1.6))
    T.add(Label(40.26, 26.52, "ca. 61 km", t0=T.w("intro", 10.0), t1=T.w("intro", 12.4), size=30, dot=False))
    # „engsten Stelle“ 11.9 → zur Engstelle
    T.cam(T.w("intro", 13.4), Cam(40.143, 26.390, 8.5, 52, 25))
    T.add(MeasureLine((40.1500, 26.3800), (40.1478, 26.3990), "ca. 1,2 km", T.w("intro", 13.4), T.w("intro", 19.0)))
    T.add(Label(*P["kilitbahir"], "Kilitbahir", t0=T.w("intro", 13.0), t1=T.w("intro", 19.5), dx=-14, align="right"))
    T.add(Label(*P["canakkale"], "Çanakkale", t0=T.w("intro", 13.0), t1=T.w("intro", 19.5)))
    # „1915“ 16.0 → weit hinaus, langsam drehen
    T.cam(T.w("intro", 19.5), Cam(40.20, 26.38, 70, 42, 30))
    T.cam(T.end("intro") + 9, Cam(40.24, 26.42, 95, 40, 12), "linear")
    T.add(TitleCard(T.end("intro") + 0.4, 8.5))
    T.wait(8.5)

    # ------------------------------------------------------------ Kapitel 1 · Weltkrieg
    t = T.t
    T.mood(t, "world")
    T.add(ChapterCard(1, "Ein Krieg erfasst die Welt", "1914", t, 5.0))
    T.cam(t + 0.8, Cam(40.24, 26.42, 95, 40, 12))
    T.cam(t + 6.5, Cam(47.5, 20.0, 4300, 0, 0))
    T.wait(5.5)
    s = T.say("europa", pre=0.4)
    s2 = T.say("strategie", pre=0.6)
    T.add(countries_layer(T, s - 1.5, T.end("strategie") + 4.0, T.w("europa", 6.4), T.w("europa", 12.0), T.w("europa", 17.4)))
    T.cam(s + 20.0, Cam(46.5, 23.0, 3900, 0, 0))
    T.add(Label(52.5, 13.4, "Deutsches Reich", t0=T.w("europa", 7.9), t1=T.w("strategie", 5.5), style="country", size=30))
    T.add(Label(47.6, 18.0, "Österreich-Ungarn", t0=T.w("europa", 9.5), t1=T.w("strategie", 5.5), style="country", size=28))
    T.add(Label(52.3, -1.4, "Großbritannien", t0=T.w("europa", 13.3), t1=T.w("strategie", 5.5), style="country", size=26))
    T.add(Label(46.6, 2.4, "Frankreich", t0=T.w("europa", 14.5), t1=T.w("strategie", 5.5), style="country", size=28))
    T.add(Label(55.5, 38.0, "Russisches Reich", t0=T.w("europa", 15.8), t1=T.w("strategie", 5.5), style="country", size=32))
    T.add(Label(38.8, 33.5, "Osmanisches Reich", t0=T.w("europa", 17.6), t1=T.w("strategie", 5.5), style="country", size=30))
    T.add(Caption([(["de"], "Mittelmächte: Deutsches Reich, Österreich-Ungarn"),
                   (["gb", "fr"], "Entente: Großbritannien, Frankreich, Russland")],
                  T.w("europa", 6.6), T.w("europa", 20.5), pos="br", width=640, title="Europa 1914"))
    # Bündnis Berlin–Istanbul
    T.add(Polyline([(52.52, 13.40), (48.2, 16.37), (44.8, 20.46), (42.7, 23.3), (41.01, 28.98)], RED,
                   t0=T.w("europa", 22.2), t1=T.w("europa", 34.0), width=3, grow=2.0, dash=(14, 8)))
    T.add(Caption([(["tr", "de"], "2. August 1914: geheimes Bündnis"), (None, "Osmanisches Reich – Deutsches Reich")],
                  T.w("europa", 22.4), T.w("europa", 31.0), pos="br", width=600))
    # Schwarzes Meer: Angriff auf russische Häfen (29. Okt. 1914)
    T.cam(T.w("europa", 24.6), Cam(43.4, 32.0, 1500, 0, 0))
    for dst in [(46.48, 30.73), (44.62, 33.52), (45.03, 35.38), (44.72, 37.77)]:
        T.add(Arrow([(41.2, 29.1), ((41.2 + dst[0]) / 2 + 0.5, (29.1 + dst[1]) / 2), dst], TR, t0=T.w("europa", 26.2), grow=2.4,
                    t1=T.w("europa", 34.5) + 1.0, width=9))
    T.add(Label(46.48, 30.73, "Odessa", t0=T.w("europa", 27.5), t1=T.w("europa", 34.5) + 1.0, size=22))
    T.add(Label(44.62, 33.52, "Sewastopol", t0=T.w("europa", 27.7), t1=T.w("europa", 34.5) + 1.0, size=22))
    T.add(Label(44.72, 37.77, "Noworossijsk", t0=T.w("europa", 27.9), t1=T.w("europa", 34.5) + 1.0, size=22))
    T.add(Label(43.3, 34.0, "Schwarzes Meer", t0=T.w("europa", 25.0), t1=T.w("europa", 34.5) + 1.0, size=26, style="sea", dot=False))
    T.add(Label(*P["istanbul"], "Istanbul", t0=T.w("europa", 24.8), t1=T.end("strategie") + 3.0, size=24, dx=-12, align="right"))
    T.add(DateStamp("November 1914", "Das Osmanische Reich im Krieg", T.w("europa", 32.0), T.w("europa", 34.7) + 6.0,
                    sub="Kriegserklärungen Russlands (2.11.) sowie Großbritanniens und Frankreichs (5.11.)"))

    # „strategie“
    s = s2
    T.cam(s - 0.5, Cam(50.0, 20.0, 4300, 0, 0))
    T.add(Label(56.3, 18.5, "Ostsee", t0=T.w("strategie", 2.6), t1=T.w("strategie", 9.0), size=26, style="sea", dot=False))
    T.add(Polyline([(57.0, 10.6), (55.3, 11.4), (54.5, 12.0)], RED, t0=T.w("strategie", 3.2), t1=T.w("strategie", 9.5), width=9, grow=0.8))
    T.add(Label(55.6, 8.5, "blockiert", t0=T.w("strategie", 3.4), t1=T.w("strategie", 9.5), size=24, dot=False, color=E.hexc("#ff8f80"), align="right", dx=0))
    route = [(35.9, 14.5), (36.6, 22.5), (38.5, 25.3), (40.02, 26.20), (40.15, 26.39), (40.42, 26.69), (40.65, 27.6), (41.01, 28.98),
             (41.25, 29.12), (43.2, 30.5), (46.4, 30.8)]
    T.add(Arrow(route, AL, t0=T.w("strategie", 4.8), grow=4.0, t1=T.w("strategie", 31.0), width=9, dashed=True))
    T.cam(T.w("strategie", 6.0), Cam(41.8, 26.0, 2300, 0, 0))
    T.add(Label(41.2, 29.4, "Bosporus", t0=T.w("strategie", 8.0), t1=T.w("strategie", 31.0), size=22))
    T.add(Label(40.05, 25.4, "Dardanellen", t0=T.w("strategie", 9.3), t1=T.w("strategie", 31.0), size=22, align="right", dx=-14))
    T.add(Explosion(40.15, 26.39, T.w("strategie", 12.0), 0.5))
    T.add(Caption([(["gb"], "Winston Churchill, Erster Lord der Admiralität"), (None, "Plan: die Dardanellen mit der Flotte durchbrechen")],
                  T.w("strategie", 14.2), T.w("strategie", 27.0), pos="br", width=640, title="London, Januar 1915"))
    T.add(Label(51.5, -0.12, "London", t0=T.w("strategie", 14.2), t1=T.w("strategie", 22.0), size=22))
    T.cam(T.w("strategie", 21.0), Cam(40.9, 27.0, 900, 0, 0))
    T.add(Arrow([(39.0, 25.0), (40.0, 26.2), (40.16, 26.40), (40.45, 26.72), (40.8, 27.9), (40.98, 28.85)], AL,
                t0=T.w("strategie", 21.8), grow=3.2, t1=T.w("strategie", 31.5), width=14))

    # ------------------------------------------------------------ Kapitel 2 · Festung
    t = T.t
    T.mood(t, "fortress")
    T.add(ChapterCard(2, "Die Festung am Meer", "Die Dardanellen 1914 – 1915", t + 0.3, 5.0))
    T.cam(t + 0.3, Cam(40.9, 27.0, 900, 0, 0))
    T.cam(t + 6.0, Cam(40.10, 26.31, 46, 38, 32))
    T.wait(5.6)
    s = T.say("festung", pre=0.3)
    FORTS_END = 1e9  # wird unten gesetzt
    forts = [("seddulbahir", "Seddülbahir", 6.8, -14, "right"), ("kumkale", "Kumkale", 8.0, 14, "left"),
             ("rumeli_mec", "Rumeli Mecidiye", 10.9, -14, "right"), ("hamidiye", "Hamidiye", 12.6, 14, "left"),
             ("kilitbahir", "Kilitbahir", 13.5, -14, "right"), ("cimenlik", "Çimenlik", 14.7, 14, "left")]
    fort_objs = {}
    for key, name, tw, dx, al in forts:
        fort_objs[key] = T.add(Fort(*P[key], name, t0=T.w("festung", tw), t1=FORTS_END, dx=dx, align=al))
    T.cam(T.w("festung", 10.0), Cam(40.115, 26.355, 22, 42, 26))
    rows = mine_rows()
    for i, row in enumerate(rows):
        T.add(Mines(row, T.w("festung", 19.0) + i * 0.25, t1=FORTS_END, size=3.6, stagger=0.03))
    T.add(Label(40.122, 26.322, "10 Minenreihen", t0=T.w("festung", 19.6), t1=T.w("festung", 28.0) + 2, size=24, align="right", dx=-10, dot=False))
    for lat, lon, base in [(40.112, 26.372, -70), (40.126, 26.405, -100), (40.098, 26.322, 60)]:
        T.add(Searchlight(lat, lon, T.w("festung", 22.4), T.w("festung", 30.0), base, 40, 0.15, 5.5))
    T.dim(T.w("festung", 21.0), 0.0)
    T.dim(T.w("festung", 22.0), 0.35)
    T.dim(T.end("festung") + 0.5, 0.0)
    T.add(Ship([(T.w("festung", 25.0), 40.085, 26.335), (T.w("festung", 29.5), 40.104, 26.348)], "gb", t0=T.w("festung", 25.0), t1=T.end("festung") + 1, size=16))
    T.add(Battle(40.103, 26.347, 0.5, T.w("festung", 26.5), T.end("festung") + 0.8, rate=5))

    s = T.say("erster_angriff", pre=0.4)
    T.add(DateStamp("3. November 1914", "Einfahrt der Dardanellen", s, T.w("erster_angriff", 11.5)))
    T.cam(s - 0.2, Cam(40.02, 26.18, 22, 45, 30))
    # 3.11.1914: zwei britische Schiffe vor Seddülbahir, zwei französische vor Kumkale – alle auf offener See
    fleet0 = [(40.040, 26.125, "gb", "seddulbahir"), (40.030, 26.135, "gb", "seddulbahir"),
              (39.993, 26.140, "fr", "kumkale"), (39.983, 26.150, "fr", "kumkale")]
    for i, (la, lo, code, tgt) in enumerate(fleet0):
        T.add(Ship([(s, la, lo - 0.04), (s + 4, la, lo)], code, t0=s, t1=T.w("erster_angriff", 11.6), size=24,
                   fire=[(T.w("erster_angriff", 2.3), T.w("erster_angriff", 10.0))], target=P[tgt]))
    T.add(Explosion(*P["seddulbahir"], T.w("erster_angriff", 8.0), 1.3))
    T.add(Battle(*P["seddulbahir"], 0.6, T.w("erster_angriff", 2.6), T.w("erster_angriff", 10.5), rate=4))
    T.add(Battle(*P["kumkale"], 0.6, T.w("erster_angriff", 3.0), T.w("erster_angriff", 10.5), rate=4, seed=3))
    T.add(DateStamp("19. Februar 1915", "Der Flottenangriff beginnt", T.w("erster_angriff", 13.6), T.w("erster_angriff", 26.0)))
    # 19.2.1915: drei Schiffe beschießen Seddülbahir, drei Kumkale
    feb = [(40.045, 26.120, "gb", "seddulbahir"), (40.036, 26.130, "gb", "seddulbahir"), (40.052, 26.112, "fr", "seddulbahir"),
           (39.996, 26.135, "gb", "kumkale"), (39.986, 26.145, "fr", "kumkale"), (40.006, 26.125, "gb", "kumkale")]
    for i, (la, lo, code, tgt) in enumerate(feb):
        T.add(Ship([(T.w("erster_angriff", 13.0) + i * 0.2, la - 0.004, lo - 0.045), (T.w("erster_angriff", 17.5), la, lo)], code,
                   t0=T.w("erster_angriff", 13.0), t1=T.w("erster_angriff", 21.0), size=24,
                   fire=[(T.w("erster_angriff", 17.0), T.w("erster_angriff", 20.5))], target=P[tgt]))
    T.add(Battle(*P["seddulbahir"], 0.7, T.w("erster_angriff", 17.0), T.w("erster_angriff", 21.0), rate=6, seed=5))
    T.add(Battle(*P["kumkale"], 0.7, T.w("erster_angriff", 17.3), T.w("erster_angriff", 21.0), rate=6, seed=6))
    T.cam(T.w("erster_angriff", 20.5), Cam(40.10, 26.35, 18, 48, 28))
    for i in range(5):
        T.add(Ship([(T.w("erster_angriff", 25.5), 40.086 + i * 0.002, 26.322 + i * 0.006),
                    (T.w("erster_angriff", 28.5), 40.100 + i * 0.002, 26.330 + i * 0.006),
                    (T.w("erster_angriff", 31.5), 40.090 + i * 0.002, 26.325 + i * 0.006)], "gb",
                   t0=T.w("erster_angriff", 25.5), t1=T.end("erster_angriff") + 1.0, size=14))
    T.add(Label(40.084, 26.322, "Minenräumer (Fischdampfer)", t0=T.w("erster_angriff", 25.8), t1=T.end("erster_angriff") + 1.0, size=22, align="right", dx=-12, dot=False))
    T.add(Battle(40.100, 26.345, 0.6, T.w("erster_angriff", 27.0), T.end("erster_angriff") + 1.0, rate=6, seed=8))

    s = T.say("nusret", pre=0.6, post=1.8)
    T.add(Tint(skia.Color4f(0.02, 0.05, 0.14, 0.42), s - 0.6, T.end("nusret") + 1.2))
    T.add(DateStamp("7./8. März 1915", "Bucht von Erenköy · nachts", s, T.end("nusret")))
    T.cam(s - 0.4, Cam(40.098, 26.37, 11, 50, 200))
    T.cam(T.w("nusret", 14.0), Cam(40.085, 26.36, 9, 52, 215))
    nus_route = [(T.w("nusret", 4.8), 40.148, 26.392), (None, 40.128, 26.384), (None, 40.108, 26.360), (T.w("nusret", 9.5), 40.066, 26.3445),
                 (T.w("nusret", 17.0), 40.100, 26.357), (None, 40.112, 26.368), (T.w("nusret", 22.0), 40.135, 26.388)]
    T.add(Ship(nus_route, "tr", t0=T.w("nusret", 4.8), t1=T.end("nusret") + 0.8, name="Nusret", size=22))
    T.add(Mines(NUSRET_MINES, T.w("nusret", 9.7), t1=FORTS_END, size=4.2, stagger=(17.0 - 9.7) / 26, highlight=True))
    T.add(Label(40.083, 26.34, "26 Minen", "parallel zum Ufer", t0=T.w("nusret", 11.0), t1=T.end("nusret"), size=26, align="right", dx=-14, dot=False))
    for k in range(3):
        T.add(Arrow([(40.05 + k * 0.006, 26.300), (40.072 + k * 0.006, 26.330), (40.080 + k * 0.006, 26.312), (40.06 + k * 0.006, 26.296)], AL,
                    t0=T.w("nusret", 17.2) + k * 0.4, grow=2.2, t1=T.end("nusret"), width=7, dashed=True))
    T.add(Label(*P["erenkoy"], "Erenköy", t0=s, t1=T.end("nusret"), size=22))

    # ------------------------------------------------------------ Kapitel 3 · 18. März
    t = T.t
    T.mood(t, "naval")
    T.add(ChapterCard(3, "18. März 1915", "Der Angriff der Flotte", t + 0.2, 5.0))
    T.cam(t, Cam(40.06, 26.25, 30, 45, 32))
    T.wait(5.4)
    s = T.say("maerz_a", pre=0.2)
    T.say("maerz_b", pre=0.2, post=2.9)
    T.say("maerz_c", pre=0.2)
    for o in T.objects:
        if isinstance(o, (Fort, Mines)) and o.t1 == FORTS_END:
            o.t1 = T.end("maerz_c") + 1.5
    T.add(DateStamp("18. März 1915", "Dardanellen", s, T.end("maerz_c") - 1))
    T.cam(T.w("maerz_a", 12.0), Cam(40.085, 26.31, 24, 47, 30))
    tin = T.w("maerz_a", 3.0)
    ships = []
    # Linie A (britisch), Linie B (französisch), Linie C (britisch, Ablösung), Flanken
    lineA = [("Queen Elizabeth", 40.0925, 26.314), ("Agamemnon", 40.0930, 26.322), ("Lord Nelson", 40.0935, 26.330), ("Inflexible", 40.0940, 26.338)]
    lineB = [("Suffren", 40.0825, 26.322), ("Bouvet", 40.0830, 26.331), ("Gaulois", 40.0820, 26.313), ("Charlemagne", 40.0815, 26.304)]
    lineC = [("Vengeance", 40.0700, 26.290), ("Irresistible", 40.0705, 26.299), ("Albion", 40.0695, 26.281), ("Ocean", 40.0710, 26.308),
             ("Swiftsure", 40.0690, 26.272), ("Majestic", 40.0685, 26.317)]
    flank = [("Prince George", 40.0985, 26.322), ("Triumph", 40.0985, 26.336), ("Canopus", 40.0560, 26.262), ("Cornwallis", 40.0555, 26.275)]
    # Wo die getroffenen Schiffe auf die Nusret-Minen laufen (Bucht von Erenköy)
    hit_pos = {"Bouvet": (40.0835, 26.3485), "Inflexible": (40.0905, 26.3505), "Irresistible": (40.0885, 26.3500), "Ocean": (40.0935, 26.3525)}
    hit_go = {"Bouvet": T.w("maerz_b", 2.0), "Inflexible": T.w("maerz_b", 13.5), "Irresistible": T.w("maerz_b", 16.0), "Ocean": T.w("maerz_b", 18.5)}
    sink = {"Bouvet": T.w("maerz_b", 6.4), "Irresistible": T.w("maerz_b", 22.6), "Ocean": T.w("maerz_b", 23.4)}
    dmg = {"Inflexible": T.w("maerz_b", 17.6), "Suffren": T.w("maerz_b", 26.8), "Gaulois": T.w("maerz_b", 27.8)}
    names_shown = {"Bouvet", "Irresistible", "Ocean", "Inflexible", "Suffren", "Gaulois", "Queen Elizabeth"}
    retreat = T.w("maerz_c", 14.2)
    for i, (name, la, lo) in enumerate(lineA + lineB + lineC + flank):
        code = "fr" if (name, la, lo) in lineB else "gb"
        st = tin + i * 0.18
        # Start auf offener See vor der Einfahrt, mittig durch die Meerenge zwischen Seddülbahir und Kumkale
        lane = (i % 4 - 1.5) * 0.0025
        route = [(st, 40.020 + lane, 26.110), (None, 40.025 + lane, 26.198), (None, 40.040 + lane, 26.245),
                 (None, 40.058 + lane * 0.5, 26.280), (st + 11.0, la, lo)]
        if name in hit_pos:
            hp = hit_pos[name]
            route.append((hit_go[name], la, lo))
            route.append((hit_go[name] + 3.5, hp[0], hp[1]))
        if name not in sink:
            back_from = hit_pos.get(name, (la, lo))
            route.append((retreat, back_from[0], back_from[1]))
            route.append((None, 40.058 + lane * 0.5, 26.280))
            route.append((None, 40.040 + lane, 26.245))
            route.append((retreat + 9.0, 40.026 + lane, 26.180))
        fire = [(T.w("maerz_a", 14.6), T.w("maerz_b", 30.0))]
        tgt = [P["rumeli_mec"], P["hamidiye"], P["kilitbahir"], P["cimenlik"]][i % 4]
        ships.append(T.add(Ship(route, code, t0=st, t1=T.end("maerz_c") + 1, sink=sink.get(name), damaged=dmg.get(name),
                                name=None, size=25, fire=fire, target=tgt)))
        if name in names_shown:
            t_lab = sink.get(name, dmg.get(name, T.w("maerz_a", 14.0))) - 2.5
            if name == "Queen Elizabeth":
                t_lab = T.w("maerz_a", 13.0)
            lp = hit_pos.get(name, (la, lo))
            T.add(Label(lp[0], lp[1], name, t0=t_lab, t1=t_lab + 6.0, size=21, dot=False, dx=0, dy=34, align="center"))
    T.add(Token(40.071, 26.316, ["gb"], [(0, 14), (T.w("maerz_b", 23.8), 12)], label="Britische Schlachtschiffe", side=AL,
                t0=T.w("maerz_a", 6.8), t1=T.end("maerz_c") - 1, dx=-170, dy=10))
    T.add(Token(40.074, 26.327, ["fr"], [(0, 4), (T.w("maerz_b", 9.7), 3)], label="Französische Schlachtschiffe", side=AL,
                t0=T.w("maerz_a", 8.1), t1=T.end("maerz_c") - 1, dx=170, dy=40))
    T.add(Token(40.086, 26.353, ["tr"], [(0, 26)], label="Minen der Nusret", side=TR, t0=T.w("maerz_a", 18.0), t1=T.end("maerz_c") - 1,
                dx=150, dy=-60, unit=""))
    for key in ["rumeli_mec", "hamidiye", "kilitbahir", "cimenlik"]:
        fort_objs[key].fire = [(T.w("maerz_a", 18.2), T.w("maerz_b", 30.0))]
    T.add(Battle(40.14, 26.385, 1.2, T.w("maerz_a", 15.0), T.w("maerz_b", 31.0), rate=9))
    T.add(Battle(40.095, 26.33, 1.6, T.w("maerz_a", 18.5), T.w("maerz_b", 31.0), rate=7, seed=11, intensity=0.8))
    s = T.vstart["maerz_b"]
    T.cam(s - 0.5, Cam(40.084, 26.335, 12, 50, 28))
    T.add(Caption([(["fr"], "Bouvet: über 600 Tote")], T.w("maerz_b", 10.5), T.w("maerz_b", 16.0), pos="br", width=440))
    T.cam(T.w("maerz_b", 16.0), Cam(40.086, 26.335, 14, 48, 22))
    T.add(Caption([(["gb", "fr"], "Versenkt: Bouvet, Irresistible, Ocean"), (["gb", "fr"], "Schwer beschädigt: Inflexible, Suffren, Gaulois")],
                  T.w("maerz_b", 30.8), T.end("maerz_b") + 4.5, pos="br", width=640, title="Bilanz des 18. März"))
    s = T.vstart["maerz_c"]
    T.cam(s - 0.3, Cam(40.137, 26.378, 6.0, 52, 300))
    T.add(Caption([(["tr"], "Seyit Onbaşı · Festung Rumeli Mecidiye"), (None, "trägt der Überlieferung nach eine 215-kg-Granate")],
                  T.w("maerz_c", 2.0), T.w("maerz_c", 12.8), pos="br", width=620, title="Korporal Seyit"))
    T.cam(T.w("maerz_c", 13.0), Cam(40.08, 26.31, 26, 45, 30))
    T.add(Caption([(["tr"], "Osmanische Verluste: wenige Dutzend Gefallene")], T.w("maerz_c", 16.8), T.w("maerz_c", 22.4), pos="br", width=580))
    T.add(Caption([(["tr"], "„Çanakkale geçilmez“"), (None, "„Çanakkale ist unbezwingbar“")], T.w("maerz_c", 22.8), T.end("maerz_c") - 0.5,
                  pos="br", width=540, title="18. März · Deniz Zaferi"))
    T.cam(T.end("maerz_c") + 0.5, Cam(40.20, 26.38, 70, 35, 20))

    # ------------------------------------------------------------ Kapitel 4 · Landung
    t = T.t
    T.mood(t, "prepare")
    T.add(ChapterCard(4, "Die Landung", "April 1915", t + 0.2, 5.0))
    T.cam(t + 5.6, Cam(39.97, 25.55, 210, 24, 72))
    T.wait(5.4)
    s = T.say("aufmarsch", pre=0.2)
    T.add(Label(*P["mudros"], "Moudros", "Insel Limnos", t0=T.w("aufmarsch", 4.0), t1=T.end("aufmarsch"), size=26))
    T.add(Label(*P["imbros"], "Imbros", t0=T.w("aufmarsch", 4.4), t1=T.end("aufmarsch"), size=22))
    T.add(Token(39.90, 25.33, ["gb"], [(0, 27400)], label="Britische Truppen", side=AL, t0=T.w("aufmarsch", 8.4), t1=T.end("aufmarsch"), dx=-150, dy=-110))
    T.add(Token(39.88, 25.30, ["au", "nz"], [(0, 30600)], label="Anzac-Korps", side=AL, t0=T.w("aufmarsch", 9.9), t1=T.end("aufmarsch"), dx=150, dy=-120))
    T.add(Token(39.86, 25.28, ["fr"], [(0, 17000)], label="Französisches Korps", side=AL, t0=T.w("aufmarsch", 14.6), t1=T.end("aufmarsch"), dx=0, dy=90))
    T.add(Caption([(["gb", "au", "nz", "fr"], "ca. 75.000 Mann"), (None, "Oberbefehl: General Sir Ian Hamilton")],
                  T.w("aufmarsch", 16.3), T.w("aufmarsch", 23.5), pos="br", width=600, title="Mittelmeer-Expeditionsstreitmacht"))
    T.add(DateStamp("März – April 1915", "Aufmarsch", T.w("aufmarsch", 19.0), T.end("aufmarsch")))
    T.cam(T.w("aufmarsch", 23.6), Cam(40.25, 26.40, 95, 35, 25))
    T.add(Token(40.30, 26.52, ["tr"], [(0, 60000)], label="5. Osmanische Armee", side=TR, t0=T.w("aufmarsch", 24.5), t1=T.end("aufmarsch") + 0.8,
                dy=-80, note="Liman von Sanders"))
    s = T.say("verteidigung", pre=0.4)
    T.cam(s, Cam(40.20, 26.48, 105, 28, 20))
    T.add(Token(*P["bolayir"], ["tr"], [(0, 20000)], label="5. & 7. Division", side=TR, t0=T.w("verteidigung", 3.8), t1=T.end("verteidigung") + 0.8, dy=-75))
    T.add(Token(*P["krithia"], ["tr"], [(0, 10000)], label="9. Division", side=TR, t0=T.w("verteidigung", 8.8), t1=T.end("verteidigung") + 0.8, dy=-75))
    T.add(Token(39.97, 26.30, ["tr"], [(0, 20000)], label="3. & 11. Division", side=TR, t0=T.w("verteidigung", 11.2), t1=T.end("verteidigung") + 0.8, dy=60))
    T.add(Token(*P["bigali"], ["tr"], [(0, 10000)], label="19. Division", side=TR, t0=T.w("verteidigung", 15.0), t1=T.end("verteidigung") + 0.8, dx=60, dy=-80,
                note="Mustafa Kemal"))
    T.add(Label(*P["eceabat"], "Eceabat", t0=T.w("verteidigung", 15.5), t1=T.end("verteidigung") + 0.8, size=22))

    # 25. April – Seddülbahir / Kap Helles
    s = T.say("helles", pre=0.8)
    T.mood(s - 0.8, "landing")
    T.add(Tint(skia.Color4f(0.30, 0.18, 0.10, 0.18), s - 0.8, T.w("helles", 10.0)))
    T.add(DateStamp("25. April 1915", "Seddülbahir · Kap Helles", s, T.end("helles")))
    T.cam(s - 0.8, Cam(40.035, 26.165, 14, 48, 40))
    T.cam(T.w("helles", 12.0), Cam(40.048, 26.182, 7, 52, 35))
    T.cam(T.end("helles") - 2, Cam(40.055, 26.195, 10, 48, 38))
    beaches = [("S", P["sbeach"], (40.035, 26.235)), ("V", P["vbeach"], (40.028, 26.180)), ("W", P["wbeach"], (40.040, 26.150)),
               ("X", P["xbeach"], (40.064, 26.150)), ("Y", P["ybeach"], (40.092, 26.170))]
    for i, (name, dst, src) in enumerate(beaches):
        T.add(Arrow([src, dst], AL, t0=T.w("helles", 9.8) + i * 0.3, grow=1.8, t1=T.end("helles") + 1, width=12))
        T.add(Label(*dst, f"{name}-Strand", t0=T.w("helles", 10.0) + i * 0.3, t1=T.end("helles") + 1, size=21, dx=-14 if name != "S" else 14,
                    align="right" if name != "S" else "left"))
    T.add(Token(40.040, 26.172, ["gb"], [(0, 12000), (T.w("helles", 28.4), 9000)], label="29. Division", side=AL, t0=T.w("helles", 6.4),
                t1=T.end("helles") + 1, dx=-160, dy=-30))
    T.add(Token(40.060, 26.205, ["tr"], [(0, 4500), (T.w("helles", 31.4), 2600)], label="26. Regiment u. a.", side=TR, t0=T.w("helles", 16.0),
                t1=T.end("helles") + 1, dx=60, dy=-70))
    T.add(Ship([(T.w("helles", 22.4), 40.036, 26.186), (T.w("helles", 24.3), 40.0435, 26.1843)], "gb", t0=T.w("helles", 22.0),
               t1=T.end("helles") + 1, name="River Clyde", size=24))
    T.add(Battle(*P["vbeach"], 0.35, T.w("helles", 12.4), T.end("helles") + 1, rate=9))
    T.add(Battle(*P["wbeach"], 0.35, T.w("helles", 13.8), T.end("helles") + 1, rate=8, seed=4))
    T.add(Area([(40.0425, 26.180), (40.0420, 26.188), (40.0400, 26.192), (40.0385, 26.185), (40.0395, 26.178)], E.hexc("#b01010"),
               t0=T.w("helles", 30.3), t1=T.end("helles") + 1, alpha=0.45, outline=False, grow=2.0))
    T.add(Area([(40.0445, 26.165), (40.0560, 26.168), (40.0520, 26.190), (40.0475, 26.196), (40.0440, 26.186)], BLUE,
               t0=T.w("helles", 33.0), t1=T.end("helles") + 1, alpha=0.30, grow=1.5))

    # 25. April – Arıburnu
    s = T.say("anzac", pre=0.6)
    T.say("kemal", pre=0.3)
    T.add(DateStamp("25. April 1915", "Arıburnu · Anzac-Bucht", s, T.end("kemal")))
    T.cam(s - 0.6, Cam(40.228, 26.255, 9, 52, 75))
    T.cam(T.w("anzac", 13.0), Cam(40.242, 26.285, 6.5, 55, 80))
    T.add(Arrow([(40.200, 26.235), (40.203, 26.262)], AL, t0=T.w("anzac", 3.0), grow=1.5, t1=T.w("anzac", 12.0), width=9, dashed=True))
    T.add(Label(*P["kabatepe"], "geplant: Kabatepe", t0=T.w("anzac", 3.4), t1=T.w("anzac", 12.0), size=22, dy=20))
    T.add(Arrow([(40.215, 26.235), (40.232, 26.262), (40.2405, 26.279)], AL, t0=T.w("anzac", 5.0), grow=2.2, t1=T.end("kemal"), width=12))
    T.add(Label(*P["ariburnu"], "Arıburnu", "Anzac-Bucht", t0=T.w("anzac", 8.8), t1=T.end("kemal"), size=26, dx=-14, align="right"))
    for dst in [P["plateau400"], P["battleship"], (40.252, 26.301)]:
        T.add(Arrow([P["anzac"], ((P["anzac"][0] + dst[0]) / 2, (P["anzac"][1] + dst[1]) / 2 + 0.002), dst], AL,
                    t0=T.w("anzac", 14.8), grow=3.0, t1=T.end("kemal"), width=10))
    T.add(Label(*P["chunuk"], "Conkbayırı", "Chunuk Bair", t0=T.w("anzac", 16.8), t1=T.end("kemal"), size=24))
    T.add(Token(40.226, 26.268, ["au", "nz"], [(0, 16000), (T.w("kemal", 21.0), 14000)], label="Anzac", side=AL,
                t0=T.w("anzac", 1.4), t1=T.end("kemal") + 1, dx=-70, dy=-60))
    T.add(Arrow([P["bigali"], (40.245, 26.330), (40.252, 26.312)], TR, t0=T.w("anzac", 22.4), grow=2.5, t1=T.end("kemal"), width=12))
    T.add(Token(40.252, 26.312, ["tr"], [(0, 10000), (T.w("kemal", 21.2), 8000)], label="57. Regiment u. a.", side=TR,
                t0=T.w("anzac", 23.0), t1=T.end("kemal") + 1, dx=90, dy=-70, note="Mustafa Kemal"))
    s = T.vstart["kemal"]
    T.add(Quote(["Ich befehle euch nicht anzugreifen.", "Ich befehle euch zu sterben."], "MUSTAFA KEMAL · 25. APRIL 1915",
                T.w("kemal", 9.4), T.w("kemal", 19.8), size=56))
    T.add(Battle(40.245, 26.293, 0.8, T.w("kemal", 19.6), T.end("kemal") + 1, rate=8))
    T.add(Area(ANZAC_AREA, BLUE,
               t0=T.w("kemal", 24.5), t1=T.end("kemal") + 1, alpha=0.32, grow=1.5))

    # Kumkale & Bolayır
    s = T.say("kumkale", pre=0.6)
    T.add(DateStamp("25. – 27. April 1915", "Kumkale · Bolayır", s, T.end("kumkale")))
    T.cam(s - 0.6, Cam(40.00, 26.215, 12, 48, 60))
    T.add(Arrow([(39.99, 26.150), (40.0035, 26.196)], AL, t0=T.w("kumkale", 0.6), grow=1.6, t1=T.w("kumkale", 11.5), width=12))
    T.add(Token(39.985, 26.170, ["fr"], [(0, 3000), (T.w("kumkale", 9.4), 2214)], label="Französische Truppen", side=AL,
                t0=T.w("kumkale", 1.2), t1=T.w("kumkale", 11.8), dx=-30, dy=-70))
    T.add(LossBadge(40.010, 26.225, ["tr"], 1735, T.w("kumkale", 9.6), T.w("kumkale", 11.8), label="Osmanische Verluste", dx=80, dy=-60))
    T.add(Battle(*P["kumkale"], 0.5, T.w("kumkale", 4.5), T.w("kumkale", 11.0), rate=8))
    T.add(Arrow([(40.0035, 26.196), (39.99, 26.150)], AL, t0=T.w("kumkale", 10.6), grow=1.4, t1=T.w("kumkale", 12.0), width=9, dashed=True))
    T.cam(T.w("kumkale", 11.0), Cam(40.47, 26.70, 32, 40, 40))
    T.add(Arrow([(40.42, 26.62), (40.48, 26.70)], AL, t0=T.w("kumkale", 12.6), grow=1.6, t1=T.end("kumkale") + 1, width=10, dashed=True))
    T.add(Token(*P["bolayir"], ["tr"], [(0, 20000)], label="5. & 7. Division", side=TR, t0=T.w("kumkale", 11.6), t1=T.end("kumkale") + 1, dy=-75))
    T.add(Label(40.43, 26.61, "Scheinlandung", t0=T.w("kumkale", 13.0), t1=T.end("kumkale") + 1, size=22, align="right", dx=-12, dot=False))

    # ------------------------------------------------------------ Kapitel 5 · Grabenkrieg
    t = T.t
    T.mood(t, "trench")
    T.add(ChapterCard(5, "Kampf um jeden Meter", "April – Juli 1915", t + 0.2, 5.0))
    T.cam(t + 5.6, Cam(40.072, 26.225, 13, 48, 45))
    T.wait(5.4)
    s = T.say("kirte", pre=0.2)
    T.say("kirte3", pre=0.6)
    T.add(Label(*P["krithia"], "Kirte", "Krithia", t0=T.w("kirte", 2.2), t1=T.end("kirte3"), size=26))
    T.add(Label(*P["achibaba"], "Alçıtepe", "Achi Baba · 218 m", t0=T.w("kirte", 5.4), t1=T.end("kirte3"), size=26))
    T.add(DateStamp("28. April 1915", "Erste Schlacht um Kirte", T.w("kirte", 8.0), T.w("kirte", 15.8)))
    front1 = [(40.0650, 26.180), (40.0650, 26.200), (40.0610, 26.220), (40.0590, 26.235)]
    T.add(Polyline(front1, BLUE, t0=T.w("kirte", 7.6), t1=T.w("kirte", 30.5), width=4, dash=(12, 6)))
    for i, lo in enumerate([26.190, 26.207, 26.224]):
        T.add(Arrow([(40.066, lo), (40.080, lo + 0.008)], AL, t0=T.w("kirte", 9.4) + i * 0.3, grow=2.0, t1=T.w("kirte", 15.6), width=11))
    T.add(Token(40.063, 26.198, ["gb"], [(0, 10000), (T.w("kirte", 14.5), 8000)], label="Briten", side=AL, t0=T.w("kirte", 9.5), t1=T.w("kirte", 15.8), dx=-130, dy=60))
    T.add(Token(40.060, 26.233, ["fr"], [(0, 4000), (T.w("kirte", 14.6), 3000)], label="Franzosen", side=AL, t0=T.w("kirte", 10.0), t1=T.w("kirte", 15.8), dx=130, dy=60))
    T.add(LossBadge(40.090, 26.215, ["tr"], 2400, T.w("kirte", 14.8), T.w("kirte", 15.8), label="Osmanische Verluste", dy=-70))
    T.add(Battle(40.075, 26.210, 1.0, T.w("kirte", 10.5), T.w("kirte", 15.5), rate=8))
    T.add(DateStamp("6. – 8. Mai 1915", "Zweite Schlacht um Kirte", T.w("kirte", 16.0), T.end("kirte")))
    T.add(Token(40.050, 26.205, ["gb", "fr", "au", "nz"], [(0, 25000), (T.w("kirte", 26.9), 18500)], label="Alliierte", side=AL,
                t0=T.w("kirte", 17.6), t1=T.end("kirte") + 0.5, dx=-30, dy=50))
    T.add(Token(*P["krithia"], ["tr"], [(0, 20000), (T.w("kirte", 27.4), 18000)], label="Osmanische Truppen", side=TR,
                t0=T.w("kirte", 17.6), t1=T.end("kirte") + 0.5, dx=40, dy=-80))
    for i, lo in enumerate([26.188, 26.205, 26.222, 26.238]):
        T.add(Arrow([(40.064, lo), (40.078, lo + 0.006)], AL, t0=T.w("kirte", 18.6) + i * 0.25, grow=2.0, t1=T.end("kirte") + 0.5, width=11))
    T.add(Battle(40.072, 26.212, 1.2, T.w("kirte", 19.5), T.w("kirte", 29.0), rate=10))
    front2 = [(40.0680, 26.180), (40.0690, 26.200), (40.0650, 26.220), (40.0620, 26.240)]
    T.add(Polyline(front2, BLUE, t0=T.w("kirte", 30.6), t1=T.end("kirte3") + 1, width=4, dash=(12, 6)))
    T.add(Polyline([(40.0725, 26.180), (40.0735, 26.200), (40.0700, 26.222), (40.0665, 26.245)], RED, t0=T.w("kirte", 30.6),
                   t1=T.end("kirte3") + 1, width=4, dash=(12, 6)))

    s = T.vstart["kirte3"]
    T.add(DateStamp("4. Juni 1915", "Dritte Schlacht um Kirte", s, T.w("kirte3", 12.0)))
    T.add(Token(40.064, 26.205, ["gb"], [(0, 20000), (T.w("kirte3", 10.0), 15500)], label="Briten", side=AL, t0=T.w("kirte3", 2.6), t1=T.w("kirte3", 12.2), dx=-130, dy=60))
    T.add(Token(40.061, 26.236, ["fr"], [(0, 10000), (T.w("kirte3", 10.2), 8000)], label="Franzosen", side=AL, t0=T.w("kirte3", 4.2), t1=T.w("kirte3", 12.2), dx=130, dy=60))
    T.add(Token(*P["krithia"], ["tr"], [(0, 25000), (T.w("kirte3", 11.0), 22000)], label="Osmanische Truppen", side=TR,
                t0=T.w("kirte3", 5.6), t1=T.w("kirte3", 12.2), dx=40, dy=-80))
    T.add(Arrow([(40.068, 26.205), (40.080, 26.212)], AL, t0=T.w("kirte3", 7.4), grow=1.4, t1=T.w("kirte3", 12.0), width=13))
    for lo in [26.195, 26.212, 26.230]:
        T.add(Arrow([(40.085, lo + 0.006), (40.073, lo)], TR, t0=T.w("kirte3", 9.6), grow=1.6, t1=T.w("kirte3", 12.0), width=11))
    T.add(Battle(40.072, 26.212, 1.2, T.w("kirte3", 4.8), T.w("kirte3", 11.8), rate=10))
    T.cam(T.w("kirte3", 11.6), Cam(40.078, 26.205, 6, 52, 30))
    T.add(DateStamp("28. Juni – 5. Juli 1915", "Zığındere · Gully Ravine", T.w("kirte3", 12.2), T.end("kirte3")))
    T.add(Label(*P["gully"], "Zığındere", "Gully Ravine", t0=T.w("kirte3", 13.0), t1=T.end("kirte3") + 1, size=24, dx=-14, align="right"))
    T.add(LossBadge(40.086, 26.212, ["tr"], 14000, T.w("kirte3", 18.4), T.end("kirte3") + 1, label="Osmanische Verluste", dx=70, dy=-70))
    T.add(LossBadge(40.072, 26.196, ["gb"], 3800, T.w("kirte3", 19.2), T.end("kirte3") + 1, label="Britische Verluste", side=AL, dx=-80, dy=70))
    T.add(Battle(40.080, 26.205, 0.6, T.w("kirte3", 14.0), T.w("kirte3", 22.5), rate=9, seed=21))
    T.cam(T.w("kirte3", 22.8), Cam(40.07, 26.215, 11, 45, 40))

    # 19. Mai – Arıburnu
    s = T.say("mai19", pre=0.8)
    T.say("waffenruhe", pre=0.5)
    T.say("see", pre=0.8)
    T.add(DateStamp("19. Mai 1915", "Arıburnu", s, T.end("mai19")))
    T.cam(s - 0.8, Cam(40.240, 26.292, 6.0, 52, 85))
    T.add(Area(ANZAC_AREA, BLUE,
               t0=s, t1=T.end("waffenruhe") + 1, alpha=0.28))
    T.add(Token(40.244, 26.310, ["tr"], [(0, 42000), (T.w("mai19", 20.0), 32000)], label="Osmanischer Angriff", side=TR,
                t0=T.w("mai19", 7.0), t1=T.end("mai19") + 1, dx=70, dy=-80))
    for i, (la, lo) in enumerate([(40.233, 26.305), (40.241, 26.308), (40.249, 26.303)]):
        T.add(Arrow([(la, lo), (la, lo - 0.010)], TR, t0=T.w("mai19", 8.0) + i * 0.3, grow=2.0, t1=T.w("mai19", 22.0), width=12))
    T.add(Token(40.238, 26.277, ["au", "nz"], [(0, 17300), (T.w("mai19", 25.8), 16660)], label="Anzac", side=AL,
                t0=T.w("mai19", 12.6), t1=T.end("mai19") + 1, dx=-70, dy=-60))
    T.add(Battle(40.241, 26.295, 0.7, T.w("mai19", 8.5), T.w("mai19", 23.5), rate=12))
    s = T.vstart["waffenruhe"]
    T.add(DateStamp("24. Mai 1915", "Waffenruhe", s, T.end("waffenruhe")))
    T.cam(s - 0.5, Cam(40.240, 26.292, 4.2, 56, 80))
    T.add(Caption([(None, "9 Stunden Waffenruhe, um die Toten zu begraben")], T.w("waffenruhe", 3.8), T.w("waffenruhe", 15.5), pos="br", width=600,
                  title="24. Mai 1915"))
    T.add(Polyline([(40.2352, 26.2895), (40.2378, 26.2915), (40.2405, 26.2922), (40.2440, 26.2935), (40.2475, 26.2900)], BLUE,
                   t0=T.w("waffenruhe", 16.0), t1=T.end("waffenruhe") + 1, width=4, grow=1.5))
    T.add(Polyline([(40.2350, 26.2910), (40.2376, 26.2928), (40.2404, 26.2934), (40.2441, 26.2948), (40.2480, 26.2912)], RED,
                   t0=T.w("waffenruhe", 16.3), t1=T.end("waffenruhe") + 1, width=4, grow=1.5))
    T.add(Label(40.2405, 26.2930, "oft nur wenige Meter", t0=T.w("waffenruhe", 18.6), t1=T.end("waffenruhe") + 1, size=22, dx=16, dot=False))

    s = T.vstart["see"]
    T.add(DateStamp("Mai 1915", "Krieg auf See", s, T.end("see")))
    T.cam(s - 0.8, Cam(40.11, 26.24, 40, 42, 30))
    T.add(Ship([(s, 40.054, 26.240)], "gb", t0=s, t1=T.end("see"), sink=T.w("see", 9.6), name="Goliath", size=24))
    T.add(Ship([(T.w("see", 4.8), 40.10, 26.335), (None, 40.076, 26.302), (T.w("see", 8.8), 40.060, 26.246), (None, 40.076, 26.302), (T.w("see", 12.0), 40.10, 26.335)], "tr",
               t0=T.w("see", 4.6), t1=T.w("see", 13.0), name="Muavenet-i Milliye", size=18))
    T.add(Ship([(s, 40.215, 26.240)], "gb", t0=s, t1=T.end("see"), sink=T.w("see", 15.0), name="Triumph", size=24))
    T.add(Ship([(s, 40.050, 26.160)], "gb", t0=s, t1=T.end("see"), sink=T.w("see", 16.2), name="Majestic", size=24))
    T.add(Ship([(T.w("see", 11.6), 40.14, 26.12), (T.w("see", 14.0), 40.17, 26.19)], "de", t0=T.w("see", 11.4), t1=T.w("see", 19.0), name="U 21", size=14))
    T.add(Arrow([(40.17, 26.19), (40.212, 26.236)], "al", t0=T.w("see", 13.4), grow=1.3, t1=T.w("see", 16.0), width=3, color=E.WHITE, head=1.6))
    T.add(Arrow([(40.10, 26.12), (40.054, 26.158)], "al", t0=T.w("see", 15.0), grow=1.0, t1=T.w("see", 17.0), width=3, color=E.WHITE, head=1.6))
    T.cam(T.w("see", 18.6), Cam(40.25, 26.48, 70, 40, 30))
    T.add(Arrow([(40.03, 26.24), (40.10, 26.34), (40.15, 26.39), (40.30, 26.56), (40.42, 26.70), (40.50, 26.95)], AL,
                t0=T.w("see", 20.4), grow=5.0, t1=T.end("see") + 1, width=7, dashed=True))
    T.add(Label(40.52, 26.98, "Marmarameer", t0=T.w("see", 24.6), t1=T.end("see") + 1, size=26, style="sea", dot=False))

    # ------------------------------------------------------------ Kapitel 6 · Augustoffensive
    t = T.t
    T.mood(t, "august")
    T.add(ChapterCard(6, "Die Augustoffensive", "6. – 21. August 1915", t + 0.2, 5.0))
    T.cam(t + 5.6, Cam(40.262, 26.300, 20, 45, 75))
    T.wait(5.4)
    s = T.say("sommer", pre=0.2)
    for k, pre, post in [("lonepine", 0.6, 1.4), ("nek", 0.6, 2.2), ("conk", 0.6, 1.4), ("kemal_conk", 0.6, 1.8), ("suvla", 0.6, 1.4), ("anafarta", 0.6, 2.4)]:
        T.say(k, pre=pre, post=post)
    T.add(Caption([(None, "Hitze, Fliegen, Wassermangel"), (None, "Ruhr und Typhus in den Gräben")], T.w("sommer", 0.4), T.w("sommer", 9.0),
                  pos="br", width=520, title="Sommer 1915"))
    T.add(Label(*P["chunuk"], "Conkbayırı", "Chunuk Bair", t0=T.w("sommer", 15.0), t1=T.end("kemal_conk"), size=24))
    T.add(Label(*P["suvla"], "Suvla-Bucht", "Anafarta", t0=T.w("sommer", 19.3), t1=T.end("anafarta"), size=24, dx=-14, align="right"))
    T.add(Arrow([(40.285, 26.180), (40.295, 26.236)], AL, t0=T.w("sommer", 19.6), grow=1.8, t1=T.end("sommer") + 0.5, width=11, dashed=True))
    T.add(Arrow([(40.262, 26.272), (40.258, 26.290), (40.2545, 26.305)], AL, t0=T.w("sommer", 15.4), grow=2.0, t1=T.end("sommer") + 0.5, width=11, dashed=True))
    T.add(Arrow([(40.296, 26.250), (40.282, 26.300), (40.262, 26.320)], AL, t0=T.w("sommer", 22.3), grow=2.0, t1=T.end("sommer") + 0.5, width=10, dashed=True))

    s = T.vstart["lonepine"]
    T.add(DateStamp("6. – 9. August 1915", "Kanlısırt · Lone Pine", s, T.end("lonepine")))
    T.cam(s - 0.6, Cam(40.2305, 26.2915, 4.6, 55, 85))
    T.add(Label(*P["lonepine"], "Kanlısırt", "Lone Pine", t0=T.w("lonepine", 8.6), t1=T.end("lonepine") + 1, size=26, dx=-30, dy=10, align="right"))
    for i in range(4):
        T.add(Arrow([(40.2295 + i * 0.0008, 26.2855), (40.2305 + i * 0.0006, 26.2905)], AL, t0=T.w("lonepine", 5.3) + i * 0.3, grow=1.5,
                    t1=T.end("lonepine") + 1, width=10))
    T.add(Battle(*P["lonepine"], 0.25, T.w("lonepine", 6.5), T.w("lonepine", 26.0), rate=11))
    T.add(LossBadge(40.228, 26.284, ["au"], 2277, T.w("lonepine", 21.2), T.end("lonepine") + 1, label="Australische Verluste", side=AL, dx=-60, dy=70))
    T.add(LossBadge(40.233, 26.296, ["tr"], 6000, T.w("lonepine", 24.4), T.end("lonepine") + 1, label="Osmanische Verluste (geschätzt)", dx=70, dy=-80))

    s = T.vstart["nek"]
    T.add(DateStamp("7. August 1915", "Cesarettepe · The Nek", s, T.end("nek")))
    T.cam(s - 0.6, Cam(40.2462, 26.2920, 4.0, 56, 75))
    T.add(Label(*P["nek"], "Cesarettepe", "The Nek", t0=T.w("nek", 6.8), t1=T.end("nek") + 1, size=24, dx=30, dy=30))
    T.add(Token(40.2462, 26.2885, ["au"], [(0, 600), (T.w("nek", 14.2), 228)], label="Leichte Reiter", side=AL, t0=T.w("nek", 2.0),
                t1=T.end("nek") + 1, dx=-60, dy=-70))
    for i in range(4):
        T.add(Arrow([(40.2464, 26.2893), (40.2470, 26.2915)], AL, t0=T.w("nek", 8.8) + i * 0.6, grow=0.9, t1=T.w("nek", 12.4) + i * 0.6, width=9))
    T.add(Battle(40.2468, 26.2910, 0.12, T.w("nek", 9.0), T.w("nek", 13.5), rate=12))

    s = T.vstart["conk"]
    T.add(DateStamp("8. August 1915", "Conkbayırı · Chunuk Bair", s, T.end("conk")))
    T.cam(s - 0.6, Cam(40.257, 26.300, 6, 52, 60))
    for path in [[(40.262, 26.272), (40.262, 26.290), (40.2555, 26.306)], [(40.268, 26.276), (40.266, 26.300), (40.259, 26.316)]]:
        T.add(Arrow(path, AL, t0=T.w("conk", 3.4), grow=4.0, t1=T.end("conk") + 0.5, width=11))
    T.add(Token(40.2537, 26.3085, ["nz"], [(0, 760), (T.w("conk", 23.6), 70)], label="Wellington-Bataillon", side=AL, t0=T.w("conk", 13.2),
                t1=T.end("conk") + 0.8, dx=-70, dy=-70))
    T.add(Battle(*P["chunuk"], 0.35, T.w("conk", 15.8), T.end("conk"), rate=10))

    s = T.vstart["kemal_conk"]
    T.add(DateStamp("10. August 1915", "Gegenangriff bei Conkbayırı", s, T.end("kemal_conk")))
    T.cam(s - 0.6, Cam(40.2555, 26.312, 4.5, 52, 265))
    for i, (la, lo) in enumerate([(40.250, 26.330), (40.256, 26.334), (40.262, 26.330)]):
        T.add(Arrow([(la, lo), (40.2545 + (i - 1) * 0.002, 26.311)], TR, t0=T.w("kemal_conk", 9.4) + i * 0.3, grow=3.0, t1=T.end("kemal_conk") + 0.8, width=12))
    T.add(Token(40.2537, 26.3085, ["gb"], [(0, 1)], label="Briten auf dem Gipfel", side=AL, t0=T.w("kemal_conk", 6.0), t1=T.w("kemal_conk", 17.4),
                dx=0, dy=-75, loss_only=True))
    T.add(Token(40.256, 26.326, ["tr"], [(0, 1)], label="Mustafa Kemal", side=TR, t0=T.w("kemal_conk", 0.2), t1=T.end("kemal_conk") + 0.8,
                dx=60, dy=-80, loss_only=True))
    T.add(Battle(*P["chunuk"], 0.35, T.w("kemal_conk", 12.0), T.w("kemal_conk", 18.5), rate=12))
    T.add(Caption([(["tr"], "Granatsplitter trifft Kemal – die Taschenuhr rettet ihn")], T.w("kemal_conk", 18.3), T.w("kemal_conk", 24.0), pos="br", width=660))
    T.add(Caption([(["gb", "au", "nz"], "Alliierte: ca. 12.500 Verluste"), (["tr"], "Osmanen: ca. 9.200 Verluste")],
                  T.w("kemal_conk", 24.0), T.end("kemal_conk") + 1.0, pos="br", width=560, title="Kampf um die Höhen, 6.–10. August"))

    s = T.vstart["suvla"]
    T.add(DateStamp("6./7. August 1915", "Suvla-Bucht · Anafartalar", s, T.end("suvla")))
    T.cam(s - 0.6, Cam(40.298, 26.265, 13, 48, 80))
    for i, (src, dst) in enumerate([((40.290, 26.190), (40.293, 26.236)), ((40.305, 26.185), (40.305, 26.226)), ((40.272, 26.205), (40.275, 26.240))]):
        T.add(Arrow([src, dst], AL, t0=T.w("suvla", 1.8) + i * 0.3, grow=1.8, t1=T.end("suvla") + 1, width=12))
    T.add(Token(40.296, 26.226, ["gb"], [(0, 20000)], label="IX. Korps", side=AL, t0=T.w("suvla", 2.6), t1=T.end("suvla") + 1, dx=-70, dy=-70))
    T.add(Token(40.300, 26.300, ["tr"], [(0, 1500)], label="Gruppe Willmer", side=TR, t0=T.w("suvla", 8.4), t1=T.end("suvla") + 1, dx=60, dy=-70))
    T.add(Arrow([(40.296, 26.240), (40.297, 26.262)], AL, t0=T.w("suvla", 13.6), grow=1.2, t1=T.w("suvla", 17.2), width=10, dashed=True))
    T.add(Label(40.292, 26.245, "Stillstand am Strand", t0=T.w("suvla", 18.6), t1=T.end("suvla") + 0.5, size=22, dy=46, dot=False))

    s = T.vstart["anafarta"]
    T.add(DateStamp("9. – 21. August 1915", "Anafartalar", s, T.end("anafarta")))
    T.cam(s - 0.6, Cam(40.292, 26.285, 14, 48, 82))
    for i, (src, dst) in enumerate([((40.285, 26.355), (40.288, 26.300)), ((40.320, 26.345), (40.312, 26.296)), ((40.300, 26.360), (40.300, 26.310))]):
        T.add(Arrow([src, dst], TR, t0=T.w("anafarta", 3.4) + i * 0.4, grow=2.6, t1=T.end("anafarta") + 1, width=13))
    T.add(Token(40.296, 26.326, ["tr"], [(0, 1)], label="Osmanische Verstärkung", side=TR, t0=T.w("anafarta", 4.0), t1=T.end("anafarta") + 1,
                dx=60, dy=-70, loss_only=True, note="7. und 12. Division"))
    T.add(Battle(40.292, 26.285, 1.0, T.w("anafarta", 9.0), T.w("anafarta", 13.2), rate=10))
    T.cam(T.w("anafarta", 14.0), Cam(40.282, 26.282, 6, 52, 85))
    T.add(Label(*P["scimitar"], "Yusufçuk Tepe", "Scimitar Hill", t0=T.w("anafarta", 17.8), t1=T.end("anafarta") + 1, size=24, dy=46))
    T.add(Token(40.282, 26.262, ["gb"], [(0, 14300), (T.w("anafarta", 25.4), 9000)], label="Britische Angreifer", side=AL,
                t0=T.w("anafarta", 22.4), t1=T.end("anafarta") + 1, dx=-70, dy=-70))
    T.add(LossBadge(40.290, 26.300, ["tr"], 2600, T.w("anafarta", 26.0), T.end("anafarta") + 1, label="Osmanische Verluste", dx=70, dy=-80))
    T.add(Arrow([(40.283, 26.268), (40.2855, 26.287)], AL, t0=T.w("anafarta", 16.6), grow=1.6, t1=T.end("anafarta") + 1, width=12))
    T.add(Battle(*P["scimitar"], 0.4, T.w("anafarta", 16.8), T.end("anafarta"), rate=11))
    T.add(Fire(40.2845, 26.284, 0.5, T.w("anafarta", 27.6), T.end("anafarta") + 1.5))

    # ------------------------------------------------------------ Kapitel 7 · Rückzug
    t = T.t
    T.mood(t, "winter")
    T.add(ChapterCard(7, "Der Rückzug", "Herbst 1915 – Januar 1916", t + 0.2, 5.0))
    T.cam(t + 5.6, Cam(43.0, 24.5, 1500, 0, 0))
    T.wait(5.4)
    s = T.say("herbst", pre=0.2, post=1.8)
    T.say("rueckzug", pre=0.8, post=2.0)
    T.add(countries_layer(T, s - 2.5, T.w("herbst", 20.5), s - 2.4, s - 2.4, s - 2.4, bulgaria_on=T.w("herbst", 5.0)))
    T.add(Label(42.7, 25.2, "Bulgarien", t0=T.w("herbst", 5.0), t1=T.w("herbst", 20.5), style="country", size=26))
    T.add(Label(*P["istanbul"], "Istanbul", t0=s, t1=T.w("herbst", 20.5), size=22))
    T.add(Polyline([(52.52, 13.40), (48.2, 16.37), (44.8, 20.46), (43.3, 21.9), (42.7, 23.3), (42.15, 24.75), (41.68, 26.56), (41.01, 28.98)],
                   E.hexc("#ffcc66"), t0=T.w("herbst", 8.4), t1=T.w("herbst", 20.5), width=4, grow=3.5, dash=(16, 10), glow=True))
    T.add(Caption([(["de"], "Bahnlinie Berlin – Wien – Sofia – Istanbul offen")], T.w("herbst", 9.0), T.w("herbst", 14.0), pos="br", width=620))
    T.add(Caption([(["gb"], "Okt. 1915: Hamilton abgelöst"), (["gb"], "General Charles Monro empfiehlt Räumung")], T.w("herbst", 14.2), T.w("herbst", 20.5),
                  pos="br", width=580))
    T.cam(T.w("herbst", 6.0), Cam(44.5, 22.0, 2000, 0, 0))
    T.cam(T.w("herbst", 20.8), Cam(40.27, 26.30, 30, 45, 75))
    T.add(Snow(T.w("herbst", 21.4), T.end("herbst") + 1.5))
    T.add(DateStamp("26. – 28. November 1915", "Schneesturm", T.w("herbst", 21.5), T.end("herbst") + 1))

    s = T.vstart["rueckzug"]
    T.add(DateStamp("Dezember 1915", "Räumung von Arıburnu und Suvla", s, T.w("rueckzug", 18.0)))
    T.add(Tint(skia.Color4f(0.02, 0.05, 0.14, 0.38), s - 0.6, T.w("rueckzug", 18.0)))
    T.cam(s - 0.8, Cam(40.27, 26.25, 24, 45, 75))
    T.add(Token(40.296, 26.236, ["gb"], [(0, 41000), (T.w("rueckzug", 8.0), 0)], label="Suvla", side=AL, t0=s, t1=T.w("rueckzug", 18.0),
                dx=-60, dy=-70, show_loss=False))
    T.add(Token(40.240, 26.281, ["au", "nz", "gb"], [(0, 36000), (T.w("rueckzug", 8.4), 0)], label="Arıburnu", side=AL, t0=s, t1=T.w("rueckzug", 18.0),
                dx=-60, dy=60, show_loss=False))
    for src in [(40.296, 26.236), (40.240, 26.278)]:
        T.add(Arrow([src, (src[0] - 0.01, src[1] - 0.09)], AL, t0=T.w("rueckzug", 9.0), grow=2.5, t1=T.w("rueckzug", 18.0), width=9, dashed=True))
    T.add(Caption([(None, "„Tropfgewehre“: Wasser füllt eine Dose,"), (None, "die den Abzug zieht – Schüsse ohne Schützen")],
                  T.w("rueckzug", 11.6), T.w("rueckzug", 18.0), pos="br", width=600))
    T.cam(T.w("rueckzug", 18.0), Cam(40.052, 26.200, 12, 48, 40))
    T.add(DateStamp("9. Januar 1916", "Räumung von Seddülbahir", T.w("rueckzug", 18.7), T.end("rueckzug") + 1))
    T.add(Token(40.055, 26.195, ["gb"], [(0, 35000), (T.w("rueckzug", 23.0), 0)], label="Kap Helles", side=AL, t0=T.w("rueckzug", 18.4),
                t1=T.end("rueckzug") + 1, dx=-60, dy=-70, show_loss=False))
    T.add(Arrow([(40.050, 26.180), (40.030, 26.100)], AL, t0=T.w("rueckzug", 22.0), grow=2.5, t1=T.end("rueckzug") + 1, width=9, dashed=True))

    # ------------------------------------------------------------ Kapitel 8 · Bilanz
    t = T.t
    T.mood(t, "legacy")
    T.add(ChapterCard(8, "Bilanz", "Acht Monate Çanakkale", t + 0.2, 5.0))
    T.cam(t + 5.6, Cam(40.17, 26.30, 60, 28, 22))
    T.wait(5.4)
    A = ["gb", "fr"]
    battles = [
        ((40.098, 26.345), "Seeschlacht", "18. März 1915", ["tr"], A, "osmanischer Sieg", 200, 10),
        ((40.046, 26.182), "Landung Seddülbahir", "25. April", ["tr"], ["gb"], "Brückenkopf", -190, 50),
        ((40.240, 26.282), "Landung Arıburnu", "25. April", ["tr"], ["au", "nz"], "Höhen bleiben osmanisch", -250, 0),
        ((40.004, 26.205), "Kumkale", "25.–27. April", ["tr"], ["fr"], "Franzosen ziehen ab", 180, 50),
        ((40.083, 26.226), "Kirte I–III", "April – Juni", ["tr"], A, "Angriffe abgewehrt", 190, 70),
        ((40.080, 26.200), "Zığındere", "Juni/Juli", ["tr"], ["gb"], "kleiner Geländegewinn", -220, -20),
        ((40.243, 26.300), "Angriff auf Arıburnu", "19. Mai", ["tr"], ["au", "nz"], "Angriff scheitert", 230, -40),
        ((40.231, 26.289), "Kanlısırt", "6.–9. August", ["tr"], ["au"], "australischer Gewinn", 220, 40),
        ((40.2537, 26.3085), "Conkbayırı", "8.–10. August", ["tr"], ["nz", "gb"], "osmanischer Sieg", 200, -110),
        ((40.300, 26.300), "Anafartalar", "August 1915", ["tr"], ["gb"], "osmanischer Sieg", -150, -80),
    ]
    tb = T.t
    for i, ((la, lo), name, date, ftr, fal, res, dx, dy) in enumerate(battles):
        T.add(BattleMarker(la, lo, name, date, ftr, fal, t0=tb + 0.6 + i * 0.55, t1=tb + 7.4 + T.vdur["bilanz"] + 1.5, dx=dx, dy=dy, result=res))
    T.wait(7.0)
    s = T.say("bilanz", pre=0.4)
    T.cam(T.w("bilanz", 15.5), Cam(40.16, 26.43, 74, 28, 22))
    T.cam(T.end("bilanz"), Cam(40.17, 26.45, 78, 28, 19), "linear")
    T.add(Caption([(["gb", "fr", "au", "nz"], "Alliierte eingesetzt: ca. 490.000"), (["tr"], "Osmanen eingesetzt: ca. 315.000")],
                  T.w("bilanz", 3.0), T.w("bilanz", 14.6), pos="br", width=560, title="Acht Monate Krieg"))
    rows = [(["tr"], "Osmanisches Reich", 56643, "Generalstab; Schätzungen bis 87.000", T.w("bilanz", 15.2)),
            (["gb"], "Britisches Empire", 35479, "inkl. Indien (1.358) und Neufundland (49)", T.w("bilanz", 26.1)),
            (["fr"], "Frankreich", 9798, None, T.w("bilanz", 31.1)),
            (["au"], "Australien", 8709, None, T.w("bilanz", 33.3)),
            (["nz"], "Neuseeland", 2721, None, T.w("bilanz", 36.0))]
    T.add(BilanzPanel(T.w("bilanz", 14.8), T.end("bilanz") + 3.0, rows, head="Gefallene"))
    T.wait(1.6)

    s = T.say("erbe", pre=0.6)
    T.say("gedenken", pre=1.0, post=2.0)
    T.mood(s - 0.6, "legacy2")
    T.cam(s - 0.6, Cam(40.245, 26.300, 8, 55, 60))
    T.cam(T.end("erbe") + 1, Cam(40.247, 26.296, 6.5, 55, 105), "linear")
    T.add(Caption([(["gb"], "Churchill verliert im Mai 1915 die Admiralität")], T.w("erbe", 3.8), T.w("erbe", 8.2), pos="br", width=620))
    T.add(Caption([(["au", "nz"], "25. April: Anzac Day")], T.w("erbe", 8.3), T.w("erbe", 15.6), pos="br", width=440))
    T.add(Caption([(["tr"], "29. Oktober 1923: Mustafa Kemal"), (None, "gründet die Republik Türkei")], T.w("erbe", 26.2), T.end("erbe") + 1.0,
                  pos="br", width=520, title="Atatürk"))
    T.add(Label(*P["ariburnu"], "Arıburnu", t0=T.w("erbe", 20.5), t1=T.end("gedenken"), size=24, dx=-14, align="right"))
    T.add(Label(*P["chunuk"], "Conkbayırı", t0=T.w("erbe", 22.0), t1=T.end("gedenken"), size=24))

    s = T.vstart["gedenken"]
    T.cam(s - 1.0, Cam(40.247, 26.296, 6.5, 55, 105))
    T.cam(T.end("gedenken") + 2, Cam(40.244, 26.286, 4.0, 58, 140), "linear")
    T.add(Label(40.2448, 26.2795, "Gedenkstein Arıburnu", t0=T.w("gedenken", 6.0), t1=T.w("gedenken", 12.0), size=24, dx=-14, align="right"))
    T.add(Quote(["Ihr Helden, die ihr euer Blut vergossen", "und euer Leben gelassen habt,", "ihr ruht nun in der Erde eines befreundeten Landes.",
                 "Für uns gibt es keinen Unterschied zwischen den Johnnies", "und den Mehmets, die hier Seite an Seite liegen."],
                "ATATÜRK ZUGESCHRIEBEN · 1934", T.w("gedenken", 12.0), T.end("gedenken") + 2.5, size=40))
    t = T.t
    T.add(Credits(t, t + 24.0, [
        "Sprecher: KI-Stimme (ElevenLabs v4 über Higgsfield)  ·  Musik: eigene Komposition",
        "Satellitenbilder: enthält modifizierte Copernicus-Sentinel-2-Daten (2024)",
        "Höhendaten: AWS Terrain Tiles (SRTM, GMTED, ETOPO1)  ·  Grenzen 1914: historical-basemaps (A. Ourednik)",
        "Flaggen: flag-icons (MIT)  ·  Schriften: Cinzel, Barlow (SIL OFL)",
        "Zahlen gerundet; die Angaben in der Literatur weichen teils deutlich voneinander ab.",
    ]))
    T.wait(24.0)
    add_battles(T)
    T.finalize()
    return T


if __name__ == "__main__":
    tl = build()
    print("Dauer:", round(tl.duration, 1), "s =", f"{int(tl.duration // 60)}:{int(tl.duration % 60):02d}")
    print("Objekte:", len(tl.objects))
    for k, v in tl.vstart.items():
        print(f"  {k:16s} {v:7.1f}")
