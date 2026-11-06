"""Story-Engine: Zeitleiste, Keyframe-Spuren, Kamera in Geo-Koordinaten, Objekte auf der Karte.

Alles ist zeitbasiert (Sekunden im fertigen Video). Ein Szenen-Skript (projects/<video>/scenes.py) füllt
eine Story; der Renderer fragt pro Bild den Zustand zur Zeit t ab.
"""
import bisect
import math
from dataclasses import dataclass, field


def smooth(k):
    k = min(max(k, 0.0), 1.0)
    return k * k * (3 - 2 * k)


def smoother(k):
    k = min(max(k, 0.0), 1.0)
    return k * k * k * (k * (6 * k - 15) + 10)


class Track:
    """Zahlenspur: Keyframes (t, v, ease). ease ∈ {'s' (smooth), 'l' (linear), 'h' (hold)} gilt für das Segment
    ab diesem Keyframe."""

    def __init__(self, default=0.0):
        self.keys = []
        self.default = default

    def key(self, t, v, ease="s"):
        i = bisect.bisect_right([k[0] for k in self.keys], t)
        self.keys.insert(i, (t, v, ease))
        return self

    def __call__(self, t):
        ks = self.keys
        if not ks:
            return self.default
        if t <= ks[0][0]:
            return ks[0][1]
        if t >= ks[-1][0]:
            return ks[-1][1]
        i = bisect.bisect_right([k[0] for k in ks], t) - 1
        (ta, va, ea), (tb, vb, _) = ks[i], ks[i + 1]
        if ea == "h":
            return va
        k = (t - ta) / max(1e-9, tb - ta)
        if ea == "s":
            k = smoother(k)
        return va + (vb - va) * k


@dataclass
class GeoCam:
    lat: float
    lon: float
    km: float              # sichtbare Breite am Zielpunkt
    pitch: float = 45.0
    yaw: float = 0.0
    fov: float = 34.0


