"""Robustes Rendern in kleinen Stücken (überlebt Abbrüche: fertige Stücke werden übersprungen).

  python3 render_chunks.py START_FRAME END_FRAME OUTDIR [WORKERS] [CHUNK]
"""
import os
import subprocess
import sys
from multiprocessing import Process


def done(path, n):
    if not os.path.exists(path):
        return False
    r = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    return r.stdout.strip() == str(n)


def worker(jobs, wid):
    import engine as E
    import render
    import scenes
    r = None
    for s, e, path in jobs:
        if done(path, e - s):
            continue
        if r is None:
            r = render.Renderer(scenes.build())
        tmp = path + ".tmp.mp4"
        w = render.ffmpeg_writer(tmp)
        for i in range(s, e):
            w.stdin.write(r.frame(i / E.FPS).tobytes())
        w.stdin.close()
        w.wait()
        os.replace(tmp, path)
        print(f"[w{wid}] fertig {os.path.basename(path)}", flush=True)


if __name__ == "__main__":
    f0, f1, outdir = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    chunk = int(sys.argv[5]) if len(sys.argv) > 5 else 600
    os.makedirs(outdir, exist_ok=True)
    jobs = [(s, min(f1, s + chunk), os.path.join(outdir, f"c_{s:06d}.mp4")) for s in range(f0, f1, chunk)]
    procs = [Process(target=worker, args=(jobs[k::n], k)) for k in range(n)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    print("ALLE FERTIG", [p.exitcode for p in procs], flush=True)
