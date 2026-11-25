#!/usr/bin/env python3
"""Build a restrained documentary bed under the supplied VO, then encode the mix.

Source: audio/vo.mp3 (the user's take). Output: audio/mix.m4a (70.8 s).
Everything here is stdlib + ffmpeg; no numpy needed.
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
VIDEO_DUR = 70.8
VOICE = AUD / "vo.mp3"
VO48 = AUD / "vo48.wav"

subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(VOICE), "-ac", "1", "-ar", str(SR), str(VO48)], check=True)
with wave.open(str(VO48), "rb") as w:
    assert w.getframerate() == SR and w.getnchannels() == 1 and w.getsampwidth() == 2
    voice = array("h", w.readframes(w.getnframes()))

N = int(round(VIDEO_DUR * SR))
L = array("f", [0.0]) * N
R = array("f", [0.0]) * N


def add_bell(t0, amp=0.065, pan=0.0):
    n = int(3.0 * SR)
    start = int(t0 * SR)
    partials = [(220.0, 1.0), (277.18, 0.55), (329.63, 0.4), (440.0, 0.3), (554.37, 0.2), (880.0, 0.1)]
    for j in range(n):
        idx = start + j
        if idx >= N:
            break
        tt = j / SR
        env = math.exp(-tt * 2.3)
        v = sum(a * math.sin(2 * math.pi * f * tt) for f, a in partials) * env * amp
        L[idx] += v * (1.0 - pan)
        R[idx] += v * (1.0 + pan)


def add_thump(t0, amp=0.055, freq=48.0, decay=9.0):
    n = int(0.55 * SR)
    start = int(t0 * SR)
    for j in range(n):
        idx = start + j
        if idx >= N:
            break
        tt = j / SR
        env = math.exp(-tt * decay)
        v = math.sin(2 * math.pi * freq * tt) * env * amp
        L[idx] += v
        R[idx] += v


def add_riser(t0, t1, amp=0.028):
    start = int(t0 * SR)
    end = min(N, int(t1 * SR))
    for idx in range(start, end):
        u = (idx - start) / max(1, end - start)
        tt = idx / SR
        v = (random.uniform(-1, 1) * 0.55 + math.sin(2 * math.pi * (90 + 70 * u) * tt) * 0.45)
        v *= (u ** 2) * amp
        L[idx] += v
        R[idx] += v


def crowd_target(t):
    if t < 6.33:
        return 0.035
    if t < 14.44:
        return 0.14
    if t < 26.25:
        return 0.50
    if t < 36.80:
        return 0.24
    if t < 45.89:
        return 0.42
    return 0.085


# Drone + filtered noise bed. The street "crowd" is filtered noise, never a sample.
lp_l = lp_r = fast_l = fast_r = env = 0.0
for i in range(N):
    t = i / SR
    lfo = 0.72 + 0.28 * math.sin(2 * math.pi * 0.041 * t)
    d = (0.030 * math.sin(2 * math.pi * 55.0 * t)
         + 0.020 * math.sin(2 * math.pi * 82.5 * t + 0.5)
         + 0.012 * math.sin(2 * math.pi * 110.0 * t + 1.1)
         + 0.018 * math.sin(2 * math.pi * 36.7 * t + 0.2))
    d *= lfo

    nl = random.uniform(-1.0, 1.0)
    nr = random.uniform(-1.0, 1.0)
    lp_l += 0.015 * (nl - lp_l)
    lp_r += 0.015 * (nr - lp_r)
    fast_l += 0.20 * (nl - fast_l)
    fast_r += 0.20 * (nr - fast_r)

    target = crowd_target(t)
    env += 0.0015 * (target - env)
    crowd_l = (nl - fast_l) * env * 0.020
    crowd_r = (nr - fast_r) * env * 0.020

    L[i] += d + lp_l * 0.25 + crowd_l
    R[i] += d + lp_r * 0.25 + crowd_r

# Scene punctuation.
for t0 in (0.70, 14.44, 45.89, 67.00):
    add_bell(t0, amp=0.060)
for t0 in (6.33, 14.44, 26.25, 36.80, 45.89):
    add_thump(t0, amp=0.050)

# Heartbeat under the "they could not stop" section.
t = 27.0
while t < 36.5:
    add_thump(t, amp=0.065, freq=55.0, decay=13.0)
    add_thump(t + 0.17, amp=0.042, freq=48.0, decay=15.0)
    t += 1.15

add_riser(44.0, 45.9, amp=0.026)

# Global fades.
for i in range(N):
    t = i / SR
    g = 1.0
    if t < 0.5:
        g *= t / 0.5
    if t > VIDEO_DUR - 2.0:
        g *= max(0.0, (VIDEO_DUR - t) / 2.0)
    L[i] *= g
    R[i] *= g

bed_peak = max(max(abs(x) for x in L), max(abs(x) for x in R)) or 1.0
voice_peak = max(abs(x) for x in voice) / 32768.0 or 1.0
bed_gain = voice_peak * 0.20 / bed_peak

mix = array("h", [0]) * N
for i in range(N):
    v = voice[i] / 32768.0 if i < len(voice) else 0.0
    s = v + (L[i] + R[i]) * 0.5 * bed_gain
    mix[i] = int(max(-1.0, min(1.0, s)) * 32767)

peak = max(abs(x) for x in mix) / 32768.0 or 1.0
norm = 0.92 / peak
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
                "-af", "volume=4.5dB,alimiter=limit=0.89:attack=5:release=80:level=false",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(AUD / "mix.m4a")], check=True)
wav_path.unlink()
VO48.unlink()
print(f"wrote {AUD/'mix.m4a'}  ({VIDEO_DUR:.1f}s, voice peak {voice_peak:.2f}, bed gain {bed_gain:.4f}, mix peak {peak:.2f})")
