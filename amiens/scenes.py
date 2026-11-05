"""Drehbuch als Zeitleiste: Kamerafahrten, Frontverläufe, Panzer, Flugzeuge, Figuren-Schlachten und Einblendungen.

Zeiten wie T.w("angriff", 7.5) beziehen sich auf die Wortzeit in der jeweiligen Sprachaufnahme (Spracherkennung).
Stärken und Verluste sind gerundete Werte aus der Literatur; wo die Zahl unsicher ist, steht „ca.“ (siehe README).
Panzer: 1 Modell = 1 Panzer. Figuren: 1 Figur = 1 Soldat (Ausschnitte der beteiligten Verbände).
"""
import json
import math
import os

import numpy as np
import skia

import armor as A
import engine as E
import vgeo as G
from engine import (Arrow, Barrage, Battle, BigWord, Burning, Cam, Caption, ChapterCard, Convoy, CraterField, Credits,
                    DateStamp, Explosion, FrontMap, GasCloud, Guns, Label, Polyline, Pulse, Quote, Rain, ShellArcs, Tint,
                    TitleCard, Token, TerritoryFlags)
from narration import SEGMENTS

HERE = os.path.dirname(os.path.abspath(__file__))
P = G.P
DE, FR, GB, AU, CA, US = "de_1871", "fr", "gb", "au", "ca_1868", "us"
RED, BLUE = E.TR_RED, E.AL_BLUE
E.SIDE_RGB.update({"ca": (95, 150, 245), "us": (120, 200, 255), "gb": (70, 130, 240), "au": (60, 180, 230), "fr": (125, 170, 255)})


class Timeline:
    def __init__(self, known=None):
        self.known = known or {}
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

    def _start(self, key):
        # Vorgriff auf spätere Abschnitte: Startzeit aus dem ersten Durchlauf
        return self.vstart[key] if key in self.vstart else self.known.get(key, 0.0)

    def w(self, key, sec):
        return self._start(key) + sec

    def end(self, key):
        return self._start(key) + self.vdur[key]

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


# ------------------------------------------------------------------ Hilfen: Front, Formationen
_N_EARLY = [(50.30, 2.86), (50.27, 2.90), (50.19, 2.93), (50.13, 3.08), (50.08, 3.12)]
_S_EARLY = [(49.58, 3.33), (49.50, 3.40), (49.38, 3.45)]
_N_1918 = [(50.30, 2.82), (50.20, 2.72), (50.12, 2.645), (50.07, 2.642)]
_N_AUG = [(50.30, 2.82), (50.20, 2.72), (50.12, 2.665), (50.07, 2.662)]
_S_1918 = [(49.59, 2.75), (49.58, 2.95), (49.48, 3.05), (49.38, 3.30)]
_S_AUG = [(49.59, 2.80), (49.58, 2.95), (49.48, 3.05), (49.38, 3.30)]


def local_line(key):
    if key == "mar20":
        pts = _N_EARLY + G.FRONTS[key] + _S_EARLY
    elif key.startswith("aug") and key != "aug08":
        pts = _N_AUG + G.FRONTS[key] + _S_AUG
    else:
        pts = _N_1918 + G.FRONTS[key] + _S_1918
    return E.resample(np.array(pts, float), 240)


def anchor_on(line, pos, side, dist_km):
    """Punkt hinter der Front: nächster Frontpunkt zu pos, um dist_km zur eigenen Seite versetzt."""
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


def anchor(key, pos, side, dist_km):
    return anchor_on(local_line(key), pos, side, dist_km)


def squad(kind, nation, n, t0, t1, a, b, alt=700.0, spread=140.0, circles=None, seed=0, shot=None, drops=None):
    """Staffel in Keilformation von a nach b (lat, lon); circles: Luftkampf um einen Punkt."""
    out = []
    k = math.cos(math.radians(a[0]))
    hd = math.atan2((b[1] - a[1]) * k, b[0] - a[0])
    for i in range(n):
        r = (i + 1) // 2
        side = 1 if i % 2 else -1
        back = r * spread
        lat_off = (-math.cos(hd) * back + math.sin(hd) * side * r * spread * 0.9) / 111320.0
        lon_off = (-math.sin(hd) * back - math.cos(hd) * side * r * spread * 0.9) / (111320.0 * k)
        keys = [(t0, a[0] + lat_off, a[1] + lon_off, alt + (i % 3) * 40), (t1, b[0] + lat_off, b[1] + lon_off, alt + (i % 3) * 40)]
        cs = None
        if circles:
            c0, c1, cla, clo, rr, per = circles
            cs = [(c0 + i * 0.15, c1, cla, clo, rr * (0.6 + 0.12 * (i % 5)), per * (0.85 + 0.06 * (i % 4)))]
        s = shot[i] if isinstance(shot, dict) and i in shot else None
        out.append(A.Plane(kind, nation, keys, circles=cs, shot=s, drops=(drops or {}).get(i), seed=seed * 31 + i))
    return out


def lerp(a, b, f):
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


