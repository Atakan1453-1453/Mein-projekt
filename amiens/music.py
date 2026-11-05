"""Filmmusik + Geräusche, passend zur Zeitleiste.

Die Musik wird als MIDI komponiert (Abschnitte je Kapitel/Stimmung) und mit FluidSynth und dem
freien Soundfont FluidR3_GM gerendert. Unter der Sprache wird sie automatisch abgesenkt (Ducking).
Geräusche (Kanonendonner, Gefechte, Explosionen) werden synthetisch erzeugt.

  python3 music.py      → out/music.wav, out/sfx.wav, out/voice_plan.json
"""
import json
import math
import os
import random
import subprocess

import mido
import numpy as np
from scipy import signal
from scipy.io import wavfile

import engine as E
import scenes

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("CNK_OUT", os.path.join(HERE, "out"))
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
SR = 48000

# ---------------------------------------------------------------- Harmonik
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"])}


def chord(name, octave=3):
    """'Dm', 'Bb', 'A', 'Gm', 'Eb', 'C', 'F', 'D' → MIDI-Noten (Grundton, Terz, Quinte)."""
    minor = name.endswith("m")
    root = NOTE[name[:-1] if minor else name]
    base = 12 * (octave + 1) + root
    return [base, base + (3 if minor else 4), base + 7]


# ---------------------------------------------------------------- Amiens 1918: eigene Musik (e-Moll, Leitmotiv)
#            bpm  Akkordfolge                                          Intensität  Stil        Takt
MOODS = {
    "intro":     (64, ["Em", "C", "G", "D", "Em", "Am", "B", "B"], 0.35, "cello", 4),
    "world":     (84, ["Em", "D", "C", "B", "Em", "D", "C", "B"], 0.55, "march", 4),
    "offensive": (104, ["Em", "Em", "C", "D", "Em", "Am", "B", "B"], 0.95, "fanfare", 4),
    "air":       (72, ["G", "D", "Em", "C", "G", "Bm", "C", "D"], 0.6, "soar", 3),
    "steel":     (96, ["Em", "F", "Em", "D", "Em", "C", "B", "B"], 0.85, "ostinato", 4),
    "plan":      (88, ["Am", "Em", "F", "E", "Am", "Dm", "E", "E"], 0.5, "clock", 4),
    "battle":    (112, ["Em", "C", "D", "B", "Em", "G", "Am", "B"], 1.0, "fanfare", 4),
    "after":     (66, ["Am", "F", "C", "G", "Am", "F", "E", "E"], 0.45, "cello", 4),
    "hundred":   (92, ["C", "G", "Am", "Em", "F", "C", "Dm", "G"], 0.75, "march", 4),
    "legacy":    (60, ["G", "D", "Em", "C", "G", "D", "C", "G"], 0.5, "hymn", 4),
}
TONIC = {"intro": ("E", "min"), "world": ("E", "min"), "offensive": ("E", "min"), "air": ("G", "maj"), "steel": ("E", "min"),
         "plan": ("A", "min"), "battle": ("E", "min"), "after": ("A", "min"), "hundred": ("C", "maj"), "legacy": ("G", "maj")}
# Leitmotiv (Tonleiterstufen, Dauer in Schlägen): E – H – A – G – E – Dis – E, Antwort G A H C H A Fis
THEME_A = [(0, 1.5), (4, 0.5), (3, 1), (2, 1), (0, 2), (-1, 1), (0, 1)]
THEME_B = [(2, 1), (3, 1), (4, 1.5), (5, 0.5), (4, 1), (3, 1), (1, 2)]
SCALES = {"min": [0, 2, 3, 5, 7, 8, 11], "maj": [0, 2, 4, 5, 7, 9, 11]}


