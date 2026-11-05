"""Stilprobe (Stopp 2): Hook P01+P02 – 21. Februar 1916, Morgengrauen, Schnee, dann Trommelfeuer.

  python3 projects/verdun_1916/stilprobe.py [--still]   → export/stilprobe_verdun.mp4
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from warazlib.geo import Grid  # noqa: E402
from warazlib.render25d import MapLayer, Renderer, Camera, Look  # noqa: E402
from warazlib import fx as FX, stage as ST, ui as UI, audio as AU  # noqa: E402
import vgeo  # noqa: E402

MAPS = os.path.join(ROOT, "assets", "ww1", "maps", "verdun")
WORK = os.path.join(ROOT, "work", "stilprobe")
FRAMES = os.path.join(WORK, "frames")
EXPORT = os.path.join(ROOT, "export")
FPS = 30
VO = 0.8                     # Stimme beginnt bei 0,8 s
T_BAR = VO + 10.75           # „Dann reißt der Himmel auf“
DUR = 23.0
G = Grid.load(os.path.join(MAPS, "L3_grid.json"))


def P(la, lo):
    return G.px(la, lo)


def build_stage(R, fxlib):
    S = ST.Stage(R, fxlib, FPS)
    rng = np.random.default_rng(5)
    # Französische Jäger am Südrand des Bois des Caures
    for (la, lo, spr, flip) in [(49.2768, 5.3790, "fr_inf_kneel", False), (49.2757, 5.3832, "fr_inf_stand", True),
                                (49.2772, 5.3870, "fr_inf_kneel", False), (49.2760, 5.3912, "fr_inf_stand", True),
                                (49.2770, 5.3950, "fr_inf_kneel", True), (49.2752, 5.3985, "fr_inf_stand", False)]:
        x, y = P(la, lo)
        S.figures.append(ST.Figure(spr, [(0, x, y)], size=74))
    # Deutsche Haubitzen im Norden
    guns = []
    for i, (la, lo) in enumerate([(49.3125, 5.3700), (49.3140, 5.3880), (49.3118, 5.4060), (49.3150, 5.4240)]):
        x, y = P(la, lo)
        f = ST.Figure("de_howitzer", [(0, x, y)], size=86, flip=(i % 2 == 1))
        S.figures.append(f)
        guns.append(f)
    # Fesselballon
    x, y = P(49.3240, 5.4150)
    S.figures.append(ST.Figure("de_balloon", [(0, x, y)], size=110, z=150, bob=0.01))
    # Rauch aus einem Unterstand (ruhige Phase)
    x, y = P(49.2753, 5.3890)
    for k in range(30):
        S.smokes.append((k * 0.55, x, y, 26, 4.5))
    # Trommelfeuer
    t = T_BAR
    while t < DUR:
        la = rng.uniform(49.266, 49.292)
        lo = rng.uniform(5.358, 5.412)
        x, y = P(la, lo)
        S.explosions.append(ST.Explosion(t, x, y, size=rng.uniform(170, 240)))
        rate = 2.2 + 2.5 * min(1.0, (t - T_BAR) / 6.0)
        t += rng.exponential(1.0 / rate)
    t = T_BAR + 0.4
    while t < DUR:     # ferne Einschläge entlang der Front
        la = rng.uniform(49.27, 49.30)
        lo = rng.choice([rng.uniform(5.30, 5.35), rng.uniform(5.42, 5.48)])
        x, y = P(la, lo)
        S.explosions.append(ST.Explosion(t, x, y, size=rng.uniform(150, 200), crater=False))
        t += rng.exponential(0.5)
    # Mündungsfeuer der Haubitzen
    t = T_BAR - 0.25
    i = 0
    while t < DUR:
        g = guns[i % len(guns)]
        S.muzzles.append((t, g, 0.42, 0.30))
        gx, gy = g.pos(0)
        S.smokes.append((t + 0.05, gx + (26 if not g.flip else -26), gy - 6, 44, 3.0))
        i += 1
        t += rng.uniform(0.18, 0.45)
    return S


def camera(t):
    ease = UI.ease
    c0 = Camera(*P(49.2790, 5.3850), 1900, pitch=52, yaw=-7)
    c1 = Camera(*P(49.2840, 5.3870), 1650, pitch=50, yaw=0)
    c2 = Camera(*P(49.2880, 5.3900), 2500, pitch=45, yaw=5)
    if t < T_BAR:
        return c0.lerp(c1, ease(t / T_BAR))
    return c1.lerp(c2, ease((t - T_BAR) / (DUR - T_BAR)))


def look(t):
    k = UI.ease((t - T_BAR) / 6.0)
    return Look(day=1.0 + 0.6 * k, snow=0.42, winter=1.0, dawn=0.6 - 0.25 * k, fog=0.20, sat=1.0)


_W = {}


def _init():
    L = MapLayer(MAPS, "L3", G, z_exag=2.0)
    R = Renderer(L)
    lib = FX.load_library(os.path.join(ROOT, "assets", "ww1", "fx"))
    _W["R"] = R
    _W["S"] = build_stage(R, lib)
    _W["snow"] = ST.Snowfall()
    _W["ov"] = UI.Overlay()


def render_frame(i):
    t = i / FPS
    R, S, snow, ov = _W["R"], _W["S"], _W["snow"], _W["ov"]
    lk = look(t)
    R.setup(camera(t))
    img = R.ground(lk)
    img = S.draw(img, t)
    img = R.grade(img, lk)
    img *= 1.0 + S.flash_amount(t)
    img = snow.draw(img, t, amount=0.8)
    dx, dy = S.shake(t)
    if abs(dx) + abs(dy) > 0.05:
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), borderMode=cv2.BORDER_REFLECT)
    # Einblendungen
    ov.clear()
    ov.date_title("21. FEBRUAR 1916", "07:15 UHR · NÖRDLICH VON VERDUN", UI.fade(t, 1.0, 5.2, 0.6, 0.6))
    ov.counter("21. FEB 1916", 1, UI.fade(t, 2.2, 99, 0.6, 0))
    pr = R.project(*P(49.2815, 5.3880))
    if pr:
        ov.place("BOIS DES CAURES", pr[0], pr[1], UI.fade(t, 5.8, 10.6, 0.9, 0.4), side=1, sub="WALDSTÜCK")
    ov.number_card("1.200+", "DEUTSCHE GESCHÜTZE", UI.fade(t, VO + 12.8, VO + 18.2, 0.4, 0.5))
    img = UI.composite(img, ov.rgba())
    # Ein-/Ausblende
    k = min(UI.ease(t / 1.0), UI.ease((DUR - t) / 0.8))
    img *= k
    out = np.clip(img, 0, 255).astype(np.uint8)[..., ::-1]
    cv2.imwrite(os.path.join(FRAMES, f"{i:05d}.jpg"), out, [cv2.IMWRITE_JPEG_QUALITY, 94])
    return i


def make_audio(voice_path, out_wav):
    n = int(DUR * AU.SR)
    voice = np.zeros(n, np.float32)
    v = AU.load_any(voice_path)
    AU.place(voice, v, VO, 1.0)
    sfx = np.zeros(n, np.float32)
    AU.place(sfx, AU.wind(DUR) * 0.10, 0)
    AU.place(sfx, AU.rumble(DUR - T_BAR, intensity=0.35), T_BAR)
    rng = np.random.default_rng(1)
    S = _W.get("S")
    times = [e.t0 for e in S.explosions] if S else []
    for k, tt in enumerate(sorted(times)):
        AU.place(sfx, AU.boom(dist=rng.uniform(0.35, 0.9), seed=k), tt, 0.22 if k else 0.5)
    # Musik: tiefe Streicherfläche (D-Moll), Pauke beim ersten Einschlag
    notes = [(0, 0.0, DUR, 38, 60), (0, 0.0, DUR, 45, 50), (1, 2.0, DUR - 2, 50, 42), (1, 6.0, DUR - 6, 53, 36),
             (2, T_BAR, DUR - T_BAR, 26, 70)]
    for k in range(int((DUR - T_BAR) * 4)):
        notes.append((3, T_BAR + k * 0.25, 0.2, 38, 70 + int(30 * min(1, k / 12))))
    mw = os.path.join(WORK, "music.wav")
    AU.midi_render(notes, DUR, mw, {0: 48, 1: 49, 2: 43, 3: 47})
    music = AU.read_wav(mw)[:n]
    music = np.pad(music, (0, n - len(music)))
    music = AU.duck(music / (np.abs(music).max() + 1e-9) * 0.30, voice)
    mix = voice * 0.95 + sfx + music
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    AU.write_wav(out_wav, mix)


def main():
    os.makedirs(FRAMES, exist_ok=True)
    os.makedirs(EXPORT, exist_ok=True)
    nfr = int(DUR * FPS)
    if "--still" in sys.argv:
        _init()
        for i in (int(3.5 * FPS), int(8 * FPS), int(13.0 * FPS), int(19 * FPS)):
            render_frame(i)
        return
    with Pool(4, initializer=_init) as pool:
        for k, _ in enumerate(pool.imap_unordered(render_frame, range(nfr), chunksize=8)):
            if k % 60 == 0:
                print("Bild", k, "/", nfr, flush=True)
    _init_audio_stage()
    wav = os.path.join(WORK, "mix.wav")
    make_audio(os.path.join(WORK, "voice_v4.mp3"), wav)
    out = os.path.join(EXPORT, "stilprobe_verdun.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(FRAMES, "%05d.jpg"),
                    "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("fertig", out)


def _init_audio_stage():
    """Für den Ton nur die Bühne (Einschlag-Zeiten) aufbauen, ohne Karte zu laden."""
    class _R:
        pass
    lib = FX.load_library(os.path.join(ROOT, "assets", "ww1", "fx"))
    _W["S"] = build_stage(_R(), lib)


if __name__ == "__main__":
    main()
