#!/usr/bin/env python3
"""The Great Emu War (1932) — 80 s low-poly short.

    python3 projects/emu-war-lowpoly/build.py <spec.json> [--snap 1.5,8,22]

The spec is merged over projects/emu-war-lowpoly/spec.json, so the workflow can
pass only {"out": "out/name.mp4"} and still get captions/timing.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "kit"))
import anim  # noqa: E402

DEFAULTS = {"duration": 80.0, "caps": []}


def check(spec):
    dur = float(spec["duration"])
    if not 60 <= dur <= 85:
        sys.exit("spec: duration should stay in the 60–85 s range")
    if not spec.get("caps"):
        sys.exit("spec: caps is empty")
    if not (HERE / "template.html").exists():
        sys.exit("template.html is missing")


def merge_spec(path):
    spec = json.loads((HERE / "spec.json").read_text())
    if path.exists():
        inline = json.loads(path.read_text())
        spec.update(inline)
    for k, v in DEFAULTS.items():
        spec.setdefault(k, v)
    return spec


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        sys.exit(__doc__)
    spec_path = Path(args[0]).resolve()
    snap = None
    if "--snap" in args:
        snap = [float(x) for x in args[args.index("--snap") + 1].split(",")]

    anim.check_setup(three=True)
    spec = merge_spec(spec_path)
    check(spec)
    dur = float(spec["duration"])

    out = Path(spec["out"]) if spec.get("out") else HERE / "renders" / (spec_path.stem + ".mp4")
    if not out.is_absolute():
        out = spec_path.parent / out
    out.parent.mkdir(parents=True, exist_ok=True)

    work = spec_path.parent / ".work" / out.stem
    anim.prepare(HERE / "template.html", spec, dur, work, three=True)
    anim.FPS = 24

    if snap:
        anim.snapshots(work, snap, out.with_suffix(".snaps"))
        return

    audio = HERE / "audio" / "mix.m4a"
    if not audio.exists():
        sys.exit("audio/mix.m4a is missing; run make_mix.py first")

    silent = out.with_suffix(".silent.mp4")
    anim.render(work, silent)
    print(f"muxing {audio.name} ...", flush=True)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(audio),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-shortest", "-movflags", "+faststart", str(out)],
        check=True,
    )
    silent.unlink()
    sh = out.with_suffix(".sheet.jpg")
    anim.sheet(out, sh, n=8)
    print(f"done: {out}\nsheet: {sh}")


if __name__ == "__main__":
    main()
