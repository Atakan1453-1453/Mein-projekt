"""Drehbuch als Zeitleiste: Kamerafahrten, Frontverläufe, Flaggen-Zähler, Figuren-Schlachten und Einblendungen.

Zeiten wie T.w("caures", 22.9) beziehen sich auf die Wortzeit in der jeweiligen Sprachaufnahme (Spracherkennung).
Truppenstärken und Verluste sind gerundete Werte aus der Literatur; wo die Stärke unsicher ist, steht „ca.“ (siehe README).
"""
import json
import math
import os

import skia

import engine as E
import vgeo as G
from engine import (Arrow, Area, Barrage, Battle, BattleMarker, BilanzPanel, Bird, Cam, Caption, ChapterCard, Convoy,
                    CraterField, Credits, DateStamp, Explosion, Fire, FrontMap, GasCloud, Guns, Label, LossBadge, MeasureLine,
                    Polyline, Pulse, Quote, ShellArcs, Snow, Tint, TitleCard, Token, VFort, TerritoryFlags, Burning, Rain, BigWord,
                    FrontPulse)
from narration import SEGMENTS

HERE = os.path.dirname(os.path.abspath(__file__))
P = G.P
DE, FR = "de_1871", "fr"          # Flaggen: Deutsches Kaiserreich (Schwarz-Weiß-Rot), Frankreich
RED, BLUE = E.TR_RED, E.AL_BLUE


class Timeline:
    def __init__(self):
        dur = json.load(open(os.path.join(HERE, "voice_durations.json")))
        self.vdur = {k: d for (k, _), d in zip(SEGMENTS, dur)}
        self.vstart = {}
        self.t = 0.0
        self.objects = []
        self.cam_keys = []
        self.dim_keys = [(0.0, 0.0)]
        self.marks = []
        self.music = []
        self.duration = 0.0
        self._campath = None

    def say(self, key, pre=0.0, post=1.4):
        self.t += pre
        self.vstart[key] = self.t
        self.marks.append((self.t, self.vdur[key], key))
        self.t += self.vdur[key] + post
        return self.vstart[key]

    def w(self, key, sec):
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

    def finalize(self):
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

    def cam(self, t, cam=None, kind="ease"):
        if cam is None:
            return self._campath.at(t)
        self.cam_keys.append((t, cam, kind))

    def dim(self, t, value=None):
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


def countries_layer(t0, t1, central_on, entente_on, ottoman_on, bulgaria_on):
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


def borders_layer(t0, t1):
    """Nur Ländergrenzen 1914 (ohne Flaggen) für die Westfront-Karten."""
    paths = E.load_countries()
    base = E.hexc("#8a8a80", 0.05)
    return E.FlagCountries([dict(path=p, base=base, t_on=t0) for p in paths.values()], t0, t1)


def bearing(a, b):
    dy = b[0] - a[0]
    dx = (b[1] - a[1]) * math.cos(math.radians(a[0]))
    return math.degrees(math.atan2(dx, dy)) % 360


def front_line(key):
    import numpy as np
    return np.concatenate([np.array(G.WEST), E.resample(G.FRONTS[key], 240), np.array(G.SOUTH)])


def anchor_on(line, pos, side, dist_km):
    """Punkt hinter der Front: nächster Frontpunkt zu pos, um dist_km zur eigenen Seite versetzt."""
    import numpy as np
    la, lo = pos
    k = math.cos(math.radians(la))
    d2 = (line[:, 0] - la) ** 2 + ((line[:, 1] - lo) * k) ** 2
    i = int(np.argmin(d2))
    j0, j1 = max(0, i - 3), min(len(line) - 1, i + 3)
    ty, tx = line[j1, 0] - line[j0, 0], (line[j1, 1] - line[j0, 1]) * k
    L = math.hypot(ty, tx) or 1.0
    ny, nx = -tx / L, ty / L
    d = dist_km / 111.0
    ger = np.concatenate([line, np.array(G.GER_CLOSE)])
    for sgn in (1, -1):
        cand = (line[i, 0] + sgn * ny * d, line[i, 1] + sgn * nx * d / k)
        inside = bool(E.inside_poly(ger, np.array([cand]))[0])
        if inside == (side == "de"):
            return cand
    return (float(la), float(lo))


def anchor_pos(key, pos, side, dist_km):
    return anchor_on(front_line(key), pos, side, dist_km)


def dist_to_line_km(line, pos):
    import numpy as np
    la, lo = pos
    k = math.cos(math.radians(la))
    return float(np.sqrt(((line[:, 0] - la) ** 2 + ((line[:, 1] - lo) * k) ** 2).min()) * 111.0)


def follow_front(units, front):
    """Verbände bleiben nach ihrer letzten Bewegung stehen und rücken mit jeder Frontverschiebung mit."""
    import numpy as np
    for u in units:
        if not getattr(u, "persist", False):
            continue
        last = u.keys[-1][0]
        pos = (u.keys[-1][1], u.keys[-1][2])
        line0, _ = front.line_at(last + 0.01)
        dist = min(1.6, max(0.35, dist_to_line_km(line0, pos)))
        for ta, tb, mid in front.states[1:]:
            if ta <= last + 0.05 or ta >= u.t1:
                continue
            line = np.concatenate([front.west, mid, front.south])
            new = anchor_on(line, pos, u.side, dist)
            if math.hypot(new[0] - pos[0], (new[1] - pos[1]) * 0.65) * 111.0 > 0.04:
                u.keys.append((ta, pos[0], pos[1]))
                u.keys.append((tb, new[0], new[1]))
                pos = new
        u.keys.sort()


def shift(pts, dlat=0.0, dlon=0.0):
    return [(la + dlat, lo + dlon) for la, lo in pts]


