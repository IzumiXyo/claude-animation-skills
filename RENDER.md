# Render on GitHub Actions

The animation skills normally render locally with HyperFrames + Chromium. That
does not work on Termux/Android, so this fork adds a workflow that renders on
GitHub Actions instead. No Chromium, Playwright or 1 GB voice models are needed
on the phone.

## Quick start

```bash
cd ~/claude-animation-skills

# from a spec file
./render.sh graph examples/graph.json followers

# or with inline JSON
./render.sh map-route \
  '{"destination":"Monas","minutes":18,"distance":6.4,"unit":"km"}' monas
```

The script triggers the workflow, waits for it, and downloads:

```
renders/<name>/<name>.mp4
renders/<name>/<name>.sheet.jpg
```

You can also trigger it from the GitHub UI:
**Actions → Render animation → Run workflow**, paste the spec JSON and fill in
the skill + output name. Download the result from the run's **Artifacts**
section.

## Supported skills

The workflow supports the quick, spec-driven skills:

`graph`, `map-route`, `breakdown`, `dan-koe`, `kurzgesagt`, `low-poly`,
`minecraft`, `minimalistic-graphics`

`stick-figure` and `zach-3d-films` / `zach-d-films` are full explainer engines
(voiceover, word timings, multi-shot sessions) and are not covered by this
one-shot workflow.

## Notes

- `render.sh` uses a Termux shebang so it can run directly on the phone. On
  another OS, run it as `bash render.sh ...`.
- The quick skills' `SKILL.md` files carry a Termux note pointing at this
  workflow, so the agent does not try a local Chromium render.
- Each render takes about 1 minute (2D) to 2–3 minutes (3D), including setup.
- The workflow caches the HyperFrames browser and npm packages between runs.
- `kit/anim.py` prefers a locally installed HyperFrames binary over `npx`, so
  the CI render is deterministic.
- The workflow installs `hyperframes@0.8.34` with
  `--onnxruntime-node-install-cuda=skip`; the CUDA binary is not available on
  the runner and is not needed for these renders.
- Artifacts expire after 90 days (GitHub's default).
- Upstream updates: `git fetch upstream && git merge upstream/main`, then push.
  The workflow and `render.sh` are additive; `kit/anim.py` has a small local
  binary change.

## Local (non-Termux) rendering

On a normal Linux/macOS machine with Chromium, the original flow still works:

```bash
./install.sh          # links skills into ~/.claude/skills and runs kit/setup.sh
python3 skills/graph/build.py my.graph.json
```
