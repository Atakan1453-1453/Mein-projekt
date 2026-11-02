"""Endmischung: stummes Video + Musik/Geräusche + Sprecher → fertiges MP4.

Läuft überall, wo ffmpeg installiert ist (hier: Higgsfield-Sandbox, weil die Sprachdateien nur dort
heruntergeladen werden können).

  python3 mix_final.py --video video.mp4 --bed bed.ogg --plan voice_plan.json --voice-dir voice --out final.mp4

voice/NN.mp3 = Sprachaufnahme Nr. NN in der Reihenfolge von narration.SEGMENTS.
"""
import argparse
import json
import subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--bed", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--voice-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bed-gain", type=float, default=1.4)
    a = ap.parse_args()
    plan = json.load(open(a.plan))
    voices = sorted(plan["voice"], key=lambda v: v["index"])
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", a.video, "-i", a.bed]
    for v in voices:
        cmd += ["-i", f"{a.voice_dir}/{v['index']:02d}.mp3"]
    parts = []
    labels = []
    for k, v in enumerate(voices):
        ms = int(round(v["start"] * 1000))
        parts.append(f"[{k + 2}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{k}]")
        labels.append(f"[v{k}]")
    parts.append("".join(labels) + f"amix=inputs={len(voices)}:normalize=0:dropout_transition=0,"
                 "highpass=f=70,acompressor=threshold=0.12:ratio=2.5:attack=8:release=180:makeup=1.6[vox]")
    parts.append(f"[1:a]aresample=48000,volume={a.bed_gain}[bed]")
    parts.append("[bed][vox]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-t", str(plan["duration"]), "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    print("fertig:", a.out)


if __name__ == "__main__":
    main()
