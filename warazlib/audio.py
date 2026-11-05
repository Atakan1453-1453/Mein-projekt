"""Ton: synthetische Geräusche (Einschläge, Grollen, Wind, Motoren) und Musik per MIDI + FluidSynth.

Alles wird im Code erzeugt → keine fremden Rechte. Musik: Soundfont FluidR3_GM (freie Lizenz, MIT).
"""
import math
import os
import subprocess
import tempfile

import numpy as np
from scipy import signal

SR = 48000
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"


def _lp(x, fc, order=4):
    b, a = signal.butter(order, fc / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def _bp(x, f1, f2, order=2):
    b, a = signal.butter(order, [f1 / (SR / 2), f2 / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def boom(dist=0.5, seed=0, dur=3.2):
    """Granateinschlag. dist 0 = nah (knallig), 1 = fern (dumpf)."""
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    env = np.exp(-t * (9 - 6 * dist)) * (1 - np.exp(-t * 400))
    crack = _lp(noise, 6000 - 5000 * dist) * np.exp(-t * (40 - 25 * dist)) * (1 - dist) * 0.8
    body = _lp(noise, 900 - 600 * dist) * env * 1.6
    thump = np.sin(2 * math.pi * (48 + 20 * rng.random()) * t * (1 - 0.25 * t)) * np.exp(-t * 6) * 1.2
    tail = _lp(rng.normal(0, 1, n), 300) * np.exp(-t * 1.6) * 0.5 * (0.5 + dist)
    x = crack + body + thump + tail
    return (x / (np.abs(x).max() + 1e-9)).astype(np.float32)


def rumble(dur, seed=1, intensity=1.0):
    """Fernes Dauerfeuer (Grollen)."""
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    x = _lp(rng.normal(0, 1, n), 140, 2)
    mod = np.interp(np.arange(n), np.linspace(0, n, int(dur * 6) + 2), rng.uniform(0.4, 1.0, int(dur * 6) + 2))
    x = x * mod
    return (x / (np.abs(x).max() + 1e-9) * intensity).astype(np.float32)


def wind(dur, seed=2):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    x = _bp(rng.normal(0, 1, n), 180, 900)
    mod = np.interp(np.arange(n), np.linspace(0, n, int(dur / 2) + 3), rng.uniform(0.3, 1.0, int(dur / 2) + 3))
    x = x * mod
    return (x / (np.abs(x).max() + 1e-9)).astype(np.float32)


def place(track, clip, t, gain=1.0):
    i = int(t * SR)
    if i >= len(track):
        return
    j = min(len(track), i + len(clip))
    track[i:j] += clip[:j - i] * gain


# ------------------------------------------------------------------ Musik
def midi_render(notes, dur, path_wav, programs, tempo_bpm=60, gain=0.9):
    """notes: Liste (kanal, start_s, länge_s, tonhöhe, lautstärke). programs: {kanal: GM-Programm}."""
    import mido
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(tempo_bpm)))
    for ch, prog in programs.items():
        tr.append(mido.Message("program_change", channel=ch, program=prog, time=0))
        tr.append(mido.Message("control_change", channel=ch, control=91, value=80, time=0))   # Hall
    ev = []
    for (ch, st, ln, p, v) in notes:
        ev.append((st, 1, mido.Message("note_on", channel=ch, note=p, velocity=v)))
        ev.append((st + ln, 0, mido.Message("note_off", channel=ch, note=p, velocity=0)))
    ev.sort(key=lambda e: (e[0], e[1]))
    tps = 480 * tempo_bpm / 60.0
    last = 0
    for (tt, _, m) in ev:
        tick = int(round(tt * tps))
        m.time = max(0, tick - last)
        last = tick
        tr.append(m)
    with tempfile.TemporaryDirectory() as td:
        mp = os.path.join(td, "m.mid")
        mid.save(mp)
        subprocess.run(["fluidsynth", "-ni", "-g", str(gain), "-r", str(SR), "-F", path_wav, SF2, mp],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read_wav(path):
    from scipy.io import wavfile
    sr, x = wavfile.read(path)
    x = x.astype(np.float32)
    if x.dtype != np.float32 or np.abs(x).max() > 2:
        x = x / 32768.0
    if x.ndim == 2:
        x = x.mean(1)
    if sr != SR:
        x = signal.resample_poly(x, SR, sr)
    return x.astype(np.float32)


def write_wav(path, x):
    from scipy.io import wavfile
    x = np.clip(x, -1, 1)
    wavfile.write(path, SR, (x * 32767).astype(np.int16))


def load_any(path):
    """Beliebige Audiodatei (mp3 …) → Mono-float32 bei SR."""
    with tempfile.TemporaryDirectory() as td:
        w = os.path.join(td, "a.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", str(SR), w], check=True)
        return read_wav(w)


def duck(music, voice, depth_db=-9.0, attack=0.15, release=0.6):
    """Musik unter der Stimme absenken."""
    env = np.abs(voice)
    win = int(SR * 0.05)
    env = np.convolve(env, np.ones(win) / win, mode="same")
    act = (env > 0.01).astype(np.float32)
    # weiche Hüllkurve
    k_a, k_r = 1 / (attack * SR), 1 / (release * SR)
    g = np.zeros_like(act)
    cur = 0.0
    for i in range(0, len(act), 64):
        target = act[i]
        cur += (target - cur) * min(1.0, (k_a if target > cur else k_r) * 64)
        g[i:i + 64] = cur
    gain = 10 ** (depth_db * g / 20)
    return music * gain
