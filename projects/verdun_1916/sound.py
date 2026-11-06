"""Ton für „Verdun 1916“: Stimme + Musik (MIDI → FluidSynth, eigene Komposition) + Geräusche (synthetisch).

  python3 sound.py            → work/audio/mix.wav (Stereo, 48 kHz) und work/audio/{voice,music,sfx}.wav
"""
import math
import os
import sys

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from warazlib import audio as AU  # noqa: E402
import timeline as TL  # noqa: E402
import scenes as SC  # noqa: E402
import script_data as SD  # noqa: E402

SR = AU.SR
OUT = os.path.join(ROOT, "work", "audio")
rng = np.random.default_rng(16)


# ------------------------------------------------------------------ Hilfen
def env_adsr(n, a=0.01, r=0.2):
    e = np.ones(n, np.float32)
    na, nr = int(a * SR), int(r * SR)
    if na > 0:
        e[:na] = np.linspace(0, 1, na)
    if nr > 0 and nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def norm(x, peak=1.0):
    return (x / (np.abs(x).max() + 1e-9) * peak).astype(np.float32)


def lp(x, fc, o=2):
    b, a = signal.butter(o, min(0.99, fc / (SR / 2)), "low")
    return signal.lfilter(b, a, x).astype(np.float32)


def hp(x, fc, o=2):
    b, a = signal.butter(o, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x).astype(np.float32)


def bp(x, f1, f2, o=2):
    b, a = signal.butter(o, [f1 / (SR / 2), min(0.99, f2 / (SR / 2))], "band")
    return signal.lfilter(b, a, x).astype(np.float32)


def noise(d):
    return rng.normal(0, 1, int(d * SR)).astype(np.float32)


def t_axis(d):
    return np.arange(int(d * SR), dtype=np.float32) / SR


def reverb(x, decay=1.2, mix=0.3):
    n = int(decay * SR)
    ir = rng.normal(0, 1, n).astype(np.float32) * np.exp(-np.arange(n) / (decay * SR / 5)).astype(np.float32)
    ir = lp(ir, 3000)
    wet = signal.fftconvolve(x, ir)[:len(x)]
    return (x * (1 - mix) + norm(wet, np.abs(x).max()) * mix).astype(np.float32)


# ------------------------------------------------------------------ Klänge
def s_mg(d):
    out = np.zeros(int(d * SR), np.float32)
    t = 0.0
    while t < d - 0.1:
        burst = rng.uniform(0.6, 1.6)
        k = 0
        while k < burst and t < d - 0.1:
            c = norm(hp(noise(0.05), 600) * np.exp(-t_axis(0.05) * 90)) * rng.uniform(0.5, 1.0)
            AU.place(out, c, t)
            t += 0.085
            k += 0.085
        t += rng.uniform(0.4, 1.2)
    return lp(out, 4000) * 0.5


def s_whistle():
    tt = t_axis(1.1)
    f = 2400 + 300 * np.sin(tt * 40)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_adsr(len(tt), 0.05, 0.3)
    return (x * 0.35).astype(np.float32)


def s_heartbeat(d):
    out = np.zeros(int(d * SR), np.float32)
    beat = lp(noise(0.18), 90, 4) * np.exp(-t_axis(0.18) * 22)
    beat = norm(beat)
    t = 0.2
    while t < d:
        AU.place(out, beat, t)
        AU.place(out, beat * 0.7, t + 0.28)
        t += 1.05
    return out * 0.8


def s_steps(d):
    out = np.zeros(int(d * SR), np.float32)
    st = norm(lp(noise(0.12), 900) * np.exp(-t_axis(0.12) * 35))
    t = 0.1
    while t < d:
        AU.place(out, st * rng.uniform(0.6, 1.0), t)
        t += rng.uniform(0.45, 0.6)
    return reverb(out, 1.8, 0.5) * 0.6