def degree(tonic, mode, d, octave=4):
    iv = SCALES[mode]
    base = 12 * (octave + 1) + NOTE[tonic]
    return base + 12 * (d // 7) + iv[d % 7]


# GM-Programme
P_STR, P_BASS, P_CELLO, P_TIMP, P_HORN, P_TBN, P_CHOIR, P_HARP, P_TPT, P_FLUTE, P_TUBA, P_PIZZ, P_CLAR, P_STRTREM = (
    48, 43, 42, 47, 60, 57, 52, 46, 56, 73, 58, 45, 71, 44)

class Song:
    def __init__(self, bpm):
        self.bpm = bpm
        self.mid = mido.MidiFile(ticks_per_beat=480)
        self.ev = {}       # channel → [(tick, msg)]
        self.programs = {}

    def prog(self, ch, program, vol=100, pan=64):
        self.programs[ch] = (program, vol, pan)

    def note(self, ch, beat, dur, pitch, vel):
        t0 = int(beat * 480)
        t1 = int((beat + dur) * 480) - 4
        vel = max(1, min(127, int(vel)))
        self.ev.setdefault(ch, []).append((t0, mido.Message("note_on", channel=ch, note=pitch, velocity=vel)))
        self.ev.setdefault(ch, []).append((t1, mido.Message("note_off", channel=ch, note=pitch, velocity=0)))

    def cc(self, ch, beat, ctrl, val):
        self.ev.setdefault(ch, []).append((int(beat * 480), mido.Message("control_change", channel=ch, control=ctrl, value=int(max(0, min(127, val))))))

    def save(self, path):
        tr0 = mido.MidiTrack()
        tr0.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(self.bpm), time=0))
        self.mid.tracks.append(tr0)
        for ch, (program, vol, pan) in self.programs.items():
            tr = mido.MidiTrack()
            tr.append(mido.Message("program_change", channel=ch, program=program, time=0))
            tr.append(mido.Message("control_change", channel=ch, control=7, value=vol, time=0))
            tr.append(mido.Message("control_change", channel=ch, control=10, value=pan, time=0))
            tr.append(mido.Message("control_change", channel=ch, control=91, value=90, time=0))
            evs = sorted(self.ev.get(ch, []), key=lambda e: (e[0], e[1].type == "note_on"))
            last = 0
            for tick, msg in evs:
                tr.append(msg.copy(time=tick - last))
                last = tick
            self.mid.tracks.append(tr)
        self.mid.save(path)