# ======================================================================= Aufbau
def build(known=None):
    if known is None:
        return build(known=build(known={}).vstart)
    T = Timeline(known)
    U = E.Unit
    w = T.w

    ALL_UNITS, ALL_ENEM, TANKS, PLANES = [], [], [], []

    def troops(units, t1, enemies=()):
        base = len(ALL_UNITS)
        for u in units:
            u.t1 = min(u.t1, t1)
            ALL_UNITS.append(u)
        ALL_ENEM.extend((base + i, base + j) for i, j in enemies)

    def tanks(*groups):
        TANKS.extend(groups)
        return groups

    zeros = np.zeros((0, 2))
    front = T.add(FrontMap([(0, 0, local_line("mar20"))], zeros, zeros, G.GER_CLOSE, G.AL_CLOSE, 1e9, 1e9,
                           box=(49.35, 1.60, 50.35, 3.60)))
    wfront = A.WFront([(0, 0, G.WF["mar20"])])

    # ------------------------------------------------------------ 0 · Luftaufnahme & Titel
    T.mood(0, "intro")
    T.cam(0.0, Cam(49.80, 2.40, 175, 40, 70))
    s = T.say("intro", pre=7.0, post=1.0)
    k = "intro"
    T.cam(w(k, 2.0), Cam(49.88, 2.48, 24, 50, 78), "smooth")
    T.add(Label(*P["amiens"], "Amiens", t0=w(k, 0.6), t1=w(k, 9.0), size=34))
    T.add(Label(49.928, 2.47, "SOMME", t0=w(k, 0.4), t1=w(k, 8.0), size=24, style="sea", dot=False))
    T.cam(w(k, 6.5), Cam(49.872, 2.565, 6.0, 55, 82))
    T.add(Label(*P["vb_denkmal"], "Australisches Ehrenmal", "Villers-Bretonneux", t0=w(k, 9.2), t1=w(k, 13.5), size=22))
    # „rollen über diese Felder Hunderte Panzer“ 13.7 / „am Himmel“ 17.4
    tanks(A.TankGroup("au", "mk5", 16, [(w(k, 12.8), 49.868, 2.548), (w(k, 30.0), 49.874, 2.610)], spacing=85, rows=2, seed=1,
                          t1=T.end(k) + 6.0),
          A.TankGroup("au", "whippet", 6, [(w(k, 14.0), 49.858, 2.552), (w(k, 30.0), 49.862, 2.618)], spacing=110, seed=2,
                          t1=T.end(k) + 6.0))
    T.add(A.AirWar(squad("camel", "gb", 7, w(k, 16.4), w(k, 31.0), (49.83, 2.53), (49.93, 2.66), alt=650, seed=1)
                   + squad("se5", "gb", 5, w(k, 17.2), w(k, 31.0), (49.84, 2.51), (49.92, 2.68), alt=800, seed=2),
                   w(k, 16.0), w(k, 31.5)))
    T.cam(w(k, 14.0), Cam(49.870, 2.585, 5.0, 56, 86))
    T.cam(w(k, 21.0), Cam(49.86, 2.60, 9.0, 54, 88))
    T.add(Label(49.95, 2.80, "DEUTSCHE", t0=w(k, 22.0), t1=w(k, 28.5), size=28, style="sea", dot=False, color=RED))
    T.cam(T.end(k) + 9, Cam(49.86, 2.55, 60, 46, 80), "linear")
    T.add(TitleCard(T.end(k) + 0.4, 8.5, title="AMIENS", year="1918", sub="DER SCHWARZE TAG DES DEUTSCHEN HEERES"))
    T.wait(8.5)

    # ------------------------------------------------------------ Kapitel 1 · Das letzte Aufgebot
    t = T.t
    T.mood(t, "world")
    T.add(ChapterCard(1, "Das letzte Aufgebot", "Frühjahr 1918", t, 5.0))
    T.cam(t + 6.5, Cam(48.5, 16.0, 4300, 0, 0))
    T.wait(5.5)
    s = T.say("europa", pre=0.4, post=2.0)
    T.say("ludendorff", pre=0.5, post=2.0)
    flags_obj = T.add(TerritoryFlags([], s - 1.5, 1e9, front=wfront, wf_n=zeros, wf_s=zeros))
    k = "europa"
    T.add(Label(52.5, 13.4, "Deutsches Reich", t0=w(k, 8.0), t1=w(k, 24.0), style="country", size=30))
    T.add(Label(47.6, 18.0, "Österreich-Ungarn", t0=w(k, 9.4), t1=w(k, 24.0), style="country", size=28))
    T.add(Label(38.8, 33.5, "Osmanisches Reich", t0=w(k, 11.1), t1=w(k, 24.0), style="country", size=28))
    T.add(Label(42.7, 25.3, "Bulgarien", t0=w(k, 12.4), t1=w(k, 24.0), style="country", size=22))
    T.add(Label(46.6, 2.4, "Frankreich", t0=w(k, 16.3), t1=w(k, 24.0), style="country", size=28))
    T.add(Label(52.3, -1.4, "Großbritannien", t0=w(k, 17.3), t1=w(k, 24.0), style="country", size=26))
    T.add(Label(43.2, 12.2, "Italien", t0=w(k, 19.6), t1=w(k, 24.0), style="country", size=24))
    T.add(Token(46.0, -12.0, [US], [(0, 0)], label="USA · seit 1917", side="al", t0=w(k, 22.6), t1=T.end(k) + 1.0, dy=-40))
    T.add(Arrow([(43.0, -14.5), (46.0, -9.0), (47.6, -4.0)], "al", t0=w(k, 22.8), grow=2.0, t1=T.end(k) + 1.0, width=12))
    T.add(Label(56.0, 40.0, "Russland", "Revolution 1917", t0=w(k, 24.7), t1=T.end(k) + 1.0, style="country", size=30))
    T.add(Label(*P["brest_litowsk"], "Brest-Litowsk", "3. März 1918", t0=w(k, 31.6), t1=T.end(k) + 1.5, size=22))
    T.add(Caption([([DE], "Mittelmächte: Deutsches Reich, Österreich-Ungarn"), (["tr", "bg"], "Osmanisches Reich, Bulgarien"),
                   ([FR, GB], "Alliierte: Frankreich, Großbritannien, Italien"), ([US], "seit April 1917: USA")],
                  w(k, 6.6), w(k, 27.0), pos="br", width=680, title="Europa 1918"))

    k = "ludendorff"
    T.cam(w(k, 0.0), Cam(50.5, 12.0, 2600, 0, 0))
    T.add(Caption([([DE], "Erich Ludendorff"), (None, "Erster Generalquartiermeister, Oberste Heeresleitung")], w(k, 2.4), w(k, 12.0),
                  pos="br", width=600))
    for pts in ([(53.0, 27.0), (52.4, 19.0), (51.0, 11.0), (50.2, 6.5)], [(50.0, 30.0), (50.2, 21.0), (49.8, 12.5), (49.3, 7.0)]):
        T.add(Arrow(pts, "de", t0=w(k, 7.0), grow=3.0, t1=w(k, 16.0), width=14))
    T.add(Token(51.8, 21.0, [DE], [(0, 0)], label="Dutzende Divisionen von Osten", side="de", t0=w(k, 7.4), t1=w(k, 16.0), dy=-50))
    T.cam(w(k, 16.5), Cam(48.5, 0.0, 2600, 0, 0))
    T.add(Arrow([(40.5, -30.0), (45.0, -15.0), (47.3, -3.5)], "al", t0=w(k, 18.2), grow=2.5, t1=T.end(k) + 1.0, width=14))
    T.add(Label(*P["st_nazaire"], "Saint-Nazaire", t0=w(k, 19.5), t1=T.end(k) + 1.0, size=20))
    T.add(Label(*P["brest"], "Brest", t0=w(k, 19.8), t1=T.end(k) + 1.0, size=20))
    T.add(Token(44.5, -16.0, [US], [(w(k, 18.0), 0), (w(k, 23.0), 1000000)], label="US-Soldaten in Frankreich (bis Herbst)",
                side="al", t0=w(k, 18.6), t1=T.end(k) + 1.0, dy=-46))

    # ------------------------------------------------------------ Michael
    t = T.t
    T.mood(t, "offensive")
    s = T.say("michael", pre=0.5, post=2.0)
    T.say("amiens_ziel", pre=0.4, post=2.0)
    T.say("verluste_michael", pre=0.4, post=2.4)
    k = "michael"
    T.add(DateStamp("21. März 1918", "Unternehmen Michael", s, w(k, 22.0)))
    T.cam(s - 0.5, Cam(49.85, 2.95, 230, 0, 0))
    front.t0, front.t1 = s - 0.5, T.end("bilanz_amiens") + 3.0
    T.add(Barrage([(50.20, 3.00), (50.20, 3.30), (49.60, 3.45), (49.60, 3.30)], w(k, 8.4), w(k, 14.0), rate=55, seed=21, size=1.6))
    T.add(Token(49.95, 3.45, [DE], [(0, 0)], label="72 Divisionen · über 6.000 Geschütze", side="de", t0=w(k, 6.6), t1=w(k, 22.0), dy=-40))
    for i, (a, b) in enumerate((((50.10, 3.15), (49.98, 2.75)), ((49.92, 3.20), (49.87, 2.62)), ((49.78, 3.25), (49.75, 2.60)),
                                ((49.66, 3.35), (49.62, 2.65)))):
        T.add(Arrow([a, lerp(a, b, 0.5), b], "de", t0=w(k, 13.0 + i * 0.4), grow=6.0, t1=T.end("amiens_ziel") + 1.0, width=14))
    front.states.append((w(k, 15.5), w("amiens_ziel", 3.0), local_line("apr04")))
    wfront.states.append((w(k, 15.5), w("amiens_ziel", 3.0), G.WF["apr05"]))
    T.add(Caption([([GB], "britische 5. Armee bricht ein"), (None, "Front an der Somme auf rund 70 km eingedrückt")], w(k, 21.5),
                  w(k, 31.0), pos="br", width=600))
    k = "amiens_ziel"
    T.cam(w(k, 3.5), Cam(49.87, 2.55, 120, 0, 0))
    T.add(Label(*P["amiens"], "AMIENS", "Eisenbahnknoten", t0=w(k, 4.6), t1=T.end("verluste_michael") + 1.0, size=34))
    T.add(Pulse(*P["amiens"], w(k, 5.1), w(k, 14.0), r=46))
    rails = [[P["amiens"], (49.95, 1.80)], [P["amiens"], (50.30, 2.40)], [P["amiens"], (49.60, 2.10)], [P["amiens"], (49.75, 2.00)],
             [P["amiens"], (49.88, 2.80)]]
    for r_ in rails:
        T.add(Polyline(r_, E.hexc("#e8d9a8"), t0=w(k, 6.6), t1=w(k, 16.0), width=3, grow=1.6, dash=(10, 8)))
    T.add(Caption([([FR], "Ferdinand Foch"), (None, "ab 26. März Koordinator, ab April Oberbefehlshaber der Alliierten")],
                  w(k, 14.4), w(k, 23.0), pos="br", width=640))
    T.cam(w(k, 22.5), Cam(49.87, 2.48, 40, 30, 80))
    T.add(Label(*P["vb"], "Villers-Bretonneux", t0=w(k, 24.2), t1=T.end("verluste_michael") + 1.0, size=24))
    T.add(MeasureLineSafe(P["vb"], P["amiens"], "ca. 15 km", w(k, 26.0), w(k, 31.0)))
    k = "verluste_michael"
    T.cam(w(k, 0.4), Cam(49.60, 3.20, 520, 0, 0))
    T.add(Caption([([DE], "Deutsche: ca. 240.000 Mann"), ([GB, FR], "Briten und Franzosen: ca. 250.000"),
                   (None, "Verluste bis Anfang April")], w(k, 4.0), w(k, 15.5), pos="br", width=560, title="Unternehmen Michael"))
    for pts, t_ in (([(50.75, 3.05), (50.67, 2.75)], 18.4), ([(49.48, 3.70), (49.15, 3.55)], 19.9), ([(49.20, 3.95), (49.02, 3.70)], 21.3)):
        T.add(Arrow(pts, "de", t0=w(k, t_), grow=1.6, t1=T.end(k) + 1.0, width=12))
    T.add(Label(50.72, 3.25, "Flandern", "April", t0=w(k, 18.4), t1=T.end(k) + 1.0, size=20))
    T.add(Label(49.40, 3.85, "Aisne", "Mai", t0=w(k, 19.9), t1=T.end(k) + 1.0, size=20))
    T.add(Label(49.02, 3.98, "Marne", "Juli", t0=w(k, 21.3), t1=T.end(k) + 1.0, size=20))

    # ------------------------------------------------------------ Luftkrieg über der Somme, Richthofen
    s = T.say("luftkrieg", pre=0.5, post=2.6)
    k = "luftkrieg"
    T.mood(s - 0.5, "air")
    T.cam(s - 0.2, Cam(49.90, 2.52, 18, 48, 75))
    T.add(Caption([([GB], "1. April 1918: Royal Air Force"), (None, "erste eigenständige Luftwaffe der Welt")], w(k, 5.8), w(k, 13.0),
                  pos="br", width=560))
    fight = (w(k, 11.0), w(k, 21.0), 49.905, 2.56, 1300, 18)
    air = (squad("camel", "gb", 6, w(k, 0.0), w(k, 30.0), (49.86, 2.42), (49.95, 2.66), alt=700, circles=fight, seed=11,
                 shot={3: w(k, 15.2)})
           + squad("fokker", "de", 6, w(k, 2.0), w(k, 30.0), (49.96, 2.70), (49.86, 2.46), alt=760, circles=fight, seed=12,
                   shot={1: w(k, 13.5), 4: w(k, 18.0)}))
    # Richthofen: roter Dreidecker, tief über der Somme, verfolgt von einer Camel; stürzt bei Vaux-sur-Somme ab
    rt0 = w(k, 19.0)
    red = A.Plane("dr1", "de", [(rt0, 49.915, 2.47, 180), (rt0 + 6.5, 49.928, 2.535, 140), (rt0 + 12, 49.935, 2.60, 140)],
                  shot=rt0 + 6.6, seed=77)
    chaser = A.Plane("camel", "gb", [(rt0 + 0.3, 49.910, 2.455, 200), (rt0 + 7.0, 49.926, 2.527, 170), (rt0 + 12, 49.95, 2.62, 260)],
                     seed=78)
    T.add(A.AirWar(air + [red, chaser], s - 0.5, T.end(k) + 2.0, fights=[(w(k, 11.0), w(k, 21.0)), (rt0, rt0 + 7)]))
    T.cam(w(k, 18.5), Cam(49.925, 2.52, 5.5, 52, 80))
    T.add(Label(*P["vaux_somme"], "Vaux-sur-Somme", t0=w(k, 25.5), t1=T.end(k) + 2.0, size=22))
    T.add(Caption([([DE], "Manfred von Richthofen, „der Rote Baron“"), (None, "† 21. April 1918 · 80 Luftsiege")], w(k, 22.0),
                  T.end(k) + 1.8, pos="br", width=600))
    T.add(Token(49.905, 2.60, [AU], [(0, 0)], label="australische Stellungen", side="al", t0=w(k, 27.5), t1=T.end(k) + 2.0, dy=-40))

    # ------------------------------------------------------------ Kapitel 2 · Stahl gegen Stahl
    t = T.t
    T.mood(t, "steel")
    T.add(ChapterCard(2, "Stahl gegen Stahl", "April – Juli 1918", t + 0.3, 5.0))
    T.cam(t + 6.0, Cam(49.865, 2.53, 14, 50, 80))
    T.wait(5.6)
    s = T.say("vb_angriff", pre=0.3, post=2.0)
    T.say("panzerduell", pre=0.4, post=2.0)
    T.say("anzac", pre=0.4, post=2.0)
    k = "vb_angriff"
    T.add(DateStamp("24. April 1918", "Villers-Bretonneux", s, T.end("anzac")))
    T.add(Label(*P["vb"], "Villers-Bretonneux", t0=s, t1=T.end("anzac") + 1.0, size=24))
    T.add(Label(*P["cachy"], "Cachy", t0=s, t1=T.end("panzerduell") + 1.0, size=20))
    T.add(A.Fog(s - 0.5, w(k, 20.0), strength=0.45))
    T.add(GasCloud([(49.885, 2.505), (49.885, 2.535), (49.855, 2.540), (49.852, 2.505)], w(k, 14.8), w(k, 26.0), n=30))
    a7v = tanks(A.TankGroup("de", "a7v", 13, [(w(k, 8.0), 49.872, 2.565), (w(k, 21.0), 49.868, 2.520), (w(k, 27.0), 49.862, 2.505)],
                            spacing=160, seed=31, fire=[(w(k, 14.0), w(k, 27.0))], t1=T.end("panzerduell") - 1.0))
    ger = [U("de", 2600, [(w(k, 9.0), 49.874, 2.572), (w(k, 21.5), 49.868, 2.522)], facing=268, area=40, aspect=3.0,
             losses=[(w(k, 17.0), 300)], fire=[(w(k, 15.0), w(k, 22.0))], seed=301),
           U("de", 2200, [(w(k, 9.4), 49.858, 2.568), (w(k, 21.8), 49.856, 2.520)], facing=272, area=40, aspect=3.0,
             losses=[(w(k, 17.4), 250)], fire=[(w(k, 15.0), w(k, 22.0))], seed=302)]
    brit = [U("gb", 2200, [(s, 49.870, 2.538), (w(k, 19.6), 49.870, 2.538), (w(k, 23.0), 49.866, 2.500)], facing=88, area=40,
              aspect=3.0, losses=[(w(k, 16.5), 500)], fire=[(w(k, 15.0), w(k, 22.0))], seed=303)]
    troops(ger + brit, T.end("anzac") - 2.0, [(0, 2), (1, 2)])
    front.states.append((w(k, 19.6), w(k, 23.0), local_line("apr24")))
    T.add(Token(49.880, 2.560, [DE], [(0, 13)], label="A7V", side="de", unit=" Panzer", t0=w(k, 8.6), t1=w(k, 26.0), dy=-60))
    T.add(Pulse(*P["amiens"], w(k, 23.6), w(k, 27.0), r=34))
    T.cam(w(k, 22.8), Cam(49.875, 2.44, 22, 45, 80))
    T.add(Label(*P["amiens"], "Amiens", t0=w(k, 23.0), t1=w(k, 27.0), size=26))

    k = "panzerduell"
    T.cam(w(k, 0.2), Cam(49.857, 2.507, 2.4, 56, 85))
    duel_de = tanks(A.TankGroup("de", "a7v", 3, [(s, 49.862, 2.524), (w(k, 4.0), 49.858, 2.518), (w(k, 12.0), 49.856, 2.512),
                                                 (w(k, 30.0), 49.856, 2.512)], spacing=220, seed=41,
                                losses=[(w(k, 23.0), 1)], fire=[(w(k, 9.0), w(k, 25.0))], t1=T.end("anzac")))
    duel_gb = tanks(A.TankGroup("gb", "mk4", 3, [(w(k, 3.5), 49.852, 2.492), (w(k, 12.0), 49.854, 2.500), (w(k, 30.0), 49.854, 2.500)],
                                spacing=200, seed=42, losses=[(w(k, 14.0), 2)], fire=[(w(k, 9.0), w(k, 25.0))], t1=T.end("anzac")))
    whip = tanks(A.TankGroup("gb", "whippet", 7, [(w(k, 25.5), 49.846, 2.488), (w(k, 31.0), 49.850, 2.512),
                                                  (w(k, 40.0), 49.852, 2.520)], spacing=120, seed=43,
                             losses=[(w(k, 29.5), 4)], fire=[(w(k, 27.0), w(k, 33.0))], t1=T.end("anzac")))
    T.add(Token(49.860, 2.524, [DE], [(0, 3)], label="A7V", side="de", unit=" Panzer", t0=w(k, 7.8), t1=w(k, 26.0), dy=-50))
    T.add(Token(49.851, 2.495, [GB], [(0, 3)], label="Mark IV", side="al", unit=" Panzer", t0=w(k, 4.3), t1=w(k, 26.0), dy=60))
    T.add(BigWord("PANZER GEGEN PANZER", w(k, 12.6), w(k, 16.5), y=0.20, color=E.hexc("#f2e2b8"), size=64))
    T.add(Caption([([GB], "Leutnant Frank Mitchell, Mark IV"), ([DE], "A7V „Nixe“ getroffen und aufgegeben")], w(k, 15.4),
                  w(k, 25.5), pos="br", width=600))
    T.add(Token(49.846, 2.490, [GB], [(0, 7)], label="Whippets", side="al", unit=" Panzer", t0=w(k, 26.6), t1=T.end(k) + 1.0, dy=60))
    T.cam(w(k, 25.0), Cam(49.852, 2.505, 3.5, 55, 85))

    k = "anzac"
    T.add(A.NightTint(w(k, -1.0), w(k, 12.5), strength=0.8, fin=2.0, fout=2.5))
    T.cam(w(k, 0.0), Cam(49.866, 2.52, 9.0, 50, 80))
    aus = [U("au", 1800, [(w(k, 2.5), 49.890, 2.470), (w(k, 7.2), 49.888, 2.520), (w(k, 11.0), 49.882, 2.548)], facing=110,
             area=40, aspect=3.0, losses=[(w(k, 8.0), 260)], fire=[(w(k, 7.0), w(k, 11.0))], seed=311),
           U("au", 1800, [(w(k, 2.7), 49.845, 2.478), (w(k, 7.4), 49.848, 2.525), (w(k, 11.0), 49.856, 2.552)], facing=70,
             area=40, aspect=3.0, losses=[(w(k, 8.2), 280)], fire=[(w(k, 7.0), w(k, 11.0))], seed=312)]
    T.add(Arrow([(49.892, 2.460), (49.892, 2.515), (49.880, 2.550)], "al", t0=w(k, 7.0), grow=2.4, t1=w(k, 18.0), width=12))
    T.add(Arrow([(49.842, 2.470), (49.846, 2.522), (49.858, 2.552)], "al", t0=w(k, 9.2), grow=2.4, t1=w(k, 18.0), width=12))
    T.add(Token(49.895, 2.46, [AU], [(0, 0)], label="13. und 15. Brigade", side="al", t0=w(k, 3.0), t1=w(k, 16.0), dy=-50))
    troops(aus, T.end(k) + 1.0, [])
    front.states.append((w(k, 10.0), w(k, 13.5), local_line("apr04")))
    T.add(Caption([([AU], "Anzac Day, 25. April 1918"), (None, "drei Jahre nach der Landung bei Gallipoli")], w(k, 15.0),
                  w(k, 21.5), pos="br", width=580))
    T.cam(w(k, 21.0), Cam(49.8687, 2.5185, 2.2, 52, 80))
    T.add(Quote(["N’oublions jamais l’Australie.“", "(Vergessen wir Australien nie.)"], "Inschrift in der Schule von Villers-Bretonneux",
                w(k, 23.0), T.end(k) + 1.8, size=44))

    # ------------------------------------------------------------ Le Hamel
    s = T.say("hamel", pre=0.5, post=2.0)
    k = "hamel"
    T.add(DateStamp("4. Juli 1918", "Le Hamel", s, T.end(k)))
    T.cam(s - 0.4, Cam(49.895, 2.565, 6.0, 52, 82))
    T.add(Label(*P["hamel"], "Le Hamel", t0=s, t1=T.end(k) + 1.0, size=24))
    T.add(Caption([([AU], "General John Monash"), (None, "Australisches Korps")], w(k, 2.6), w(k, 9.0), pos="br", width=480))
    t_go = w(k, 8.0)
    tanks(A.TankGroup("au", "mk5", 60, [(t_go, 49.893, 2.548), (t_go + 14, 49.902, 2.592), (w(k, 40), 49.903, 2.596)], spacing=70,
                      rows=2, row_gap=90, seed=51, losses=[(t_go + 10, 3)], fire=[(t_go + 4, t_go + 16)], t1=T.end(k) + 1.0))
    T.add(Barrage(line_keys=[(t_go, [(49.915, 2.565), (49.880, 2.562)]), (t_go + 14, [(49.918, 2.602), (49.884, 2.600)])],
                  t0=t_go, t1=t_go + 15, rate=40, seed=52))
    ham = [U("au", 3000, [(t_go, 49.890, 2.545), (t_go + 14, 49.898, 2.588)], facing=78, area=40, aspect=3.2,
             losses=[(t_go + 8, 200)], fire=[(t_go + 5, t_go + 15)], seed=321),
           U("us", 1000, [(t_go, 49.902, 2.548), (t_go + 14, 49.908, 2.588)], facing=78, area=40, aspect=3.2,
             losses=[(t_go + 8, 60)], fire=[(t_go + 5, t_go + 15)], seed=322),
           U("de", 2000, [(s, 49.902, 2.588), (t_go + 9, 49.902, 2.588), (t_go + 16, 49.905, 2.620)], facing=258, area=40,
             aspect=3.0, losses=[(t_go + 9, 700)], fire=[(t_go + 5, t_go + 15)], seed=323)]
    troops(ham, T.end(k) + 1.0, [(0, 2), (1, 2)])
    drops = {i: [(w(k, 21.0) + i * 0.3, 49.896 + 0.002 * (i % 3), 2.578 + 0.003 * i)] for i in range(4)}
    T.add(A.AirWar(squad("dh9", "gb", 4, w(k, 18.5), w(k, 28.0), (49.875, 2.520), (49.920, 2.630), alt=300, spread=160, seed=53,
                         drops=drops), w(k, 18.0), w(k, 29.0)))
    T.add(A.Parachutes([(w(k, 21.4) + i * 0.35, 49.895 + 0.002 * (i % 4), 2.575 + 0.0025 * i) for i in range(10)], alt=260))
    T.add(Token(49.890, 2.540, [AU], [(0, 0)], label="ca. 60 Mark V", side="al", t0=w(k, 14.2), t1=w(k, 22.0), dy=60))
    T.add(Token(49.908, 2.550, [US], [(0, 1000)], label="erste US-Einheiten", side="al", t0=w(k, 24.4), t1=T.end(k), dy=-50))
    T.add(BigWord("93 MINUTEN", w(k, 27.0), w(k, 31.5), y=0.22, color=E.hexc("#f2e2b8"), size=72))
    front.states.append((t_go + 4, t_go + 15, local_line("jul04")))

    # ------------------------------------------------------------ Marne
    s = T.say("marne", pre=0.5, post=2.6)
    k = "marne"
    T.cam(s - 0.5, Cam(49.20, 3.40, 380, 0, 0))
    wfront.states.append((s - 1.0, s, G.WF["jul15"]))
    T.add(Label(49.05, 3.55, "Marne", "15. Juli", t0=w(k, 1.8), t1=w(k, 12.0), size=24))
    T.add(Battle(49.10, 3.55, 25, w(k, 2.0), w(k, 6.0), rate=6, intensity=0.9))
    for pts in ([(49.25, 2.95), (49.30, 3.25)], [(49.10, 3.05), (49.20, 3.35)], [(49.00, 3.30), (49.15, 3.55)]):
        T.add(Arrow(pts, "al", t0=w(k, 6.5), grow=1.8, t1=w(k, 16.0), width=12))
    T.add(Token(49.05, 2.95, [FR, US], [(0, 0)], label="18. Juli: Gegenangriff mit Hunderten Panzern", side="al", t0=w(k, 6.5),
                t1=w(k, 15.0), dy=50))
    wfront.states.append((w(k, 8.0), w(k, 14.0), G.WF["aug07"]))
    T.add(Caption([([FR], "Ferdinand Foch"), (None, "6. August 1918: Marschall von Frankreich")], w(k, 15.6), w(k, 22.0), pos="br",
                  width=520))
    T.cam(w(k, 22.0), Cam(49.87, 2.62, 110, 10, 60))
    T.add(Pulse(*P["amiens"], w(k, 24.0), T.end(k) + 2.0, r=40))

    # ------------------------------------------------------------ Kapitel 3 · Der Plan
    t = T.t
    T.mood(t, "plan")
    T.add(ChapterCard(3, "Der Plan", "Juli – August 1918", t + 0.3, 5.0))
    T.cam(t + 6.0, Cam(49.86, 2.62, 42, 30, 80))
    T.wait(5.6)
    s = T.say("plan", pre=0.3, post=2.0)
    T.say("geheim", pre=0.4, post=2.0)
    T.say("aufmarsch", pre=0.4, post=2.4)
    k = "plan"
    T.add(Caption([([GB], "General Sir Henry Rawlinson"), (None, "britische 4. Armee")], w(k, 2.0), w(k, 8.5), pos="br", width=500))
    T.add(MeasureLineSafe((49.930, 2.590), (49.800, 2.505), "ca. 20 km", w(k, 6.6), w(k, 12.0)))
    T.add(Label(*G.SOMME_LABEL, "SOMME", t0=w(k, 8.8), t1=T.end(k) + 1.0, size=22, style="sea", dot=False))
    T.add(Label(49.815, 2.47, "LUCE", t0=w(k, 10.2), t1=T.end(k) + 1.0, size=20, style="sea", dot=False))
    T.add(Token(49.955, 2.560, [GB], [(0, 0)], label="III. Korps", side="al", t0=w(k, 13.3), t1=T.end("aufmarsch"), dy=-40))
    T.add(Token(49.880, 2.530, [AU], [(0, 0)], label="Australier · Monash", side="al", t0=w(k, 16.6), t1=T.end("aufmarsch"), dy=-40))
    T.add(Token(49.835, 2.490, [CA], [(0, 0)], label="Kanadier · Currie", side="al", t0=w(k, 19.2), t1=T.end("aufmarsch"), dy=-40))
    T.add(Token(49.730, 2.480, [FR], [(0, 0)], label="1. Armee · Debeney", side="al", t0=w(k, 22.3), t1=T.end("aufmarsch"), dy=-40))
    for pts, t_ in (([(49.955, 2.585), (49.950, 2.66)], 13.6), ([(49.885, 2.565), (49.875, 2.70)], 16.8),
                    ([(49.835, 2.535), (49.810, 2.68)], 19.5), ([(49.740, 2.520), (49.735, 2.62)], 23.6)):
        T.add(Arrow(pts, "al", t0=w(k, t_), grow=1.8, t1=T.end(k) + 1.0, width=12, dashed=True))

    k = "geheim"
    T.add(A.NightTint(w(k, 2.0), w(k, 21.0), strength=0.6, fin=2.0, fout=2.0))
    T.cam(w(k, 1.5), Cam(50.10, 2.55, 140, 0, 0))
    T.add(Label(*P["arras"], "Arras", t0=w(k, 9.5), t1=w(k, 21.0), size=22))
    T.add(Convoy(G.CANADA_MOVE, w(k, 6.4), w(k, 20.0), spacing_km=2.2, speed_kmps=6.0))
    T.add(Token(50.25, 2.40, [CA], [(0, 100000)], label="kanadisches Korps, nachts verlegt", side="al", t0=w(k, 3.2), t1=w(k, 14.0), dy=-40))
    T.cam(w(k, 12.4), Cam(50.40, 2.75, 260, 0, 0))
    T.add(Label(*P["kemmel"], "Kemmel (Flandern)", t0=w(k, 13.0), t1=w(k, 22.0), size=22))
    for i in range(5):
        T.add(Pulse(*P["kemmel"], w(k, 15.8) + i * 1.0, w(k, 17.0) + i * 1.0, color=E.hexc("#9fd0ff"), r=30 + i * 8))
    T.add(Token(50.82, 2.55, [CA], [(0, 0)], label="2 Bataillone + Funk: Täuschung", side="al", t0=w(k, 14.0), t1=w(k, 22.0), dy=-40))
    T.add(Quote(["KEEP YOUR MOUTH SHUT!“", "(Halt den Mund!)"], "Zettel in den Soldbüchern", w(k, 21.8), w(k, 27.0), size=48))
    T.cam(w(k, 26.0), Cam(49.86, 2.60, 30, 46, 80))

    k = "aufmarsch"
    T.add(A.NightTint(w(k, 22.0), T.end(k) + 6.0, strength=0.65, fin=2.0, fout=3.0))
    guns_al = [(49.90 - i * 0.012, 2.505 + (i % 3) * 0.006) for i in range(16)]
    T.add(Guns(guns_al, "al", w(k, 2.8), T.end("angriff") + 4.0, facing=90, fire=[(w("angriff", 7.5), w("angriff", 26.0))], seed=61))
    T.add(Token(49.90, 2.48, [GB, FR], [(0, 2000)], label="Geschütze", side="al", unit="+", t0=w(k, 3.2), t1=w(k, 13.0), dy=-50))
    T.add(Token(49.86, 2.50, [GB, AU, CA], [(0, 534)], label="Mark V · Whippet · Versorgung", side="al", unit=" Panzer",
                t0=w(k, 5.3), t1=w(k, 13.5), dy=60))
    T.add(Token(49.95, 2.50, [GB, FR], [(0, 1900)], label="Flugzeuge (ca. 800 brit. + 1.100 franz.)", side="al", t0=w(k, 14.4),
                t1=w(k, 22.5), dy=-50))
    T.add(Token(49.95, 2.78, [DE], [(0, 365)], label="deutsche Flugzeuge", side="de", t0=w(k, 19.8), t1=w(k, 22.5), dy=-50))
    T.add(A.AirWar(squad("camel", "gb", 9, w(k, 14.0), w(k, 24.0), (49.80, 2.40), (49.97, 2.62), alt=900, seed=61)
                   + squad("spad", "fr", 7, w(k, 15.4), w(k, 24.0), (49.74, 2.40), (49.90, 2.66), alt=1000, seed=62)
                   + squad("dh9", "gb", 2, w(k, 26.8), w(k, 33.0), (49.80, 2.46), (49.92, 2.60), alt=250, spread=500, seed=63),
                   w(k, 14.0), T.end(k) + 2.0))
    T.cam(w(k, 23.0), Cam(49.86, 2.545, 9.0, 52, 82))

    # Panzer: 1 Modell = 1 Panzer, sie rollen in der Nacht an die Ausgangslinie und am 8. August vor
    tg = w(k, 24.6)                    # Anfahrt in der Nacht
    ta = None                          # Angriff (wird unten gesetzt)

    # ------------------------------------------------------------ Kapitel 4 · 8. August 1918
    t = T.t
    T.mood(t, "battle")
    T.add(ChapterCard(4, "8. August 1918", "Der schwarze Tag", t + 0.3, 5.0))
    T.cam(t + 6.0, Cam(49.855, 2.56, 12, 52, 84))
    T.wait(5.6)
    s = T.say("angriff", pre=0.3, post=2.0)
    for key in ("kanadier", "australier", "musical_box", "luftschlacht", "chipilly", "schwarzer_tag"):
        T.say(key, pre=0.4, post=2.0 if key != "schwarzer_tag" else 3.0)
    k = "angriff"
    ta = w(k, 11.6)
    T.add(DateStamp("8. August 1918", "4:20 Uhr", s, w(k, 20.0)))
    T.add(A.Fog(s - 2.0, w("kanadier", 14.0), strength=0.6, fin=2.0, fout=5.0))
    T.add(Barrage(line_keys=[(w(k, 7.5), local_line("jul04")[60:160] + np.array([0.0, 0.004])),
                             (w(k, 28.0), local_line("jul04")[60:160] + np.array([0.0, 0.040])),
                             (w("kanadier", 20.0), local_line("aug08")[50:150] - np.array([0.0, 0.006]))],
                  t0=w(k, 7.5), t1=w("kanadier", 20.0), rate=60, seed=71, depth_km=0.35))
    T.add(Barrage([(49.92, 2.70), (49.92, 2.80), (49.80, 2.78), (49.80, 2.68)], w(k, 23.5), w(k, 29.0), rate=18, seed=72, size=1.2))
    T.add(Burning([(49.905, 2.62), (49.905, 2.70), (49.80, 2.70), (49.80, 2.60)], w(k, 10.0), T.end("schwarzer_tag") + 10, n=40,
                  ramp=40.0, seed=73))
    T.cam(w(k, 6.0), Cam(49.862, 2.565, 7.0, 53, 84))
    T.cam(w(k, 17.0), Cam(49.858, 2.58, 4.0, 55, 86))
    # Panzer der vier Sektoren: Mark V (Kanadier, Australier), Mark V* (trägt MG-Trupps), Whippets, Versorgungspanzer
    secs = [("ca", (49.842, 2.535), (49.800, 2.650), 1.0), ("ca", (49.830, 2.520), (49.785, 2.630), 1.0),
            ("au", (49.885, 2.566), (49.885, 2.690), 1.0), ("au", (49.870, 2.556), (49.860, 2.690), 1.0),
            ("gb", (49.940, 2.592), (49.930, 2.640), 0.5)]
    lines = {"ca": "jul04", "au": "jul04", "gb": "jul04"}
    for i, (nat, a, b, depth) in enumerate(secs):
        start = (a[0], a[1] - 0.030)
        n_heavy = [62, 62, 66, 66, 40][i]
        tanks(A.TankGroup(nat, "mk5", n_heavy, [(tg, start[0], start[1]), (tg + 6, a[0], a[1] - 0.004), (ta, a[0], a[1]),
                                                 (ta + 40, lerp(a, b, 0.55)[0], lerp(a, b, 0.55)[1]),
                                                 (w("australier", 22.0), b[0], b[1])],
                          spacing=68, rows=2, row_gap=110, seed=80 + i, losses=[(ta + 16, 4), (w("kanadier", 10.0), 5)],
                          breakdowns=[(ta + 8, 5), (w("australier", 4.0), 4)], fire=[(ta + 3, w("australier", 20.0))],
                          t1=T.end("bilanz_amiens") + 1.0))
    for i, (nat, a, b) in enumerate((("ca", (49.828, 2.515), (49.790, 2.660)), ("au", (49.868, 2.548), (49.855, 2.700)))):
        tanks(A.TankGroup(nat, "mk5s", 24, [(tg + 2, a[0], a[1] - 0.034), (ta + 2, a[0], a[1] - 0.006),
                                              (w("kanadier", 12.0), lerp(a, b, 0.6)[0], lerp(a, b, 0.6)[1]),
                                              (w("australier", 22.0), b[0], b[1])], spacing=60, rows=2, seed=90 + i,
                          losses=[(w("kanadier", 6.0), 3)], breakdowns=[(ta + 12, 2)], fire=[(ta + 6, w("australier", 18.0))],
                          t1=T.end("bilanz_amiens") + 1.0))
    for i, (nat, a, b) in enumerate((("ca", (49.825, 2.505), (49.785, 2.670)), ("au", (49.862, 2.540), (49.850, 2.710)))):
        tanks(A.TankGroup(nat, "whippet", 36, [(tg + 3, a[0], a[1] - 0.030), (w("kanadier", 14.0), a[0], a[1]),
                                                 (w("kanadier", 24.0), lerp(a, b, 0.7)[0], lerp(a, b, 0.7)[1]),
                                                 (w("australier", 22.0), b[0], b[1])], spacing=70, rows=2, seed=95 + i,
                          losses=[(w("kanadier", 22.0), 5)], breakdowns=[(w("kanadier", 18.0), 3)],
                          fire=[(w("kanadier", 15.0), w("australier", 20.0))], t1=T.end("bilanz_amiens") + 1.0))
    for i, (nat, a, b) in enumerate((("ca", (49.832, 2.500), (49.800, 2.600)), ("au", (49.875, 2.535), (49.868, 2.640)))):
        tanks(A.TankGroup(nat, "supply", 60, [(tg + 4, a[0], a[1] - 0.026), (ta + 20, a[0], a[1]),
                                                (w("australier", 22.0), b[0], b[1])], spacing=55, rows=3, row_gap=60, seed=99 + i,
                          breakdowns=[(ta + 30, 4)], t1=T.end("bilanz_amiens") + 1.0))
    T.add(Token(49.835, 2.47, [CA, AU, GB], [(0, 534)], label="Panzer im Einsatz (1 Modell = 1 Panzer)", side="al", unit="",
                t0=w(k, 17.8), t1=w(k, 27.0), dy=60))

    # Infanterie: Wellen hinter der Feuerwalze; deutsche Verteidiger
    inf = []
    for i, (nat, a, b) in enumerate((("ca", (49.840, 2.530), (49.800, 2.645)), ("ca", (49.825, 2.512), (49.783, 2.625)),
                                     ("au", (49.887, 2.566), (49.886, 2.685)), ("au", (49.870, 2.555), (49.858, 2.685)),
                                     ("gb", (49.945, 2.595), (49.935, 2.628)))):
        inf.append(U(nat, 4000, [(ta, a[0], a[1]), (w("kanadier", 18.0), lerp(a, b, 0.6)[0], lerp(a, b, 0.6)[1]),
                                 (w("australier", 22.0), b[0], b[1])], facing=96, area=40, aspect=3.5,
                     losses=[(ta + 6, 180), (w("kanadier", 8.0), 160)], fire=[(ta + 3, w("australier", 20.0))], seed=400 + i))
    gde = []
    for i, la in enumerate((49.94, 49.89, 49.865, 49.84, 49.82)):
        p0 = anchor("jul04", (la, 2.58), "de", 0.6)
        p1 = anchor("aug08", (la, 2.68), "de", 1.2)
        gde.append(U("de", 3000, [(s, p0[0], p0[1]), (ta + 6, p0[0], p0[1]), (w("australier", 12.0), p1[0], p1[1])], facing=268,
                     area=40, aspect=3.0, losses=[(ta + 5, 900), (w("kanadier", 6.0), 700)], fire=[(ta, w("kanadier", 20.0))],
                     seed=420 + i))
    troops(inf + gde, T.end("bilanz_amiens") + 1.0, [(0, 8), (1, 9), (2, 6), (3, 7), (4, 5)])
    front.states.append((ta + 2, w("australier", 22.0), local_line("aug08")))
    wfront.states.append((ta + 2, w("australier", 22.0), G.WF["aug07"]))

    k = "kanadier"
    T.cam(w(k, 0.0), Cam(49.815, 2.56, 9.0, 52, 84))
    for nm, t_ in (("hangard", 3.6), ("demuin", 4.6), ("beaucourt", 5.3), ("le_quesnel", 19.5)):
        T.add(Label(*P[nm], {"hangard": "Hangard", "demuin": "Demuin", "beaucourt": "Beaucourt", "le_quesnel": "Le Quesnel"}[nm],
                    t0=w(k, t_), t1=T.end(k) + 1.0, size=22))
    T.add(Token(49.832, 2.47, [CA], [(0, 0)], label="kanadisches Korps", side="al", t0=w(k, 1.2), t1=w(k, 13.0), dy=-50))
    cav = [U("ca", 1400, [(w(k, 14.0), 49.820, 2.540), (w(k, 22.0), 49.800, 2.630)], facing=100, area=60, aspect=4.0,
             losses=[(w(k, 20.0), 120)], seed=440)]
    troops(cav, T.end(k) + 6.0)
    T.add(Caption([([CA], "Vorstoß am ersten Tag: rund 13 km"), (None, "Rekord an der Westfront seit 1914")], w(k, 19.6), T.end(k) + 0.8,
                  pos="br", width=560))
    T.add(MeasureLineSafe((49.830, 2.512), (49.790, 2.650), "ca. 13 km", w(k, 20.0), T.end(k) + 0.5))
    T.cam(w(k, 17.0), Cam(49.80, 2.60, 14, 48, 84))

    k = "australier"
    T.cam(w(k, 0.0), Cam(49.870, 2.62, 9.5, 52, 84))
    for nm, lbl, t_ in (("warfusee", "Warfusée", 9.0), ("bayonvillers", "Bayonvillers", 10.0), ("harbonnieres", "Harbonnières", 11.0)):
        T.add(Label(*P[nm], lbl, t0=w(k, t_), t1=T.end(k) + 2.0, size=22))
    T.add(Token(49.890, 2.55, [AU], [(0, 0)], label="Australisches Korps", side="al", t0=w(k, 1.0), t1=w(k, 9.0), dy=-50))
    T.add(Label(49.858, 2.685, "Eisenbahngeschütz erbeutet", t0=w(k, 17.2), t1=T.end(k) + 1.5, size=20))
    T.add(Pulse(49.858, 2.685, w(k, 17.2), w(k, 21.0), r=26))
    T.add(MeasureLineSafe((49.880, 2.560), (49.880, 2.690), "ca. 11 km", w(k, 20.8), T.end(k) + 0.8))
    T.cam(w(k, 14.0), Cam(49.862, 2.66, 7.0, 52, 84))

    k = "musical_box"
    T.cam(w(k, 0.0), Cam(49.852, 2.630, 8.0, 52, 84))
    mb = A.TankGroup("gb", "whippet", 1, [(w(k, 3.0) + 3.3 * i, la, lo) for i, (la, lo) in enumerate(G.MUSICAL_BOX)], spacing=1,
                     seed=111, losses=[(w(k, 19.6), 1)], fire=[(w(k, 12.0), w(k, 19.0))], lag=0.0, t1=T.end("bilanz_amiens") + 1.0)
    tanks(mb)
    T.add(Polyline(G.MUSICAL_BOX, E.hexc("#ffd27a"), t0=w(k, 3.0), t1=T.end(k) + 1.0, width=3, grow=20.0, dash=(10, 7)))
    T.add(Token(G.MUSICAL_BOX[0][0], G.MUSICAL_BOX[0][1], [GB], [(0, 3)], label="„Musical Box“ · Lt. Arnold", side="al", unit=" Mann",
                t0=w(k, 3.2), t1=w(k, 12.0), dy=-50))
    for i, (la, lo) in enumerate(G.MUSICAL_BOX[2:6]):
        T.add(Explosion(la + 0.002, lo + 0.003, w(k, 13.5) + i * 1.3, size=0.8))
    T.add(Caption([(None, "rund 9 Stunden allein hinter den deutschen Linien"), ([GB], "1 Mann fällt, 2 geraten in Gefangenschaft")],
                  w(k, 11.5), T.end(k) + 0.8, pos="br", width=620))
    T.cam(w(k, 16.0), Cam(49.848, 2.680, 4.0, 54, 84))

    k = "luftschlacht"
    T.cam(w(k, 0.0), Cam(49.88, 2.75, 28, 46, 84))
    T.mood(w(k, -0.4), "air")
    fight2 = (w(k, 15.5), w(k, 26.0), 49.88, 2.86, 2200, 20)
    strafers = squad("camel", "gb", 10, w(k, 3.0), w(k, 13.0), (49.84, 2.62), (49.92, 2.86), alt=250, spread=180, seed=121)
    bombers = squad("dh9", "gb", 8, w(k, 9.5), w(k, 27.0), (49.80, 2.66), (49.90, 2.98), alt=900, spread=220, circles=fight2, seed=122,
                    shot={2: w(k, 18.5), 5: w(k, 22.0)}, drops={i: [(w(k, 13.0) + i * 0.4, *G.BRIDGES[i % 4])] for i in range(8)})
    fokkers = squad("fokker", "de", 9, w(k, 15.0), w(k, 28.0), (49.98, 3.05), (49.82, 2.80), alt=1000, spread=160, circles=fight2,
                    seed=123, shot={1: w(k, 20.0)})
    escorts = squad("se5", "gb", 6, w(k, 10.0), w(k, 28.0), (49.82, 2.66), (49.92, 2.98), alt=1100, spread=200, circles=fight2,
                    seed=124, shot={0: w(k, 24.0), 3: w(k, 25.5)})
    T.add(A.AirWar(strafers + bombers + fokkers + escorts, w(k, 2.5), T.end(k) + 2.0, fights=[(w(k, 15.5), w(k, 27.0))]))
    for i, br in enumerate(G.BRIDGES):
        T.add(Explosion(br[0] + 0.004, br[1] - 0.006, w(k, 15.2) + i * 0.6, size=1.0))
    T.add(Label(*P["peronne"], "Péronne", "Somme-Brücken", t0=w(k, 11.0), t1=T.end(k) + 1.0, size=22))
    T.cam(w(k, 9.5), Cam(49.88, 2.86, 34, 44, 84))
    T.add(Token(49.95, 2.72, [GB], [(0, 0), (w(k, 23.0), 0), (w(k, 26.0), 97)], label="RAF: Verluste am 8. August", side="al",
                unit=" Flugzeuge", t0=w(k, 21.5), t1=T.end(k) + 1.0, dy=-50))

    k = "chipilly"
    T.cam(w(k, 0.0), Cam(49.915, 2.63, 6.0, 54, 84))
    T.add(Label(*P["chipilly"], "Chipilly-Rücken", t0=w(k, 5.2), t1=T.end("tag9") + 1.0, size=24))
    mg = [U("de", 900, [(s, 49.913, 2.652)], facing=200, area=30, aspect=2.0, fire=[(w(k, 10.0), w("tag9", 17.0))], seed=450)]
    troops(mg, T.end("tag9"))
    T.add(ShellArcs((49.913, 2.652), (49.898, 2.640), w(k, 11.0), w(k, 16.0), every=0.5, flight=0.8, height=40, size=0.6))
    T.cam(w(k, 15.2), Cam(49.72, 2.58, 26, 44, 84))
    T.add(Token(49.72, 2.50, [FR], [(0, 0)], label="französische 1. Armee", side="al", t0=w(k, 16.0), t1=T.end(k) + 1.0, dy=-50))
    T.add(Barrage([(49.76, 2.52), (49.76, 2.56), (49.68, 2.57), (49.68, 2.54)], w(k, 17.6), w(k, 21.0), rate=30, seed=91))
    fr_inf = [U("fr", 4000, [(w(k, 20.5), 49.755, 2.520), (T.end(k), 49.745, 2.585)], facing=100, area=40, aspect=3.5,
                losses=[(w(k, 22.0), 250)], fire=[(w(k, 20.5), T.end(k))], seed=460),
              U("fr", 4000, [(w(k, 20.8), 49.715, 2.540), (T.end(k), 49.705, 2.575)], facing=100, area=40, aspect=3.5,
                losses=[(w(k, 22.3), 250)], fire=[(w(k, 20.5), T.end(k))], seed=461)]
    troops(fr_inf, T.end("tag10") + 1.0)

    k = "schwarzer_tag"
    T.add(Tint(skia.Color4f(0.25, 0.10, 0.04, 0.22), w(k, -0.5), T.end(k) + 2.0, fin=1.5, fout=1.5))
    T.cam(w(k, 0.0), Cam(49.83, 2.62, 40, 36, 82))
    T.add(MeasureLineSafe((49.938, 2.632), (49.776, 2.612), "über 20 km", w(k, 3.2), w(k, 8.0)))
    T.add(Token(49.86, 2.76, [DE], [(w(k, 8.6), 0), (w(k, 10.4), 27000)], label="deutsche Verluste am 8. August", side="de", unit="",
                t0=w(k, 8.4), t1=w(k, 18.0), dy=-50))
    T.add(Caption([([DE], "rund 27.000 Mann verloren"), (None, "darunter mehr als 12.000 Gefangene"), (None, "rund 400 Geschütze")],
                  w(k, 9.0), w(k, 18.5), pos="br", width=520, title="8. August 1918"))
    pris = [U("de", 3000, [(w(k, 12.0), 49.850, 2.660), (w(k, 26.0), 49.855, 2.560)], facing=270, area=25, aspect=1.2, seed=470),
            U("de", 3000, [(w(k, 12.4), 49.815, 2.640), (w(k, 26.0), 49.825, 2.540)], facing=270, area=25, aspect=1.2, seed=471)]
    for u in pris:
        u.nation = "de"
    troops(pris, T.end(k) + 1.0)
    T.add(Quote(["Der 8. August ist der schwarze Tag", "des deutschen Heeres in der Geschichte dieses Krieges.“"],
                "Erich Ludendorff, Kriegserinnerungen", w(k, 19.5), T.end(k) + 2.6, size=42))

    # ------------------------------------------------------------ Kapitel 5 · Die Tage danach
    t = T.t
    T.mood(t, "after")
    T.add(ChapterCard(5, "Die Tage danach", "9. – 11. August 1918", t + 0.3, 5.0))
    T.cam(t + 6.0, Cam(49.85, 2.70, 30, 42, 82))
    T.wait(5.6)
    s = T.say("tag9", pre=0.3, post=2.0)
    for key in ("tag10", "tag11", "bilanz_amiens"):
        T.say(key, pre=0.4, post=2.4)
    k = "tag9"
    T.add(DateStamp("9. August 1918", "Die Überraschung ist vorbei", s, T.end(k)))
    for la in (49.95, 49.88, 49.83, 49.78):
        T.add(Arrow([(la, 2.95), (la, 2.78)], "de", t0=w(k, 5.5), grow=1.6, t1=w(k, 11.0), width=11))
    T.cam(w(k, 10.5), Cam(49.915, 2.645, 5.0, 54, 84))
    us = [U("us", 1500, [(w(k, 12.0), 49.930, 2.615), (w(k, 19.0), 49.915, 2.650)], facing=120, area=40, aspect=3.0,
            losses=[(w(k, 16.0), 120)], fire=[(w(k, 14.0), w(k, 19.0))], seed=480),
          U("gb", 1500, [(w(k, 12.4), 49.940, 2.628), (w(k, 19.0), 49.925, 2.660)], facing=120, area=40, aspect=3.0,
            losses=[(w(k, 16.4), 120)], fire=[(w(k, 14.0), w(k, 19.0))], seed=481)]
    troops(us, T.end("bilanz_amiens"))
    T.add(Token(49.935, 2.60, [US], [(0, 0)], label="131. US-Infanterieregiment (33. Division)", side="al", t0=w(k, 12.4),
                t1=w(k, 19.5), dy=-50))
    front.states.append((w(k, 15.0), w(k, 22.0), local_line("aug09")))
    T.cam(w(k, 19.5), Cam(49.83, 2.70, 18, 46, 84))
    T.add(Token(49.80, 2.62, [CA, AU, GB], [(w(k, 19.5), 415), (w(k, 25.0), 145)], label="einsatzbereite Kampfpanzer", side="al",
                unit="", t0=w(k, 19.6), t1=T.end("tag11") - 2.0, dy=60))

    k = "tag10"
    T.cam(w(k, 0.0), Cam(49.66, 2.62, 16, 46, 84))
    T.add(Label(*P["montdidier"], "Montdidier", t0=w(k, 2.3), t1=w(k, 9.0), size=26))
    T.add(Token(49.655, 2.52, [FR], [(0, 0)], label="Franzosen rücken ein", side="al", t0=w(k, 2.6), t1=w(k, 9.0), dy=-50))
    front.states.append((w(k, 2.0), w(k, 9.0), local_line("aug10")))
    T.cam(w(k, 13.5), Cam(49.84, 2.76, 7.0, 54, 84))
    T.add(CraterField([(G.ZONES["somme1916"], w(k, 14.5), w(k, 20.0))], w(k, 14.5), T.end("bilanz_amiens") + 2.0, strength=0.65))
    T.add(Label(*P["lihons"], "Lihons", t0=w(k, 15.0), t1=T.end("tag11") + 1.0, size=22))
    T.add(Label(*P["chaulnes"], "Chaulnes", t0=w(k, 15.4), t1=T.end("tag11") + 1.0, size=22))
    T.add(Caption([(None, "altes Schlachtfeld der Somme-Schlacht 1916"), (None, "Trichter, Gräben und Stacheldraht")], w(k, 15.5),
                  T.end(k) + 0.8, pos="br", width=560))

    k = "tag11"
    T.cam(w(k, 0.0), Cam(49.80, 2.72, 22, 44, 84))
    front.states.append((w(k, 1.0), w(k, 8.0), local_line("aug11")))
    wfront.states.append((w(k, 1.0), w(k, 8.0), G.WF["aug12"]))
    T.add(Caption([([GB], "Feldmarschall Douglas Haig"), (None, "lässt den Angriff bei Amiens einstellen")], w(k, 14.0), w(k, 21.0),
                  pos="br", width=560))
    T.add(Quote(["Wir sind an der Grenze unserer Leistungsfähigkeit.", "Der Krieg muss beendet werden.“"],
                "Kaiser Wilhelm II. (überliefert)", w(k, 22.0), T.end(k) + 2.2, size=42))

    k = "bilanz_amiens"
    T.cam(w(k, 0.0), Cam(49.83, 2.62, 48, 30, 80))
    T.add(MeasureLineSafe((49.870, 2.555), (49.868, 2.766), "bis zu 20 km", w(k, 4.6), w(k, 12.0)))
    T.add(E.BilanzPanel(w(k, 6.6), T.end(k) + 1.5, [([GB, AU, CA], "Briten und Dominions", 22000, "ca., Tote, Verwundete, Vermisste", w(k, 9.6)),
                                                     ([FR], "Franzosen", 24000, "ca.", w(k, 12.6)),
                                                     ([DE], "Deutsche", 75000, "ca., davon fast 30.000 Gefangene", w(k, 15.6))],
                        head="Verluste 8. – 11. August 1918"))
    front.t1 = T.end(k) + 3.0

    # ------------------------------------------------------------ Kapitel 6 · Hundert Tage
    t = T.t
    T.mood(t, "hundred")
    T.add(ChapterCard(6, "Hundert Tage", "August – November 1918", t + 0.3, 5.0))
    T.cam(t + 6.0, Cam(49.6, 3.6, 760, 0, 0))
    T.wait(5.6)
    s = T.say("hundert", pre=0.3, post=2.0)
    T.say("hindenburg", pre=0.4, post=2.0)
    T.say("zusammenbruch", pre=0.4, post=2.0)
    T.say("waffenstillstand", pre=0.4, post=3.0)
    k = "hundert"
    for pts, t_, lbl, pos in (([(50.00, 2.55), (50.05, 2.90)], 6.8, "Albert", (50.02, 2.60)),
                               ([(50.28, 2.70), (50.25, 3.05)], 7.7, "Arras", P["arras"]),
                               ([(49.40, 3.20), (49.45, 3.55)], 8.8, "Aisne", (49.40, 3.40)),
                               ([(49.12, 4.95), (49.40, 5.05)], 10.2, "Argonnen", (49.15, 4.95))):
        T.add(Arrow(pts, "al", t0=w(k, t_), grow=1.6, t1=T.end(k) + 1.0, width=12))
        T.add(Label(*pos, lbl, t0=w(k, t_), t1=T.end(k) + 1.0, size=20, dot=False))
    wfront.states.append((w(k, 11.0), w(k, 17.0), G.WF["sep26"]))
    T.add(Polyline(G.HINDENBURG, E.hexc("#ffcf6a"), t0=w(k, 17.3), t1=T.end("hindenburg") + 1.0, width=5, grow=2.0, dash=(14, 8),
                   glow=True))
    T.add(Label(50.10, 3.55, "Siegfriedstellung", "„Hindenburg-Linie“", t0=w(k, 17.6), t1=T.end(k) + 1.0, size=22, dot=False))

    k = "hindenburg"
    T.cam(w(k, 0.0), Cam(49.93, 3.25, 40, 40, 80))
    T.add(Label(*P["bellicourt"], "Bellicourt", t0=w(k, 5.0), t1=T.end(k) + 1.0, size=22))
    T.add(Label(*P["stquentin"], "Saint-Quentin", t0=w(k, 5.4), t1=T.end(k) + 1.0, size=22))
    T.add(Barrage([(50.00, 3.20), (50.00, 3.27), (49.90, 3.30), (49.90, 3.24)], w(k, 4.0), w(k, 10.0), rate=40, seed=131))
    tanks(A.TankGroup("au", "mk5", 30, [(w(k, 6.0), 49.965, 3.170), (w(k, 12.0), 49.960, 3.260)], spacing=80, rows=2, seed=132,
                      losses=[(w(k, 9.0), 6)], fire=[(w(k, 7.0), w(k, 12.0))], t1=T.end(k) + 1.0),
          A.TankGroup("gb", "mk5", 20, [(w(k, 6.4), 49.930, 3.180), (w(k, 12.0), 49.925, 3.265)], spacing=80, rows=2, seed=133,
                      losses=[(w(k, 9.4), 4)], fire=[(w(k, 7.0), w(k, 12.0))], t1=T.end(k) + 1.0))
    T.add(Token(49.99, 3.12, [AU, US, GB], [(0, 0)], label="29. September 1918", side="al", t0=w(k, 7.6), t1=w(k, 14.0), dy=-50))
    T.cam(w(k, 6.0), Cam(49.955, 3.235, 12, 50, 82))
    T.add(Caption([([DE], "Ludendorff: Krieg militärisch nicht mehr zu gewinnen"), (None, "Forderung nach Waffenstillstand")],
                  w(k, 12.0), w(k, 20.0), pos="br", width=640))
    T.cam(w(k, 19.5), Cam(50.0, 5.0, 2200, 0, 0))
    T.add(Arrow([(51.0, 8.0), (49.0, -10.0), (42.0, -40.0)], "de", t0=w(k, 21.0), grow=2.5, t1=T.end(k) + 1.0, width=12, dashed=True))
    T.add(Caption([([US], "Präsident Woodrow Wilson")], w(k, 24.8), T.end(k) + 1.5, pos="br", width=440))

    k = "zusammenbruch"
    T.cam(w(k, 0.0), Cam(48.5, 16.0, 4300, 0, 0))
    for nm, lbl, t_ in ((P["berlin"], "Berlin", 23.0), (P["kiel"], "Kiel", 13.6)):
        T.add(Label(*nm, lbl, t0=w(k, t_), t1=T.end(k) + 1.0, size=24))
    T.add(Label(42.7, 25.3, "Bulgarien", "29. September", t0=w(k, 3.4), t1=T.end(k) + 1.0, style="country", size=22))
    T.add(Label(38.8, 33.5, "Osmanisches Reich", "30. Oktober", t0=w(k, 6.4), t1=T.end(k) + 1.0, style="country", size=24))
    T.add(Label(47.6, 18.0, "Österreich-Ungarn", "3. November", t0=w(k, 8.9), t1=T.end(k) + 1.0, style="country", size=24))
    T.add(Pulse(*P["kiel"], w(k, 13.8), w(k, 18.5), r=40))
    T.add(Caption([([DE], "9. November 1918"), (None, "Abdankung des Kaisers verkündet, Republik ausgerufen")], w(k, 19.3),
                  T.end(k) + 1.5, pos="br", width=600))

    k = "waffenstillstand"
    T.cam(w(k, -0.4), Cam(49.43, 2.90, 60, 30, 0))
    T.add(Label(*P["rethondes"], "Lichtung von Rethondes", "Wald von Compiègne", t0=w(k, 0.5), t1=w(k, 14.0), size=24))
    T.add(DateStamp("11. November 1918", "11:00 Uhr", w(k, 8.4), T.end(k) + 2.0, sub="Waffenstillstand"))
    wfront.states.append((w(k, 6.0), w(k, 13.0), G.WF["nov11"]))
    T.cam(w(k, 13.0), Cam(49.6, 4.2, 900, 0, 0))
    T.add(BigWord("17 MILLIONEN TOTE", w(k, 20.0), T.end(k) + 2.5, y=0.22, color=E.hexc("#efe6d6"), size=72))

    # ------------------------------------------------------------ Kapitel 7 · Erbe
    t = T.t
    T.mood(t, "legacy")
    T.add(ChapterCard(7, "Das Erbe", "Amiens heute", t + 0.3, 5.0))
    T.cam(t + 6.0, Cam(49.88, 2.56, 30, 46, 80))
    T.wait(5.6)
    s = T.say("erbe", pre=0.3, post=2.0)
    T.say("gedenken", pre=0.4, post=3.0)
    k = "erbe"
    T.cam(w(k, 16.0), Cam(49.885, 2.545, 7.0, 54, 80))
    for pos, lbl, t_ in ((P["vb_denkmal"], "Australisches Ehrenmal", 21.8), (P["le_quesnel_denkmal"], "Kanadisches Denkmal Le Quesnel", 23.0),
                         (P["hamel_denkmal"], "Australian Corps Memorial", 22.4)):
        T.add(Label(*pos, lbl, t0=w(k, t_), t1=T.end(k) + 1.0, size=20))
    T.cam(T.end(k) + 0.5, Cam(49.88, 2.60, 16, 50, 84), "linear")
    k = "gedenken"
    T.cam(w(k, 0.0), Cam(49.8946, 2.3022, 3.0, 52, 30))
    T.add(DateStamp("8. August 2018", "Kathedrale von Amiens", s, w(k, 16.0)))
    T.add(Label(*P["kathedrale"], "Kathedrale Notre-Dame d’Amiens", t0=w(k, 6.0), t1=T.end(k), size=24))
    T.add(Caption([([GB, AU, CA], "Nachfahren der Soldaten"), ([FR, US], "Frankreich und USA"),
                   ([DE], "Joachim Gauck, früherer Bundespräsident")], w(k, 9.4), w(k, 22.0), pos="br", width=580,
                  title="Hundert Jahre danach"))
    T.cam(T.end(k) + 2.0, Cam(49.894, 2.302, 9.0, 50, 60), "linear")

    # ------------------------------------------------------------ Flaggen-Gebiete (Karten)
    paths = E.load_countries()
    thrace = E.thrace_path()
    bg_path = skia.Op(paths["Bulgaria"], thrace, skia.PathOp.kDifference_PathOp) or paths["Bulgaria"]
    ru_rect, ot_rect, gb_rect = (44.0, 20.0, 60.0, 60.0), (33.0, 27.0, 43.6, 46.0), (49.9, -10.6, 58.7, 1.8)
    on = T.vstart["europa"] + 6.6
    al_on = T.vstart["europa"] + 15.1
    ru_off = T.vstart["europa"] + 26.0
    f_end = 1e9
    bg_off, ot_off, ah_off = w("zusammenbruch", 4.5), w("zusammenbruch", 7.5), w("zusammenbruch", 10.0)
    ent = [dict(name="de_held", flag="de1871", side="cp", t_on=on, t_off=f_end),
           dict(name="fr_held", flag="fr", side="en", t_on=al_on, t_off=f_end),
           dict(name="Austro-Hungarian Empire", flag="ah1869", side="cp", t_on=on + 2.7, t_off=ah_off),
           dict(name="Ottoman Empire", flag="tr", side="cp", rect=ot_rect, t_on=on + 4.4, t_off=ot_off),
           dict(name="thrace", path=thrace, flag="tr", side="cp", rect=ot_rect, t_on=on + 4.4, t_off=ot_off),
           dict(name="bulgaria", path=bg_path, flag="bg", side="cp", t_on=on + 5.7, t_off=bg_off),
           dict(name="United Kingdom of Great Britain and Ireland", flag="gb", side="en", rect=gb_rect, t_on=al_on + 2.2, t_off=f_end),
           dict(name="Kingdom of Italy", flag="it1861", side="en", t_on=al_on + 4.5, t_off=f_end),
           dict(name="Russian Empire", flag="ru1914", side="en", rect=ru_rect, t_on=al_on, t_off=ru_off),
           dict(name="Grand Duchy of Finland", flag="ru1914", side="en", rect=ru_rect, t_on=al_on, t_off=ru_off)]
    for nm in ("Georgia", "Armenia", "Azerbaijan"):
        if nm in paths:
            ent.append(dict(name=nm, flag="ru1914", side="en", rect=ru_rect, t_on=al_on, t_off=ru_off))
    flags_obj.entries = ent
    flags_obj.t1 = T.end("waffenstillstand") + 3.0

    # Wolken: über dem Schlachtfeld in drei Höhen (in den Nahszenen liegt die Kamera darunter)
    T.add(A.Clouds(G.CLOUD_BOX, [(22, 240, 5, 14, 0.72), (34, 180, 6, 16, 0.66), (50, 130, 8, 20, 0.6)], 0.0, 1e9, campath=T.cam,
                   seed=18))

    # Panzer, Truppen
    T.add(A.Tanks(TANKS, min(g.t0 for g in TANKS), 1e9))
    T.add(E.Troops(ALL_UNITS, min(u.t0 for u in ALL_UNITS), T.end("bilanz_amiens") + 1.0, ALL_ENEM))

    t = T.t
    T.add(Credits(t, t + 27.0, roles=[("Produzent", "Atakan Zengin"), ("Kanal", "WarAZ")], title="AMIENS 1918"))
    T.wait(27.0)
    T.finalize()
    return T


def MeasureLineSafe(a, b, text, t0, t1):
    return E.MeasureLine(a, b, text, t0, t1)


if __name__ == "__main__":
    tl = build()
    print("Dauer", round(tl.duration, 2))
    for k, v in tl.vstart.items():
        print(f"{k:18s} {v:8.2f}")