def s_bell(f0=196.0, d=5.0):
    tt = t_axis(d)
    x = np.zeros_like(tt)
    for m, a, dec in ((1.0, 1.0, 1.2), (2.0, 0.6, 1.8), (2.4, 0.4, 2.2), (3.0, 0.3, 2.8), (4.2, 0.2, 3.5), (5.4, 0.12, 4.5)):
        x += a * np.sin(2 * np.pi * f0 * m * tt) * np.exp(-tt * dec)
    return norm(x, 0.6)


def s_stamp():
    tt = t_axis(0.35)
    th = lp(noise(0.35), 200) * np.exp(-tt * 30)
    pa = bp(noise(0.35), 1500, 5000) * np.exp(-tt * 60) * 0.3
    return norm(th + pa, 0.8)


def s_plop():
    tt = t_axis(0.18)
    f = 900 * np.exp(-tt * 8)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 25) * 0.35).astype(np.float32)


def s_tick():
    tt = t_axis(0.05)
    return (hp(noise(0.05), 2000) * np.exp(-tt * 200) * 0.4).astype(np.float32)


def s_clock(d):
    out = np.zeros(int(d * SR), np.float32)
    t = 0.0
    k = 0
    while t < d:
        AU.place(out, s_tick() * (1.0 if k % 2 else 0.7), t)
        t += 0.5
        k += 1
    return out


def s_engine(d, f0=38, rough=0.6):
    tt = t_axis(d)
    f = f0 * (1 + 0.05 * np.sin(tt * 1.3))
    ph = np.cumsum(f) / SR
    x = signal.sawtooth(2 * np.pi * ph) * 0.5 + rough * lp(noise(d), 300)
    x = lp(x, 600)
    return norm(x, 0.5)


def s_rain(d):
    return norm(bp(noise(d), 800, 7000), 0.35) * (0.8 + 0.2 * np.sin(t_axis(d) * 0.7)).astype(np.float32)


def s_wind(d):
    return AU.wind(d) * 0.45


def s_shovel(d):
    out = np.zeros(int(d * SR), np.float32)
    sc = norm(bp(noise(0.3), 1500, 6000) * env_adsr(int(0.3 * SR), 0.02, 0.2))
    t = 0.2
    while t < d:
        AU.place(out, sc * rng.uniform(0.3, 0.6), t)
        t += rng.uniform(0.6, 1.4)
    return out


def s_wings():
    tt = t_axis(1.4)
    x = bp(noise(1.4), 300, 3000) * (0.5 + 0.5 * np.sin(2 * np.pi * 11 * tt)) * env_adsr(len(tt), 0.05, 0.6)
    return norm(x, 0.5)


def s_gas_shell():
    tt = t_axis(0.6)
    return norm(lp(noise(0.6), 250) * np.exp(-tt * 9), 0.5)


def s_hiss(d):
    return norm(bp(noise(d), 2500, 9000), 0.22) * env_adsr(int(d * SR), 1.0, 1.5)


def s_breath(d):
    tt = t_axis(d)
    cyc = 0.5 + 0.5 * np.sin(2 * np.pi * tt / 2.6)
    return norm(bp(noise(d), 200, 1400) * cyc ** 2, 0.5)


def s_wheels(d):
    x = AU.rumble(d, seed=7, intensity=0.5)
    return x + s_shovel(d) * 0.2


def s_march(d):
    out = np.zeros(int(d * SR), np.float32)
    st = norm(lp(noise(0.1), 500) * np.exp(-t_axis(0.1) * 40))
    t = 0.0
    while t < d:
        AU.place(out, st * 0.5, t)
        t += 0.55
    return reverb(out, 1.0, 0.4)


def s_train(d):
    out = np.zeros(int(d * SR), np.float32)
    ch = norm(lp(noise(0.25), 400) * np.exp(-t_axis(0.25) * 12))
    t = 0.0
    while t < d:
        for j in range(2):
            AU.place(out, ch * (0.6 if j else 0.9), t + j * 0.18)
        t += 0.8
    return out * 0.6 + AU.rumble(d, seed=9, intensity=0.2)


