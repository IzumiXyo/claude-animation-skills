#!/usr/bin/env python3
"""Sound bed for The Great Emu War low-poly short.

Source: audio/vo.mp3 (user take). Output: audio/mix.m4a (80.0 s).
Stdlib + ffmpeg only: wind, low drone, a marching snare for the deployment,
a truck, sparse rifle fire, bells and a warm sunset pad.
"""
import math
import random
import subprocess
import wave
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUD = ROOT / "audio"
SR = 48000
VIDEO_DUR = 80.0
VOICE = AUD / "vo.mp3"
VO48 = AUD / "vo48.wav"

subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(VOICE), "-ac", "1", "-ar", str(SR), str(VO48)], check=True)
with wave.open(str(VO48), "rb") as w:
    assert w.getframerate() == SR and w.getnchannels() == 1 and w.getsampwidth() == 2
    voice = array("h", w.readframes(w.getnframes()))

N = int(round(VIDEO_DUR * SR))
L = array("f", [0.0]) * N
R = array("f", [0.0]) * N
rnd = random.Random(1932)


def add_bell(t0, amp=0.05, pan=0.0):
    n = int(2.6 * SR)
    start = int(t0 * SR)
    partials = [(196.0, 1.0), (246.94, 0.55), (293.66, 0.4), (392.0, 0.3), (493.88, 0.2), (784.0, 0.08)]
    for j in range(n):
        idx = start + j
        if idx >= N:
            break
        tt = j / SR
        env = math.exp(-tt * 2.6)
        v = sum(a * math.sin(2 * math.pi * f * tt) for f, a in partials) * env * amp
        L[idx] += v * (1.0 - pan)
        R[idx] += v * (1.0 + pan)


def add_thump(t0, amp=0.05, freq=50.0, decay=10.0):
    n = int(0.6 * SR)
    start = int(t0 * SR)
    for j in range(n):
        idx = start + j
        if idx >= N:
            break
        tt = j / SR
        v = math.sin(2 * math.pi * freq * tt) * math.exp(-tt * decay) * amp
        L[idx] += v
        R[idx] += v


def add_snare(t0, amp=0.03):
    n = int(0.14 * SR)
    start = int(t0 * SR)
    lp = 0.0
    for j in range(n):
        idx = start + j
        if idx >= N:
            break
        tt = j / SR
        nl = rnd.uniform(-1.0, 1.0)
        lp += 0.35 * (nl - lp)
        v = ((nl - lp) * 0.9 + math.sin(2 * math.pi * 185.0 * tt) * 0.5) * math.exp(-tt * 34.0) * amp
        L[idx] += v * 0.9
        R[idx] += v * 1.1


def add_gunshot(t0, amp=0.055):
    n = int(0.30 * SR)
    start = int(t0 * SR)
    lp = 0.0
    for j in range(n):
        idx = start + j
        if idx >= N:
            break
        tt = j / SR
        nl = rnd.uniform(-1.0, 1.0)
        lp += 0.10 * (nl - lp)
        crack = (nl - lp) * math.exp(-tt * 55.0)
        body = math.sin(2 * math.pi * 62.0 * tt) * math.exp(-tt * 16.0)
        v = (crack * 1.1 + body * 0.9) * amp
        L[idx] += v
        R[idx] += v
        if j == int(0.19 * SR):
            for k in range(int(0.25 * SR)):
                jj = idx + k
                if jj >= N:
                    break
                ee = math.exp(-(k / SR) * 14.0)
                echo = rnd.uniform(-1.0, 1.0) * ee * amp * 0.16
                L[jj] += echo
                R[jj] += echo * 0.8


def add_truck(t0, t1, amp=0.028):
    start = int(t0 * SR)
    end = min(N, int(t1 * SR))
    lp = 0.0
    ph = 0.0
    for idx in range(start, end):
        u = (idx - start) / max(1, end - start)
        env = min(1.0, u * 8.0) * min(1.0, (1.0 - u) * 8.0)
        tt = idx / SR
        ph += (44.0 + 5.0 * math.sin(2 * math.pi * 0.6 * tt)) / SR
        saw = (ph % 1.0) * 2.0 - 1.0
        nl = rnd.uniform(-1.0, 1.0)
        lp += 0.04 * (nl - lp)
        v = (saw * 0.45 + lp * 0.9) * env * amp
        L[idx] += v
        R[idx] += v


def add_pad(t0, t1, amp=0.020):
    start = int(t0 * SR)
    end = min(N, int(t1 * SR))
    notes = [(130.81, 0.55), (164.81, 0.40), (196.00, 0.34), (261.63, 0.18)]
    for idx in range(start, end):
        tt = (idx - start) / SR
        u = (idx - start) / max(1, end - start)
        env = min(1.0, u * 3.0) * min(1.0, (1.0 - u) * 2.2)
        v = sum(a * math.sin(2 * math.pi * f * tt + i) for i, (f, a) in enumerate(notes)) * env * amp
        L[idx] += v
        R[idx] += v * 0.92


