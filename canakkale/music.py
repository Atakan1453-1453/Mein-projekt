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


HICAZ = [62, 63, 66, 67, 69, 70, 72, 74]          # D Eb F# G A Bb C D
DMINOR = [62, 64, 65, 67, 69, 70, 72, 74]

MOODS = {
    #            bpm  progression                                 intensity  melody
    "intro":    (60, ["Dm", "Bb", "Gm", "A", "Dm", "Eb", "Dm", "A"], 0.35, "ney"),
    "world":    (76, ["Dm", "C", "Bb", "A"], 0.55, "horn"),
    "fortress": (66, ["Dm", "Eb", "Dm", "C", "Bb", "Eb", "A", "A"], 0.45, "ney"),
    "naval":    (96, ["Dm", "Bb", "C", "A", "Dm", "Bb", "Gm", "A"], 0.95, "brass"),
    "prepare":  (80, ["Gm", "Dm", "Eb", "A"], 0.55, "horn"),
    "landing":  (100, ["Dm", "Bb", "C", "A", "Gm", "Bb", "Eb", "A"], 1.0, "brass"),
    "trench":   (64, ["Dm", "Gm", "Bb", "A", "Dm", "F", "Gm", "A"], 0.5, "cello"),
    "august":   (96, ["Dm", "C", "Bb", "A", "Gm", "Eb", "Bb", "A"], 0.95, "brass"),
    "winter":   (58, ["Dm", "Bb", "F", "A", "Dm", "Gm", "Eb", "A"], 0.3, "strings"),
    "legacy":   (64, ["Dm", "Bb", "F", "C", "Gm", "Bb", "Eb", "A"], 0.55, "ney"),
    "legacy2":  (62, ["Bb", "F", "Gm", "Eb", "Bb", "F", "C", "D"], 0.6, "hymn"),
}

# GM-Programme
P_STR, P_BASS, P_CELLO, P_TIMP, P_HORN, P_TBN, P_CHOIR, P_HARP, P_NEY, P_TAIKO, P_STRTREM = 48, 43, 42, 47, 60, 57, 52, 46, 77, 116, 44


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