def compose(mood, seconds, seed, last=False):
    bpm, prog, inten, style, meter = MOODS[mood]
    tonic, mode = TONIC[mood]
    rnd = random.Random(seed)
    s = Song(bpm)
    beats_total = seconds * bpm / 60.0
    bars = int(math.ceil(beats_total / meter)) + 2
    s.prog(0, P_STR, 100, 64)
    s.prog(1, P_BASS, 96, 54)
    s.prog(2, P_CELLO, 92, 50)
    s.prog(3, P_TIMP, 108, 64)
    s.prog(4, P_HORN, 94, 74)
    s.prog(5, P_CHOIR, 78, 64)
    s.prog(6, P_CLAR if style == "clock" else P_HARP, 84, 84)
    s.prog(8, P_TBN, 92, 44)
    s.prog(11, P_STRTREM, 80, 60)
    s.prog(12, P_TPT, 96, 70)
    s.prog(13, P_FLUTE, 92, 80)
    s.prog(14, P_TUBA, 96, 50)
    s.prog(15, P_PIZZ, 96, 40)
    mel_oct = {"cello": 2, "soar": 5, "fanfare": 4, "march": 4, "hymn": 4, "ostinato": 4, "clock": 4}[style]
    k3 = meter / 4.0
    for b in range(bars):
        name = prog[b % len(prog)]
        ch3 = chord(name, 3)
        beat0 = b * meter
        pos = b / max(1, bars - 1)
        arc = 0.62 + 0.38 * math.sin(math.pi * min(1, pos * 1.1))
        v = (40 + 62 * inten) * arc
        # Streicher-Fläche und Bass
        if style == "soar":
            arp = [ch3[0] + 12, ch3[1] + 12, ch3[2] + 12, ch3[1] + 24, ch3[2] + 12, ch3[1] + 12]
            for kk in range(6):
                s.note(0, beat0 + kk * 0.5, 0.55, arp[kk], v * 0.55)
            s.note(1, beat0, meter, ch3[0] - 12, v * 0.7)
        else:
            for p in ch3:
                s.note(0, beat0, meter, p + 12, v * 0.72)
            s.note(1, beat0, meter, ch3[0] - 12, v * 0.9)
        # Stil-Begleitung
        if style == "march":
            for kk, (bt, vel) in enumerate(((0, 1.0), (0.75, 0.5), (1, 0.8), (2, 0.9), (2.5, 0.5), (2.75, 0.6), (3, 0.8), (3.5, 0.6))):
                s.note(9, beat0 + bt, 0.25, 38, v * 0.55 * vel)
            s.note(9, beat0, 0.5, 36, v * 0.8)
            s.note(9, beat0 + 2, 0.5, 36, v * 0.7)
            if b % 8 == 0:
                s.note(9, beat0, 2, 49, v * 0.7)
            for kk in range(4):
                s.note(2, beat0 + kk, 0.9, ch3[0] + (7 if kk % 2 else 0), v * 0.7)
        elif style == "fanfare":
            for kk in range(16):
                s.note(11, beat0 + kk * 0.25, 0.25, ch3[2] + 12 + (12 if kk % 4 == 0 else 0), v * 0.45)
            for kk in range(8):
                s.note(2, beat0 + kk * 0.5, 0.5, ch3[0] + (12 if kk % 2 else 0), v * 0.8)
            s.note(3, beat0, 1, ch3[0], v * 1.05)
            s.note(3, beat0 + 2.5, 0.5, ch3[0], v * 0.8)
            if b % 4 == 3:
                for kk in range(8):
                    s.note(3, beat0 + 2 + kk * 0.25, 0.25, ch3[0], v * (0.5 + kk * 0.07))
            for kk in range(8):
                s.note(9, beat0 + kk * 0.5, 0.25, 38, v * (0.5 + 0.3 * (kk % 2 == 0)))
            s.note(9, beat0, 1, 36, v * 0.9)
            s.note(9, beat0 + 2, 1, 36, v * 0.8)
            if b % 8 == 0:
                s.note(9, beat0, 2, 57, v * 0.75)
            if b % 8 >= 4:
                for p in ch3:
                    s.note(5, beat0, meter, p + 12, v * 0.5)
        elif style == "ostinato":
            pat = [0, 0, 1, 0, 0, 0, -1, 0]
            for kk, d in enumerate(pat):
                s.note(14, beat0 + kk * 0.5, 0.45, degree(tonic, "min", d, 1) + (1 if d == 1 else 0), v * (0.85 if kk % 4 == 0 else 0.6))
                s.note(8, beat0 + kk * 0.5, 0.45, degree(tonic, "min", d, 2) + (1 if d == 1 else 0), v * (0.7 if kk % 4 == 0 else 0.45))
            s.note(3, beat0, 1, ch3[0], v)
            s.note(9, beat0 + 1, 0.25, 38, v * 0.5)
            s.note(9, beat0 + 3, 0.25, 38, v * 0.5)
            if b % 2 == 1:
                s.note(11, beat0, meter, ch3[2] + 24, v * 0.5)
        elif style == "clock":
            for kk in range(8):
                s.note(15, beat0 + kk * 0.5, 0.3, (ch3[0] + 12) if kk % 2 == 0 else (ch3[2] + 12), v * 0.75)
                s.note(9, beat0 + kk * 0.5, 0.1, 76 if kk % 2 == 0 else 77, v * 0.35)
            if b % 4 == 3:
                s.note(3, beat0, 4, ch3[0], v * 0.6)
        elif style == "cello":
            arp = [ch3[0] + 12, ch3[1] + 12, ch3[2] + 12, ch3[0] + 24]
            for kk in range(8):
                s.note(6, beat0 + kk * 0.5, 0.6, arp[kk % 4] + (12 if kk >= 4 else 0), v * 0.4)
            if b % 4 == 0:
                s.note(3, beat0, 4, ch3[0], v * 0.45)
        elif style == "hymn":
            for p in ch3:
                s.note(5, beat0, meter, p + 12, v * 0.6)
                s.note(4, beat0, meter, p, v * 0.5)
            if b % 4 == 3:
                for kk in range(8):
                    s.note(3, beat0 + 2 + kk * 0.25, 0.25, ch3[0], v * (0.35 + kk * 0.05))
        elif style == "soar":
            if b % 6 == 0:
                s.note(9, beat0, 3, 52, v * 0.35)
        # Leitmotiv: A (2 Takte) + B (2 Takte), alle vier Takte, ab Takt 2
        if b >= 2 and (b - 2) % 4 in (0, 2):
            phrase = THEME_A if (b - 2) % 8 < 4 and (b - 2) % 4 == 0 else (THEME_B if (b - 2) % 4 == 2 else THEME_A)
            if (b - 2) % 8 >= 4 and (b - 2) % 4 == 0:
                phrase = [(d + 2, du) for d, du in THEME_A]          # Variation eine Terz höher
            t = 0.0
            for d, du in phrase:
                du2 = du * k3 if meter == 3 else du
                p = degree(tonic, mode, d, mel_oct)
                if style == "fanfare":
                    s.note(12, beat0 + t, du2, p + 12, v * 1.0)
                    s.note(4, beat0 + t, du2, p, v * 0.85)
                    s.note(8, beat0 + t, du2, p - 12, v * 0.7)
                elif style == "march":
                    s.note(4, beat0 + t, du2, p, v * 0.95)
                    if b % 8 >= 4:
                        s.note(12, beat0 + t, du2, p + 12, v * 0.7)
                elif style == "soar":
                    s.note(13, beat0 + t, du2 * 1.02, p, v * 0.9)
                    s.note(0, beat0 + t, du2, p - 12, v * 0.4)
                elif style == "cello":
                    s.note(2, beat0 + t, du2, p, v * 0.95)
                elif style == "ostinato":
                    s.note(4, beat0 + t, du2, p, v * 0.9)
                elif style == "clock":
                    s.note(6, beat0 + t, du2, p, v * 0.75)
                elif style == "hymn":
                    s.note(12, beat0 + t, du2, p + 12, v * 0.8)
                t += du2
    if last:
        endb = bars * meter
        for p in chord(tonic, 3):
            s.note(0, endb, 8, p + 12, 80)
            s.note(5, endb, 8, p + 12, 62)
        s.note(1, endb, 8, chord(tonic, 3)[0] - 12, 80)
        s.note(12, endb, 8, chord(tonic, 3)[0] + 24, 60)
    return s


