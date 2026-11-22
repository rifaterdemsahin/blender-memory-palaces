# 🏗️ Architecture

The top-level map of the project: what is built, how the pieces connect, and where each one is published.

## 🧭 The big picture

```
            ┌──────────────┐      ┌────────────────────┐      ┌──────────────────┐
  Blender ─▶│ palace build │─────▶│ renders + .blend   │─────▶│ palace pages     │
            └──────────────┘      └────────────────────┘      └──────────────────┘
                                                                       │
            ┌──────────────┐      ┌────────────────────┐              ▼
  DeepInfra▶│ generators   │─────▶│ images, videos,    │─────▶ ┌──────────────────┐
            │ (budget guard)│     │ narration (MP3)    │       │ index.html       │
            └──────────────┘      └────────────────────┘       │ (top page)       │
                                          │                    └──────────────────┘
            ┌──────────────┐              ▼                             ▲
  Story  ──▶│ story + board│─────▶ ┌────────────────────┐              │
            │ (approval)   │       │ HyperFrames film   │──────────────┘
            └──────────────┘       └────────────────────┘
                                                                       │
                                  GitHub Actions (static.yml) ◀────────┘
                                                │
                                                ▼
                                  GitHub Pages (live site)
```

## 🧱 Components

| Component | What it does | Where it lives |
|---|---|---|
| 🏛️ Palace (Blender) | Builds the 7-station 3D palace headless and renders the stations and the walkthrough. | `memory-palace/build_palace.py`, `memory-palace/renders/` |
| 🧩 Skill-built clay shot | The blender-director skill's helpers build a grey clay shot. | `memory-palace/clay/`, `.claude/skills/blender-director/` |
| 🎨 Media generator | Makes images, videos and narration per station, with a $1.90 hard guard. | `memory-palace/generate_assets.py`, `memory-palace/assets/` |
| 🎙️ Voiceover | Reads the story with the narration model; durations come from a full decode. | `memory-palace/story/voiceover.py` |
| 🎞️ Film | A HyperFrames composition stitched from the palace media, voiceover and word subtitles. | `memory-palace/hyperframes-film/`, `memory-palace/film/` |
| 🎞️ Story and storyboard | The story and its storyboard, which must be approved before production. | `memory-palace/story/STORY.md`, `memory-palace/storyboard.html` |
| 🛠️ Site builder | Writes the top page from the station data, the cost ledger and the media. | `memory-palace/build_site.py` → `index.html` |
| 📜 Changelog | Every version, with the bad implementations recorded. | `memory-palace/CHANGELOG.md` |
| 🚀 Deploy | Builds and publishes the Pages site on every push to `main`. | `.github/workflows/static.yml` |

## 🔀 Flow of one change

1. A change is made in the repo (script, story, or page).
2. Media and film are regenerated only where the change needs them (the cost guard stops paid calls past $1.90).
3. `build_site.py` regenerates `index.html` from the station data, the ledger and the media files.
4. The change is committed to `main` and pushed.
5. The `static.yml` workflow uploads the repo as a Pages artifact, waits 60 s for it to be indexed, and deploys.
6. The live site is checked with HTTP requests, and a changelog entry records what changed.

## 🗺️ Site map (top page to pages)

- 🏠 **Top page** (`index.html`): stations, pop-up media, the film, costs and the menu.
- 🏗️ **Architecture** (`architecture.html`): this page, rendered from `ARCHITECTURE.md`.
- 📜 **Changelog** (`memory-palace/changelog.html`): rendered from `CHANGELOG.md`.
- 🎞️ **Storyboard** (`memory-palace/storyboard.html`): storyboard for approval.
- 🧠 **Why it works** (`memory-palace/why.html`) and 🚀 **Leverage it** (`memory-palace/leverage.html`).
- 📋 **Reports** (`memory-palace/report.html`, `memory-palace/sanity-check.html`).
- 🧩 **Architecture board (Whiteboard)**: a shared board titled "Memory Palace Architecture": [open the board](https://claude.ai/artifact/C34ZR7eo5Gt3utaiFZ5Fwn).

## 🔐 Rules the architecture follows

- 🔑 API keys are read only from the environment and are never written to files or to the repo.
- 📦 The Pages artifact stays small. Full-size renders stay on the external drive, and the repo holds the web versions.
- ✅ Story and storyboard are approved before any voice, subtitle or film is rendered.
- 🧾 Every version is recorded in the changelog, including the failed attempts.