def s_birds(d):
    out = np.zeros(int(d * SR), np.float32)
    t = 0.3
    while t < d - 0.5:
        n = rng.integers(2, 5)
        f0 = rng.uniform(2500, 4200)
        for j in range(n):
            tt = t_axis(0.09)
            f = f0 * (1 + 0.25 * np.sin(tt * 60))
            ch = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 30) * 0.2
            AU.place(out, ch.astype(np.float32), t + j * 0.12)
        t += rng.uniform(0.6, 2.0)
    return out


def s_flare():
    tt = t_axis(2.0)
    return norm(bp(noise(2.0), 2000, 7000) * np.exp(-tt * 1.5), 0.3)


def s_whoosh():
    tt = t_axis(1.0)
    x = noise(1.0)
    b, a = signal.butter(2, 0.05)
    y = np.zeros_like(x)
    for i, (lo, hi) in enumerate([(200, 600), (400, 1400), (800, 3000), (500, 1600), (200, 700)]):
        seg = slice(int(i * 0.2 * SR), int((i + 1) * 0.2 * SR))
        y[seg] = bp(x[seg], lo, hi)
    return norm(y * np.sin(np.pi * tt), 0.5)


def s_tunnel(d):
    out = np.zeros(int(d * SR), np.float32)
    t = 0.2
    while t < d:
        AU.place(out, lp(AU.boom(dist=0.95, seed=int(t * 10)), 300) * 0.5, t)
        t += rng.uniform(0.7, 1.6)
    return reverb(out, 2.0, 0.6)


BOOMS = None


def boom_bank():
    global BOOMS
    if BOOMS is None:
        BOOMS = [AU.boom(dist=d, seed=i) for i, d in enumerate(np.linspace(0.15, 0.95, 12))]
    return BOOMS


# ------------------------------------------------------------------ Musik
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"])}


def chord(name, octave=3):
    minor = name.endswith("m")
    root = NOTE[name[:-1] if minor else name]
    base = 12 * (octave + 1) + root
    return [base, base + (3 if minor else 4), base + 7]