def add_emu_boom(t0, amp=0.05):
    n = int(0.55 * SR)
    start = int(t0 * SR)
    for j in range(n):
        idx = start + j
        if idx >= N:
            break
        tt = j / SR
        f = 74.0 - 26.0 * min(1.0, tt / 0.45)
        v = math.sin(2 * math.pi * f * tt) * math.exp(-tt * 6.0) * amp
        L[idx] += v
        R[idx] += v


# Wind + low drone bed, one pass.
lp_l = lp_r = 0.0
for i in range(N):
    t = i / SR
    lfo = 0.70 + 0.30 * math.sin(2 * math.pi * 0.037 * t + 0.4)
    d = (0.026 * math.sin(2 * math.pi * 55.0 * t)
         + 0.017 * math.sin(2 * math.pi * 82.5 * t + 0.5)
         + 0.010 * math.sin(2 * math.pi * 110.0 * t + 1.1)
         + 0.016 * math.sin(2 * math.pi * 36.7 * t + 0.2))
    d *= lfo

    nl = rnd.uniform(-1.0, 1.0)
    nr = rnd.uniform(-1.0, 1.0)
    lp_l += 0.012 * (nl - lp_l)
    lp_r += 0.012 * (nr - lp_r)
    gust = 0.65 + 0.35 * math.sin(2 * math.pi * 0.071 * t + 1.7)
    L[i] += d + lp_l * 0.42 * gust
    R[i] += d + lp_r * 0.42 * gust

# Deployment march.
t = 26.1
while t < 51.4:
    add_snare(t, amp=0.024)
    if (round((t - 26.1) / 0.55) % 4) in (0, 2):
        add_thump(t, amp=0.020, freq=74.0, decay=16.0)
    t += 0.55

# Truck in and out.
add_truck(25.9, 30.6, amp=0.032)
add_truck(64.4, 68.2, amp=0.030)

# Rifle fire, spread under the chaos.
for k, t0 in enumerate([40.7, 41.25, 41.9, 42.55, 43.1, 43.75, 44.35]):
    add_gunshot(t0, amp=0.050 if k % 2 else 0.058)

# Scene punctuation.
for t0 in (0.75, 8.35, 25.65, 33.45, 51.95, 60.15, 68.25):
    add_bell(t0, amp=0.042)
for t0 in (8.30, 25.55, 33.37, 51.99, 60.08, 68.18):
    add_thump(t0, amp=0.045, freq=48.0, decay=11.0)

# Two emu booms: the reveal and the title.
add_emu_boom(12.05, amp=0.048)
add_emu_boom(70.85, amp=0.042)

# Warm sunset pad under the legacy.
add_pad(68.2, 80.0, amp=0.021)

# Global fades.
for i in range(N):
    t = i / SR
    g = 1.0
    if t < 0.5:
        g *= t / 0.5
    if t > VIDEO_DUR - 1.4:
        g *= max(0.0, (VIDEO_DUR - t) / 1.4)
    L[i] *= g
    R[i] *= g

bed_peak = max(max(abs(x) for x in L), max(abs(x) for x in R)) or 1.0
voice_peak = max(abs(x) for x in voice) / 32768.0 or 1.0
bed_gain = voice_peak * 0.24 / bed_peak

mix = array("h", [0]) * N
for i in range(N):
    v = voice[i] / 32768.0 if i < len(voice) else 0.0
    s = v + (L[i] + R[i]) * 0.5 * bed_gain
    mix[i] = int(max(-1.0, min(1.0, s)) * 32767)

peak = max(abs(x) for x in mix) / 32768.0 or 1.0
norm = 0.94 / peak
for i in range(N):
    mix[i] = int(mix[i] * norm)

wav_path = AUD / "mix.wav"
with wave.open(str(wav_path), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    stereo = array("h", [0]) * (N * 2)
    for i in range(N):
        stereo[2 * i] = mix[i]
        stereo[2 * i + 1] = mix[i]
    w.writeframes(stereo.tobytes())

subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav_path),
                "-af", "alimiter=limit=0.89:attack=5:release=80:level=false",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(AUD / "mix.m4a")], check=True)
wav_path.unlink()
VO48.unlink()
print(f"wrote {AUD/'mix.m4a'}  ({VIDEO_DUR:.1f}s, voice peak {voice_peak:.2f}, bed gain {bed_gain:.4f}, mix peak {peak:.2f})")