def compose(mood, seconds, seed):
    bpm, prog, inten, mel = MOODS[mood]
    rnd = random.Random(seed)
    s = Song(bpm)
    beats_total = seconds * bpm / 60.0
    bars = int(math.ceil(beats_total / 4)) + 2
    s.prog(0, P_STR, 100, 64)
    s.prog(1, P_BASS, 96, 54)
    s.prog(2, P_CELLO, 92, 50)
    s.prog(3, P_TIMP, 110, 64)
    s.prog(4, P_HORN, 92, 74)
    s.prog(5, P_CHOIR, 80, 64)
    s.prog(6, P_HARP, 80, 84)
    s.prog(7, P_NEY, 104, 70)
    s.prog(8, P_TBN, 92, 44)
    s.prog(10, P_TAIKO, 100, 64)
    s.prog(11, P_STRTREM, 82, 60)
    scale = HICAZ if mel in ("ney",) else DMINOR
    for b in range(bars):
        name = prog[b % len(prog)]
        ch3 = chord(name, 3)
        beat0 = b * 4
        # Dynamik-Bogen: leiser Beginn, Steigerung, sanftes Ende
        pos = b / max(1, bars - 1)
        arc = 0.65 + 0.35 * math.sin(math.pi * min(1, pos * 1.15))
        v = (40 + 60 * inten) * arc
        # Streicher-Akkord (gehalten), Bass
        for p in ch3:
            s.note(0, beat0, 4, p + 12, v * 0.8)
        s.note(0, beat0, 4, ch3[0] + 24, v * 0.6)
        s.note(1, beat0, 4, ch3[0] - 12, v * 0.9)
        # Chor in ruhigen Stimmungen und an Höhepunkten
        if mood in ("intro", "winter", "legacy", "legacy2", "fortress") or (inten > 0.9 and b % 8 >= 4):
            for p in ch3:
                s.note(5, beat0, 4, p + 12, v * 0.55)
        # Ostinato bei treibenden Stimmungen
        if inten >= 0.5:
            n_sub = 8 if inten > 0.8 else 4
            for k in range(n_sub):
                pitch = ch3[0] + (12 if k % 2 else 0) + (7 if k % 4 == 3 else 0)
                s.note(2, beat0 + k * 4 / n_sub, 4 / n_sub, pitch, v * (0.75 + 0.2 * (k % 2 == 0)))
        else:
            s.note(2, beat0, 4, ch3[0], v * 0.7)
        # Pauken
        if inten >= 0.9:
            s.note(3, beat0, 1, ch3[0] - 12 + 12, v * 1.1)
            s.note(3, beat0 + 2.5, 0.5, ch3[0] - 12 + 12, v * 0.8)
            if b % 4 == 3:
                for k in range(8):
                    s.note(3, beat0 + 2 + k * 0.25, 0.25, ch3[0], v * (0.5 + k * 0.07))
            s.note(10, beat0, 1, 40, v)
            s.note(10, beat0 + 1.5, 0.5, 40, v * 0.7)
            s.note(10, beat0 + 3, 1, 40, v * 0.85)
        elif inten >= 0.5 and b % 2 == 0:
            s.note(3, beat0, 2, ch3[0], v * 0.8)
        elif b % 4 == 0:
            s.note(3, beat0, 4, ch3[0], v * 0.5)
        # Militärische Trommel (Kanal 9 = Schlagzeug)
        if inten >= 0.9:
            for k in range(8):
                s.note(9, beat0 + k * 0.5, 0.25, 38, v * (0.55 + 0.25 * (k % 2 == 0)))
            if b % 8 == 0:
                s.note(9, beat0, 2, 49, v * 0.8)
        elif mood in ("world", "prepare") and b % 2 == 0:
            for k in (0, 0.75, 1, 2, 2.75, 3):
                s.note(9, beat0 + k, 0.25, 38, v * 0.45)
        # Harfe in ruhigen Stimmungen
        if mood in ("intro", "fortress", "winter", "legacy", "legacy2", "trench"):
            arp = [ch3[0] + 12, ch3[1] + 12, ch3[2] + 12, ch3[0] + 24]
            for k in range(8):
                s.note(6, beat0 + k * 0.5, 0.6, arp[k % 4] + (12 if k >= 4 else 0), v * 0.45)
        # Streichertremolo bei Spannung
        if mood in ("fortress", "prepare", "naval", "landing", "august") and b % 2 == 1:
            s.note(11, beat0, 4, ch3[2] + 24, v * 0.55)
        # Melodie: Ney / Horn / Blech / Cello
        if b % 2 == 0 and b >= 2:
            phrase_len = 8
            start = beat0
            cur = rnd.choice([0, 2, 4])
            t = 0.0
            while t < phrase_len - 0.5:
                d = rnd.choice([1, 1, 2, 0.5, 1.5]) if mel != "brass" else rnd.choice([1, 0.5, 0.5, 2])
                cur = max(0, min(len(scale) - 1, cur + rnd.choice([-2, -1, -1, 1, 1, 2, 0])))
                pitch = scale[cur]
                if mel == "ney":
                    s.note(7, start + t, d * 0.95, pitch + 12, v * 0.95)
                elif mel == "horn":
                    s.note(4, start + t, d, pitch, v * 0.9)
                elif mel == "brass":
                    s.note(4, start + t, d, pitch, v * 0.95)
                    s.note(8, start + t, d, pitch - 12, v * 0.8)
                elif mel == "cello":
                    s.note(2, start + t, d, pitch - 12, v * 0.95)
                elif mel == "hymn":
                    s.note(4, start + t, d, pitch, v * 0.8)
                    s.note(7, start + t, d, pitch + 12, v * 0.6)
                elif mel == "strings":
                    s.note(0, start + t, d, pitch + 12, v * 0.7)
                t += d
    if mood == "legacy2":
        # Schluss: D-Dur, lang gehalten
        endb = bars * 4
        for p in chord("D", 3):
            s.note(0, endb, 8, p + 12, 80)
            s.note(5, endb, 8, p + 12, 60)
        s.note(1, endb, 8, 38, 80)
        s.note(4, endb, 8, 66, 70)
    return s


def render_mood(mood, seconds, seed):
    os.makedirs(os.path.join(OUT, "music"), exist_ok=True)
    mid = os.path.join(OUT, "music", f"{seed:02d}_{mood}.mid")
    wav = mid.replace(".mid", ".wav")
    compose(mood, seconds + 6, seed).save(mid)
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
        elif name == "Ship" and o.sink is not None:
            place(sfx, booms[2], o.sink, 0.45, 0.0)
            place(sfx, booms[4] * 0.6, o.sink + 0.7, 0.3, 0.2)
        elif name == "Ship" and o.fire:
            for ta, tb in o.fire:
                for k in range(int((tb - ta) * 0.25)):
                    place(sfx, booms[(k + 1) % len(booms)], ta + rnd.random() * (tb - ta), 0.06, rnd.uniform(-0.7, 0.7))
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
        seg = render_mood(mood, t1 - t0 + xf, i)
        i0 = int(t0 * SR)
        L = min(len(seg), n - i0)
        seg = seg[:L]
        fin = np.clip(np.arange(L) / (xf * SR), 0, 1) if i > 0 else np.ones(L)
        tail_start = int((t1 - t0) * SR)
        fout = np.clip(1 - (np.arange(L) - tail_start) / (xf * SR), 0, 1)
        if mood == "legacy2":
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