def compose(tl, S):
    """Liefert MIDI-Noten (kanal, start, länge, tonhöhe, lautstärke) für das ganze Video."""
    n = []
    T = lambda pid, f=0.0: tl[pid][0] + (tl[pid][1] - tl[pid][0]) * f  # noqa: E731
    stops = sorted(e.t for e in S.sfx if e.kind == "music_stop")

    def cut(t0, t1):
        """Abschnitt [t0, t1) ohne Musik-Stopps (0,6 s Stille nach jedem Stopp)."""
        for s in stops:
            if t0 <= s < t1:
                return s
        return t1

    def pad(t0, t1, prog_chords, ch=0, vel=52, octave=3, top=True):
        if t1 <= t0:
            return
        L = (t1 - t0) / len(prog_chords)
        for i, c in enumerate(prog_chords):
            a = t0 + i * L
            for p in chord(c, octave):
                n.append((ch, a, L * 1.02, p, vel))
            n.append((ch, a, L * 1.02, chord(c, octave - 1)[0], vel + 6))
            if top:
                n.append((1, a, L * 1.02, chord(c, octave + 1)[2], vel - 14))

    def ostinato(t0, t1, notes, step, ch=2, vel=60):
        t = t0
        i = 0
        while t < t1:
            n.append((ch, t, step * 0.9, notes[i % len(notes)], vel))
            t += step
            i += 1

    def timp(t0, t1, step, vel=70, pitch=38):
        t = t0
        while t < t1:
            n.append((3, t, 0.3, pitch, vel))
            t += step

    def hit(t, vel=110):
        n.append((3, t, 1.5, 38, vel))
        n.append((3, t, 1.5, 33, vel))
        for p in chord("Dm", 2):
            n.append((4, t, 2.2, p, vel - 20))

    # Kapitel 1 – Hook
    a = 0.0
    e = cut(a, T("P04"))
    pad(a, min(e, T("P02")), ["Dm"], vel=48)
    pad(T("P02"), e, ["Dm", "Bb", "Gm", "A"], vel=62)
    timp(T("P02") + 0.05, e, 0.25, 74)
    hit(T("P02") + 0.05, 118)
    hit(tl["P04"][1] + 0.25, 120)                       # Titel-Schlag
    # Kapitel 2 – Lage / Planung
    pad(T("P05") - 0.5, T("P11"), ["Dm", "F", "C", "Dm", "Bb", "Gm", "A", "Dm"], vel=44)
    ostinato(T("P05"), T("P11"), [62, 65, 69, 65, 62, 65, 69, 72], 0.40, ch=2, vel=46)
    pad(T("P11"), T("P16") - 0.4, ["Gm", "Dm", "Eb", "A"], ch=4, vel=50, octave=2, top=False)
    # Kapitel 3 – Angriff
    e = cut(T("P16") - 0.3, T("P21"))
    pad(T("P16") - 0.3, e, ["Dm", "Dm", "Bb", "A", "Dm", "Gm", "A", "A"], vel=62)
    ostinato(T("P16"), e, [50, 50, 57, 50, 53, 50, 57, 55], 0.22, ch=5, vel=58)
    timp(T("P16"), e, 0.44, 72)
    pad(T("P21") + 0.8, T("P23", 0.5), ["Dm", "Dm"], ch=6, vel=40, octave=2, top=False)
    hit(T("P23", 0.56), 105)
    e = cut(T("P24"), tl["P25"][1] + 0.4)
    pad(T("P24"), e, ["Bb", "Gm", "A", "A"], vel=60)
    timp(T("P25"), e, 0.3, 80)
    hit(tl["P25"][1] + 0.3, 115)
    # Kapitel 4 – Lebensader
    pad(T("P26") - 0.3, T("P33"), ["Dm", "Bb", "F", "C", "Dm", "Bb", "F", "A"], vel=50)
    ostinato(T("P27"), T("P33"), [62, 69, 65, 69, 62, 69, 67, 69], 0.25, ch=5, vel=50)
    pad(T("P33"), tl["P34"][1] + 0.6, ["Dm", "Gm", "A", "Dm"], ch=6, vel=46, octave=3, top=False)
    # Kapitel 5 – Hölle
    e = cut(T("P35") - 0.3, T("P46"))
    pad(T("P35") - 0.3, e, ["Dm", "Eb", "Dm", "C#", "Dm", "Eb", "Gm", "A"] * 2, ch=7, vel=56)
    pad(T("P35") - 0.3, e, ["Dm", "Eb", "Dm", "C#", "Dm", "Eb", "Gm", "A"] * 2, ch=4, vel=50, octave=2, top=False)
    timp(T("P35"), e, 0.9, 66)
    pad(T("P47"), tl["P50"][1], ["Dm", "Bb", "Gm", "A", "Dm", "Bb", "A", "A"], vel=64)
    timp(T("P49"), tl["P50"][1], 0.2, 86)
    hit(T("P49", 0.98), 120)
    # Kapitel 6 – Wende
    pad(T("P51") - 0.3, T("P57", 0.6), ["Dm", "F", "Gm", "C", "F", "Bb", "C", "C"], vel=52)
    pad(T("P57", 0.6), tl["P58"][1] + 0.4, ["F", "C", "D", "D"], vel=64)
    hit(T("P57", 0.62), 100)
    # Kapitel 7 – Finale / Bilanz
    pad(T("P59") - 0.3, T("P65"), ["Dm", "Bb", "F", "A", "Dm", "Gm", "A", "Dm"], ch=0, vel=50)
    ostinato(T("P61"), T("P65"), [74, 72, 69, 65, 69, 72], 0.9, ch=9, vel=72)
    pad(T("P65"), T("P69"), ["Dm", "Bb", "Gm", "A"], vel=58)
    pad(T("P69"), tl["P69"][1] + 1.0, ["Dm", "Bb", "F", "A"], vel=70)
    pad(T("P70"), tl["P71"][1] + 0.8, ["F", "C", "Dm", "Bb", "F", "C"], ch=0, vel=50)
    ostinato(T("P70"), tl["P71"][1], [77, 76, 72, 69, 72, 76], 0.7, ch=9, vel=68)
    # Outro
    pad(T("P72") - 0.2, S.duration, ["Dm", "C", "Bb", "A", "Dm"], vel=54)
    ostinato(T("P72"), S.duration - 1.0, [62, 62, 69, 67, 65, 64], 0.35, ch=2, vel=50)
    timp(T("P72"), S.duration - 1.5, 0.7, 60)
    return n


