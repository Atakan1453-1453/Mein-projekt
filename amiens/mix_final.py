"""Endmischung: stummes Video + Musik/Geräusche + Sprecher → fertiges MP4.

Läuft überall, wo ffmpeg installiert ist (hier: Higgsfield-Sandbox, weil die Sprachdateien nur dort
heruntergeladen werden können).

  python3 mix_final.py --video video.mp4 --bed bed.ogg --plan voice_plan.json --voice-dir voice --out final.mp4

voice/NN.mp3 = Sprachaufnahme Nr. NN in der Reihenfolge von narration.SEGMENTS.
Die Sprachspur wird aus Stille + Aufnahmen aneinandergereiht (schnell), leicht komprimiert und
über die Musik gelegt; ein Limiter verhindert Übersteuerung.
"""
import argparse
import json
import subprocess


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--bed", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--voice-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bed-gain", type=float, default=2.2)
    ap.add_argument("--voice-gain", type=float, default=1.25)
    a = ap.parse_args()
    plan = json.load(open(a.plan))
    voices = sorted(plan["voice"], key=lambda v: v["start"])
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", a.video, "-i", a.bed]
    parts, seq = [], []
    cursor = 0.0
    for k, v in enumerate(voices):
        f = f"{a.voice_dir}/{v['index']:02d}.mp3"
        cmd += ["-i", f]
        gap = max(0.0, v["start"] - cursor)
        parts.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={gap:.4f}[s{k}]")
        parts.append(f"[{k + 2}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[v{k}]")
        seq += [f"[s{k}]", f"[v{k}]"]
        cursor = v["start"] + duration(f)
    parts.append("".join(seq) + f"concat=n={len(seq)}:v=0:a=1,highpass=f=70,"
                 f"acompressor=threshold=0.12:ratio=2.5:attack=8:release=180:makeup=1.4,volume={a.voice_gain}[vox]")
    parts.append(f"[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume={a.bed_gain}[bed]")
    parts.append("[bed][vox]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89:level=false[a]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-t", str(plan["duration"]), "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    print("fertig:", a.out)


if __name__ == "__main__":
    main()