def render_mood(mood, seconds, seed, last=False):
    os.makedirs(os.path.join(OUT, "music"), exist_ok=True)
    mid = os.path.join(OUT, "music", f"{seed:02d}_{mood}.mid")
    wav = mid.replace(".mid", ".wav")
    compose(mood, seconds + 6, seed, last).save(mid)
    subprocess.run(["fluidsynth", "-ni", "-g", "0.55", "-r", str(SR), "-o", "synth.reverb.room-size=0.85",
                    "-o", "synth.reverb.width=1.0", "-o", "synth.reverb.level=0.75", "-F", wav, SF2, mid],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sr, a = wavfile.read(wav)
    a = a.astype(np.float32) / 32768.0
    if a.ndim == 1:
        a = np.stack([a, a], 1)
    return a


def envelope_points(n, pts):
    """Stückweise lineare Hüllkurve aus [(t, gain)]."""
    t = np.arange(n) / SR
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return np.interp(t, xs, ys).astype(np.float32)


# ---------------------------------------------------------------- Geräusche
def boom(dur=2.5, low=45.0, rnd=None):
    rnd = rnd or np.random.default_rng(0)
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rnd.standard_normal(n).astype(np.float32)
    b, a = signal.butter(2, 380 / (SR / 2), "low")
    rumble = signal.lfilter(b, a, noise) * np.exp(-t * 2.2)
    thump = np.sin(2 * np.pi * low * t * (1 - 0.25 * t)) * np.exp(-t * 4.0)
    crack = signal.lfilter(*signal.butter(2, [800 / (SR / 2), 4000 / (SR / 2)], "band"), noise) * np.exp(-t * 30)
    x = 0.9 * rumble / (np.abs(rumble).max() + 1e-9) + 0.8 * thump + 0.25 * crack / (np.abs(crack).max() + 1e-9)
    return x.astype(np.float32)


def gunfire(dur=0.12, rnd=None):
    rnd = rnd or np.random.default_rng(1)
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rnd.standard_normal(n).astype(np.float32)
    b, a = signal.butter(2, [300 / (SR / 2), 2500 / (SR / 2)], "band")
    return (signal.lfilter(b, a, noise) * np.exp(-t * 45)).astype(np.float32)


def place(buf, clip, t, gain, pan=0.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    clip = clip[: len(buf) - i]
    l = gain * math.cos((pan + 1) * math.pi / 4)
    r = gain * math.sin((pan + 1) * math.pi / 4)
    buf[i:i + len(clip), 0] += clip * l
    buf[i:i + len(clip), 1] += clip * r


def engine_rumble(dur, rnd):
    """Panzermotoren: tiefes Dröhnen mit Kettenrasseln."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rnd.standard_normal(n).astype(np.float32)
    low = signal.lfilter(*signal.butter(2, 140 / (SR / 2), "low"), noise)
    low /= (np.abs(low).max() + 1e-9)
    hum = np.sin(2 * np.pi * 36 * t + 0.6 * np.sin(2 * np.pi * 0.7 * t)) * 0.5
    clank = signal.lfilter(*signal.butter(2, [900 / (SR / 2), 3000 / (SR / 2)], "band"), noise)
    clank = clank / (np.abs(clank).max() + 1e-9) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 6.5 * t))) * 0.25
    x = (0.8 * low + hum + clank) * envelope_points(n, [(0, 0), (1.5, 1), (max(1.6, dur - 2), 1), (dur, 0)])
    return x.astype(np.float32)


def plane_drone(dur, f0, rnd):
    """Kolbenmotor eines Doppeldeckers: Sägezahn-Grundton mit Obertönen, an- und abschwellend."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + 0.06 * np.sin(2 * np.pi * t / max(dur, 1) * 1.0) + 0.01 * np.sin(2 * np.pi * 5 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(k * ph) / k for k in range(1, 9))
    x = signal.lfilter(*signal.butter(2, 1100 / (SR / 2), "low"), x)
    x = x / (np.abs(x).max() + 1e-9) * envelope_points(n, [(0, 0), (min(3, dur / 3), 1), (max(0.1, dur - 3), 1), (dur, 0)])
    return x.astype(np.float32)


def build_sfx(tl, n):
    sfx = np.zeros((n, 2), np.float32)
    rnd = np.random.default_rng(7)
    booms = [boom(rnd=rnd) for _ in range(6)]
    shots = [gunfire(rnd=rnd) for _ in range(8)]
    for o in tl.objects:
        name = type(o).__name__
        if name == "Explosion":
            place(sfx, booms[0] * 1.0, o.t0, 0.55, 0.0)
        elif name == "Battle":
            dur = max(0.0, min(o.t1, tl.duration) - o.t0)
            nb = int(dur * 0.9 * o.intensity)
            for k in range(nb):
                tt = o.t0 + rnd.random() * dur
                place(sfx, booms[k % len(booms)], tt, 0.10 + 0.08 * rnd.random(), rnd.uniform(-0.6, 0.6))
            ns = int(dur * 5 * o.intensity)
            for k in range(ns):
                tt = o.t0 + rnd.random() * dur
                place(sfx, shots[k % len(shots)], tt, 0.05 + 0.05 * rnd.random(), rnd.uniform(-0.8, 0.8))
        elif name == "Barrage":
            dur = max(0.0, min(o.t1, tl.duration) - o.t0)
            nb = int(dur * min(7.0, o.rate * 0.14))
            for k in range(nb):
                place(sfx, booms[k % len(booms)], o.t0 + rnd.random() * dur, 0.06 + 0.07 * rnd.random(), rnd.uniform(-0.8, 0.8))
        elif name == "Troops":
            for u in o.units:
                for ta, tb in u.fire:
                    ta, tb = max(ta, o.t0), min(tb, o.t1, tl.duration)
                    for k in range(int(max(0.0, tb - ta) * 7)):
                        place(sfx, shots[k % len(shots)], ta + rnd.random() * (tb - ta), 0.035 + 0.04 * rnd.random(), rnd.uniform(-0.9, 0.9))
        elif name == "Guns" and o.fire:
            for ta, tb in o.fire:
                ta, tb = max(ta, o.t0), min(tb, o.t1, tl.duration)
                for k in range(int(max(0.0, tb - ta) * 1.6)):
                    place(sfx, booms[(k + 3) % len(booms)] * 0.7, ta + rnd.random() * (tb - ta), 0.05, rnd.uniform(-0.8, 0.8))
        elif name == "ShellArcs":
            n = int((o.t1 - o.t0) / o.every) + 1
            for k in range(n):
                place(sfx, booms[2], o.t0 + k * o.every + o.flight, 0.30, 0.1)
        elif name == "Ship" and o.sink is not None:
            place(sfx, booms[2], o.sink, 0.45, 0.0)
            place(sfx, booms[4] * 0.6, o.sink + 0.7, 0.3, 0.2)
        elif name == "Ship" and o.fire:
            for ta, tb in o.fire:
                for k in range(int((tb - ta) * 0.25)):
                    place(sfx, booms[(k + 1) % len(booms)], ta + rnd.random() * (tb - ta), 0.06, rnd.uniform(-0.7, 0.7))
    # Panzer: Motoren, solange sie fahren; Treffer
    for o in tl.objects:
        name = type(o).__name__
        if name == "Tanks":
            for g in o.groups:
                ta, tb = g.keys[0][0], min(g.keys[-1][0], tl.duration - 1)
                if tb - ta < 1:
                    continue
                gain = min(0.03, 0.006 * math.log2(1 + g.n))
                place(sfx, engine_rumble(tb - ta + 2.0, rnd), ta, gain, rnd.uniform(-0.4, 0.4))
                for tk in g.ko[np.isfinite(g.ko)]:
                    if tk < tl.duration:
                        place(sfx, booms[int(rnd.integers(0, 6))], float(tk), 0.22, rnd.uniform(-0.6, 0.6))
        elif name == "AirWar":
            ps = o.planes
            ta, tb = o.t0, min(o.t1, tl.duration - 0.5)
            if tb - ta < 1:
                continue
            for j, f0 in enumerate((96.0, 118.0, 141.0)[: min(3, len(ps))]):
                place(sfx, plane_drone(tb - ta, f0 * (0.97 + 0.06 * rnd.random()), rnd), ta + j * 0.4,
                      min(0.10, 0.03 + 0.01 * len(ps)), (-0.5, 0.5, 0.0)[j])
            for f0, f1 in o.fights:
                for k in range(int(max(0.0, f1 - f0) * 6)):
                    tt = f0 + rnd.random() * (f1 - f0)
                    for r in range(5):
                        place(sfx, shots[(k + r) % len(shots)] * 0.8, tt + r * 0.07, 0.05, rnd.uniform(-0.7, 0.7))
            for pl in ps:
                if pl.shot is not None and pl.shot + 5.5 < tl.duration:
                    place(sfx, booms[1], pl.shot + 5.5, 0.30, rnd.uniform(-0.5, 0.5))
    # sanft begrenzen
    sfx = np.tanh(sfx * 1.2) / 1.2
    return sfx


def main():
    os.makedirs(OUT, exist_ok=True)
    tl = scenes.build()
    n = int((tl.duration + 0.5) * SR)
    music = np.zeros((n, 2), np.float32)
    cues = sorted(tl.music) + [(tl.duration, None)]
    xf = 3.0
    for i, ((t0, mood), (t1, _)) in enumerate(zip(cues, cues[1:])):
        seg = render_mood(mood, t1 - t0 + xf, i, last=(i == len(cues) - 2))
        i0 = int(t0 * SR)
        L = min(len(seg), n - i0)
        seg = seg[:L]
        fin = np.clip(np.arange(L) / (xf * SR), 0, 1) if i > 0 else np.ones(L)
        tail_start = int((t1 - t0) * SR)
        fout = np.clip(1 - (np.arange(L) - tail_start) / (xf * SR), 0, 1)
        if i == len(cues) - 2:
            fout = np.ones(L)
        g = (np.sin(fin * np.pi / 2) * np.cos((1 - fout) * np.pi / 2)).astype(np.float32)
        music[i0:i0 + L] += seg * g[:, None]
        print(f"Musik {mood:9s} {t0:7.1f}–{t1:7.1f}s", flush=True)
    # Normieren
    music /= (np.abs(music).max() + 1e-9)
    # Ducking unter der Sprache
    pts = [(0, 1.0)]
    for k, st in sorted(tl.vstart.items(), key=lambda x: x[1]):
        en = st + tl.vdur[k]
        pts += [(st - 0.6, 1.0), (st, 0.30), (en, 0.30), (en + 0.9, 1.0)]
    pts.append((tl.duration + 1, 1.0))
    pts.sort()
    duck = envelope_points(n, pts)
    fade = envelope_points(n, [(0, 0.0), (2.0, 1.0), (tl.duration - 5, 1.0), (tl.duration, 0.0)])
    music *= (duck * fade)[:, None] * 0.55
    sfx = build_sfx(tl, n) * (0.55 + 0.45 * duck)[:, None]
    wavfile.write(os.path.join(OUT, "music.wav"), SR, (np.clip(music, -1, 1) * 32767).astype(np.int16))
    wavfile.write(os.path.join(OUT, "sfx.wav"), SR, (np.clip(sfx, -1, 1) * 32767).astype(np.int16))
    order = {k: i for i, (k, _) in enumerate(scenes.SEGMENTS)}
    plan = {"duration": round(tl.duration, 3),
            "voice": [{"index": order[k], "key": k, "start": round(st, 3)} for k, st in sorted(tl.vstart.items(), key=lambda x: x[1])]}
    json.dump(plan, open(os.path.join(OUT, "voice_plan.json"), "w"), indent=1)
    print("fertig:", tl.duration, "s")


if __name__ == "__main__":
    main()
