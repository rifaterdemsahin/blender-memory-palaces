# 🏛️ blender-memory-palaces

🧠 A 7-station **3D memory palace** built in Blender 5.3 (Method of Loci), brought to life with DeepInfra images 🖼️, videos 🎬 and narration 🎙️, with the costs shown.

## 🔗 Important links

| | Link |
|---|---|
| 🌐 | **Live site:** [rifaterdemsahin.github.io/blender-memory-palaces](https://rifaterdemsahin.github.io/blender-memory-palaces/) |
| 🏠 | **Home page** (stations, pop-ups, costs): [`index.html`](index.html) |
| 🧠 | **Why it works:** [`memory-palace/why.html`](memory-palace/why.html) |
| 🚀 | **Leverage it (for Erdem):** [`memory-palace/leverage.html`](memory-palace/leverage.html) |
| 🎞️ | **Storyboard v3 (awaiting approval):** [`memory-palace/storyboard.html`](memory-palace/storyboard.html) |
| 📜 | **Changelog (versions and bad implementations):** [`memory-palace/changelog.html`](memory-palace/changelog.html) |
| 📋 | **Report hub:** [`memory-palace/report.html`](memory-palace/report.html) |
| 🔍 | **Sanity check:** [`memory-palace/sanity-check.html`](memory-palace/sanity-check.html) |
| 🧩 | **blender-director skill:** [`.claude/skills/blender-director`](https://github.com/rifaterdemsahin/blender-memory-palaces/tree/main/.claude/skills/blender-director) |
| 📜 | **Process spec:** [`master.spec`](master.spec) |
| 📚 | **This README on GitHub:** [github.com/rifaterdemsahin/blender-memory-palaces](https://github.com/rifaterdemsahin/blender-memory-palaces/tree/main) |

## 🧱 3D palace (Blender)

- 💾 Scene: [`memory-palace/memory_palace.blend`](memory-palace/memory_palace.blend)
- 🐍 Build script: [`memory-palace/build_palace.py`](memory-palace/build_palace.py)
- 🎞️ Walkthrough video: [`memory-palace/renders/walkthrough.mp4`](memory-palace/renders/walkthrough.mp4)
- 📝 Build log: [`memory-palace/BUILD_LOG.md`](memory-palace/BUILD_LOG.md)

Rebuild it:

```sh
blender -b --python memory-palace/build_palace.py
```

The script writes large files to `/Volumes/Samsung/MemoryPalace/` (see `OUT` at the top of the script).

## 🎨 Generated media (DeepInfra)

- 🖼️ Images: [`memory-palace/assets/`](memory-palace/assets/) (`station_NN.jpg`)
- 🎬 Videos: [`memory-palace/assets/`](memory-palace/assets/) (`station_NN.mp4`)
- 🎙️ Narration: [`memory-palace/assets/`](memory-palace/assets/) (`station_NN.mp3`)
- 📒 Budget ledger (backup): [`memory-palace/assets/ledger.json`](memory-palace/assets/ledger.json)
- 🐍 Generator (budget guard): [`memory-palace/generate_assets.py`](memory-palace/generate_assets.py)
- 🛠️ Site builder: [`memory-palace/build_site.py`](memory-palace/build_site.py)

Generate (your key goes in your shell only, never in a file):

```sh
export DEEPINFRA_API_KEY=...
python3 memory-palace/generate_assets.py --all
python3 memory-palace/build_site.py
```

## ⚪ Clay shot (blender-director skill)

- 🎬 Clip: [`memory-palace/clay/shot_clay.mp4`](memory-palace/clay/shot_clay.mp4)
- 🐍 Build: [`memory-palace/clay/build_clay_shot.py`](memory-palace/clay/build_clay_shot.py)

## 🎬 Story film (HyperFrames)

- 🎞️ Film: [`memory-palace/film/memory_palace_film.mp4`](memory-palace/film/memory_palace_film.mp4) (115.9 s, 1280×720)
- 🎙️ Voiceover: [`memory-palace/story/voiceover.mp3`](memory-palace/story/voiceover.mp3) · 📜 Story text: [`memory-palace/story/story.json`](memory-palace/story/story.json)
- 🧩 HyperFrames project: [`memory-palace/hyperframes-film/`](memory-palace/hyperframes-film/index.html) · 🧱 Builders: [`story/build_film.py`](memory-palace/story/build_film.py), [`story/voiceover.py`](memory-palace/story/voiceover.py)
- 🛡️ The 95 MB full-quality render stays on the external drive; the repo keeps the 1280×720 web version.

## 🧩 Skills

- 🎥 [`blender-director`](.claude/skills/blender-director/SKILL.md): turns a one-line shot idea into a 10-second clay Blender clip with a camera move, plus a Google Flow prompt.
  - 📜 Its helpers: [`scripts/director.py`](.claude/skills/blender-director/scripts/director.py)
  - 📝 Flow prompts: [`flow-prompts.md`](.claude/skills/blender-director/flow-prompts.md) · 💳 Credits: [`credit-planner.md`](.claude/skills/blender-director/credit-planner.md)
  - 🧾 How it was used here: [report](memory-palace/report.html#skill)

## 🚀 Deploy

- ⚙️ GitHub Pages is deployed by the Actions workflow [`.github/workflows/static.yml`](.github/workflows/static.yml) on every push to `main`.