def grid(lat0, lat1, lon0, lon1, n, seed=0, jitter=0.35):
    import numpy as np
    rng = np.random.default_rng(seed)
    k = int(math.sqrt(n * (lon1 - lon0) / max(1e-6, (lat1 - lat0)) / 1.5)) + 1
    m = max(1, n // k)
    out = []
    for i in range(m):
        for j in range(k):
            la = lat0 + (lat1 - lat0) * (i + 0.5 + rng.uniform(-jitter, jitter)) / m
            lo = lon0 + (lon1 - lon0) * (j + 0.5 + rng.uniform(-jitter, jitter)) / k
            out.append((la, lo))
    return out[:n]


# ======================================================================= Aufbau
def build():
    T = Timeline()
    U = E.Unit
    w = T.w

    ALL_UNITS, ALL_ENEM = [], []

    def troops(units, t0, t1, enemies):
        base = len(ALL_UNITS)
        for u in units:
            if not getattr(u, "no_persist", False):
                u.persist = True
            else:
                u.t1 = min(u.t1, t1)
            ALL_UNITS.append(u)
        ALL_ENEM.extend((base + i, base + j) for i, j in enemies)

    # Frontverlauf (Linie erscheint ab dem Frontbogen; Flaggen-Gebiete nutzen ihn schon vorher)
    front = T.add(FrontMap([(0, 0, G.FRONTS["feb21"])], G.WEST, G.SOUTH, G.GER_CLOSE, G.FR_CLOSE, 1e9, 1e9))

    # ------------------------------------------------------------ 0 · Luftaufnahme & Titel
    T.mood(0, "intro")
    T.cam(0.0, Cam(48.98, 5.33, 70, 56, 8))
    s = T.say("intro", pre=7.0, post=1.0)
    T.add(Label(*P["verdun"], "Verdun", t0=w("intro", 0.1), t1=w("intro", 9.0), size=34))
    T.add(Label(49.205, 5.345, "MAAS", t0=w("intro", 1.0), t1=w("intro", 8.0), size=26, style="sea", dot=False))
    T.cam(w("intro", 3.0), Cam(49.12, 5.38, 26, 54, 10))
    T.cam(w("intro", 8.0), Cam(49.20, 5.41, 13, 56, 18))
    # „zerrissene Landschaft“ 9.4 / „Trichter an Trichter“ 11.1 → kurz die Trichterwüste
    T.add(CraterField([(G.ZONES["douaumont"], w("intro", 9.6), w("intro", 12.5))], w("intro", 9.6), w("intro", 17.5), strength=0.45))
    T.cam(w("intro", 12.5), Cam(49.218, 5.432, 6.5, 58, 24))
    T.add(Label(*P["douaumont"], "Fort Douaumont", t0=w("intro", 12.0), t1=w("intro", 17.0), size=24))
    T.cam(w("intro", 19.0), Cam(49.19, 5.40, 32, 50, 12))
    T.add(Label(49.29, 5.40, "DEUTSCHE", t0=w("intro", 18.8), t1=w("intro", 25.0), size=30, style="sea", dot=False, color=RED))
    T.add(Label(49.11, 5.38, "FRANZOSEN", t0=w("intro", 19.4), t1=w("intro", 25.0), size=30, style="sea", dot=False))
    T.cam(T.end("intro") + 9, Cam(49.15, 5.39, 55, 48, 0), "linear")
    T.add(TitleCard(T.end("intro") + 0.4, 8.5, title="VERDUN", year="1916", sub="DIE HÖLLE AN DER MAAS"))
    T.wait(8.5)

    # ------------------------------------------------------------ Kapitel 1 · Weltkrieg
    t = T.t
    T.mood(t, "world")
    T.add(ChapterCard(1, "Ein Krieg erfasst die Welt", "1914 – 1915", t, 5.0))
    T.cam(t + 6.5, Cam(48.5, 16.0, 4300, 0, 0))
    T.wait(5.5)
    s = T.say("europa", pre=0.4, post=2.0)
    T.say("westfront", pre=0.5, post=2.0)
    T.say("falkenhayn", pre=0.6, post=2.0)
    flags_obj = T.add(TerritoryFlags([], s - 1.5, 1e9, front=front, wf_n=G.WF_N, wf_s=G.WF_S))
    T.add(Label(52.5, 13.4, "Deutsches Reich", t0=w("europa", 8.2), t1=w("europa", 22.0), style="country", size=30))
    T.add(Label(47.6, 18.0, "Österreich-Ungarn", t0=w("europa", 9.7), t1=w("europa", 22.0), style="country", size=28))
    T.add(Label(38.8, 33.5, "Osmanisches Reich", t0=w("europa", 12.1), t1=w("europa", 22.0), style="country", size=28))
    T.add(Label(42.7, 25.3, "Bulgarien", t0=w("europa", 13.5), t1=w("europa", 22.0), style="country", size=22))
    T.add(Label(46.6, 2.4, "Frankreich", t0=w("europa", 17.2), t1=w("europa", 22.0), style="country", size=28))
    T.add(Label(52.3, -1.4, "Großbritannien", t0=w("europa", 18.2), t1=w("europa", 22.0), style="country", size=26))
    T.add(Label(55.5, 38.0, "Russisches Reich", t0=w("europa", 19.8), t1=w("europa", 22.0), style="country", size=32))
    T.add(Caption([([DE], "Mittelmächte: Deutsches Reich, Österreich-Ungarn"), (["tr", "bg"], "später: Osmanisches Reich, Bulgarien"),
                   ([FR, "gb"], "Entente: Frankreich, Großbritannien, Russland")],
                  w("europa", 6.6), w("europa", 21.5), pos="br", width=680, title="Europa 1914"))
    # „schnellen Sieg im Westen“ 24.2 → Blick nach Westen, Vormarsch durch Belgien
    T.cam(w("europa", 22.5), Cam(49.9, 4.6, 1150, 0, 0))
    T.add(Arrow([(50.77, 6.10), (50.63, 5.57), (50.85, 4.35), (50.30, 3.20), (49.25, 2.70)], "de", t0=w("europa", 26.4), grow=3.0,
                t1=T.end("europa") + 4.0, width=13))
    T.add(Arrow([(49.75, 6.05), (49.70, 4.90), (49.30, 3.90), (48.98, 3.30)], "de", t0=w("europa", 26.9), grow=2.8,
                t1=T.end("europa") + 4.0, width=11))
    T.add(Label(*P["liege"], "Lüttich", t0=w("europa", 26.6), t1=T.end("europa") + 3.0, size=20))
    T.add(Label(*P["paris"], "Paris", t0=w("europa", 29.4), t1=T.end("westfront") + 1.0, size=26))
    T.add(Label(50.75, 4.0, "BELGIEN", t0=w("europa", 27.2), t1=T.end("europa") + 3.0, size=22, style="sea", dot=False))

    s = T.vstart["westfront"]
    T.cam(s + 0.2, Cam(49.2, 3.6, 760, 0, 0))
    T.add(Label(48.95, 3.55, "Marne", "September 1914", t0=w("westfront", 0.4), t1=w("westfront", 7.0), size=26))
    T.add(Battle(48.95, 3.30, 25, w("westfront", 0.6), w("westfront", 5.5), rate=6, intensity=0.9))
    T.add(Arrow([(48.90, 3.20), (49.15, 3.25), (49.40, 3.30)], "al", t0=w("westfront", 2.6), grow=2.0, t1=w("westfront", 7.0), width=10))
    # „durchgehende Linie“ 7.6 → Westfront wächst von der Nordsee (10.4) bis zur Schweiz (13.5)
    T.cam(w("westfront", 6.0), Cam(49.4, 4.6, 1000, 0, 0))
    T.add(Polyline(G.WESTERN_FRONT, E.hexc("#ff5a4a"), t0=w("westfront", 9.6), t1=T.end("falkenhayn") + 2.0, width=5, grow=4.6, glow=True))
    T.add(Label(51.25, 2.45, "Nordsee", t0=w("westfront", 10.4), t1=w("westfront", 16.0), size=22, style="sea", dot=False))
    T.add(Label(47.30, 7.70, "Schweiz", t0=w("westfront", 13.3), t1=w("westfront", 16.0), size=22))
    T.add(Label(50.15, 4.65, "WESTFRONT", t0=w("westfront", 14.6), t1=T.end("westfront") + 1.0, size=26, style="sea", dot=False, color=E.hexc("#ffb0a0")))
    T.add(Caption([([DE], "deutsch besetzt: Belgien und Nordfrankreich")], w("westfront", 11.0), w("westfront", 16.2), pos="br", width=560))
    # 1915: Offensiven im Artois und in der Champagne
    for pts in ([(50.25, 2.45), (50.38, 2.72)], [(49.08, 4.45), (49.20, 4.55)], [(50.47, 2.55), (50.52, 2.75)], [(49.10, 4.70), (49.21, 4.75)]):
        T.add(Arrow(pts, "al", t0=w("westfront", 17.4), grow=1.6, t1=w("westfront", 24.5), width=10))
    T.add(Battle(50.36, 2.75, 18, w("westfront", 18.0), w("westfront", 24.5), rate=5, intensity=0.8))
    T.add(Battle(49.18, 4.55, 18, w("westfront", 18.2), w("westfront", 24.5), rate=5, intensity=0.8, seed=4))
    T.add(Caption([([FR, "gb"], "1915: Angriffe im Artois und in der Champagne"), (None, "kaum Geländegewinne, sehr hohe Verluste")],
                  w("westfront", 17.6), T.end("westfront") + 0.8, pos="br", width=620, title="Stellungskrieg"))

    s = T.vstart["falkenhayn"]
    T.cam(s - 0.3, Cam(49.4, 4.6, 1000, 0, 0))
    T.add(Caption([([DE], "Erich von Falkenhayn"), (None, "Chef des deutschen Generalstabs")], w("falkenhayn", 2.4), w("falkenhayn", 11.0),
                  pos="br", width=520, title="Ende 1915"))
    T.cam(w("falkenhayn", 8.5), Cam(49.3, 4.9, 520, 0, 0))
    T.add(Caption([(None, "„Weihnachtsdenkschrift“ (Dezember 1915)"), (None, "nur aus Falkenhayns Erinnerungen bekannt,"),
                   (None, "ein Original wurde nie gefunden")], w("falkenhayn", 16.0), w("falkenhayn", 25.0), pos="br", width=560))
    T.add(Pulse(*P["verdun"], w("falkenhayn", 25.6), T.end("falkenhayn") + 3.0, r=40))
    T.cam(w("falkenhayn", 26.4), Cam(49.17, 5.38, 210, 15, 0))
    T.add(Label(*P["verdun"], "VERDUN", t0=w("falkenhayn", 27.5), t1=T.end("falkenhayn") + 3.0, size=40, dx=18))

    # ------------------------------------------------------------ Kapitel 2 · Festung Verdun
    t = T.t
    T.mood(t, "fortress")
    T.add(ChapterCard(2, "Die Festung Verdun", "Ende 1915 – Februar 1916", t + 0.3, 5.0))
    T.cam(t + 6.0, Cam(49.13, 5.40, 34, 42, 0))
    T.wait(5.6)
    s = T.say("festung", pre=0.3, post=2.0)
    T.say("frontbogen", pre=0.4, post=2.0)
    T.say("gericht", pre=0.5, post=3.0)
    # Forts erscheinen nacheinander („Ring aus 19 großen Forts“ 3.7)
    fort_end = 1e9
    forts = {}
    order = sorted(G.FORTS, key=lambda f: math.atan2(f[1] - P["verdun"][0], (f[2] - P["verdun"][1]) * 0.65))
    for i, (name, la, lo, big) in enumerate(order):
        owners = [(0.0, "fr")]
        forts[name] = T.add(VFort(la, lo, name if big else None, owners, t0=w("festung", 3.6) + i * 0.16, t1=fort_end,
                                  size=1.0 if big else 0.62, label=big, max_width=140))
    T.add(Label(*P["verdun"], "Verdun", t0=s, t1=T.end("frontbogen"), size=30))
    T.cam(w("festung", 8.6), Cam(49.20, 5.43, 15, 50, 8))
    T.add(Pulse(*P["douaumont"], w("festung", 10.9), w("festung", 16.0), color=E.GOLD, r=26))
    T.add(Caption([(None, "Fort Douaumont: das größte und stärkste Fort"), (None, "Stahlbeton, Panzertürme, auf 388 m Höhe")],
                  w("festung", 11.0), w("festung", 17.0), pos="br", width=600))
    T.cam(w("festung", 16.5), Cam(50.0, 5.0, 330, 0, 0))
    T.add(Label(50.75, 4.45, "BELGIEN", t0=w("festung", 18.0), t1=w("festung", 26.0), size=24, style="sea", dot=False))
    T.add(Label(*P["liege"], "Lüttich", t0=w("festung", 21.8), t1=w("festung", 26.0), size=24))
    T.add(Label(*P["namur"], "Namur", t0=w("festung", 22.6), t1=w("festung", 26.0), size=24))
    T.add(Explosion(*P["liege"], w("festung", 22.0), 0.7))
    T.add(Explosion(*P["namur"], w("festung", 22.8), 0.7))
    T.cam(w("festung", 25.2), Cam(49.16, 5.40, 30, 45, 0))
    T.add(Caption([([FR], "1915: Geschütze und Besatzungen werden"), (None, "aus den Forts von Verdun abgezogen")],
                  w("festung", 26.0), T.end("festung") + 1.2, pos="br", width=560))
    for name, la, lo, big in G.FORTS:
        T.add(Arrow([(la, lo), (la - 0.03, lo - 0.05)], "al", t0=w("festung", 28.4), grow=1.4, t1=T.end("festung") + 0.8, width=4, dashed=True))

    s = T.vstart["frontbogen"]
    T.cam(s - 0.3, Cam(49.02, 5.42, 95, 30, 0))
    front.t0, front.t1 = s + 0.5, 1e9
    T.add(Label(49.10, 5.47, "Frontbogen von Verdun", t0=w("frontbogen", 1.2), t1=w("frontbogen", 10.0), size=26, dot=False, align="center", dx=0))
    T.add(Caption([([DE], "rot: deutsch besetzt"), ([FR], "blau: französisch")], w("frontbogen", 5.3), w("frontbogen", 14.5), pos="br", width=380))
    rail_sm = [(49.160, 5.384), (49.120, 5.410), (49.060, 5.460), (48.990, 5.505), (48.890, 5.545), (48.770, 5.590)]
    rail_cm = [(49.160, 5.384), (49.150, 5.300), (49.140, 5.170), (49.125, 5.080), (49.093, 4.900)]
    T.add(Polyline(rail_sm, E.hexc("#e8e4d8"), t0=w("frontbogen", 10.4), t1=w("frontbogen", 22.0), width=3, grow=1.2, dash=(10, 6)))
    T.add(Polyline(rail_cm, E.hexc("#e8e4d8"), t0=w("frontbogen", 10.6), t1=w("frontbogen", 22.0), width=3, grow=1.2, dash=(10, 6)))
    T.add(Label(48.89, 5.545, "Saint-Mihiel", "Bahn unterbrochen", t0=w("frontbogen", 12.2), t1=w("frontbogen", 22.0), size=22, color=E.hexc("#ffb0a0")))
    T.add(Label(49.13, 5.09, "unter Beschuss", t0=w("frontbogen", 13.8), t1=w("frontbogen", 22.0), size=22, dx=-12, align="right", color=E.hexc("#ffb0a0")))
    T.add(Battle(49.13, 5.09, 2.5, w("frontbogen", 13.6), w("frontbogen", 21.0), rate=3, intensity=0.8))
    road = T.add(Polyline(G.VOIE_SACREE, E.GOLD, t0=w("frontbogen", 17.2), t1=1e9, width=4.5, grow=2.0, glow=True))
    T.add(Label(*P["barleduc"], "Bar-le-Duc", t0=w("frontbogen", 17.4), t1=w("frontbogen", 26.0), size=22))
    T.add(Label(48.93, 5.25, "Landstraße", "und Kleinbahn", t0=w("frontbogen", 17.8), t1=w("frontbogen", 26.0), size=22, dx=14, color=E.GOLD))

    s = T.vstart["gericht"]
    T.add(DateStamp("Januar 1916", "Unternehmen Gericht", s, w("gericht", 22.0)))
    T.cam(s - 0.2, Cam(49.30, 5.42, 46, 50, 188))
    gpts = grid(49.312, 49.370, 5.22, 5.62, 110, seed=2) + grid(49.15, 49.26, 5.61, 5.70, 30, seed=3)
    guns_de = T.add(Guns(gpts, "de", w("gericht", 9.4), 1e9, facing=200))
    T.add(Token(49.345, 5.42, [DE], [(0, 1220)], label="Geschütze", side="de", t0=w("gericht", 9.8), t1=w("gericht", 21.0), dy=-80,
                note="darunter 42-cm-Mörser"))
    T.add(Caption([(None, "1 Symbol = rund 10 Geschütze")], w("gericht", 10.5), w("gericht", 18.0), pos="bl", width=380))
    T.cam(w("gericht", 16.0), Cam(49.27, 5.41, 30, 48, 185))
    tok_de = T.add(Token(49.325, 5.40, [DE], [(0, 140000)], label="5. Armee · 9 Divisionen", side="de", t0=w("gericht", 17.5),
                         t1=1e9, dy=-80, note="ca."))
    tok_fr = T.add(Token(49.250, 5.40, [FR], [(0, 34000)], label="Französische Verteidiger", side="fr", t0=w("gericht", 30.6),
                         t1=1e9, dy=70, note="ca."))
    T.add(Snow(w("gericht", 24.6), w("gericht", 31.0), n=380))
    T.add(DateStamp("12. bis 21. Februar", "Angriff verschoben", w("gericht", 22.6), T.end("gericht") + 1.0, sub="Regen, Schnee und Nebel"))

    # ------------------------------------------------------------ Kapitel 3 · 21. Februar 1916
    t = T.t
    T.mood(t, "barrage")
    T.add(ChapterCard(3, "21. Februar 1916", "Das Trommelfeuer", t + 0.2, 5.0))
    T.cam(t, Cam(49.27, 5.41, 30, 48, 185))
    T.cam(t + 5.6, Cam(49.22, 5.40, 32, 52, 5))
    T.wait(5.4)
    s = T.say("trommelfeuer", pre=0.2, post=5.0)
    T.say("caures", pre=0.3, post=3.5)
    T.say("vormarsch", pre=0.3, post=3.0)
    T.say("douaumont", pre=0.5, post=3.0)
    guns_de.t1 = tok_de.t1 = tok_fr.t1 = T.end("vormarsch") + 1.0
    T.add(DateStamp("21. Februar 1916", "Unternehmen Gericht beginnt", s, T.end("trommelfeuer")))
    guns_de.fire = [(w("trommelfeuer", 3.8), T.end("vormarsch"))]
    fr_pos = [(49.310, 5.300), (49.312, 5.450), (49.290, 5.495), (49.240, 5.505), (49.238, 5.470), (49.262, 5.420),
              (49.266, 5.360), (49.272, 5.320)]
    T.add(Barrage(fr_pos, w("trommelfeuer", 3.8), T.end("vormarsch") - 2.0, rate=60, seed=1, size=0.9))
    T.add(Barrage([(49.250, 5.15), (49.270, 5.27), (49.240, 5.28), (49.225, 5.16)], w("trommelfeuer", 4.5), T.end("vormarsch") - 4.0,
                  rate=12, seed=2, size=0.8))
    T.add(Barrage([(49.24, 5.50), (49.24, 5.60), (49.11, 5.62), (49.12, 5.55)], w("trommelfeuer", 5.0), T.end("trommelfeuer") + 1.0,
                  rate=10, seed=3, size=0.8))
    T.add(MeasureLine((49.215, 5.14), (49.215, 5.64), "ca. 40 km Front", w("trommelfeuer", 7.4), w("trommelfeuer", 12.5)))
    T.add(Caption([([DE], "Am ersten Tag: rund 1 Million Granaten")], w("trommelfeuer", 18.0), T.end("trommelfeuer") + 1.0, pos="br", width=520))
    T.cam(w("trommelfeuer", 12.5), Cam(49.27, 5.39, 16, 55, 0))
    # Stoßtrupps (Figuren: 1 Figur = 1 Soldat)
    de_start = [(49.318, 5.310), (49.322, 5.345), (49.318, 5.378), (49.320, 5.410), (49.312, 5.445), (49.292, 5.480)]
    fr_hold = [(49.282, 5.320), (49.290, 5.350), (49.287, 5.420), (49.276, 5.445), (49.262, 5.478)]
    de_mid = [(49.300, 5.312), (49.304, 5.345), (49.302, 5.380), (49.304, 5.412), (49.292, 5.448), (49.272, 5.488)]
    k = "trommelfeuer"
    vm = T.vstart["vormarsch"]
    units = [U("de", 8000, [(w(k, 23.0), *a), (w(k, 26.0) + 6.0, *b), (vm, *b), (w("vormarsch", 9.0), *anchor_pos("feb24", b, "de", 0.5))],
               facing=180, area=60, aspect=4.0, fire=[(w(k, 25.0), w("vormarsch", 16.0))], losses=[(w("vormarsch", 10.0), 2600)],
               seed=10 + i) for i, (a, b) in enumerate(zip(de_start, de_mid))]
    units += [U("fr", 6000, [(w(k, 0.0), *a), (w("vormarsch", 4.0), *a), (w("vormarsch", 9.0), *anchor_pos("feb24", a, "fr", 0.6))],
                facing=0, area=60, aspect=4.0, fire=[(w(k, 25.0), w("vormarsch", 13.0))], seed=20 + i,
                losses=[(w(k, 10.0), 900), (w("vormarsch", 9.6), 2700)]) for i, a in enumerate(fr_hold)]
    troops(units, w(k, 0.0), T.end(k) + 2.2, [(0, 6), (1, 7), (2, 8), (3, 8), (4, 9), (5, 10)])
    T.add(Burning(fr_pos, w(k, 5.0), T.end("vormarsch") + 30.0, n=70, ramp=24.0, seed=41))

    # ---------------- Bois des Caures
    s = T.vstart["caures"]
    k = "caures"
    T.add(DateStamp("21. – 22. Februar 1916", "Bois des Caures", s, T.end(k)))
    T.cam(s - 0.3, Cam(49.283, 5.387, 6.5, 55, 2))
    T.add(Label(49.2735, 5.3880, "Bois des Caures", t0=s, t1=T.end(k) + 1, size=26, dot=False, dx=0, dy=60, align="center"))
    T.add(Caption([([FR], "Oberstleutnant Émile Driant"), (None, "56. und 59. Jägerbataillon")], w(k, 6.4), w(k, 13.0), pos="br", width=480))
    T.add(Barrage([(49.292, 5.372), (49.292, 5.404), (49.276, 5.404), (49.276, 5.372)], s, w(k, 13.0), rate=30, seed=5, size=0.8))
    T.add(Burning([(49.292, 5.372), (49.292, 5.404), (49.276, 5.404), (49.276, 5.372)], s + 0.5, T.end(k) + 25.0, n=22, ramp=8.0, seed=45))
    T.add(CraterField([(G.ZONES["nord"], w("trommelfeuer", 6.0), T.end("vormarsch")), (G.ZONES["douaumont"], w("vormarsch", 2.0), w("vormarsch", 2.0) + 180.0)],
                      w("trommelfeuer", 5.0), 1e9))
    units = [
        U("fr", 1200, [(s, 49.2875, 5.3880), (w(k, 24.0), 49.2875, 5.3880), (w(k, 28.0), 49.2780, 5.3900)], facing=0, area=40, aspect=4.5,
          losses=[(w(k, 15.6), 300), (w(k, 21.0), 400), (w(k, 22.8), 382)], fire=[(w(k, 13.0), w(k, 24.0))], t1=T.end(k) + 1.5, seed=31),
        U("de", 4000, [(w(k, 12.6), 49.3020, 5.3790), (w(k, 20.0), 49.2925, 5.3820)], facing=175, area=40, aspect=4.0,
          losses=[(w(k, 16.0), 700)], fire=[(w(k, 14.8), w(k, 24.0))], t1=T.end(k) + 1.5, seed=32),
        U("de", 4000, [(w(k, 12.9), 49.3000, 5.4000), (w(k, 20.5), 49.2915, 5.3975)], facing=185, area=40, aspect=4.0,
          losses=[(w(k, 16.4), 600)], fire=[(w(k, 14.8), w(k, 24.0))], t1=T.end(k) + 1.5, seed=33),
    ]
    troops(units, s, T.end(k) + 1.6, [(0, 1), (0, 2)])
    T.add(Token(49.2850, 5.3880, [FR], [(0, 1200), (w(k, 25.0), 118)], label="Jäger von Driant", side="fr", t0=w(k, 3.6), t1=T.end(k) + 1.0,
                dx=-150, dy=40))
    T.add(Label(49.2862, 5.3905, "† Driant", t0=w(k, 22.8), t1=T.end(k) + 1.0, size=22, color=E.hexc("#ffd0c8")))

    # ---------------- Vormarsch bis 25. Februar
    s = T.vstart["vormarsch"]
    k = "vormarsch"
    front.states.append((w(k, 2.6), w(k, 10.0), E.resample(G.FRONTS["feb24"], 240)))
    front.states.append((w(k, 16.6), w(k, 22.0), E.resample(G.FRONTS["feb25"], 240)))
    T.cam(s - 0.4, Cam(49.24, 5.42, 26, 50, 0))
    T.add(DateStamp("22. – 25. Februar 1916", "Rechtes Maasufer", s, T.end(k)))
    for name, tw in (("haumont", 3.4), ("samogneux", 4.8), ("beaumont", 5.9)):
        T.add(Label(*P[name], name.capitalize(), "erobert", t0=w(k, tw), t1=T.end(k) + 0.5, size=22, color=E.hexc("#ffb8a8")))
    T.add(Barrage([(49.262, 5.330), (49.262, 5.490), (49.240, 5.500), (49.240, 5.340)], s, w(k, 12.0), rate=30, seed=7, size=0.85))
    T.add(Burning([(49.262, 5.330), (49.262, 5.490), (49.240, 5.500), (49.240, 5.340)], s, T.end(k) + 30.0, n=35, ramp=10.0, seed=43))
    tok_de.keys.append((w(k, 10.4), 115000))
    tok_fr.keys.append((w(k, 11.1), 10000))
    tok_de.lat, tok_de.lon = 49.300, 5.40
    T.add(Caption([([FR], "bis 25. Februar: ca. 24.000 Mann verloren"), ([DE], "ca. 25.000 Mann verloren")], w(k, 11.0), w(k, 17.0),
                  pos="br", width=560, title="Verluste"))
    T.cam(w(k, 16.0), Cam(49.20, 5.52, 30, 45, 350))
    T.add(Label(49.20, 5.585, "Woëvre-Ebene", t0=w(k, 17.4), t1=T.end(k) + 0.5, size=24, dot=False, align="center", dx=0))
    for la in (49.24, 49.21, 49.18, 49.15):
        T.add(Arrow([(la, 5.59), (la - 0.004, 5.52)], "al", t0=w(k, 18.8), grow=1.8, t1=T.end(k) + 0.5, width=8))

    # ---------------- Fort Douaumont
    s = T.vstart["douaumont"]
    k = "douaumont"
    T.add(DateStamp("25. Februar 1916", "Fort Douaumont", s, T.end(k)))
    T.cam(s - 0.5, Cam(49.2185, 5.4395, 2.4, 56, 210))
    front.states.append((w(k, 23.0), w(k, 27.0), E.resample(G.FRONTS["feb26"], 240)))
    forts["Douaumont"].owners.append((w(k, 22.4), "de"))
    garrison = U("fr", 57, [(s, 49.2170, 5.4390)], facing=20, area=25, aspect=1.5, fire=[], t1=w(k, 22.8), seed=61)
    garrison.no_persist = True
    raid = U("de", 98, [(w(k, 11.4), 49.2235, 5.4480), (w(k, 17.2), 49.2185, 5.4405), (w(k, 21.0), 49.2172, 5.4392)], facing=210,
             area=18, aspect=2.0, t1=T.end(k) + 1.5, seed=62)
    troops([garrison, raid], s, T.end(k) + 1.5, [])
    T.add(Token(49.2165, 5.4385, [FR], [(0, 57), (w(k, 22.6), 0)], label="Besatzung", side="fr", t0=w(k, 7.4), t1=T.end(k) + 0.5,
                dx=150, dy=40, note="gefangen genommen" if False else None))
    T.add(Caption([([DE], "Brandenburgisches Infanterie-Regiment Nr. 24"), (None, "Fort genommen – ohne einen einzigen Schuss")],
                  w(k, 12.4), w(k, 24.6), pos="br", width=640))
    T.add(Caption([([DE], "In Deutschland: Siegesfeiern"), ([FR], "In Frankreich: Schock")], w(k, 25.0), T.end(k) + 1.2, pos="br", width=460))

    # ------------------------------------------------------------ Kapitel 4 · Pétain und die Voie Sacrée
    t = T.t
    T.mood(t, "prepare")
    T.add(ChapterCard(4, "Der heilige Weg", "Februar – März 1916", t + 0.2, 5.0))
    T.cam(t + 5.8, Cam(49.09, 5.34, 40, 40, 0))
    T.wait(5.4)
    s = T.say("petain", pre=0.2, post=2.0)
    T.say("voie_sacree", pre=0.4, post=3.5)
    T.say("noria", pre=0.4, post=2.5)
    road.t1 = T.end("voie_sacree") + 2
    k = "petain"
    T.add(Caption([([FR], "General Philippe Pétain"), (None, "Oberbefehl über die 2. Armee bei Verdun")], w(k, 1.4), w(k, 10.0),
                  pos="br", width=560, title="25. Februar 1916"))
    T.add(Label(*P["souilly"], "Souilly", "Hauptquartier Pétain", t0=w(k, 8.0), t1=T.end("voie_sacree") + 1.0, size=24))
    T.add(Pulse(*P["souilly"], w(k, 8.0), w(k, 14.0), color=BLUE, r=24))
    gfr = grid(49.17, 49.22, 5.18, 5.34, 30, seed=5) + grid(49.15, 49.19, 5.38, 5.48, 18, seed=6)
    guns_fr = T.add(Guns(gfr, "fr", w(k, 12.0), 1e9, facing=20))
    T.cam(w(k, 11.5), Cam(49.18, 5.36, 24, 48, 10))
    T.add(Caption([([FR], "neue Batterien, Stellungen, Nachschub")], w(k, 12.4), w(k, 21.0), pos="br", width=500))
    T.cam(w(k, 21.0), Cam(48.98, 5.27, 72, 38, 6))

    s = T.vstart["voie_sacree"]
    k = "voie_sacree"
    T.add(Label(*P["barleduc"], "Bar-le-Duc", t0=w(k, 0.2), t1=T.end(k) + 1.0, size=24))
    T.add(Label(*P["verdun"], "Verdun", t0=w(k, 2.8), t1=T.end(k) + 1.0, size=24))
    T.add(Convoy(G.VOIE_SACREE, w(k, 4.4), T.end("noria") + 1.0, spacing_km=0.55, speed_kmps=1.4))
    T.cam(w(k, 8.0), Cam(48.92, 5.245, 18, 52, 12))
    T.add(Caption([(None, "Zu Spitzenzeiten: alle 14 Sekunden ein Fahrzeug")], w(k, 9.2), w(k, 14.5), pos="br", width=560))
    T.add(Caption([([FR], "rund 13.000 Soldaten"), ([FR], "fast 8.000 t Material und Munition")], w(k, 13.4), w(k, 22.0), pos="br",
                  width=500, title="Pro Tag (Durchschnitt)"))
    T.cam(w(k, 20.0), Cam(49.00, 5.28, 60, 40, 8))
    T.add(Label(48.90, 5.235, "VOIE SACRÉE", "„Heiliger Weg“", t0=w(k, 29.2), t1=T.end("noria") + 1.0, size=30, dx=16, color=E.GOLD))

    s = T.vstart["noria"]
    k = "noria"
    T.cam(s - 0.2, Cam(49.08, 5.32, 50, 40, 6))
    for i in range(3):
        T.add(Arrow([(49.00 + i * 0.01, 5.262), (49.08 + i * 0.01, 5.302), (49.15, 5.36)], "al", t0=w(k, 4.0) + i * 0.6, grow=2.0,
                    t1=T.end(k) + 0.5, width=9))
        T.add(Arrow([(49.15, 5.40), (49.08 + i * 0.01, 5.35), (49.00 + i * 0.01, 5.31)], "al", t0=w(k, 6.0) + i * 0.6, grow=2.0,
                    t1=T.end(k) + 0.5, width=7, dashed=True, color=E.hexc("#8aa0c0")))
    T.add(Label(49.11, 5.25, "frische Truppen", t0=w(k, 7.4), t1=T.end(k), size=22, dot=False, align="right", dx=-10, color=E.hexc("#a8c8ff")))
    T.add(Label(49.10, 5.37, "abgelöste Truppen", t0=w(k, 7.8), t1=T.end(k), size=22, dot=False, dx=10, color=E.hexc("#c0c8d8")))
    T.add(Caption([([FR], "„Noria“ (Schöpfrad): ständige Ablösung"), ([FR], "bis Ende 1916: rund 3/4 der französischen Armee")],
                  w(k, 9.6), T.end(k) + 0.8, pos="br", width=620, title="Ablösung"))

    # ------------------------------------------------------------ Kapitel 5 · Hölle (März – Mai)
    t = T.t
    T.mood(t, "trench")
    T.add(ChapterCard(5, "Die Hölle von Verdun", "März – Mai 1916", t + 0.2, 5.0))
    T.cam(t + 6.0, Cam(49.215, 5.27, 16, 50, 330))
    T.wait(5.6)
    s = T.say("linkes_ufer", pre=0.2, post=4.0)
    T.say("hoelle", pre=0.3, post=3.5)
    T.say("mai", pre=0.5, post=3.0)
    guns_fr.t1 = T.end("linkes_ufer") + 1.0
    guns_fr.fire = [(w("petain", 12.6), T.end("linkes_ufer"))]
    k = "linkes_ufer"
    T.add(DateStamp("6. März – 29. Mai 1916", "Linkes Maasufer", s, T.end(k) + 1.0))
    for (la, lo) in gfr[:30:3]:
        T.add(Arrow([(la, lo), (la + 0.04, lo + 0.10)], "al", t0=w(k, 2.0), grow=1.6, t1=w(k, 7.0), width=5, dashed=True))
    front.states.append((w(k, 7.6), w(k, 21.0), E.resample(G.FRONTS["apr15"], 240)))
    front.states.append((w(k, 23.0), w(k, 27.6), E.resample(G.FRONTS["may31"], 240)))
    T.add(Label(*P["mort_homme"], "Toter Mann", "Höhe 295", t0=w(k, 13.2), t1=T.end("hoelle"), size=26))
    T.add(Label(*P["cote304"], "Höhe 304", t0=w(k, 14.7), t1=T.end("hoelle"), size=26, dx=-14, align="right"))
    T.add(CraterField([(G.ZONES["links"], w(k, 8.0), w("hoelle", 14.0))], w(k, 7.5), 1e9))
    T.add(Barrage([(49.250, 5.180), (49.252, 5.290), (49.218, 5.292), (49.212, 5.185)], w(k, 8.2), T.end(k) + 1.0, rate=34, seed=11, size=0.85))
    T.add(Burning([(49.250, 5.180), (49.252, 5.290), (49.218, 5.292), (49.212, 5.185)], w(k, 8.6), T.end(k) + 25.0, n=35, ramp=14.0, seed=55))
    units = [U("de", 10000, [(w(k, 8.0), 49.262, 5.205), (w(k, 21.0), 49.236, 5.207), (w(k, 25.5), 49.228, 5.208)], facing=180, area=55, aspect=4.0,
               losses=[(w(k, 18.8), 3200)], fire=[(w(k, 11.0), T.end(k))], t1=T.end(k) + 1.5, seed=71),
             U("de", 10000, [(w(k, 8.4), 49.262, 5.262), (w(k, 21.0), 49.243, 5.260), (w(k, 27.0), 49.236, 5.260)], facing=180, area=55, aspect=4.0,
               losses=[(w(k, 19.2), 3400)], fire=[(w(k, 11.0), T.end(k))], t1=T.end(k) + 1.5, seed=72),
             U("fr", 8000, [(w(k, 6.0), 49.232, 5.210), (w(k, 23.0), 49.232, 5.210), (w(k, 25.0), 49.217, 5.205)], facing=0, area=55, aspect=4.0,
               losses=[(w(k, 21.2), 3000)], fire=[(w(k, 11.0), T.end(k))], t1=T.end(k) + 1.5, seed=73),
             U("fr", 8000, [(w(k, 6.0), 49.238, 5.262), (w(k, 25.6), 49.238, 5.262), (w(k, 27.6), 49.224, 5.258)], facing=0, area=55, aspect=4.0,
               losses=[(w(k, 21.6), 3000)], fire=[(w(k, 11.0), T.end(k))], t1=T.end(k) + 1.5, seed=74)]
    troops(units, w(k, 6.0), T.end(k) + 1.6, [(0, 2), (1, 3)])
    T.cam(w(k, 16.0), Cam(49.232, 5.24, 11, 55, 340))

    s = T.vstart["hoelle"]
    k = "hoelle"
    cf_hoelle = T.add(CraterField([(G.ZONES["fleury"], w(k, 1.0), w(k, 12.0))], w(k, 0.5), 1e9))
    T.cam(s - 0.2, Cam(49.225, 5.33, 18, 56, 20))
    T.cam(w(k, 10.0), Cam(49.218, 5.405, 9, 58, 40))
    T.add(Tint(skia.Color4f(0.12, 0.10, 0.08, 0.18), w(k, 4.0), T.end(k) + 0.5))
    # „Wälder verschwinden“ 4.9: Waldbrände über dem ganzen Schlachtfeld
    T.add(Burning([(49.245, 5.37), (49.245, 5.49), (49.19, 5.49), (49.19, 5.38)], w(k, 4.6), T.end(k) + 20.0, n=48, ramp=8.0, seed=51))
    # „Dörfer zerfallen zu Staub“ 6.5
    for i, key in enumerate(("fleury", "douaumont_dorf", "vaux_dorf", "bezonvaux", "louvemont", "ornes")):
        T.add(Explosion(*P[key], w(k, 6.4) + i * 0.25, 0.55))
    # „Schlamm und Kälte“ 12.9
    T.add(Rain(w(k, 11.0), w(k, 18.8)))
    # „Hölle“ 24.5 · „Knochenmühle“ 25.4 · „Blutpumpe“ 26.7
    T.cam(w(k, 21.5), Cam(49.205, 5.428, 7.5, 58, 18))
    T.add(Barrage([(49.236, 5.380), (49.236, 5.480), (49.200, 5.490), (49.198, 5.385)], w(k, 23.6), T.end(k) + 3.2, rate=45, seed=53, size=0.9))
    T.add(BigWord("DIE HÖLLE", w(k, 24.3), T.end(k) + 3.3, y=0.30, color=E.hexc("#ff9a3c"), size=82))
    T.add(BigWord("DIE KNOCHENMÜHLE", w(k, 25.3), T.end(k) + 3.3, y=0.43, color=E.hexc("#efe6d6"), size=82))
    T.add(BigWord("DIE BLUTPUMPE", w(k, 26.6), T.end(k) + 3.3, y=0.56, color=E.hexc("#ff3b30"), size=82))
    T.add(FrontPulse(front, w(k, 26.4), T.end(k) + 3.4))
    T.add(Tint(skia.Color4f(0.35, 0.0, 0.0, 0.16), w(k, 26.6), T.end(k) + 3.4, fin=0.8, fout=1.2))
    mill = []
    for wave in range(4):
        for j, lo in enumerate((5.388, 5.408, 5.428, 5.448, 5.468)):
            t_go = w(k, 18.6) + wave * 2.1 + j * 0.15
            for side, rear, close, face in (("de", 2.6, 0.25, 185), ("fr", 2.6, 0.25, 5)):
                base = anchor_pos("may31", (49.215, lo), side, close)
                start = anchor_pos("may31", (49.215, lo), side, rear)
                mill.append(U(side, 600, [(t_go, *start), (t_go + 2.8, *base)], facing=face, area=30, aspect=3.0,
                              losses=[(t_go + 3.0, 470)], fire=[(t_go + 2.2, t_go + 4.5)], seed=900 + wave * 20 + j * 2 + (side == "fr")))
    for u in mill:
        u.no_persist = True      # Bild für die „Knochenmühle“, keine echten Verbände
    troops(mill, w(k, 18.6), T.end(k) + 3.5, [(i, i + 1) for i in range(0, len(mill), 2)])
    T.cam(T.end(k) + 1.0, Cam(49.215, 5.43, 8, 56, 60), "linear")

    s = T.vstart["mai"]
    k = "mai"
    T.add(Quote(["Courage, on les aura !", "Nur Mut, wir kriegen sie!"], "GENERAL PÉTAIN · APRIL 1916", w(k, 2.8), w(k, 8.0), size=52))
    T.add(Caption([([FR], "General Robert Nivelle"), (None, "übernimmt im Mai das Kommando bei Verdun")], w(k, 10.2), w(k, 16.0),
                  pos="br", width=560, title="Mai 1916"))
    T.cam(w(k, 14.0), Cam(49.2140, 5.4380, 3.2, 56, 15))
    T.add(DateStamp("22. Mai 1916", "Angriff auf Fort Douaumont", w(k, 16.2), T.end(k) + 0.5, sub="General Charles Mangin"))
    T.add(Barrage([(49.2195, 5.4350), (49.2195, 5.4430), (49.2148, 5.4430), (49.2148, 5.4350)], w(k, 14.0), w(k, 18.5), rate=14, seed=13, size=0.7))
    units = [U("fr", 4000, [(w(k, 17.4), 49.2075, 5.4300), (w(k, 24.0), 49.2150, 5.4370), (w(k, 26.8), 49.2085, 5.4320)], facing=20, area=30,
               aspect=3.0, losses=[(w(k, 25.0), 2300)], fire=[(w(k, 19.0), T.end(k))], t1=T.end(k) + 1.0, seed=81),
             U("fr", 3000, [(w(k, 17.6), 49.2090, 5.4450), (w(k, 24.0), 49.2155, 5.4420), (w(k, 26.8), 49.2100, 5.4460)], facing=340, area=30,
               aspect=3.0, losses=[(w(k, 25.4), 1600)], fire=[(w(k, 19.0), T.end(k))], t1=T.end(k) + 1.0, seed=82),
             U("de", 3500, [(w(k, 15.0), 49.2195, 5.4400)], facing=190, area=26, aspect=2.5, losses=[(w(k, 23.8), 900)],
               fire=[(w(k, 19.0), T.end(k))], t1=T.end(k) + 1.0, seed=83)]
    troops(units, w(k, 15.0), T.end(k) + 1.0, [(0, 2), (1, 2)])

    # ------------------------------------------------------------ Kapitel 6 · Kampf um die Forts (Juni – Juli)
    t = T.t
    T.mood(t, "forts")
    T.add(ChapterCard(6, "Kampf um die Forts", "Juni – Juli 1916", t + 0.2, 5.0))
    T.cam(t + 6.0, Cam(49.2025, 5.4700, 3.4, 56, 340))
    T.wait(5.6)
    s = T.say("vaux", pre=0.2)
    T.say("raynal", pre=0.3, post=3.5)
    T.say("gas", pre=0.4, post=2.5)
    T.say("fleury", pre=0.3, post=3.5)
    T.say("somme", pre=0.5, post=2.5)
    T.say("souville", pre=0.5, post=3.5)
    cf_hoelle.t1 = w("vaux", 0.5)
    k = "vaux"
    T.add(DateStamp("1. – 7. Juni 1916", "Fort Vaux", s, T.end("raynal")))
    T.add(CraterField([(G.ZONES["fleury"], w(k, 0.0), w(k, 0.1))], w(k, 0.0), 1e9))
    garr = U("fr", 600, [(s, 49.2005, 5.4700)], facing=20, area=10, aspect=1.4, fire=[(w(k, 7.0), w("raynal", 24.0))],
             losses=[(w(k, 24.6), 60), (w("raynal", 3.0), 40)], t1=w("raynal", 25.6), seed=91)
    garr.no_persist = True
    attackers = [U("de", 3000, [(s, 49.2120, 5.4650), (w(k, 7.0), 49.2035, 5.4690)], facing=170, area=26, aspect=2.5,
                   losses=[(w(k, 21.0), 700)], fire=[(w(k, 7.0), w("raynal", 24.0))], t1=T.end("raynal") + 1.0, seed=92),
                 U("de", 3000, [(s, 49.2090, 5.4840), (w(k, 7.2), 49.2025, 5.4745)], facing=230, area=26, aspect=2.5,
                   losses=[(w(k, 21.4), 600)], fire=[(w(k, 7.0), w("raynal", 24.0))], t1=T.end("raynal") + 1.0, seed=93),
                 U("de", 2000, [(s, 49.2010, 5.4890), (w(k, 7.4), 49.1990, 5.4760)], facing=270, area=26, aspect=2.5,
                   losses=[(w(k, 21.8), 500)], fire=[(w(k, 7.0), w("raynal", 24.0))], t1=T.end("raynal") + 1.0, seed=94)]
    troops([garr] + attackers, s, T.end("raynal") + 1.0, [(1, 0), (2, 0), (3, 0)])
    T.add(Token(49.2000, 5.4700, [FR], [(0, 600), (w("raynal", 25.0), 0)], label="im Fort", side="fr", t0=w(k, 9.2), t1=T.end("raynal") + 0.6,
                dx=-170, dy=50, show_loss=False))
    T.add(Caption([(None, "gebaut für etwa 250 Mann")], w(k, 13.6), w(k, 19.0), pos="br", width=380))
    T.add(Fire(49.2012, 5.4705, 0.06, w(k, 20.2), w(k, 27.0)))
    T.add(Battle(49.2005, 5.4700, 0.25, w(k, 7.0), w("raynal", 23.0), rate=4, intensity=0.8))
    k = "raynal"
    T.add(Caption([([FR], "Kommandant Sylvain-Eugène Raynal")], w(k, 9.6), w(k, 15.0), pos="br", width=520))
    T.cam(w(k, 8.0), Cam(49.182, 5.425, 14, 48, 330))
    T.add(Bird(P["vaux"], (49.1580, 5.3790), w(k, 13.5), w(k, 21.5), label="Le Vaillant"))
    T.add(Caption([(None, "„Wir halten noch … Entsatz ist dringend nötig.“")], w(k, 15.8), w(k, 21.0), pos="br", width=560,
                  title="Letzte Taubenpost"))
    T.cam(w(k, 22.0), Cam(49.2025, 5.4700, 3.4, 56, 340))
    forts["Vaux"].owners.append((w(k, 25.0), "de"))
    front.states.append((w(k, 24.6), w(k, 27.0), E.resample(G.FRONTS["jun07"], 240)))
    T.add(Caption([([DE], "Kronprinz Wilhelm ehrt Raynal mit einem Offiziersdegen")], w(k, 26.4), T.end(k) + 1.4, pos="br", width=640))

    s = T.vstart["gas"]
    k = "gas"
    T.add(DateStamp("22./23. Juni 1916", "Grünkreuz", s, T.end(k)))
    T.cam(s - 0.4, Cam(49.198, 5.415, 9, 52, 0))
    T.add(Tint(skia.Color4f(0.02, 0.05, 0.14, 0.40), w(k, 3.4), w(k, 24.0)))
    gpos = grid(49.182, 49.198, 5.385, 5.445, 22, seed=9)
    T.add(Guns(gpos, "fr", s, w(k, 23.4), facing=10, fire=[(s, w(k, 22.4))]))
    T.add(GasCloud([(49.200, 5.380), (49.200, 5.450), (49.180, 5.450), (49.180, 5.380)], w(k, 8.0), w("fleury", 4.0)))
    T.add(Caption([([DE], "über 100.000 Gasgranaten")], w(k, 7.6), w(k, 13.4), pos="br", width=440))
    T.add(Caption([(None, "Grünkreuz: Kampfstoff auf Phosgenbasis (Diphosgen)")], w(k, 13.6), w(k, 21.0), pos="br", width=620))

    s = T.vstart["fleury"]
    k = "fleury"
    T.add(DateStamp("23. Juni 1916", "Thiaumont und Fleury", s, w(k, 12.0)))
    front.states.append((w(k, 0.0), w(k, 4.0), E.resample(G.FRONTS["jun23"], 240)))
    thiau = T.add(VFort(*P["thiaumont"], "Thiaumont", [(0, "fr"), (w(k, 1.1), "de")], t0=s - 3, t1=fort_end, size=0.8))
    flips = [(0, "fr"), (w(k, 3.4), "de")] + [(w(k, 18.6) + i * 0.5, "fr" if i % 2 == 0 else "de") for i in range(15)]
    T.add(VFort(*P["fleury"], "Fleury", flips, t0=s - 1, t1=T.end("souville"), size=0.8, shape="circle", dx=-14, align="right"))
    units = [U("de", 12000, [(s, 49.2090, 5.4080), (w(k, 3.6), 49.1985, 5.4200)], facing=170, area=40, aspect=3.5,
               losses=[(w(k, 20.0), 4000)], fire=[(w(k, 1.0), T.end(k))], t1=T.end(k) + 1.0, seed=101),
             U("de", 10000, [(s, 49.2060, 5.4400), (w(k, 3.8), 49.1975, 5.4360)], facing=190, area=40, aspect=3.5,
               losses=[(w(k, 20.4), 3500)], fire=[(w(k, 1.0), T.end(k))], t1=T.end(k) + 1.0, seed=102),
             U("fr", 8000, [(s, 49.1900, 5.4160)], facing=10, area=40, aspect=3.5, losses=[(w(k, 21.0), 3000)],
               fire=[(w(k, 1.0), T.end(k))], t1=T.end(k) + 1.0, seed=103),
             U("fr", 8000, [(s, 49.1885, 5.4400)], facing=350, area=40, aspect=3.5, losses=[(w(k, 21.4), 2800)],
               fire=[(w(k, 1.0), T.end(k))], t1=T.end(k) + 1.0, seed=104)]
    troops(units, s, T.end(k) + 1.0, [(0, 2), (1, 3), (0, 3)])
    T.add(Barrage([(49.202, 5.420), (49.202, 5.445), (49.190, 5.445), (49.190, 5.420)], w(k, 0.5), T.end(k), rate=16, seed=15, size=0.7))
    T.add(Burning([(49.204, 5.405), (49.204, 5.448), (49.188, 5.448), (49.188, 5.405)], w(k, 1.0), T.end(k) + 20.0, n=24, ramp=8.0, seed=57))
    T.add(MeasureLine(P["fleury"], (49.1605, 5.3845), "ca. 5 km", w(k, 5.0), w(k, 10.5)))
    T.cam(w(k, 4.6), Cam(49.180, 5.405, 14, 50, 15))
    T.add(Quote(["Ils ne passeront pas !", "Sie werden nicht durchkommen!"], "GENERAL NIVELLE · 23. JUNI 1916", w(k, 12.6), w(k, 18.0), size=52))
    T.cam(w(k, 18.0), Cam(49.197, 5.428, 4.0, 55, 10))
    T.add(Caption([(None, "Fleury wechselt bis August 16-mal den Besitzer")], w(k, 21.2), T.end(k) + 1.0, pos="br", width=600))

    s = T.vstart["somme"]
    k = "somme"
    T.cam(s - 0.4, Cam(50.5, 12.0, 3200, 0, 0))
    T.add(Polyline(G.WESTERN_FRONT, E.hexc("#ff5a4a"), t0=s - 0.5, t1=T.end(k) + 1.0, width=4, glow=True))
    T.add(Pulse(*P["verdun"], s, T.end(k), r=26))
    T.add(Label(*P["verdun"], "Verdun", t0=s, t1=T.end(k), size=22))
    T.add(Arrow([(50.4, 26.6), (50.7, 25.0), (50.9, 23.6)], "al", t0=w(k, 3.6), grow=2.0, t1=T.end(k), width=14))
    T.add(Arrow([(49.2, 26.2), (49.0, 24.6), (48.8, 23.4)], "al", t0=w(k, 4.2), grow=2.0, t1=T.end(k), width=12))
    T.add(Label(51.3, 25.5, "Brussilow-Offensive", "ab 4. Juni 1916", t0=w(k, 5.6), t1=T.end(k), size=24))
    T.add(Arrow([(49.85, 2.35), (49.97, 2.75)], "al", t0=w(k, 9.6), grow=1.4, t1=T.end(k), width=12))
    T.add(Label(*P["somme"], "Somme", "ab 1. Juli 1916", t0=w(k, 12.6), t1=T.end(k), size=24, dx=-14, align="right"))
    T.add(Battle(*P["somme"], 30, w(k, 12.6), T.end(k) + 0.5, rate=6))
    T.add(Arrow([(49.16, 5.40), (49.60, 4.20), (49.95, 2.95)], "de", t0=w(k, 15.6), grow=2.4, t1=T.end(k), width=8, dashed=True))
    T.add(Arrow([(49.30, 5.70), (50.30, 13.0), (50.70, 22.5)], "de", t0=w(k, 16.2), grow=2.6, t1=T.end(k), width=8, dashed=True))
    T.cam(w(k, 9.0), Cam(49.8, 8.0, 1900, 0, 0))

    s = T.vstart["souville"]
    k = "souville"
    T.add(DateStamp("11. – 12. Juli 1916", "Fort Souville", s, T.end(k) + 1.0))
    T.cam(s - 0.4, Cam(49.183, 5.430, 4.6, 55, 5))
    T.add(GasCloud([(49.192, 5.420), (49.192, 5.445), (49.180, 5.445), (49.180, 5.420)], w(k, 4.2), w(k, 14.0), n=22, radius_m=260))
    front.states.append((w(k, 9.8), w(k, 14.2), E.resample(G.FRONTS["jul12"], 240)))
    units = [U("de", 5000, [(w(k, 3.0), 49.1965, 5.4360), (w(k, 11.0), 49.1895, 5.4340)], facing=190, area=30, aspect=3.0,
               losses=[(w(k, 20.2), 1600)], fire=[(w(k, 6.0), T.end(k))], t1=T.end(k) + 1.5, seed=111),
             U("de", 30, [(w(k, 11.0), 49.1890, 5.4320), (w(k, 13.6), 49.1858, 5.4302)], facing=200, area=10, aspect=1.5,
               losses=[(w(k, 20.4), 30)], fire=[(w(k, 13.6), w(k, 20.0))], t1=T.end(k) + 1.5, seed=112),
             U("fr", 4000, [(w(k, 3.0), 49.1800, 5.4280), (w(k, 18.8), 49.1800, 5.4280), (w(k, 21.4), 49.1860, 5.4300)], facing=10, area=30,
               aspect=3.0, losses=[(w(k, 20.8), 500)], fire=[(w(k, 6.0), T.end(k))], t1=T.end(k) + 1.5, seed=113)]
    troops(units, w(k, 3.0), T.end(k) + 1.5, [(0, 2), (1, 2)])
    T.add(MeasureLine(P["souville"], (49.1605, 5.3845), "keine 5 km bis Verdun", w(k, 15.0), w(k, 20.0)))
    T.add(Label(*P["lion"], "Kapelle Sainte-Fine", "weitester deutscher Vorstoß", t0=w(k, 22.2), t1=T.end(k) + 1.5, size=22, dx=14))

    # ------------------------------------------------------------ Kapitel 7 · Gegenoffensive
    t = T.t
    T.mood(t, "counter")
    T.add(ChapterCard(7, "Die Gegenoffensive", "August – Dezember 1916", t + 0.2, 5.0))
    T.cam(t + 6.0, Cam(49.205, 5.42, 22, 45, 0))
    T.wait(5.6)
    s = T.say("wende", pre=0.2, post=2.0)
    T.say("vorbereitung", pre=0.4, post=3.0)
    T.say("douaumont_zurueck", pre=0.4, post=4.0)
    T.say("vaux_zurueck", pre=0.4, post=2.5)
    T.say("dezember", pre=0.4, post=4.0)
    k = "wende"
    T.add(Caption([([DE], "29. August: Falkenhayn abgelöst"), ([DE], "neu: Hindenburg und Ludendorff (OHL)")], w(k, 0.8), w(k, 9.0),
                  pos="br", width=560, title="Oberste Heeresleitung"))
    front.states.append((w(k, 9.6), w(k, 13.0), E.resample(G.FRONTS["sep01"], 240)))
    T.add(DateStamp("2. September 1916", "Deutsche Angriffe eingestellt", w(k, 9.6), T.end(k) + 1.0))

    s = T.vstart["vorbereitung"]
    k = "vorbereitung"
    T.cam(s - 0.3, Cam(49.175, 5.385, 19, 48, 40))
    gfr2 = grid(49.165, 49.195, 5.36, 5.50, 46, seed=12)
    T.add(Guns(gfr2, "fr", w(k, 3.2), T.end("douaumont_zurueck"), facing=10, fire=[(w(k, 4.0), w("douaumont_zurueck", 18.0))]))
    T.add(Label(*P["baleycourt"], "Baleycourt", "Eisenbahngeschütze 40 cm", t0=w(k, 6.6), t1=T.end(k) + 0.5, size=22, dx=-14, align="right"))
    T.add(ShellArcs(P["baleycourt"], P["douaumont"], w(k, 12.0), T.end(k), every=1.8, flight=2.4, height=170, size=1.1))
    T.add(Barrage([(49.225, 5.395), (49.228, 5.470), (49.205, 5.475), (49.205, 5.400)], w(k, 5.0), w("douaumont_zurueck", 6.0), rate=26,
                  seed=17, size=0.8))
    T.add(Burning([(49.226, 5.398), (49.228, 5.468), (49.208, 5.472), (49.207, 5.402)], w(k, 5.5), T.end("douaumont_zurueck") + 10.0, n=30, ramp=14.0,
                  seed=59))
    T.cam(w(k, 14.0), Cam(49.205, 5.420, 12, 50, 20))
    T.add(Caption([([FR], "Treffer durchschlagen die Betondecke von Douaumont")], w(k, 16.6), T.end(k) + 0.8, pos="br", width=640))

    s = T.vstart["douaumont_zurueck"]
    k = "douaumont_zurueck"
    T.add(DateStamp("24. Oktober 1916", "Französische Gegenoffensive", s, T.end(k)))
    T.add(Tint(skia.Color4f(0.78, 0.80, 0.82, 0.30), w(k, 3.8), w(k, 19.0), fin=2.0, fout=3.0))
    T.cam(s - 0.3, Cam(49.200, 5.425, 11, 52, 5))
    line0 = shift(G.FRONTS["sep01"][7:17], 0.004)
    line1 = shift(G.FRONTS["oct24"][7:17], 0.006)
    T.add(Barrage(line_keys=[(w(k, 6.4), line0), (w(k, 17.6), line1)], t0=w(k, 6.4), t1=w(k, 18.5), rate=40, seed=19, size=0.8,
                  depth_km=0.35))
    front.states.append((w(k, 7.0), w(k, 20.0), E.resample(G.FRONTS["oct24"], 240)))
    units = [U("fr", 10000, [(w(k, 5.0), 49.1945, 5.4080), (w(k, 7.0), 49.1945, 5.4080), (w(k, 18.0), 49.2235, 5.4160)], facing=10, area=40,
               aspect=4.0, losses=[(w(k, 14.0), 1800)], fire=[(w(k, 9.0), T.end(k))], t1=T.end(k) + 1.0, seed=121),
             U("fr", 10000, [(w(k, 5.0), 49.1930, 5.4340), (w(k, 7.0), 49.1930, 5.4340), (w(k, 18.5), 49.2205, 5.4385)], facing=10, area=40,
               aspect=4.0, losses=[(w(k, 14.4), 1600)], fire=[(w(k, 9.0), T.end(k))], t1=T.end(k) + 1.0, seed=122),
             U("fr", 10000, [(w(k, 5.0), 49.1940, 5.4560), (w(k, 7.0), 49.1940, 5.4560), (w(k, 18.0), 49.2120, 5.4560)], facing=10, area=40,
               aspect=4.0, losses=[(w(k, 14.8), 1400)], fire=[(w(k, 9.0), T.end(k))], t1=T.end(k) + 1.0, seed=123),
             U("de", 5000, [(w(k, 5.0), 49.2080, 5.4120), (w(k, 10.0), 49.2080, 5.4120), (w(k, 17.0), 49.2335, 5.4150)], facing=190, area=40,
               aspect=3.5, losses=[(w(k, 12.0), 1800)], fire=[(w(k, 9.0), w(k, 19.0))], t1=T.end(k) + 1.0, seed=124),
             U("de", 5000, [(w(k, 5.0), 49.2050, 5.4380), (w(k, 10.0), 49.2050, 5.4380), (w(k, 17.0), 49.2310, 5.4420)], facing=190, area=40,
               aspect=3.5, losses=[(w(k, 12.4), 2000)], fire=[(w(k, 9.0), w(k, 19.0))], t1=T.end(k) + 1.0, seed=125),
             U("de", 5000, [(w(k, 5.0), 49.2040, 5.4580), (w(k, 10.0), 49.2040, 5.4580), (w(k, 17.0), 49.2230, 5.4620)], facing=190, area=40,
               aspect=3.5, losses=[(w(k, 12.8), 1600)], fire=[(w(k, 9.0), w(k, 19.0))], t1=T.end(k) + 1.0, seed=126)]
    troops(units, w(k, 5.0), T.end(k) + 1.0, [(0, 3), (1, 4), (2, 5)])
    T.add(Caption([([FR], "Kolonialregiment aus Marokko (RICM)"), (None, "mit Bataillonen aus Somalia und dem Senegal")], w(k, 13.0), w(k, 19.5),
                  pos="br", width=620))
    T.cam(w(k, 17.0), Cam(49.2165, 5.4385, 3.6, 55, 10))
    forts["Douaumont"].owners.append((w(k, 20.0), "fr"))
    thiau.owners.append((w(k, 15.0), "fr"))
    T.add(LossBadge(49.2190, 5.4400, [DE], 6000, w(k, 23.2), T.end(k) + 1.5, label="Gefangene", dx=170, dy=-40, side="de"))

    s = T.vstart["vaux_zurueck"]
    k = "vaux_zurueck"
    T.cam(s - 0.4, Cam(49.2030, 5.4690, 3.6, 55, 345))
    T.add(DateStamp("2. November 1916", "Fort Vaux", s, T.end(k)))
    front.states.append((w(k, 0.8), w(k, 4.0), E.resample(G.FRONTS["nov02"], 240)))
    forts["Vaux"].owners.append((w(k, 2.6), "fr"))
    T.add(Token(49.2005, 5.4700, [FR], [(0, 0)], label="Fort Vaux", side="fr", t0=w(k, 7.6), t1=T.end(k) + 1.0, dx=0, dy=-80, loss_only=True))
    T.cam(w(k, 8.0), Cam(49.205, 5.43, 12, 50, 10))

    s = T.vstart["dezember"]
    k = "dezember"
    T.add(DateStamp("15. – 18. Dezember 1916", "Louvemont und Bezonvaux", s, w(k, 18.6)))
    T.cam(s - 0.3, Cam(49.228, 5.430, 13, 50, 0))
    l0 = shift(G.FRONTS["nov02"][7:16], 0.004)
    l1 = shift(G.FRONTS["dec18"][7:16], 0.005)
    T.add(Barrage(line_keys=[(w(k, 3.0), l0), (w(k, 9.6), l1)], t0=w(k, 3.0), t1=w(k, 10.0), rate=34, seed=21, size=0.8))
    T.add(Burning([(49.262, 5.380), (49.262, 5.490), (49.235, 5.495), (49.232, 5.385)], w(k, 3.5), T.end(k) + 6.0, n=26, ramp=7.0, seed=61))
    front.states.append((w(k, 5.6), w(k, 10.4), E.resample(G.FRONTS["dec18"], 240)))
    units = [U("fr", 8000, [(w(k, 2.0), la - 0.004, lo), (w(k, 3.0), la - 0.004, lo), (w(k, 10.0), la2 - 0.004, lo2)], facing=10, area=45,
               aspect=4.0, losses=[(w(k, 8.0), 900)], fire=[(w(k, 4.0), w(k, 12.0))], t1=w(k, 19.0), seed=131 + i)
             for i, ((la, lo), (la2, lo2)) in enumerate(zip(G.FRONTS["nov02"][8:16:2], G.FRONTS["dec18"][8:16:2]))]
    units += [U("de", 6000, [(w(k, 2.0), la + 0.006, lo), (w(k, 4.0), la + 0.006, lo), (w(k, 9.0), la2 + 0.010, lo2)], facing=190, area=45,
                aspect=4.0, losses=[(w(k, 8.6), 2200)], fire=[(w(k, 4.0), w(k, 11.0))], t1=w(k, 19.0), seed=141 + i)
              for i, ((la, lo), (la2, lo2)) in enumerate(zip(G.FRONTS["nov02"][9:16:2], G.FRONTS["dec18"][9:16:2]))]
    nf = 4
    troops(units, w(k, 2.0), w(k, 19.0), [(i, nf + min(i, len(units) - nf - 1)) for i in range(nf)])
    T.add(Label(*P["louvemont"], "Louvemont", t0=w(k, 10.8), t1=T.end(k) + 1.0, size=22))
    T.add(Label(*P["bezonvaux"], "Bezonvaux", t0=w(k, 11.6), t1=T.end(k) + 1.0, size=22))
    T.add(LossBadge(49.252, 5.445, [DE], 11000, w(k, 13.6), w(k, 19.5), label="Gefangene", dx=0, dy=-80, side="de"))
    T.add(Caption([([FR], "115 deutsche Geschütze erbeutet")], w(k, 16.0), w(k, 20.0), pos="br", width=460))
    T.add(DateStamp("18. Dezember 1916", "Die Schlacht endet", w(k, 18.8), T.end(k) + 1.5))
    T.cam(w(k, 19.0), Cam(49.235, 5.40, 24, 45, 0))
    T.add(Polyline(G.WEST[-1:] + G.FRONTS["feb21"] + G.SOUTH[:1], E.hexc("#ffffff"), t0=w(k, 24.0), t1=T.end(k) + 1.8, width=2.6,
                   dash=(10, 8), grow=2.5))
    T.add(Label(49.304, 5.395, "Front am 21. Februar", t0=w(k, 24.8), t1=T.end(k) + 1.8, size=22, dot=False, dy=-18))

    # ------------------------------------------------------------ Kapitel 8 · Bilanz
    t = T.t
    T.mood(t, "legacy")
    T.add(ChapterCard(8, "Bilanz", "21. Februar – 18. Dezember 1916", t + 0.2, 5.0))
    T.cam(t + 6.0, Cam(49.215, 5.490, 32, 32, 0))
    T.wait(5.6)
    s = T.say("bilanz", pre=0.2, post=3.0)
    T.say("landschaft", pre=0.4, post=3.0)
    T.say("erbe", pre=0.5, post=2.5)
    T.say("gedenken", pre=0.8, post=3.5)
    k = "bilanz"
    markers = [(P["caures"], "Bois des Caures", "21.–22.2.", "deutsch", -40, -70), (P["douaumont"], "Fort Douaumont", "25.2. / 24.10.", None, 130, -60),
               ((49.234, 5.235), "Toter Mann · Höhe 304", "März – Mai", "deutsch", -60, -70), (P["vaux"], "Fort Vaux", "7.6. / 2.11.", None, 40, 75),
               (P["fleury"], "Fleury · Thiaumont", "Juni – Aug.", None, -190, 10), (P["souville"], "Fort Souville", "11.–12.7.", "gehalten", -150, 85),
               ((49.248, 5.440), "Louvemont · Bezonvaux", "15.–18.12.", "französisch", 120, -95)]
    for i, (pos, name, date, res, dx, dy) in enumerate(markers):
        T.add(BattleMarker(*pos, name, date, [DE], [FR], s - 0.5 + i * 0.35, T.end("landschaft") - 1.0, dx=dx, dy=dy, result=res))
    rows = [([FR], "Frankreich", 377000, "Tote, Verwundete, Vermisste · davon rund 163.000 Tote", w(k, 6.0)),
            ([DE], "Deutsches Reich", 337000, "davon rund 143.000 Tote", w(k, 12.6)),
            ([FR, DE], "Zusammen", 714000, "davon rund 300.000 Tote", w(k, 16.0))]
    T.add(BilanzPanel(w(k, 5.0), T.end(k) + 1.2, rows, head="Verluste 1916 (Schätzung)"))
    T.cam(T.end(k) - 1.0, Cam(49.215, 5.485, 30, 32, 2), "linear")
    T.cam(T.end(k) + 2.4, Cam(49.215, 5.38, 26, 40, 8))

    s = T.vstart["landschaft"]
    k = "landschaft"
    dead = [("beaumont", "Beaumont"), ("bezonvaux", "Bezonvaux"), ("cumieres", "Cumières"), ("douaumont_dorf", "Douaumont"),
            ("fleury", "Fleury"), ("haumont", "Haumont"), ("louvemont", "Louvemont"), ("ornes", "Ornes"), ("vaux_dorf", "Vaux")]
    for i, (key, name) in enumerate(dead):
        T.add(Label(*P[key], "† " + name, t0=w(k, 0.2) + i * 0.22, t1=T.end(k) + 0.5, size=21, color=E.hexc("#e8e0d0")))
    T.add(Caption([(None, "„Mort pour la France“ – für Frankreich gestorben")], w(k, 6.0), w(k, 12.0), pos="br", width=560))
    T.add(Label(49.245, 5.42, "WALD VON VERDUN", t0=w(k, 19.2), t1=T.end(k) + 1.5, size=30, style="sea", dot=False, color=E.hexc("#b8e0b0")))
    T.cam(w(k, 14.0), Cam(49.225, 5.41, 16, 52, 15))
    craters_end = w(k, 17.8)
    for o in T.objects:
        if isinstance(o, CraterField) and o.t1 > 1e8:
            o.t1 = craters_end
            o.fout = 3.5
    for o in T.objects:
        if isinstance(o, VFort) and o.t1 > 1e8:
            o.t1 = T.end(k) + 1.0
    front.t1 = T.end(k) + 1.0

    s = T.vstart["erbe"]
    k = "erbe"
    T.mood(s - 0.5, "legacy2")
    T.cam(s - 0.4, Cam(49.2060, 5.4255, 4.5, 55, 0))
    T.add(Label(*P["beinhaus"], "Beinhaus von Douaumont", t0=w(k, 2.0), t1=T.end("gedenken"), size=26))
    T.add(Caption([(None, "Gebeine von rund 130.000 unbekannten Soldaten"), ([FR], "davor rund 16.000 französische Gräber")], w(k, 5.4), w(k, 16.5),
                  pos="br", width=600))
    T.cam(T.end(k) + 1.0, Cam(49.2070, 5.4250, 4.2, 55, 25), "linear")

    s = T.vstart["gedenken"]
    k = "gedenken"
    T.add(DateStamp("22. September 1984", "Beinhaus von Douaumont", s, w(k, 16.0)))
    T.add(Caption([([FR], "François Mitterrand, Präsident Frankreichs"), (["de"], "Helmut Kohl, deutscher Bundeskanzler")], w(k, 6.8), w(k, 16.0),
                  pos="br", width=600, title="Hand in Hand"))
    T.cam(T.end(k) + 2.0, Cam(49.200, 5.420, 9, 52, 40), "linear")
    # Flaggen-Gebiete: 1914 Bündniskarte, ab der Westfront deutsch/französisch gehaltenes Gebiet
    import skia as _sk
    paths = E.load_countries()
    thrace = E.thrace_path()
    bg_path = _sk.Op(paths["Bulgaria"], thrace, _sk.PathOp.kDifference_PathOp) or paths["Bulgaria"]
    ru_rect, ot_rect, gb_rect = (44.0, 20.0, 60.0, 60.0), (33.0, 27.0, 43.6, 46.0), (49.9, -10.6, 58.7, 1.8)
    cp_on, en_on = w("europa", 6.8), w("europa", 16.2)
    war = w("westfront", 9.4)
    f_end = T.end("bilanz") + 1.5
    ent = [dict(name="German Empire", flag="de1871", side="cp", t_on=cp_on, t_off=war),
           dict(name="Austro-Hungarian Empire", flag="ah1869", side="cp", t_on=cp_on, t_off=f_end),
           dict(name="Ottoman Empire", flag="tr", side="cp", rect=ot_rect, t_on=w("europa", 12.1), t_off=f_end),
           dict(name="thrace", path=thrace, flag="tr", side="cp", rect=ot_rect, t_on=w("europa", 12.1), t_off=f_end),
           dict(name="bulgaria", path=bg_path, flag="bg", side="cp", t_on=w("europa", 13.5), t_off=f_end),
           dict(name="France", flag="fr", side="en", t_on=en_on, t_off=war),
           dict(name="Belgium", flag="be", side="en", t_on=en_on, t_off=war),
           dict(name="United Kingdom of Great Britain and Ireland", flag="gb", side="en", rect=gb_rect, t_on=en_on, t_off=f_end),
           dict(name="Russian Empire", flag="ru1914", side="en", rect=ru_rect, t_on=en_on, t_off=f_end),
           dict(name="Grand Duchy of Finland", flag="ru1914", side="en", rect=ru_rect, t_on=en_on, t_off=f_end),
           dict(name="Serbia", flag="rs", side="en", t_on=en_on, t_off=T.vstart["falkenhayn"]),
           dict(name="Montenegro", flag="me", side="en", t_on=en_on, t_off=T.vstart["falkenhayn"]),
           dict(name="Kingdom of Italy", flag="it1861", side="en", t_on=w("westfront", 16.2), t_off=f_end),
           dict(name="de_held", flag="de1871", side="cp", t_on=war, t_off=f_end),
           dict(name="fr_held", flag="fr", side="en", t_on=war, t_off=f_end)]
    for nm in ("Georgia", "Armenia", "Azerbaijan"):
        if nm in paths:
            ent.append(dict(name=nm, flag="ru1914", side="en", rect=ru_rect, t_on=en_on, t_off=f_end))
    flags_obj.entries = ent
    flags_obj.t1 = f_end + 1.5

    # Truppen: alle Verbände bleiben stehen (bis Ende der Schlacht) und rücken mit der Front mit
    t_troops_end = T.end("bilanz") + 1.0
    for u in ALL_UNITS:
        if getattr(u, "persist", False):
            u.t1 = t_troops_end
    follow_front(ALL_UNITS, front)
    T.add(E.Troops(ALL_UNITS, min(u.t0 for u in ALL_UNITS), t_troops_end, ALL_ENEM))

    t = T.t
    T.add(Credits(t, t + 27.0, roles=[("Produzent", "Atakan Zengin"), ("Kanal", "WarAZ")], title="VERDUN 1916"))
    T.wait(27.0)
    T.finalize()
    return T


if __name__ == "__main__":
    tl = build()
    print("Dauer:", round(tl.duration, 1), "s =", f"{int(tl.duration // 60)}:{int(tl.duration % 60):02d}")
    print("Objekte:", len(tl.objects))
    for k, v in tl.vstart.items():
        print(f"  {k:18s} {int(v // 60)}:{v % 60:04.1f}")