class CamTrack:
    def __init__(self):
        self.keys = []          # (t, GeoCam, ease)

    def key(self, t, cam, ease="s"):
        i = bisect.bisect_right([k[0] for k in self.keys], t)
        self.keys.insert(i, (t, cam, ease))

    def __call__(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            c = ks[0][1]
        elif t >= ks[-1][0]:
            c = ks[-1][1]
        else:
            i = bisect.bisect_right([k[0] for k in ks], t) - 1
            (ta, a, ea), (tb, b, _) = ks[i], ks[i + 1]
            k = (t - ta) / max(1e-9, tb - ta)
            k = smoother(k) if ea == "s" else (k if ea == "l" else 0.0)
            c = GeoCam(a.lat + (b.lat - a.lat) * k, a.lon + (b.lon - a.lon) * k,
                       math.exp(math.log(a.km) + (math.log(b.km) - math.log(a.km)) * k),
                       a.pitch + (b.pitch - a.pitch) * k, a.yaw + (b.yaw - a.yaw) * k, a.fov + (b.fov - a.fov) * k)
        # ständige leichte Bewegung (nie Stillstand)
        drift = 0.8 * math.sin(t * 0.21) + 0.5 * math.sin(t * 0.13 + 1.0)
        return GeoCam(c.lat, c.lon, c.km * (1 + 0.012 * math.sin(t * 0.31)), c.pitch + 0.6 * math.sin(t * 0.17),
                      c.yaw + drift, c.fov)


@dataclass
class Fig:
    sprite: str
    path: list                       # [(t, lat, lon)]
    size_m: float = 280.0            # Höhe der Figur in Metern (Spielfiguren-Maßstab)
    flip: bool = False
    t0: float = -1e9
    t1: float = 1e9
    z_m: float = 0.0                 # Schwebehöhe (Ballon, Flugzeug)
    bob: float = 0.0
    min_px: float = 16.0
    fade: float = 0.4
    tag: str = ""
    swap: list = field(default_factory=list)   # [(t, sprite)] – Bildwechsel (z. B. Fort → Ruine)

    def pos(self, t):
        p = self.path
        if t <= p[0][0]:
            return p[0][1], p[0][2]
        for (ta, la, loa), (tb, lb, lob) in zip(p, p[1:]):
            if t <= tb:
                k = smooth((t - ta) / max(1e-6, tb - ta))
                return la + (lb - la) * k, loa + (lob - loa) * k
        return p[-1][1], p[-1][2]

    def alpha(self, t):
        if t < self.t0 or t > self.t1:
            return 0.0
        if self.fade <= 0:
            return 1.0
        return min(1.0, (t - self.t0) / self.fade, (self.t1 - t) / self.fade)

    def sprite_at(self, t):
        s = self.sprite
        for (ts, sp) in self.swap:
            if t >= ts:
                s = sp
        return s

    def moving_left(self, t):
        a = self.pos(t - 0.1)
        b = self.pos(t + 0.1)
        return b[1] < a[1]


@dataclass
class Boom:
    t: float
    lat: float
    lon: float
    size_m: float = 1100.0
    crater: bool = True
    loud: float = 1.0


@dataclass
class Smoke:
    t: float
    lat: float
    lon: float
    size_m: float = 220.0
    dur: float = 4.0
    dark: bool = False


@dataclass
class Gas:
    t0: float
    t1: float
    lat: float
    lon: float
    radius_m: float = 900.0
    drift: tuple = (0.0, 0.0)        # Grad pro Sekunde (lat, lon)


@dataclass
class Fire:
    t0: float
    t1: float
    lat: float
    lon: float
    size_m: float = 300.0


@dataclass
class Arrow:
    t0: float
    t1: float
    path: list                       # [(lat, lon)]
    side: str = "de"                 # de | fr
    width_km: float = 0.9
    grow: float = 1.2                # Sekunden zum Ausfahren
    dashed: bool = False


@dataclass
class Label:
    t0: float
    t1: float
    text: str
    lat: float
    lon: float
    sub: str = None
    side: int = 1


@dataclass
class Muzzle:
    t: float
    fig: Fig


@dataclass
class Clip:
    t0: float
    t1: float
    path: str
    lat: float
    lon: float
    speed: float = 1.0


@dataclass
class Sfx:
    t: float
    kind: str
    gain: float = 1.0
    dur: float = 0.0


class Story:
    def __init__(self, timeline):
        self.tl = timeline                     # {pid: (t0, t1)}
        self.duration = max(v[1] for v in timeline.values()) + 4.0
        self.cam = CamTrack()
        T = Track
        self.day = T(1.0)
        self.snow = T(0.0)
        self.winter = T(0.0)
        self.night = T(0.0)
        self.dawn = T(0.0)
        self.fog = T(0.18)
        self.gas = T(0.0)
        self.regrow = T(0.0)
        self.sat = T(1.0)
        self.mapmix = T(0.0)                   # 0 = Detailkarte L3, 1 = Regionalkarte L2
        self.front_a = T(0.0)                  # Sichtbarkeit Frontlinie
        self.terr_a = T(0.0)                   # Sichtbarkeit Gebietsfärbung
        self.counter_a = T(0.0)
        self.snowfall = T(0.0)
        self.rain = T(0.0)
        self.fogscreen = T(0.0)
        self.figs, self.booms, self.smokes, self.gases, self.fires = [], [], [], [], []
        self.arrows, self.labels, self.muzzles, self.clips, self.sfx = [], [], [], [], []
        self.overlays = []                     # (t0, t1, fn(ov, t, k, R)) – k = Sichtbarkeit 0..1
        self.ground_fx = []                    # (t0, t1, fn(frame, t, k, ctx))
        self.static_fronts = []                # (t0, t1, front_key, style)
        self.highlight = []                    # (t0, t1, Fig, text)
        self.flags = []                        # (lat, lon, [(t_from, side)]) Wimpel an Forts

    # Hilfen
    def P(self, pid):
        return self.tl[pid]

    def at(self, pid, frac):
        a, b = self.tl[pid]
        return a + (b - a) * frac

    def overlay(self, t0, t1, fn, fin=0.4, fout=0.4):
        self.overlays.append((t0, t1, fn, fin, fout))

    def fig(self, *a, **k):
        f = Fig(*a, **k)
        self.figs.append(f)
        return f