PROGRAMS = {0: 48, 1: 49, 2: 45, 3: 47, 4: 57, 5: 44, 6: 42, 7: 52, 8: 0, 9: 0}


def main():
    os.makedirs(OUT, exist_ok=True)
    tl = TL.build()
    S = SC.build(tl)
    N = int(S.duration * SR) + SR
    # ---------------- Stimme
    voice = np.zeros(N, np.float32)
    for p in SD.P:
        v = AU.read_wav(os.path.join(HERE, "voice", f"{p['id']}.wav"))
        AU.place(voice, v, tl[p["id"]][0], 1.0)
    # ---------------- Geräusche (Stereo)
    L = np.zeros(N, np.float32)
    R = np.zeros(N, np.float32)

    def put(x, t, g=1.0, pan=0.0):
        a = math.cos((pan + 1) * math.pi / 4)
        b = math.sin((pan + 1) * math.pi / 4)
        AU.place(L, x, t, g * a * 1.41)
        AU.place(R, x, t, g * b * 1.41)

    bank = boom_bank()
    lib = {"whistle": s_whistle(), "bell": s_bell(), "bell_soft": s_bell(392.0, 3.0) * 0.5, "stamp": s_stamp(),
           "plop": s_plop(), "tick": s_tick(), "wings": s_wings(), "gas_shell": s_gas_shell(), "flare": s_flare(),
           "chapter": s_whoosh()}
    nb = 0
    for e in S.sfx:
        k = e.kind
        if k in ("boom", "first_boom", "last_boom"):
            if k == "boom":
                # Dichte begrenzen
                nb += 1
            x = bank[rng.integers(0, 4)] if k != "boom" else bank[rng.integers(0, len(bank))]
            g = (0.9 if k != "boom" else 0.26) * e.gain
            put(x, e.t, g, rng.uniform(-0.6, 0.6))
        elif k == "gun":
            put(bank[rng.integers(6, 12)], e.t, 0.18 * e.gain, rng.uniform(-0.8, 0.8))
        elif k in lib:
            put(lib[k], e.t, 0.9 * e.gain, 0.0)
        elif k == "mg":
            put(s_mg(e.dur), e.t, 0.6 * e.gain, -0.3)
        elif k == "heartbeat":
            put(s_heartbeat(e.dur), e.t, 0.7 * e.gain)
        elif k == "echo_steps":
            put(s_steps(e.dur), e.t, 0.8 * e.gain)
        elif k == "clock":
            put(s_clock(e.dur), e.t, 0.6 * e.gain)
        elif k in ("car", "trucks"):
            put(s_engine(e.dur, 34 if k == "trucks" else 55), e.t, (0.35 if k == "trucks" else 0.3) * e.gain)
        elif k == "rain":
            put(s_rain(e.dur), e.t, 0.6 * e.gain)
        elif k == "shovel":
            put(s_shovel(e.dur), e.t, 0.8 * e.gain)
        elif k == "wheels":
            put(s_wheels(e.dur), e.t, 0.5 * e.gain)
        elif k == "march":
            put(s_march(e.dur), e.t, 0.6 * e.gain)
        elif k == "train":
            put(s_train(e.dur), e.t, 0.6 * e.gain)
        elif k == "hiss":
            put(s_hiss(e.dur), e.t, 0.6 * e.gain)
        elif k == "mask_breath":
            put(s_breath(e.dur), e.t, 0.7 * e.gain)
        elif k == "birds":
            put(s_birds(e.dur), e.t, 0.6 * e.gain)
        elif k == "rumble_far":
            put(AU.rumble(e.dur, seed=3, intensity=0.5), e.t, 0.5 * e.gain)
        elif k == "tunnel_fight":
            put(s_tunnel(e.dur), e.t, 0.6 * e.gain)
        elif k == "wind_on":
            pass
    # Atmosphäre: Wind im Schnee, Grollen in Kampfphasen
    wind = s_wind(S.duration + 1)[:N]
    wenv = np.array([S.snowfall(i / 10.0) for i in range(int(S.duration * 10) + 11)], np.float32)
    wenv = np.interp(np.arange(N) / SR, np.arange(len(wenv)) / 10.0, wenv).astype(np.float32)
    L += wind * (0.15 + 0.5 * wenv)
    R += np.roll(wind, 4800) * (0.15 + 0.5 * wenv)
    rum = AU.rumble(S.duration + 1, seed=11, intensity=1.0)[:N]
    dens = np.zeros(int(S.duration) + 2, np.float32)
    for b in S.booms:
        if 0 <= b.t < len(dens):
            dens[int(b.t)] += 1
    dens = np.convolve(dens, np.ones(5) / 5, mode="same")
    renv = np.interp(np.arange(N) / SR, np.arange(len(dens)), np.clip(dens / 3.0, 0, 1)).astype(np.float32)
    L += rum * 0.25 * renv
    R += rum * 0.25 * renv
    # ---------------- Musik
    notes = compose(tl, S)
    mw = os.path.join(OUT, "music_raw.wav")
    AU.midi_render(notes, S.duration, mw, PROGRAMS, gain=0.7)
    from scipy.io import wavfile
    sr, m = wavfile.read(mw)
    m = m.astype(np.float32) / 32768.0
    if m.ndim == 1:
        m = np.stack([m, m], 1)
    if sr != SR:
        m = signal.resample_poly(m, SR, sr, axis=0)
    mL = np.zeros(N, np.float32)
    mR = np.zeros(N, np.float32)
    k = min(N, len(m))
    mL[:k], mR[:k] = m[:k, 0], m[:k, 1]
    pk = max(np.abs(mL).max(), np.abs(mR).max()) + 1e-9
    mL, mR = mL / pk * 0.95, mR / pk * 0.95
    mL = AU.duck(mL, voice, depth_db=-9.0)
    mR = AU.duck(mR, voice, depth_db=-9.0)
    # SFX unter der Stimme leicht absenken
    sL = AU.duck(L, voice, depth_db=-4.0)
    sR = AU.duck(R, voice, depth_db=-4.0)
    sL, sR = sL * 1.4, sR * 1.4
    sL, sR = 0.85 * np.tanh(sL / 0.85), 0.85 * np.tanh(sR / 0.85)
    outL = voice * 0.95 + mL + sL
    outR = voice * 0.95 + mR + sR
    def soft(x, th=0.8):
        y = x.copy()
        m = np.abs(x) > th
        y[m] = np.sign(x[m]) * (th + (1 - th) * np.tanh((np.abs(x[m]) - th) / (1 - th)))
        return y
    outL, outR = soft(outL), soft(outR)
    st = np.stack([outL, outR], 1)
    wavfile.write(os.path.join(OUT, "mix.wav"), SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
    wavfile.write(os.path.join(OUT, "voice.wav"), SR, (np.clip(voice, -1, 1) * 32767).astype(np.int16))
    wavfile.write(os.path.join(OUT, "music.wav"), SR, (np.clip(np.stack([mL, mR], 1), -1, 1) * 32767).astype(np.int16))
    wavfile.write(os.path.join(OUT, "sfx.wav"), SR, (np.clip(np.stack([sL, sR], 1), -1, 1) * 32767).astype(np.int16))
    print("fertig", round(S.duration, 1), "s", "Explosionen", nb)


if __name__ == "__main__":
    main()
