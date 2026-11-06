"""Regie „Verdun 1916“: Kamera, Figuren, Effekte und Einblendungen für alle 73 Absätze.

Zeiten beziehen sich auf die Zeitleiste (timeline.py) – Absatz pid läuft von tl[pid][0] bis tl[pid][1].
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from warazlib.story import Story, GeoCam, Fig, Boom, Smoke, Gas, Fire, Arrow, Label, Muzzle, Clip, Sfx  # noqa
from warazlib import cards as CD, ui as UI, insets as IN, mapfx as MF  # noqa
import vgeo  # noqa

P = vgeo.P
CLIPS = os.path.join(HERE, "clips")
DAYS = [("feb21", 1), ("feb24", 4), ("feb25", 5), ("feb26", 6), ("apr15", 55), ("may31", 101), ("jun07", 108),
        ("jun23", 124), ("jul12", 143), ("sep01", 194), ("oct24", 247), ("nov02", 256), ("dec18", 302)]
DESTROYED = ["beaumont", "bezonvaux", "cumieres", "douaumont_dorf", "fleury", "haumont", "louvemont", "ornes", "vaux_dorf"]
DESTROYED_NAMES = {"beaumont": "BEAUMONT", "bezonvaux": "BEZONVAUX", "cumieres": "CUMIÈRES", "douaumont_dorf": "DOUAUMONT",
                   "fleury": "FLEURY", "haumont": "HAUMONT", "louvemont": "LOUVEMONT", "ornes": "ORNES", "vaux_dorf": "VAUX"}
INF = 430.0       # Figurengröße Infanterie (m)
GUN = 520.0


def fronts():
    return MF.Fronts(vgeo.FRONTS, DAYS, west=vgeo.WEST, south=vgeo.SOUTH, ger_close=vgeo.GER_CLOSE)


def build(tl, rng_seed=1916):
    S = Story(tl)
    S.duration = tl["P73"][1] + 5.0
    rng = np.random.default_rng(rng_seed)
    FR = fronts()

    def T(pid, f=0.0):
        return S.at(pid, f)

    def ll(w):
        return P[w] if isinstance(w, str) else w

    def cam(t, where, km, pitch=46, yaw=0.0, ease="s"):
        la, lo = ll(where)
        S.cam.key(t, GeoCam(la, lo, km, pitch, yaw), ease)

    def label(t0, t1, text, where, sub=None, side=1):
        la, lo = ll(where)
        S.labels.append(Label(t0, t1, text, la, lo, sub, side))

    def ov(t0, t1, fn, fin=0.4, fout=0.4):
        S.overlay(t0, t1, fn, fin, fout)

    def squad(sprite, where, n, t0, t1, dest=None, tm=None, spread=0.006, size=INF, flip=None, seed=0, z=0.0):
        la, lo = ll(where)
        r = np.random.default_rng(seed)
        out = []
        for i in range(n):
            dla, dlo = r.normal(0, spread * 0.6), r.normal(0, spread)
            path = [(t0, la + dla, lo + dlo)]
            if dest is not None:
                dl, dn = ll(dest)
                path = [(tm[0], la + dla, lo + dlo), (tm[1], dl + dla * 0.8, dn + dlo * 0.8)]
            fl = (r.random() < 0.5) if flip is None else flip
            out.append(S.fig(sprite, path, size_m=size * r.uniform(0.92, 1.06), flip=fl, t0=t0, t1=t1, z_m=z,
                             tag=f"{sprite}{seed}{i}"))
        return out

    def guns(sprite, where_list, t0, t1, fire=None, rate=1.6, flip=False, size=GUN):
        gs = []
        for i, w in enumerate(where_list):
            la, lo = ll(w)
            gs.append(S.fig(sprite, [(t0, la, lo)], size_m=size, flip=flip if i % 2 == 0 else not flip, t0=t0, t1=t1,
                            tag=f"{sprite}{i}{t0}"))
        if fire:
            t = fire[0]
            i = 0
            while t < fire[1]:
                g = gs[i % len(gs)]
                S.muzzles.append(Muzzle(t, g))
                la, lo = g.pos(t)
                S.smokes.append(Smoke(t + 0.05, la + 0.0006, lo + (0.0012 if not g.flip else -0.0012), 260, 3.0))
                S.sfx.append(Sfx(t, "gun", 0.5))
                i += 1
                t += rng.exponential(1.0 / rate)
        return gs

    def barrage(t0, t1, box, rate, size=(900, 1350), crater=True, loud=1.0, sfx=True):
        t = t0
        while t < t1:
            la = rng.uniform(box[0], box[1])
            lo = rng.uniform(box[2], box[3])
            S.booms.append(Boom(t, la, lo, rng.uniform(*size), crater, loud))
            if sfx:
                S.sfx.append(Sfx(t, "boom", loud))
            t += rng.exponential(1.0 / rate)

    def front_barrage(t0, t1, day, rate, lon=(5.1, 5.7), depth=(-0.8, 1.6), size=(800, 1250), loud=0.7):
        line = FR.at(day)
        sel = line[(line[:, 1] > lon[0]) & (line[:, 1] < lon[1])]
        if len(sel) < 2:
            return
        t = t0
        while t < t1:
            j = rng.integers(0, len(sel))
            la, lo = sel[j]
            off = rng.uniform(*depth)
            S.booms.append(Boom(t, la - off / 111.0, lo + rng.normal(0, 0.004), rng.uniform(*size), True, loud))
            S.sfx.append(Sfx(t, "boom", loud * 0.8))
            t += rng.exponential(1.0 / rate)

    def day(t, d, ease="s"):
        S.day.key(t, d, ease)

    def counter(t, a):
        S.counter_a.key(t, a)

    def chapter_card(pid, num, name):
        a = T(pid) - 0.6
        ov(a, a + 3.6, lambda o, t, k, L, n=num, nm=name: CD.chapter(o, k, n, nm), 0.4, 0.6)
        S.sfx.append(Sfx(a, "chapter", 1.0))

    def fort_sprites(t0, t1, ruin_days=None):
        ruin_days = ruin_days or {}
        out = {}
        for (name, la, lo, big) in vgeo.FORTS:
            size = 620 if name == "Douaumont" else (470 if big else 330)
            f = S.fig("fort", [(t0, la, lo)], size_m=size, t0=t0, t1=t1, min_px=12, tag="fort" + name)
            out[name] = f
        return out

    # =============================================================== Grundzustand
    S.fog.key(0, 0.20)
    S.sat.key(0, 1.0)
    counter(0, 0.0)
    day(0, 1.0, "h")

    # Forts dauerhaft (Ruinen ab dem Tag, an dem sie zerschossen sind)
    forts = fort_sprites(0, S.duration)
    # Zeitpunkte, ab denen die großen Forts Ruinen sind, werden unten über day→Zeit gesetzt
    T_FORTS = tl["P07"][0] + (tl["P07"][1] - tl["P07"][0]) * 0.5
    S.flags.append((*P["douaumont"], [(T_FORTS, "fr")]))
    S.flags.append((*P["vaux"], [(T_FORTS, "fr")]))

    # =============================================================== 1 HOOK
    a, b = tl["P01"]
    day(0, 1.0, "h")
    S.dawn.key(0, 0.6).key(T("P02", 0.3), 0.45).key(T("P04"), 0.15)
    S.snowfall.key(0, 0.7).key(T("P04", 0.8), 0.5).key(T("P05"), 0.0)
    counter(a + 1.6, 0.0)
    counter(a + 2.4, 1.0)
    cam(0, (49.2700, 5.3880), 10.5, 54, -9)
    cam(b, (49.2810, 5.3880), 8.5, 50, -2)
    fr1 = squad("fr_inf_kneel", (49.2765, 5.3880), 5, 0, T("P04", 0.5), spread=0.010, seed=1)
    fr2 = squad("fr_inf_stand", (49.2752, 5.3860), 2, 0, T("P04", 0.5), spread=0.008, seed=2)
    for k in range(int((b - a) / 0.55) + 6):
        S.smokes.append(Smoke(k * 0.55, 49.2755, 5.3890, 160, 4.5))
    gun_pos = [(49.3125, 5.3700), (49.3140, 5.3880), (49.3118, 5.4060), (49.3150, 5.4240), (49.3170, 5.3560)]
    de_guns = guns("de_howitzer", gun_pos, 0, T("P04", 0.5), fire=(T("P02") + 0.1, T("P03", 1.0)), rate=4.0)
    S.fig("de_balloon", [(0, 49.3250, 5.4150)], size_m=700, z_m=900, bob=0.01, t0=0, t1=T("P05"), tag="ballon1")
    ov(a + 0.2, a + 4.8, lambda o, t, k, L: o.date_title("21. FEBRUAR 1916", "07:15 UHR · NÖRDLICH VON VERDUN", k), 0.6, 0.6)
    label(a + 5.2, T("P02", 0.1), "BOIS DES CAURES", (49.2815, 5.3880), "WALDSTÜCK")
    S.sfx.append(Sfx(0.0, "wind_on", 0.5))

    a, b = tl["P02"]
    S.sfx.append(Sfx(a + 0.05, "first_boom", 1.0))
    barrage(a + 0.2, tl["P03"][1], (49.266, 49.294, 5.355, 5.415), 3.4)
    barrage(a + 0.6, tl["P03"][1], (49.25, 49.30, 5.30, 5.48), 1.6, size=(700, 1000), crater=False, loud=0.5)
    c0 = a + 0.75
    cam(c0 - 0.6, (49.2860, 5.3880), 7.0, 50, 0)
    cam(c0, (49.3100, 5.3880), 2.2, 60, 2)
    S.clips.append(Clip(c0, c0 + 4.6, os.path.join(CLIPS, "K1_trommelfeuer.mp4"), 49.31, 5.388, speed=0.86))
    cam(c0 + 4.6, (49.2900, 5.3900), 9.0, 47, 3)
    cam(b + 0.4, (49.2880, 5.3900), 12.0, 45, 5)
    ov(c0 + 4.8, b + 0.5, lambda o, t, k, L: o.number_card("1.200+", "DEUTSCHE GESCHÜTZE", k))

    a, b = tl["P03"]
    day(a + 0.8, 1.0, "l")
    day(b - 0.8, 302.0, "h")
    S.front_a.key(a + 0.4, 0.0).key(a + 1.2, 1.0).key(b, 1.0).key(T("P04") + 0.6, 0.0)
    S.terr_a.key(a + 0.4, 0.0).key(a + 1.2, 0.6).key(b, 0.6).key(T("P04") + 0.6, 0.0)
    cam(a + 0.6, (49.2500, 5.3900), 16.0, 42, 3)
    cam(b, (49.2150, 5.3850), 26.0, 36, -2)
    front_barrage(a + 1.0, b - 0.8, 120, 2.5, size=(1500, 2200), loud=0.5)
    ov(a + 2.0, a + 5.8, lambda o, t, k, L: o.number_card("302 TAGE", "21. FEB – 18. DEZ 1916", k))
    ov(a + 6.0, b + 0.6, lambda o, t, k, L: o.number_card("≈ 300.000", "TOTE", k, badge="SCHÄTZUNG"))

    a, b = tl["P04"]
    day(a, 302.0, "s")
    day(a + 0.7, 1.0, "h")
    cam(a + 0.8, (49.2000, 5.3900), 13.0, 44, 0)
    cam(b + 2.6, (49.1900, 5.3860), 9.0, 46, 6)
    ov(a + 0.1, b + 0.2, lambda o, t, k, L: CD.question(o, k, "WARUM STARBEN HIER\nRUND 300.000 MENSCHEN\nFÜR EIN PAAR KILOMETER?"),
       0.5, 0.4)
    ov(b + 0.25, b + 2.75, lambda o, t, k, L: CD.title(o, k, t), 0.35, 0.5)
    S.sfx.append(Sfx(a + 0.05, "music_stop", 1.0))
    S.sfx.append(Sfx(b + 0.25, "title_hit", 1.0))
    counter(b, 1.0)
    counter(b + 0.6, 0.0)

    # =============================================================== 2 WARUM VERDUN?
    chapter_card("P05", 1, "WARUM VERDUN?")
    a, b = tl["P05"]
    day(a - 1.0, 0.0, "h")
    S.mapmix.key(a, 0.0).key(a + 1.6, 1.0).key(b - 2.2, 1.0).key(b, 0.0)
    cam(a + 1.8, (49.0800, 5.3300), 78.0, 26, 0)
    cam(b - 2.0, (49.1300, 5.3700), 40.0, 34, 0)
    cam(b + 0.3, (49.1650, 5.3850), 9.0, 44, -4)
    fr_inset = IN.Inset(-5.0, 42.0, 9.5, 51.5, 520, 470)
    ov(a + 0.6, b - 1.0, lambda o, t, k, L: IN.place_inset(o, fr_inset.render(lambda d, i, tt: i.pin(d, 49.16, 5.384, "VERDUN", tt), t), k,
                                                           title="FRANKREICH 1916"))
    label(b - 1.6, T("P06", 0.15), "VERDUN", "verdun", "STADT AN DER MAAS")
    label(b - 1.2, T("P06", 0.15), "MAAS", (49.2060, 5.3615), side=-1)

    a, b = tl["P06"]
    S.mapmix.key(a, 0.0).key(a + 1.2, 1.0).key(b, 1.0).key(T("P07", 0.12), 0.0)
    cam(a + 1.4, (49.1200, 5.4300), 62.0, 28, 0)
    cam(b, (49.1300, 5.4000), 54.0, 30, 3)
    S.front_a.key(a + 1.0, 0.0).key(a + 2.6, 1.0).key(b, 1.0).key(T("P07", 0.1), 0.0)
    S.terr_a.key(a + 2.0, 0.0).key(a + 3.4, 0.7).key(b, 0.7).key(T("P07", 0.1), 0.0)
    for (w, sd) in [((49.36, 5.40), 1), ((49.20, 5.66), 2), ((48.93, 5.58), 3)]:
        squad("de_inf_stand", w, 3, a + 3.0 + sd * 0.6, b + 0.5, spread=0.03, size=2600, seed=10 + sd)
    S.arrows.append(Arrow(T("P06", 0.72), b + 0.6, [(49.15, 5.37), (49.02, 5.29), (48.86, 5.20)], "fr", 6.0, 1.2))
    label(a + 3.2, b, "FRONTBOGEN VON VERDUN", (49.31, 5.28))
    label(T("P06", 0.75), b + 0.5, "EINZIGER OFFENER WEG", (48.93, 5.24), side=-1)

    a, b = tl["P07"]
    cam(T("P07", 0.12), (49.1750, 5.4000), 17.0, 40, -12)
    cam(T("P07", 0.65), (49.1800, 5.4050), 15.0, 42, 12)
    cam(b, (49.2170, 5.4390), 3.6, 50, 6)
    for i, (name, la, lo, big) in enumerate(vgeo.FORTS):
        forts[name].t0 = T("P07", 0.12) + i * 0.22
        S.sfx.append(Sfx(forts[name].t0, "plop", 0.4))
    for f in forts.values():
        f.fade = 0.25
    ov(T("P07", 0.2), T("P07", 0.75), lambda o, t, k, L: CD.headline(o, k, "FESTUNGSRING", "FAST 40 FORTS UND WERKE", y=60))
    label(T("P07", 0.72), T("P08", 0.3), "FORT DOUAUMONT", "douaumont", "GRÖSSTES FORT DES RINGS")

    a, b = tl["P08"]
    cam(a + 0.5, (49.1640, 5.3860), 4.2, 50, -4)
    cam(b, (49.1620, 5.3840), 3.6, 52, 4)
    S.flags.append((49.1590, 5.3800, [(a + 0.3, "fr")]))
    ov(T("P08", 0.30), b + 0.4, lambda o, t, k, L: CD.stamp(o, k, "1792", 640, 300, -10, size=70, strike=True))
    ov(T("P08", 0.50), b + 0.4, lambda o, t, k, L: CD.stamp(o, k, "1870", 960, 260, 6, size=70, strike=True))
    ov(T("P08", 0.78), b + 0.4, lambda o, t, k, L: CD.stamp(o, k, "1916 ?", 1290, 310, -6, size=78, color=UI.STYLE["warn"]))
    for f in (0.30, 0.50, 0.78):
        S.sfx.append(Sfx(T("P08", f), "stamp", 0.8))

    a, b = tl["P09"]
    cam(a + 0.4, (49.1900, 5.4200), 11.0, 44, -6)
    cam(b, (49.1950, 5.4250), 9.5, 46, 4)
    be_inset = IN.Inset(2.6, 49.3, 7.4, 51.4, 540, 400)

    def be_draw(d, i, tt, a=a):
        i.pin(d, 50.633, 5.567, "LÜTTICH", tt)
        i.pin(d, 50.467, 4.867, "NAMUR", tt)
        i.pin(d, 49.16, 5.384, "VERDUN", tt, color=(104, 138, 186))
    ov(a + 0.3, b, lambda o, t, k, L: IN.place_inset(o, be_inset.render(be_draw, t), k, title="BELGIEN · AUGUST 1914"))
    ov(T("P09", 0.55), b + 0.2, lambda o, t, k, L: CD.stamp(o, k, "ZERSCHLAGEN", 1580, 560, -8, size=54))
    S.sfx.append(Sfx(T("P09", 0.55), "stamp", 0.6))

    a, b = tl["P10"]
    cam(a + 0.5, (49.1750, 5.3950), 14.0, 42, -3)
    cam(b, (49.1700, 5.3800), 15.0, 42, 5)
    for i, (name, la, lo, big) in enumerate(vgeo.FORTS[:12]):
        S.fig("fr_gun75", [(a, la - 0.002, lo + 0.003), (a + 0.6 + i * 0.12, la - 0.002, lo + 0.003),
                           (b + 0.5, 49.10 + i * 0.004, 5.28 + i * 0.006)], size_m=420, t0=a, t1=b + 0.4, flip=True,
              tag="gunleave" + name)
    ov(T("P10", 0.25), b + 0.3, lambda o, t, k, L: o.number_card("− 54", "BATTERIEN ABGEZOGEN", k))
    ov(T("P10", 0.2), b + 0.3, lambda o, t, k, L: CD.stamp(o, k, "AUGUST 1915", 360, 230, -7, size=56))
    S.sfx.append(Sfx(T("P10", 0.2), "stamp", 0.6))
    S.sfx.append(Sfx(a + 0.5, "wheels", 0.6, dur=b - a))

    a, b = tl["P11"]
    cam(a + 0.8, (49.3000, 5.4600), 15.0, 42, 8)
    cam(b, (49.2900, 5.4400), 13.0, 44, 2)
    S.terr_a.key(a, 0.0).key(a + 1.5, 0.55).key(T("P13", 0.9), 0.55).key(T("P15"), 0.0)
    S.front_a.key(a, 0.0).key(a + 1.5, 1.0).key(T("P15", 0.9), 1.0).key(T("P16"), 0.0)
    ov(a + 0.4, T("P11", 0.55), lambda o, t, k, L: CD.medallion(o, k, "ERICH VON FALKENHAYN", "CHEF DER OBERSTEN HEERESLEITUNG"))
    S.arrows.append(Arrow(T("P11", 0.6), T("P12", 0.6), [(49.33, 5.42), (49.27, 5.41), (49.20, 5.40)], "de", 1.8, 1.4))
    ov(T("P11", 0.72), b + 0.5, lambda o, t, k, L: CD.stamp(o, k, "UNTERNEHMEN GERICHT", 960, 860, -5, size=64))
    S.sfx.append(Sfx(T("P11", 0.72), "stamp", 0.8))
    S.sfx.append(Sfx(a, "clock", 0.5, dur=(b - a) + 3))

    a, b = tl["P12"]
    cam(a + 0.5, (49.3150, 5.4100), 10.0, 46, -4)
    cam(b, (49.3100, 5.3900), 11.0, 46, 4)
    for j, (sla, slo) in enumerate([(49.355, 5.37), (49.355, 5.42), (49.350, 5.47)]):
        squad("de_inf_run", (sla, slo), 5, a, T("P14", 0.5), dest=(sla - 0.035, slo), tm=(a, b), spread=0.006, seed=30 + j,
              flip=False)
    guns("de_howitzer", [(49.330, 5.37), (49.332, 5.40), (49.330, 5.44)], a + 0.5, T("P14", 0.5))
    for j, w in enumerate([(49.345, 5.39), (49.342, 5.45)]):
        S.fig("de_balloon", [(a, w[0], w[1]), (b, w[0], w[1])], size_m=700, z_m=700, bob=0.01, t0=a + 0.4 + j * 0.5,
              t1=T("P15"), tag=f"ballon2{j}")
    ov(a + 0.3, b + 0.3, lambda o, t, k, L: CD.lower_third(o, k, "5. ARMEE", "OBERBEFEHL: KRONPRINZ WILHELM"))
    S.sfx.append(Sfx(a, "march", 0.5, dur=b - a))

    a, b = tl["P13"]
    cam(a + 0.6, (49.2400, 5.3700), 12.0, 36, -4)
    cam(b, (49.2200, 5.3700), 13.0, 34, 2)
    for j in range(3):
        squad("fr_inf_run", (49.10 + j * 0.01, 5.30 + j * 0.02), 4, a + j * 0.6, b + 0.3, dest=(49.20, 5.39),
              tm=(a + j * 0.6, b), spread=0.006, seed=50 + j, flip=False)
    ov(T("P13", 0.35), b + 0.6, lambda o, t, k, L: o.quote("„… so werden sich\nFrankreichs Kräfte verbluten …“",
                                                             "Falkenhayn, Memoiren 1920 – angeblich aus einer Denkschrift von 1915", k,
                                                             badge="UMSTRITTEN"))
    S.sat.key(a, 1.0).key(b, 0.8).key(T("P15", 0.5), 1.0)

    a, b = tl["P14"]
    cam(a + 0.5, (49.2700, 5.4300), 11.0, 42, 4)
    cam(b, (49.2750, 5.4200), 10.0, 44, -2)
    ov(a + 0.2, b + 0.2, lambda o, t, k, L, a=a, b=b: CD.document(o, k, t, gone=max(0.0, min(1.0, (t - (a + (b - a) * 0.6)) / 1.6))))
    ov(T("P14", 0.62), b + 0.6, lambda o, t, k, L: CD.stamp(o, k, "ORIGINAL NIE GEFUNDEN", 1290, 640, -6, size=50))
    S.sfx.append(Sfx(T("P14", 0.62), "stamp", 0.7))

    a, b = tl["P15"]
    cam(a + 0.5, (49.2850, 5.4000), 11.0, 44, 0)
    cam(b + 0.6, (49.2850, 5.3880), 6.0, 50, -6)
    ov(a + 0.2, b + 0.4, lambda o, t, k, L: CD.headline(o, k, "UMSTRITTEN", "UNTER HISTORIKERN", color=UI.STYLE["warn"]))

    # =============================================================== 3 DER ANGRIFF
    chapter_card("P16", 2, "DER ANGRIFF")
    a, b = tl["P16"]
    day(a - 0.8, 1.0, "s")
    day(b, 2.0, "s")
    counter(a - 0.6, 0.0)
    counter(a + 0.2, 1.0)
    S.snowfall.key(a - 0.5, 0.0).key(a + 0.5, 0.6)
    S.dawn.key(a - 0.5, 0.0).key(a + 0.5, 0.25).key(b, 0.1)
    S.front_a.key(a, 0.0).key(a + 1.0, 1.0)
    S.terr_a.key(a, 0.0).key(a + 1.0, 0.35)
    cam(a + 0.3, (49.2840, 5.3860), 5.0, 54, -6)
    cam(b, (49.2830, 5.3860), 4.2, 55, 4)
    barrage(a, tl["P17"][1], (49.270, 49.294, 5.365, 5.410), 4.2, size=(700, 1100))
    for k in range(6):
        S.fires.append(Fire(a + 0.5 + k * 0.6, tl["P19"][1], 49.276 + rng.uniform(0, 0.012), 5.372 + rng.uniform(0, 0.03), 320))
    fr_caures = squad("fr_inf_kneel", (49.2780, 5.3880), 8, a, T("P19", 0.4), spread=0.010, seed=61)
    squad("fr_inf_stand", (49.2770, 5.3870), 3, a, T("P19", 0.4), spread=0.008, seed=62)

    a, b = tl["P17"]
    de_storm = squad("de_inf_run", (49.2990, 5.3880), 9, a + 0.2, T("P19", 0.9), dest=(49.2855, 5.3880),
                     tm=(a + 0.3, T("P18", 0.6)), spread=0.010, seed=63, flip=False)
    S.sfx.append(Sfx(a + 0.3, "whistle", 0.8))
    S.sfx.append(Sfx(T("P17", 0.72), "mg", 0.8, dur=6.0))
    for j in range(12):
        f = fr_caures[j % len(fr_caures)]
        S.muzzles.append(Muzzle(T("P17", 0.72) + j * 0.35, f))
    cam(a + 0.4, (49.2900, 5.3880), 4.6, 52, 2)
    cam(b, (49.2850, 5.3880), 3.8, 54, -3)

    a, b = tl["P18"]
    cam(a + 0.4, (49.2810, 5.3880), 3.2, 56, -4)
    cam(b, (49.2800, 5.3900), 3.6, 55, 3)
    label(a + 0.2, b, "BOIS DES CAURES", (49.2830, 5.3880), "WALDSTÜCK")
    ov(T("P18", 0.4), b + 0.3, lambda o, t, k, L: CD.lower_third(o, k, "OBERSTLEUTNANT ÉMILE DRIANT", "≈ 1.200 FRANZÖSISCHE JÄGER"))
    S.arrows.append(Arrow(a + 0.5, a + 2.4, [(49.302, 5.380), (49.288, 5.384)], "de", 0.7, 0.9))
    S.arrows.append(Arrow(T("P18", 0.55), T("P18", 0.55) + 2.0, [(49.302, 5.398), (49.288, 5.392)], "de", 0.7, 0.9))
    S.sfx.append(Sfx(a, "mg", 0.7, dur=b - a))

    a, b = tl["P19"]
    day(a, 2.0, "s")
    day(b, 4.0, "s")
    cam(a + 0.5, (49.2700, 5.3750), 10.0, 46, -3)
    cam(b, (49.2550, 5.3900), 12.0, 44, 4)
    for f in fr_caures:
        la, lo = f.pos(a)
        f.path = [(a, la, lo), (b, la - 0.018, lo + rng.normal(0, 0.004))]
        f.t1 = b + 0.4
    for j, v in enumerate(["haumont", "beaumont", "samogneux"]):
        tv = T("P19", 0.55 + j * 0.12)
        label(tv, b + 0.3, v.upper(), v, "GEFALLEN")
        S.fires.append(Fire(tv, T("P21"), *P[v], 420))
        S.sfx.append(Sfx(tv, "plop", 0.5))
    front_barrage(a, b, 3, 3.0, lon=(5.30, 5.50), depth=(-0.3, 1.2))

    a, b = tl["P20"]
    day(a, 5.0, "s")
    S.snowfall.key(a, 0.6).key(a + 1.0, 1.0).key(T("P23"), 1.0).key(T("P24"), 0.4).key(T("P27"), 0.3).key(T("P29"), 0.0)
    cam(a + 0.4, (49.2250, 5.4380), 5.0, 52, -8)
    cam(b, (49.2175, 5.4395), 2.4, 56, 4)
    label(T("P20", 0.55), b + 0.4, "FORT DOUAUMONT", "douaumont", "25. FEBRUAR 1916")
    S.sfx.append(Sfx(a, "music_stop", 1.0))

    a, b = tl["P21"]
    kunze = squad("de_inf_run", (49.2262, 5.4505), 10, a, T("P23", 0.9), dest=(49.2183, 5.4402),
                  tm=(a, T("P22", 0.4)), spread=0.0018, size=300, seed=71, flip=True)
    c0 = a + 2.0
    cam(c0 - 0.5, (49.2190, 5.4420), 1.4, 60, 0)
    S.clips.append(Clip(c0, c0 + 4.6, os.path.join(CLIPS, "K2_douaumont.mp4"), 49.218, 5.440, speed=0.86))
    cam(c0 + 4.6, (49.2185, 5.4410), 2.2, 56, -3)
    cam(b + 0.4, (49.2180, 5.4400), 2.0, 57, 3)
    ov(c0 + 4.7, b + 0.4, lambda o, t, k, L: CD.lower_third(o, k, "FELDWEBEL KUNZE", "≈ 10 PIONIERE"))
    S.sfx.append(Sfx(a, "heartbeat", 0.7, dur=(b - a) + 6))

    a, b = tl["P22"]
    cam(b, (49.2175, 5.4395), 1.9, 58, -2)

    def section(o, t, k, L, a=a, b=b):
        d = o.d
        x, y, w, h = 1160, 560, 680, 360
        UI.plate(d, (x, y, x + w, y + h), k, cut=14)
        A = int(255 * k)
        d.polygon([(x + 40, y + 140), (x + 160, y + 80), (x + 520, y + 80), (x + 640, y + 140), (x + 640, y + 320),
                   (x + 40, y + 320)], fill=(120, 118, 110, A))
        d.rectangle((x + 140, y + 70, x + 540, y + 86), fill=(110, 130, 80, A))
        for yy in (150, 250):
            d.rectangle((x + 90, y + yy, x + 590, y + yy + 28), fill=(40, 38, 36, A))
        d.rectangle((x + 320, y + 86, x + 346, y + 250), fill=(40, 38, 36, A))
        p = max(0.0, min(1.0, (t - a) / max(1.0, (b - a) * 0.8)))
        px = x + 330 + (p - 0.5) * 300 if p > 0.25 else x + 333
        py = y + 100 + min(p, 0.25) * 4 * 60 if p <= 0.25 else y + 160
        d.ellipse((px - 10, py - 10, px + 10, py + 10), fill=(150, 154, 144, A), outline=(255, 255, 255, A), width=2)
        for j in range(4):
            qx = x + 140 + j * 34
            d.ellipse((qx - 9, y + 255, qx + 9, y + 273), fill=(104, 138, 186, A))
        UI.spaced(d, (x + 24, y + 16), "FORT DOUAUMONT · QUERSCHNITT", UI.font("bold", 26), UI.STYLE["text"] + (A,), 2)
        UI.spaced(d, (x + 140, y + 290), "RESTBESATZUNG", UI.font("bold", 20), UI.STYLE["fr"] + (A,), 2)
    ov(a + 0.2, b + 0.3, section)
    S.sfx.append(Sfx(a, "echo_steps", 0.6, dur=b - a))

    a, b = tl["P23"]
    squad("de_inf_run", (49.2240, 5.4480), 12, a, T("P25", 0.5), dest=(49.2188, 5.4408), tm=(a, b), spread=0.002, size=300,
          seed=72, flip=True)
    S.flags[0] = (*P["douaumont"], [(T_FORTS, "fr"), (T("P23", 0.55), "de")])
    cam(b + 0.6, (49.2185, 5.4400), 2.6, 55, 4)
    ov(T("P23", 0.58), b + 0.8, lambda o, t, k, L: CD.headline(o, k, "FORT DOUAUMONT FÄLLT", "OHNE EINEN SCHUSS"))
    S.sfx.append(Sfx(T("P23", 0.56), "bell", 1.0))

    a, b = tl["P24"]
    cam(b, (49.2200, 5.4390), 3.2, 54, -3)

    def medals(o, t, k, L, a=a, b=b):
        d = o.d
        names = ["FW. KUNZE", "LT. RADTKE", "OBLT. VON BRANDIS"]
        p = max(0.0, min(1.0, (t - (a + (b - a) * 0.45)) / 1.2))
        for i, nm in enumerate(names):
            x, y = 430 + i * 390, 760
            dim = 0.45 if (i < 2 and p > 0.6) else 1.0
            UI.plate(d, (x, y, x + 340, y + 70), k * dim, cut=10)
            UI.spaced(d, (x + 24, y + 16), nm, UI.font("bold", 32), UI.STYLE["text"] + (int(255 * k * dim),), 2)
        mx = 430 + 170 + p * 2 * 390
        d.ellipse((mx - 24, 680 - 24, mx + 24, 680 + 24), fill=(214, 176, 80, int(255 * k)), outline=(255, 255, 255, int(255 * k)), width=3)
        UI.spaced(d, (mx - 88, 616), "POUR LE MÉRITE", UI.font("bold", 22), (214, 176, 80, int(255 * k)), 1.5)
    ov(a + 0.2, b + 0.4, medals)

    a, b = tl["P25"]
    day(a, 5.0, "h")
    cam(a + 0.5, (49.2300, 5.3850), 14.0, 44, -3)
    cam(b + 0.6, (49.2250, 5.3800), 15.0, 43, 3)
    S.arrows.append(Arrow(a + 0.2, T("P26", 0.2), [(49.300, 5.400), (49.250, 5.410), (49.218, 5.420)], "de", 2.4, 1.0))
    for j, (la, lo) in enumerate([(49.205, 5.37), (49.185, 5.385)]):
        S.arrows.append(Arrow(T("P25", 0.3) + j * 0.3, T("P26", 0.1), [(la, lo), (la - 0.006, lo - 0.04)], "fr", 0.9, 0.8))
    ov(T("P25", 0.45), b + 0.8, lambda o, t, k, L: CD.headline(o, k, "FRANKREICH WANKT", color=UI.STYLE["accent"]))
    S.sfx.append(Sfx(b + 0.3, "hit", 1.0))

    # =============================================================== 4 DIE HEILIGE STRASSE
    chapter_card("P26", 3, "DIE HEILIGE STRASSE")
    VS = vgeo.VOIE_SACREE
    a, b = tl["P26"]
    S.night.key(a - 0.5, 0.0).key(a + 0.5, 0.7).key(b, 0.6).key(T("P27", 0.2), 0.0)
    S.mapmix.key(a - 0.6, 0.0).key(a + 0.8, 1.0)
    S.rain.key(a, 0.0).key(a + 0.6, 0.8).key(b, 0.6).key(T("P27", 0.2), 0.0)
    cam(a + 0.9, (49.0500, 5.3000), 26.0, 40, -4)
    cam(b, (49.0300, 5.2900), 18.0, 44, 3)
    S.fig("fr_staffcar", [(a, 48.90, 5.235), (b, 49.024, 5.282)], size_m=1500, t0=a, t1=T("P27", 0.3), flip=True, tag="car")
    label(T("P26", 0.5), T("P27", 0.4), "SOUILLY", "souilly", "HAUPTQUARTIER")
    ov(a + 0.6, b + 0.2, lambda o, t, k, L: CD.lower_third(o, k, "GENERAL PHILIPPE PÉTAIN", "2. ARMEE · AB 25. FEBRUAR 1916"))
    S.sfx.append(Sfx(a, "car", 0.6, dur=b - a))
    S.sfx.append(Sfx(a, "rain", 0.5, dur=b - a + 2))

    a, b = tl["P27"]
    day(a, 6.0, "s")
    cam(a + 1.0, (48.9700, 5.2800), 62.0, 30, 0)
    cam(b, (48.9600, 5.2800), 58.0, 31, 3)
    S.front_a.key(a, 0.0).key(a + 1.2, 1.0).key(T("P31"), 1.0).key(T("P33"), 0.0)
    S.terr_a.key(a, 0.0).key(a + 1.2, 0.5).key(T("P31"), 0.5).key(T("P33"), 0.0)
    rails = [[(49.160, 5.384), (49.05, 5.48), (48.889, 5.542)], [(49.160, 5.384), (49.14, 5.20), (49.09, 4.90)]]

    def rail_fx(img, t, lay, a=a, b=b):
        k = UI.fade(t, a + 0.8, T("P28", 0.1), 0.4, 0.6)
        for r in rails:
            lay.paint.polyline(img, r, (60, 56, 52), 5, k, dashed=True)

    def voie_fx(img, t, lay, a=a):
        p = max(0.0, min(1.0, (t - (a + (tl["P27"][1] - a) * 0.55)) / 2.2))
        if p <= 0:
            return
        n = max(2, int(len(MF.resample(VS, 120)) * p))
        pts = MF.resample(VS, 120)[:n]
        glow = 0.0 if t < T("P30") else min(1.0, (t - T("P30")) / 1.0)
        col = (236, 232, 222) if glow <= 0 else (240, 200, 110)
        lay.paint.polyline(img, pts, col, 5 + 3 * glow, 1.0, outline=(40, 36, 30), glow=glow > 0)
    S.ground_fx.append((a, T("P28", 0.2), rail_fx))
    S.ground_fx.append((a, T("P34"), voie_fx))
    ov(T("P27", 0.3), T("P27", 0.8), lambda o, t, k, L: CD.stamp(o, k, "BAHN ABGESCHNITTEN", 1450, 260, -6, size=46))
    S.sfx.append(Sfx(T("P27", 0.3), "stamp", 0.6))
    label(T("P27", 0.6), T("P28", 0.4), "BAR-LE-DUC", "barleduc", side=-1)
    label(T("P27", 0.62), T("P28", 0.4), "VERDUN", "verdun")
    label(T("P27", 0.85), T("P28", 0.4), "≈ 72 KM", (48.97, 5.27), side=1)

    a, b = tl["P28"]
    cam(a + 0.6, (49.0000, 5.2900), 34.0, 38, -6)
    cam(b, (49.0400, 5.3100), 30.0, 40, 4)
    S.night.key(a, 0.0).key(a + 2.0, 0.6).key(a + 4.0, 0.0).key(a + 6.0, 0.6).key(b, 0.0)
    rs = MF.resample(VS, 200)

    def truck_path(t0, dur, north=True):
        pts = (rs if north else rs[::-1])[::10]
        return [(t0 + dur * i / (len(pts) - 1), la, lo) for i, (la, lo) in enumerate(pts)]
    t = a - 1.0
    i = 0
    while t < tl["P32"][1]:
        S.fig("fr_truck", truck_path(t, 14.0, True), size_m=1900, t0=t, t1=t + 14.0, flip=False, min_px=14, tag=f"tn{i}")
        S.fig("fr_truck", truck_path(t + 0.5, 14.0, False), size_m=1900, t0=t + 0.5, t1=t + 14.5, flip=True, min_px=14,
              tag=f"ts{i}")
        t += 0.9
        i += 1
    c0 = a + 2.6
    S.clips.append(Clip(c0, c0 + 4.6, os.path.join(CLIPS, "K3_voie_sacree.mp4"), 49.0, 5.28, speed=0.86))
    ov(a + 0.4, c0 - 0.3, lambda o, t, k, L: CD.clock14(o, k, t))
    ov(c0 + 4.8, b + 0.3, lambda o, t, k, L: CD.clock14(o, k, t))
    S.sfx.append(Sfx(a - 0.5, "trucks", 0.6, dur=(tl["P32"][1] - a) + 1))

    a, b = tl["P29"]
    S.mapmix.key(a, 1.0).key(a + 1.2, 0.0).key(T("P30", 0.6), 0.0).key(T("P31"), 0.0)
    cam(a + 1.3, (49.1180, 5.3420), 4.6, 52, -6)
    cam(b, (49.1250, 5.3500), 4.2, 52, 4)
    for j, (la, lo) in enumerate(MF.resample(VS, 200)[150:186:4]):
        S.fig("fr_worker", [(a, la + 0.0012 * (1 if j % 2 else -1), lo - 0.002 * (1 if j % 2 else -1))], size_m=330,
              t0=a + 0.3, t1=T("P30", 0.6), flip=bool(j % 2), tag=f"w{j}")
    stuck = MF.resample(VS, 200)[168]
    S.fig("fr_truck", [(a, stuck[0], stuck[1]), (T("P29", 0.6), stuck[0], stuck[1]), (T("P29", 0.8), stuck[0] + 0.0015, stuck[1] - 0.004)],
          size_m=520, t0=a, t1=T("P30", 0.6), tag="stuck")
    ov(T("P29", 0.3), b + 0.3, lambda o, t, k, L: o.number_card("≈ 8.000", "MANN AM STRASSENRAND", k))
    S.sfx.append(Sfx(a, "shovel", 0.6, dur=b - a))

    a, b = tl["P30"]
    cam(a + 0.4, (49.1350, 5.3600), 7.0, 46, -4)
    cam(b + 0.6, (49.1550, 5.3800), 6.0, 48, 6)
    ov(a + 0.3, b + 0.6, lambda o, t, k, L: CD.headline(o, k, "VOIE SACRÉE", "DIE HEILIGE STRASSE", y=90))
    S.sfx.append(Sfx(a + 0.3, "swell", 0.8))

    a, b = tl["P31"]
    cam(a + 0.6, (49.1900, 5.3800), 13.0, 44, -5)
    cam(b, (49.2000, 5.3900), 12.0, 45, 5)
    for j in range(4):
        tj = a + j * 1.8
        squad("fr_inf_run", (49.17, 5.37 + j * 0.01), 4, tj, tj + 5.0, dest=(49.215, 5.39 + j * 0.01), tm=(tj, tj + 3.5),
              spread=0.004, seed=80 + j, flip=False)
    ov(a + 0.4, b + 0.3, lambda o, t, k, L: CD.wheel(o, k, t))

    a, b = tl["P32"]
    cam(b, (49.1950, 5.3850), 12.5, 44, -2)
    ov(a + 0.2, b + 0.6, lambda o, t, k, L: CD.bar(o, k, 0.75, "DER FRANZÖSISCHEN ARMEE", "≈ 3/4"))

    a, b = tl["P33"]
    rr = MF.resample(VS, 200)
    hero_path = [(a - 0.5 + (tl["P34"][1] + 1.3 - a) * i / 26, *rr[170 + i]) for i in range(27)]
    hero_truck = S.fig("fr_truck", hero_path, size_m=560, t0=a - 0.5, t1=tl["P34"][1] + 0.8, tag="herotruck")
    hero = S.fig("fr_inf_stand", [(t, la, lo) for (t, la, lo) in hero_path], size_m=170, z_m=60, t0=a - 0.5,
                 t1=tl["P34"][1] + 0.8, tag="hero1")
    S.highlight.append((a + 0.3, tl["P34"][1] + 0.5, hero, "EIN SOLDAT WIE VIELE"))
    for tt in np.linspace(a, tl["P34"][1], 7):
        la, lo = hero.pos(tt)
        cam(tt, (la + 0.0035, lo), 1.6, 58, -4 + 8 * (tt - a) / max(1, tl["P34"][1] - a))
    S.sat.key(a, 1.0).key(a + 1.0, 0.7).key(tl["P34"][1], 0.7).key(T("P35"), 1.0)

    a, b = tl["P34"]
    cam(b + 0.8, (rr[196][0] + 0.012, rr[196][1]), 3.4, 52, 4)
    barrage(a + 1.0, b + 1.0, (49.20, 49.24, 5.36, 5.44), 1.2, size=(900, 1300), crater=False, loud=0.35)
    S.sfx.append(Sfx(a, "rumble_far", 0.6, dur=b - a + 1))

    # =============================================================== 5 DIE HÖLLE
    chapter_card("P35", 4, "DIE HÖLLE")
    a, b = tl["P35"]
    day(a - 0.8, 50.0, "s")
    day(a + 0.4, 15.0, "s")
    day(b, 20.0, "s")
    S.front_a.key(a, 0.0).key(a + 1.0, 1.0).key(tl["P60"][1], 1.0).key(T("P61", 0.1), 0.0)
    S.terr_a.key(a, 0.0).key(a + 1.0, 0.4).key(tl["P60"][1], 0.4).key(T("P61", 0.1), 0.0)
    cam(a + 0.6, (49.2400, 5.3300), 14.0, 44, 8)
    cam(b, (49.2350, 5.2700), 13.0, 44, -4)
    guns("fr_gun75", [(49.212, 5.250), (49.206, 5.275), (49.214, 5.300)], a + 0.5, tl["P36"][1], fire=(a + 1.0, tl["P36"][1]),
         rate=2.0, flip=False)
    barrage(a + 1.2, tl["P36"][1], (49.235, 49.265, 5.37, 5.43), 1.0, loud=0.4)
    S.arrows.append(Arrow(T("P35", 0.45), T("P36", 0.5), [(49.285, 5.245), (49.262, 5.245), (49.245, 5.24)], "de", 1.6, 1.2))

    a, b = tl["P36"]
    cam(a + 0.5, (49.2340, 5.2350), 6.5, 48, -4)
    cam(b, (49.2330, 5.2380), 6.0, 50, 4)
    label(T("P36", 0.15), T("P38", 0.9), "HÖHE 304", "cote304", "CÔTE 304")
    label(T("P36", 0.30), T("P38", 0.9), "TOTER MANN", "mort_homme", "MORT-HOMME", side=-1)
    front_barrage(a, tl["P38"][1], 40, 3.0, lon=(5.15, 5.30), depth=(-0.6, 0.8))

    a, b = tl["P37"]
    day(a, 50.0, "s")
    squad("fr_inf_stand", (49.226, 5.236), 6, a + 0.2, b + 0.6, spread=0.010, seed=91)
    cam(b, (49.2300, 5.2400), 6.4, 49, -2)
    ov(T("P37", 0.55), b + 0.8, lambda o, t, k, L: o.quote("Courage ! On les aura !", "Philippe Pétain, Tagesbefehl vom 10. April 1916 · „Mut! Wir kriegen sie!“", k))
    S.sfx.append(Sfx(T("P37", 0.55), "fanfare", 0.7))

    a, b = tl["P38"]
    day(a, 55.0, "s")
    day(b, 101.0, "s")
    cam(a + 0.5, (49.2350, 5.2300), 8.0, 46, 3)
    cam(b, (49.2300, 5.2300), 8.5, 46, -3)

    def ruler_fx(img, t, lay, a=a, b=b):
        k = UI.fade(t, T("P38", 0.55), b + 0.6, 0.5, 0.5)
        if k > 0:
            lay.paint.ruler(img, 49.258, 5.235, 49.220, 5.226, "≈ 4 KM IN 3 MONATEN", _OVL[0], k)
    S.ground_fx.append((a, b + 0.8, ruler_fx))
    S.sfx.append(Sfx(T("P38", 0.85), "pizz", 0.8))

    a, b = tl["P39"]
    day(a, 103.0, "s")
    cam(a + 0.7, (49.2040, 5.4650), 4.0, 52, -6)
    cam(b, (49.2010, 5.4700), 3.0, 55, 4)
    S.flags[1] = (*P["vaux"], [(T_FORTS, "fr"), (T("P40", 0.75), "de"), (T("P58", 0.3), "fr")])
    squad("de_inf_stand", (49.2012, 5.4705), 4, a + 0.5, tl["P40"][1], spread=0.0012, size=260, seed=95, z=40)
    barrage(a, tl["P40"][1], (49.194, 49.208, 5.455, 5.485), 1.6, size=(600, 900))
    label(a + 0.3, T("P40", 0.3), "FORT VAUX", "vaux", "2.–7. JUNI 1916")

    def vaux_section(o, t, k, L, a=a, b=b):
        d = o.d
        x, y, w, h = 1160, 560, 680, 330
        UI.plate(d, (x, y, x + w, y + h), k, cut=14)
        A = int(255 * k)
        d.rectangle((x + 40, y + 90, x + 640, y + 300), fill=(112, 108, 100, A))
        d.rectangle((x + 80, y + 170, x + 600, y + 210), fill=(36, 34, 32, A))
        fl = 0.5 + 0.5 * math.sin(t * 13)
        d.ellipse((x + 290 - 40 * fl, y + 160, x + 330 + 40 * fl, y + 220), fill=(255, 170, 60, int(A * fl)))
        for j in range(3):
            d.ellipse((x + 120 + j * 30, y + 178, x + 138 + j * 30, y + 196), fill=(150, 154, 144, A))
            d.ellipse((x + 470 + j * 30, y + 178, x + 488 + j * 30, y + 196), fill=(104, 138, 186, A))
        for j in range(4):
            d.ellipse((x + 200 + j * 70, y + 70, x + 218 + j * 70, y + 88), fill=(150, 154, 144, A))
        UI.spaced(d, (x + 24, y + 16), "FORT VAUX · KAMPF IN DEN GÄNGEN", UI.font("bold", 26), UI.STYLE["text"] + (A,), 2)
    ov(T("P39", 0.45), b + 0.4, vaux_section)
    S.sfx.append(Sfx(T("P39", 0.45), "tunnel_fight", 0.7, dur=(b - a) * 0.6))

    a, b = tl["P40"]
    day(b, 108.0, "s")
    S.fig("pigeon", [(a + 0.3, 49.2010, 5.4690), (T("P40", 0.5), 49.1620, 5.3880)], size_m=260, z_m=300, t0=a + 0.3,
          t1=T("P40", 0.5) + 0.3, tag="pigeon", flip=True)
    cam(a + 0.4, (49.1900, 5.4400), 9.0, 46, -4)
    cam(b, (49.2000, 5.4600), 5.0, 50, 3)
    for j in range(2):
        S.arrows.append(Arrow(T("P40", 0.35) + j * 0.8, T("P40", 0.35) + j * 0.8 + 1.8,
                              [(49.185, 5.455 + j * 0.01), (49.195, 5.465 + j * 0.005)], "fr", 0.6, 0.6))
    ov(a + 0.3, T("P40", 0.6), lambda o, t, k, L: CD.lower_third(o, k, "MAJOR SYLVAIN-EUGÈNE RAYNAL", "KOMMANDANT FORT VAUX"))

    def water(o, t, k, L, a=a, b=b):
        d = o.d
        x, y = 1600, 300
        lvl = max(0.0, 1 - (t - a) / max(1.0, b - a))
        UI.plate(d, (x - 30, y - 60, x + 200, y + 300), k, cut=12)
        d.rectangle((x + 30, y, x + 140, y + 220), outline=UI.STYLE["text"] + (int(255 * k),), width=4)
        d.rectangle((x + 34, y + 4 + 212 * (1 - lvl), x + 136, y + 216), fill=(80, 140, 200, int(255 * k)))
        UI.spaced(d, (x - 6, y - 50), "WASSER", UI.font("bold", 30), UI.STYLE["text"] + (int(255 * k),), 3)
    ov(T("P40", 0.55), b + 0.3, water)
    S.sfx.append(Sfx(a + 0.3, "wings", 0.7))

    a, b = tl["P41"]
    day(a, 108.0, "s")
    day(a + 1.6, 5.0, "s")
    day(T("P41", 0.85), 118.0, "s")
    cam(a + 0.6, (49.2150, 5.4050), 13.0, 42, -6)
    cam(b + 0.4, (49.2050, 5.4200), 11.0, 44, 5)
    ov(a + 1.3, a + 2.6, lambda o, t, k, L: CD.headline(o, k, "FEBRUAR", y=70))
    ov(T("P41", 0.8), b + 0.5, lambda o, t, k, L: CD.headline(o, k, "JUNI", y=70))

    a, b = tl["P42"]
    cam(a + 0.4, (49.2000, 5.4200), 9.0, 46, -4)
    cam(b, (49.1980, 5.4300), 8.0, 47, 3)
    t = a
    while t < b + 0.4:
        S.booms.append(Boom(t, rng.uniform(49.185, 49.215), rng.uniform(5.39, 5.47), rng.uniform(700, 1000), True, 0.6))
        S.sfx.append(Sfx(t, "boom", 0.5))
        t += 0.45
    ov(a + 0.3, b + 0.5, lambda o, t, k, L: CD.metronome(o, k, t))

    a, b = tl["P43"]
    day(a, 120.0, "s")
    cam(a + 0.6, (49.1975, 5.4410), 1.6, 58, -6)
    cam(b, (49.1972, 5.4405), 1.3, 60, 3)
    crater_pos = (49.1970, 5.4400)
    S.booms.append(Boom(a - 3.0, *crater_pos, 900, True, 0.0))
    for j, (dla, dlo) in enumerate([(0.0006, -0.0020), (-0.0004, 0.0019), (0.0009, 0.0006)]):
        S.fig("fr_inf_kneel", [(a, crater_pos[0] + dla, crater_pos[1] + dlo)], size_m=200, t0=a, t1=tl["P47"][1],
              flip=bool(j % 2), tag=f"cam{j}")
    hero2 = S.fig("fr_inf_kneel", [(a, crater_pos[0] - 0.0002, crater_pos[1] - 0.0001)], size_m=210, t0=a,
                  t1=tl["P47"][1], tag="hero2", swap=[(T("P46", 0.1), "fr_gasmask")])
    S.highlight.append((a + 0.3, tl["P46"][1], hero2, "EIN SOLDAT WIE VIELE"))
    barrage(a, tl["P45"][1], (49.190, 49.205, 5.43, 5.455), 0.8, size=(500, 800), loud=0.5)

    a, b = tl["P44"]
    S.night.key(a - 0.3, 0.0).key(a + 0.6, 0.8).key(b, 0.75).key(T("P45", 0.2), 0.0)
    cam(a + 0.5, (49.1940, 5.4400), 2.6, 56, 4)
    cam(b, (49.1950, 5.4400), 2.4, 56, -2)
    carriers = []
    for j in range(5):
        f = S.fig("fr_carrier", [(a, 49.1890 - j * 0.0008, 5.4370 + j * 0.0012), (b, 49.1955 - j * 0.0004, 5.4395 + j * 0.0006)],
                  size_m=210, t0=a, t1=b + 0.5, flip=False, tag=f"car{j}")
        carriers.append(f)
    for j in (1, 3):
        tb = T("P44", 0.55 + j * 0.08)
        la, lo = carriers[j].pos(tb)
        S.booms.append(Boom(tb, la, lo, 650, True, 0.8))
        S.sfx.append(Sfx(tb, "boom", 0.8))
        carriers[j].t1 = tb + 0.1
        carriers[j].fade = 0.1
    S.sfx.append(Sfx(a, "flare", 0.5))

    a, b = tl["P45"]
    day(a, 123.0, "s")
    cam(a + 0.5, (49.1930, 5.4320), 5.5, 50, -4)
    cam(b, (49.1950, 5.4380), 4.2, 52, 3)
    t = a + 0.6
    while t < b:
        la, lo = rng.uniform(49.185, 49.20), rng.uniform(5.42, 5.45)
        S.booms.append(Boom(t, la, lo, 420, False, 0.3))
        S.sfx.append(Sfx(t, "gas_shell", 0.6))
        t += rng.exponential(0.35)
    for j, w in enumerate([(49.1955, 5.4300), (49.1880, 5.4300), (49.1920, 5.4420)]):
        S.gases.append(Gas(a + 0.8 + j * 0.6, tl["P47"][1], w[0], w[1], 900, (0.0, 0.00004)))
    S.gas.key(a, 0.0).key(a + 3.0, 0.5).key(tl["P46"][1], 0.7).key(T("P47", 0.6), 0.0)
    c0 = T("P45", 0.42)
    S.clips.append(Clip(c0, c0 + 4.6, os.path.join(CLIPS, "K4_gas.mp4"), 49.197, 5.44, speed=0.86))
    cam(c0 - 0.5, (49.1972, 5.4405), 1.2, 62, 0)
    cam(c0 + 4.6, (49.1972, 5.4405), 1.5, 60, 2)
    ov(a + 0.3, c0 - 0.3, lambda o, t, k, L: o.number_card("> 100.000", "GASGRANATEN · GRÜNKREUZ", k))
    S.sfx.append(Sfx(a + 0.3, "hiss", 0.6, dur=(tl["P46"][1] - a)))

    a, b = tl["P46"]
    cam(b + 0.8, (49.1972, 5.4404), 1.1, 62, -2)
    S.sat.key(a, 1.0).key(a + 0.6, 0.6).key(b + 0.8, 0.6).key(T("P47", 0.4), 1.0)
    S.sfx.append(Sfx(a, "mask_breath", 0.8, dur=b - a + 1.0))
    S.sfx.append(Sfx(a, "music_stop", 1.0))

    a, b = tl["P47"]
    day(a, 124.0, "s")
    cam(a + 0.6, (49.1880, 5.4300), 6.0, 48, 5)
    cam(b, (49.1870, 5.4280), 5.5, 49, -3)
    ov(T("P47", 0.4), b + 0.8, lambda o, t, k, L: o.quote("Ils ne passeront pas !", "nach General Robert Nivelle, Tagesbefehl vom 23. Juni 1916 · „Sie werden nicht durchkommen!“",
                                                         k, badge="WORTLAUT UMSTRITTEN"))
    S.sfx.append(Sfx(T("P47", 0.4), "drumroll", 0.6, dur=3.0))

    a, b = tl["P48"]
    cam(a + 0.5, (49.1975, 5.4280), 3.0, 54, -4)
    cam(b, (49.1955, 5.4300), 2.8, 55, 4)
    fl = [(0, "fr")]
    tt = a + 0.4
    step = (b - a - 0.8) / 16
    for i in range(16):
        fl.append((tt + i * step, "de" if i % 2 == 0 else "fr"))
        S.sfx.append(Sfx(tt + i * step, "tick", 0.6))
    S.flags.append((49.1955, 5.4300, fl))
    label(a + 0.2, b + 0.3, "FLEURY", "fleury", "23. JUNI – 17. AUGUST")

    def flips(o, t, k, L, a=a, step=step):
        n = int(min(16, max(0, (t - (a + 0.4)) / step + 1)))
        CD.tick_counter(o, k, n)
    ov(a + 0.3, b + 0.5, flips)

    a, b = tl["P49"]
    day(a, 142.0, "s")
    cam(a + 0.6, (49.1750, 5.4100), 7.5, 45, -4)
    cam(b, (49.1720, 5.4050), 7.0, 46, 3)
    S.arrows.append(Arrow(a + 0.4, T("P50", 0.9), [(49.205, 5.435), (49.196, 5.432), (49.188, 5.431)], "de", 1.5, 1.4))
    squad("de_inf_run", (49.1950, 5.4320), 6, a + 0.5, T("P51", 0.2), dest=(49.1862, 5.4302), tm=(a + 0.5, T("P49", 0.7)),
          spread=0.0015, size=260, seed=99, flip=True)
    label(a + 0.4, T("P50", 0.8), "FORT SOUVILLE", "souville", "11. JULI 1916")
    front_barrage(a, tl["P50"][1], 142, 3.2, lon=(5.38, 5.50), depth=(-0.5, 0.6))

    def ruler2(img, t, lay, a=a, b=b):
        k = UI.fade(t, T("P49", 0.65), T("P50", 0.9), 0.5, 0.4)
        if k > 0:
            lay.paint.ruler(img, 49.1855, 5.4300, 49.1600, 5.3840, "< 5 KM BIS VERDUN", _OVL[0], k)
    S.ground_fx.append((a, tl["P50"][1] + 0.5, ruler2))

    a, b = tl["P50"]
    cam(b + 0.9, (49.1800, 5.4150), 6.6, 46, 0)
    S.sfx.append(Sfx(b + 0.1, "music_stop", 1.0))

    # =============================================================== 6 DIE WENDE
    chapter_card("P51", 5, "DIE WENDE")
    a, b = tl["P51"]
    day(a, 132.0, "s")
    S.mapmix.key(a - 0.6, 0.0).key(a + 1.0, 1.0).key(tl["P52"][1] - 1.0, 1.0).key(tl["P52"][1] + 0.4, 0.0)
    cam(a + 1.0, (49.1300, 5.3500), 70.0, 28, 0)
    cam(b, (49.1500, 5.3700), 62.0, 30, 3)
    eu = IN.Inset(-1.0, 46.5, 9.5, 52.0, 560, 470)
    WF = vgeo.WESTERN_FRONT

    def eu_draw(d, i, tt, a=a, b=b):
        i.line(d, WF, (200, 56, 38, 255), 4)
        i.pin(d, 49.16, 5.384, "VERDUN", tt, color=(104, 138, 186))
        i.pin(d, 49.97, 2.75, "SOMME", tt)
        p = max(0.0, min(1.0, (tt - (a + 1.5)) / 1.5))
        if p > 0:
            i.arrow(d, (50.6, 1.8), (49.97, 2.85), (90, 110, 170, 255), 10, p)
    ov(a + 0.5, b + 0.3, lambda o, t, k, L: IN.place_inset(o, eu.render(eu_draw, t), k, title="WESTFRONT · 1. JULI 1916"))

    a, b = tl["P52"]
    eu2 = IN.Inset(-1.0, 44.0, 32.0, 56.0, 600, 330)

    def eu2_draw(d, i, tt, a=a):
        i.line(d, WF, (200, 56, 38, 255), 3)
        i.pin(d, 49.16, 5.384, "VERDUN", tt, color=(104, 138, 186))
        p = max(0.0, min(1.0, (tt - (a + 0.8)) / 1.6))
        i.arrow(d, (49.6, 5.8), (49.95, 3.2), (150, 154, 144, 255), 8, p)
        i.arrow(d, (50.0, 6.5), (51.0, 22.0), (150, 154, 144, 255), 8, p)
        UI.spaced(d, i.xy(50.4, 3.0), "→ SOMME", UI.font("bold", 22), (20, 20, 22, int(255 * p)), 1)
        UI.spaced(d, i.xy(51.6, 17.0), "→ OSTFRONT", UI.font("bold", 22), (20, 20, 22, int(255 * p)), 1)
    ov(a + 0.3, b + 0.3, lambda o, t, k, L: IN.place_inset(o, eu2.render(eu2_draw, t), k, title="DEUTSCHE TRUPPEN ROLLEN AB"))
    for j in range(5):
        S.fig("de_howitzer", [(a, 49.29 - j * 0.01, 5.40 + j * 0.02), (b + 1.0, 49.42, 5.50 + j * 0.03)], size_m=2200,
              t0=a, t1=b + 0.6, flip=False, tag=f"leave{j}")
    S.sfx.append(Sfx(a, "train", 0.6, dur=b - a))

    a, b = tl["P53"]
    day(a, 160.0, "s")
    day(b, 191.0, "s")
    cam(a + 0.8, (49.2200, 5.4200), 12.0, 44, -4)
    cam(b, (49.2150, 5.4250), 11.0, 45, 4)
    ov(a + 0.3, T("P53", 0.45), lambda o, t, k, L: CD.medallion(o, k, "ERICH VON FALKENHAYN", "29. AUGUST 1916: ABGESETZT"))
    ov(T("P53", 0.25), b + 0.4, lambda o, t, k, L: CD.stamp(o, k, "ABGESETZT", 960, 420, -8, size=80))
    ov(T("P53", 0.48), b + 0.4, lambda o, t, k, L: CD.lower_third(o, k, "NACHFOLGER", "HINDENBURG & LUDENDORFF"))
    S.sfx.append(Sfx(T("P53", 0.25), "stamp", 0.8))

    a, b = tl["P54"]
    rr2 = MF.resample(VS, 200)
    hp = [(a - 0.3 + (b + 1.1 - a) * i / 22, *rr2[192 - i]) for i in range(23)]
    S.fig("fr_truck", hp, size_m=560, t0=a - 0.3, t1=b + 0.8, flip=True, tag="herotruck2")
    hero3 = S.fig("fr_inf_stand", hp, size_m=170, z_m=60, t0=a - 0.3, t1=b + 0.8, flip=True, tag="hero3")
    S.highlight.append((a + 0.2, b + 0.5, hero3, "EIN SOLDAT WIE VIELE"))
    for tt in np.linspace(a, b, 5):
        la, lo = hero3.pos(tt)
        cam(tt, (la + 0.0035, lo), 1.6, 58, 4 - 6 * (tt - a) / max(1, b - a))
    S.sat.key(a, 1.0).key(a + 0.8, 0.75).key(tl["P55"][1], 0.75).key(T("P56"), 1.0)

    a, b = tl["P55"]
    cam(a + 0.6, (49.2020, 5.4400), 1.5, 58, -4)
    cam(b, (49.2025, 5.4395), 1.3, 60, 3)
    S.booms.append(Boom(a - 3.0, 49.2022, 5.4400, 900, True, 0.0))
    de_s = S.fig("de_inf_kneel", [(a, 49.2022, 5.4399)], size_m=210, t0=a, t1=b + 0.6, flip=True, tag="dehero")
    S.highlight.append((a + 0.2, b + 0.4, de_s, "EIN SOLDAT WIE VIELE"))

    a, b = tl["P56"]
    day(a, 247.0, "s")
    S.fog.key(a, 0.2).key(a + 1.0, 0.6).key(b, 0.6).key(T("P57", 0.5), 0.25)
    S.fogscreen.key(a, 0.0).key(a + 1.0, 0.7).key(b, 0.7).key(T("P57", 0.6), 0.0)
    cam(a + 0.6, (49.2050, 5.4300), 6.5, 47, -4)
    cam(b, (49.2100, 5.4350), 5.5, 49, 3)
    guns("fr_gun75", [(49.192, 5.41), (49.190, 5.425), (49.191, 5.44), (49.189, 5.455)], a + 0.3, tl["P57"][1],
         fire=(T("P56", 0.55), tl["P57"][1]), rate=3.0)

    a, b = tl["P57"]
    t = a
    while t < T("P57", 0.62):
        p = (t - a) / max(0.1, T("P57", 0.62) - a)
        la = 49.203 + p * 0.020
        for lo in np.linspace(5.420, 5.458, 5):
            S.booms.append(Boom(t + rng.uniform(0, 0.2), la + rng.normal(0, 0.0008), lo + rng.normal(0, 0.002), 700, True, 0.5))
        S.sfx.append(Sfx(t, "boom", 0.7))
        t += 0.5
    squad("fr_inf_run", (49.2000, 5.4390), 10, a, T("P58", 0.6), dest=(49.2165, 5.4390), tm=(a + 0.3, T("P57", 0.66)),
          spread=0.006, seed=111, flip=False)
    S.flags[0] = (*P["douaumont"], [(T_FORTS, "fr"), (tl["P23"][0] + (tl["P23"][1] - tl["P23"][0]) * 0.55, "de"), (T("P57", 0.6), "fr")])
    cam(a + 0.6, (49.2080, 5.4390), 4.0, 52, -3)
    cam(b, (49.2170, 5.4390), 3.0, 54, 4)
    ov(T("P57", 0.62), b + 0.8, lambda o, t, k, L: CD.headline(o, k, "DOUAUMONT ZURÜCKEROBERT", "24. OKTOBER 1916"))
    ov(a + 0.3, T("P57", 0.6), lambda o, t, k, L: CD.lower_third(o, k, "GENERAL CHARLES MANGIN", "RICM · KOLONIALREGIMENT AUS MAROKKO"))
    S.sfx.append(Sfx(T("P57", 0.62), "triumph", 0.8))

    a, b = tl["P58"]
    day(a, 250.0, "s")
    day(b, 256.0, "s")
    cam(a + 0.4, (49.2050, 5.4650), 5.0, 50, -2)
    cam(b + 0.8, (49.2100, 5.4400), 10.0, 44, 4)
    label(T("P58", 0.2), b + 0.6, "FORT VAUX", "vaux", "2. NOVEMBER 1916")

    # =============================================================== 7 FINALE
    chapter_card("P59", 6, "FINALE")
    a, b = tl["P59"]
    day(a - 0.5, 256.0, "s")
    day(a + 0.6, 299.0, "s")
    day(b, 301.0, "s")
    S.snowfall.key(a - 0.5, 0.0).key(a + 0.8, 0.6).key(tl["P61"][1], 0.4).key(T("P62", 0.3), 0.0)
    cam(a + 0.6, (49.2450, 5.4300), 10.0, 45, -4)
    cam(b, (49.2500, 5.4350), 9.0, 46, 3)
    S.arrows.append(Arrow(a + 0.6, b + 0.4, [(49.232, 5.405), (49.252, 5.408)], "fr", 1.2, 1.2))
    S.arrows.append(Arrow(a + 0.9, b + 0.4, [(49.222, 5.462), (49.240, 5.468)], "fr", 1.2, 1.2))
    label(T("P59", 0.5), b + 0.4, "LOUVEMONT", "louvemont")
    label(T("P59", 0.58), b + 0.4, "BEZONVAUX", "bezonvaux")
    ov(T("P59", 0.72), b + 0.6, lambda o, t, k, L: o.number_card("> 11.000", "DEUTSCHE GEFANGENE", k))
    front_barrage(a, T("P59", 0.7), 299, 2.5, lon=(5.38, 5.50), depth=(0.0, 1.2))

    a, b = tl["P60"]
    day(a, 301.0, "s")
    day(b, 302.0, "h")
    cam(b + 0.8, (49.2400, 5.4100), 12.0, 44, 0)
    for j in range(10):
        S.smokes.append(Smoke(a + j * 0.3, rng.uniform(49.22, 49.26), rng.uniform(5.38, 5.48), 500, 5.0, dark=True))
    S.sfx.append(Sfx(a + 0.2, "last_boom", 1.0))

    a, b = tl["P61"]
    cam(a + 1.2, (49.2400, 5.3600), 24.0, 36, 0)
    cam(b, (49.2350, 5.3650), 22.0, 37, 3)
    S.static_fronts.append((a + 0.6, tl["P64"][1], "feb21", "dashed"))
    S.static_fronts.append((T("P61", 0.45), tl["P64"][1], "dec18", "solid"))
    label(T("P61", 0.25), T("P62", 0.4), "21.02.1916", (49.300, 5.412), "FRONT IM FEBRUAR")
    label(T("P61", 0.55), T("P62", 0.4), "18.12.1916", (49.252, 5.395), "FRONT IM DEZEMBER", side=-1)
    counter(T("P61", 0.1), 1.0)
    counter(T("P61", 0.5), 0.0)

    a, b = tl["P62"]
    cam(b, (49.2450, 5.3800), 18.0, 38, -3)
    feb = FR.by_key["feb21"]
    dec = FR.by_key["dec18"]
    pts = []
    for i in range(700):
        j = rng.integers(0, len(feb))
        u = rng.random()
        la = feb[j][0] * (1 - u) + dec[j][0] * u
        lo = feb[j][1] * (1 - u) + dec[j][1] * u
        pts.append((la, lo, 0 if rng.random() < 0.54 else 1, rng.random()))

    def crosses(img, t, lay, a=a, b=b, pts=pts):
        k = UI.fade(t, a + 0.3, tl["P63"][1], 0.6, 0.6)
        if k <= 0:
            return
        import cv2 as _cv
        sx, sy, ok = lay.paint.screen([(p[0], p[1]) for p in pts])
        for (x, y, o, p) in zip(sx, sy, ok, pts):
            if not o or p[3] > (t - a) / 3.0:
                continue
            col = (104, 138, 186) if p[2] == 0 else (170, 172, 164)
            _cv.line(img, (int(x - 3), int(y)), (int(x + 3), int(y)), col, 2)
            _cv.line(img, (int(x), int(y - 4)), (int(x), int(y + 3)), col, 2)
    S.ground_fx.append((a, tl["P63"][1] + 1.0, crosses))
    ov(T("P62", 0.2), b + 0.5, lambda o, t, k, L: o.number_card("≈ 300.000", "TOTE · FR ≈ 162.000 · DE ≈ 143.000", k, badge="SCHÄTZUNG"))

    a, b = tl["P63"]
    cam(b, (49.2400, 5.3900), 17.0, 39, 3)
    ov(a + 0.2, b + 0.5, lambda o, t, k, L: CD.city(o, k, t))

    a, b = tl["P64"]
    cam(a + 0.6, (49.2400, 5.3900), 16.0, 40, -3)
    cam(b + 0.6, (49.2350, 5.4000), 15.0, 41, 3)
    step = (b - a - 0.6) / 9
    for i, v in enumerate(DESTROYED):
        tv = a + 0.3 + i * step
        S.fig("village_ruin", [(tv, *P[v])], size_m=900, t0=tv, t1=tl["P65"][1], min_px=26, tag="ruin" + v)
        label(tv, tv + step * 2.2, DESTROYED_NAMES[v], v, "MORT POUR LA FRANCE")
        S.sfx.append(Sfx(tv, "bell_soft", 0.5))

    a, b = tl["P65"]
    cam(a + 0.6, (49.2200, 5.3900), 14.0, 40, 4)
    cam(b, (49.2150, 5.3900), 13.0, 42, -2)
    ov(a + 0.1, T("P65", 0.5), lambda o, t, k, L: CD.question(o, k, "WARUM STARBEN HIER\nRUND 300.000 MENSCHEN\nFÜR EIN PAAR KILOMETER?"))
    ov(T("P65", 0.5), b + 0.4, lambda o, t, k, L: CD.headline(o, k, "1 · DER KÖDER", "FALKENHAYNS SPÄTERE BEHAUPTUNG"))

    a, b = tl["P66"]
    cam(b, (49.2200, 5.3950), 12.5, 42, 3)
    ov(a + 0.1, b + 0.3, lambda o, t, k, L, a=a, b=b: CD.document(o, k, t, gone=max(0.0, min(1.0, (t - (a + (b - a) * 0.5)) / 1.4))))
    ov(a + 0.3, b + 0.3, lambda o, t, k, L: CD.headline(o, k, "UMSTRITTEN", color=UI.STYLE["warn"], y=60))

    a, b = tl["P67"]
    cam(a + 0.5, (49.1800, 5.3850), 9.0, 45, -4)
    cam(b, (49.1700, 5.3850), 8.0, 46, 3)
    ov(a + 0.1, b + 0.3, lambda o, t, k, L: CD.headline(o, k, "2 · DAS SYMBOL", y=60))
    ov(T("P67", 0.3), b + 0.4, lambda o, t, k, L: CD.scales(o, k, t))

    a, b = tl["P68"]
    cam(a + 0.5, (49.2250, 5.4200), 10.0, 44, -4)
    cam(b, (49.2200, 5.4250), 9.0, 45, 3)
    guns("de_howitzer", [(49.262, 5.40), (49.265, 5.43), (49.260, 5.46)], a, b + 0.5, fire=(a + 0.5, b), rate=2.5)
    guns("fr_gun75", [(49.192, 5.40), (49.190, 5.43), (49.193, 5.46)], a, b + 0.5, fire=(a + 0.7, b), rate=2.5, flip=True)
    barrage(a + 0.6, b, (49.235, 49.255, 5.38, 5.48), 2.0, loud=0.5)
    barrage(a + 0.8, b, (49.205, 49.225, 5.38, 5.48), 2.0, loud=0.5)
    ov(a + 0.1, b + 0.3, lambda o, t, k, L: CD.headline(o, k, "3 · DIE FALLE", "SCHNAPPTE FÜR BEIDE SEITEN ZU", y=60))

    a, b = tl["P69"]
    cam(a + 0.5, (49.2200, 5.4000), 13.0, 42, 0)
    cam(b + 1.2, (49.2150, 5.4000), 12.4, 42, 1)
    ov(a + 0.1, b + 1.2, lambda o, t, k, L: CD.answer(o, k, "KEIN KAMPF UM KILOMETER.\nEIN KAMPF DARUM,\nWER ZUERST AUFGIBT."), 0.5, 0.6)

    a, b = tl["P70"]
    S.regrow.key(a, 0.0).key(T("P70", 0.6), 1.0)
    S.snow.key(a - 0.5, 0.3).key(a + 0.8, 0.0)
    S.winter.key(a - 0.5, 0.9).key(a + 0.8, 0.0)
    cam(a + 0.6, (49.2150, 5.4300), 6.0, 48, -4)
    cam(b, (49.2100, 5.4255), 3.4, 52, 4)
    S.fig("ossuary", [(a, *P["beinhaus"])], size_m=700, t0=T("P70", 0.45), t1=S.duration, tag="ossuary")
    label(T("P70", 0.5), b + 0.6, "BEINHAUS VON DOUAUMONT", "beinhaus", "≈ 130.000 UNBEKANNTE")
    ov(a + 0.3, T("P70", 0.6), lambda o, t, k, L: CD.headline(o, k, "HEUTE", y=60))
    S.sfx.append(Sfx(a, "birds", 0.6, dur=(tl["P71"][1] - a) + 2))

    a, b = tl["P71"]
    cam(b + 1.0, (49.2095, 5.4255), 2.6, 54, -3)

    def flags84(o, t, k, L):
        pr = L.proj(*P["beinhaus"], 0.0)
        if not pr:
            return
        d = o.d
        x, y = pr[0], pr[1] - 220
        A = int(255 * k)
        for j, cols in enumerate([[(0, 0, 0), (221, 0, 0), (255, 206, 0)], [(0, 85, 164), (255, 255, 255), (239, 65, 53)]]):
            fx = x - 120 + j * 150
            d.line((fx, y, fx, y + 140), fill=(40, 36, 30, A), width=4)
            for i, c in enumerate(cols):
                if j == 0:
                    d.rectangle((fx + 2, y + i * 22, fx + 92, y + (i + 1) * 22), fill=c + (A,))
                else:
                    d.rectangle((fx + 2 + i * 30, y, fx + 2 + (i + 1) * 30, y + 66), fill=c + (A,))
    ov(a + 0.3, b + 1.0, flags84)
    ov(T("P71", 0.3), b + 1.0, lambda o, t, k, L: CD.lower_third(o, k, "22. SEPTEMBER 1984", "HELMUT KOHL & FRANÇOIS MITTERRAND"))

    # =============================================================== 8 OUTRO
    a, b = tl["P72"]
    S.mapmix.key(a - 0.4, 0.0).key(a + 1.4, 1.0)
    cam(a + 1.6, (49.1600, 5.3000), 46.0, 30, -3)
    cam(b, (49.1300, 5.3000), 50.0, 29, -5)
    so = IN.Inset(0.5, 48.6, 7.5, 51.5, 600, 380)

    def so_draw(d, i, tt):
        i.line(d, WF, (200, 56, 38, 255), 4)
        i.pin(d, 49.97, 2.75, "SOMME", tt)
        i.pin(d, 49.16, 5.384, "VERDUN", tt, color=(104, 138, 186))
    ov(a + 0.6, b + 0.4, lambda o, t, k, L: IN.place_inset(o, so.render(so_draw, t), k, title="NÄCHSTER SCHAUPLATZ"))
    ov(T("P72", 0.55), b + 0.6, lambda o, t, k, L: CD.teaser(o, k, t))

    a, b = tl["P73"]
    cam(S.duration, (49.1100, 5.3000), 54.0, 28, -6)
    ov(a - 0.2, S.duration + 1, lambda o, t, k, L: CD.endcard(o, k, t), 0.6, 0.0)
    S.sfx.append(Sfx(a - 0.2, "outro", 1.0))

    # Forts: Ruinen-Bild, sobald das Gelände dort zum Trichterfeld wird (über day-Spur angenähert)
    ruin_day = {"Douaumont": 70, "Vaux": 104, "Souville": 135, "Tavannes": 150}
    for name, d in ruin_day.items():
        tday = _time_of_day(S, d, tl["P16"][0])
        if tday is not None:
            forts[name].swap = [(tday, "fort_ruin")]
    return S


_OVL = [None]      # Overlay-Verweis für Bodengrafiken mit Beschriftung (wird vom Renderer gesetzt)


def _time_of_day(S, d, t0=0.0):
    """Erster Zeitpunkt ab t0, an dem die day-Spur den Wert d erreicht."""
    t = t0
    while t < S.duration:
        if S.day(t) >= d:
            return t
        t += 0.25
    return None
