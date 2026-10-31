#!/usr/bin/env python3
"""Erzeugt eine lizenzfreie, synthetische Hintergrundmusik (60 s, 96 BPM, D-Dur).

Alles wird mit numpy berechnet – keine externen Samples, keine Rechte Dritter.
Ein Takt dauert 2,5 s, damit Szenenwechsel im Video auf Taktgrenzen fallen.
"""
import wave

import numpy as np

SR = 44100
BPM = 96
BEAT = 60.0 / BPM          # 0,625 s
BAR = 4 * BEAT             # 2,5 s


def midi_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


# Dmaj9 – Bm7 – Gmaj7 – A(sus)
CHORDS = [
    [50, 57, 61, 64, 66],
    [47, 54, 57, 62, 66],
    [43, 50, 54, 59, 62],
    [45, 52, 57, 61, 64],
]


def env_adsr(n, a, r):
    """Einfache Hüllkurve: lineares Attack, Sustain, lineares Release (in Samples)."""
    e = np.ones(n)
    a = min(a, n)
    r = min(r, n - a)
    if a > 0:
        e[:a] = np.linspace(0, 1, a)
    if r > 0:
        e[n - r:] = np.linspace(1, 0, r)
    return e


def pad_note(freq, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for detune in (-0.0018, 0.0018):
        f = freq * (1 + detune)
        for k in range(1, 6):
            out += np.sin(2 * np.pi * f * k * t + k * 0.7) / (k ** 1.6)
    # langsames "Atmen" der Lautstärke
    out *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.23 * t)
    return out * env_adsr(n, int(0.6 * SR), int(1.0 * SR))


def bell(freq, dur=1.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * freq * t)
         + 0.28 * np.sin(2 * np.pi * freq * 2 * t)
         + 0.08 * np.sin(2 * np.pi * freq * 3.01 * t))
    e = np.exp(-t * 4.2) * np.minimum(1, t / 0.004)
    return s * e


def bass_pluck(freq, dur=0.55):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * freq * 2 * t)
    return s * np.exp(-t * 5.0) * np.minimum(1, t / 0.01)


def kick(dur=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 45 + 85 * np.exp(-t * 28)
    phase = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(phase) * np.exp(-t * 11)


def hat(rng, dur=0.06):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    noise = np.diff(noise, prepend=0)          # grober Hochpass
    return noise * np.exp(-t * 70)


def add(buf, sig, start_s, gain):
    i = int(start_s * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[: j - i] * gain


def reverb(sig, seed, length=2.4):
    rng = np.random.default_rng(seed)
    n = int(length * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 2.6)
    ir[0] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    size = 1 << int(np.ceil(np.log2(len(sig) + n)))
    wet = np.fft.irfft(np.fft.rfft(sig, size) * np.fft.rfft(ir, size), size)[: len(sig)]
    return wet


def render(path, duration=60.0):
    total = int(duration * SR)
    rng = np.random.default_rng(7)
    pad = np.zeros(total)
    arp = np.zeros(total)
    low = np.zeros(total)
    drums = np.zeros(total)

    bars = int(round(duration / BAR))
    arp_pattern = [0, 2, 3, 4, 3, 2, 1, 2]
    for b in range(bars):
        t0 = b * BAR
        last = b == bars - 1
        chord = CHORDS[0] if last else CHORDS[b % 4]
        # Flächen-Akkord (überlappend für weiche Übergänge)
        for note in chord:
            add(pad, pad_note(midi_hz(note), BAR + (1.6 if not last else 0.0)), t0, 0.075)
        if last:
            continue
        # Arpeggio ab Takt 2
        if b >= 1:
            for i, idx in enumerate(arp_pattern):
                note = chord[idx] + 12
                vel = 0.5 if b < 3 else 1.0
                add(arp, bell(midi_hz(note)), t0 + i * BEAT / 2, 0.075 * vel * (1.0 if i % 2 == 0 else 0.7))
        # Bass ab Takt 3
        if b >= 2:
            root = chord[0] - 12
            for beat in range(4):
                add(low, bass_pluck(midi_hz(root)), t0 + beat * BEAT, 0.30 if beat == 0 else 0.18)
        # dezenter Beat ab Takt 4, Hi-Hats ab Takt 6, Pause in Takt 15 (Atempause)
        if b >= 3 and b != 14:
            for beat in (0, 2):
                add(drums, kick(), t0 + beat * BEAT, 0.45)
        if b >= 5 and b != 14:
            for beat in range(4):
                add(drums, hat(rng), t0 + beat * BEAT + BEAT / 2, 0.05)

    dry = pad + arp + low + drums
    wet_l = reverb(pad + arp, seed=1)
    wet_r = reverb(pad + arp, seed=2)
    left = dry + 0.35 * wet_l
    right = dry + 0.35 * wet_r
    # leichte Stereobreite für das Arpeggio
    shift = int(0.012 * SR)
    right[shift:] += 0.25 * arp[:-shift]
    left += 0.25 * arp

    st = np.stack([left, right], axis=1)
    # Ein- und Ausblenden
    fi = int(0.4 * SR)
    fo = int(3.5 * SR)
    st[:fi] *= np.linspace(0, 1, fi)[:, None]
    st[-fo:] *= (np.linspace(1, 0, fo) ** 1.5)[:, None]
    # Pegel: RMS auf ca. -19 dBFS (angenehme Hintergrundlautstärke),
    # Spitzen weich auf unter -1 dBFS begrenzen
    rms = np.sqrt(np.mean(st ** 2))
    st *= (10 ** (-19 / 20)) / rms
    ceiling = 10 ** (-1 / 20)
    st = ceiling * np.tanh(st / ceiling)
    pcm = (st * 32767).astype(np.int16)

    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    import sys
    render(sys.argv[1] if len(sys.argv) > 1 else "music.wav")
