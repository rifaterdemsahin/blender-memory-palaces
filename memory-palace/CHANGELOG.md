# 📜 Changelog

Every version of the palace and the film, what changed, and which attempts were bad implementations. Newest first.

## 🚦 Current state

⏳ **v0.8: story v3 drafted, awaiting approval.** The new story is a connected relay, and its storyboard is on the [storyboard page](storyboard.html). The film is not re-rendered until the storyboard is approved.

---

## 🗂️ Versions

### 🎞️ v0.8 · Story v3 and storyboard (draft) · ⏳ awaiting approval

📖 A new story built on the linking (chain) method: one handoff per station, so the seven items form one chain. Storyboard with nine scenes, approaches considered, and an approval step. Changelog page added.

🔬 Method sources: the chain-story method, and the AI mnemonic story in the KMind Palace README ([suka233/kmind-palace](https://github.com/suka233/kmind-palace)), which ties each item to its spot with one vivid scene.

📄 Files: `memory-palace/story/STORY.md`, `memory-palace/storyboard.html`, `memory-palace/changelog.html`.

### 🎬 v0.7 · Story film v2 (133 s) · ❌ bad implementation

Exaggerated narration, word-by-word subtitles, and opening and closing word cards. Built and published without an approved story.

**What was wrong:**

- ❌ **Not a connected story.** Each station still stood alone, so the viewer had no chain to remember. This is the main failure.
- ❌ **Published without approval.** I rendered and deployed the film before the story was approved. That broke the process.
- ⚠️ **Subtitle timing is estimated** from word length, not transcribed.
- ⚠️ **Closing card overlapped the clip inset** at first. Fixed in the final render.

🔧 Fixed here: the timing error (see v0.6), the closing overlap, and the word cards. Not fixed: the story structure. That is why v3 exists.

### 🎬 v0.6 · Story film v1 (116 s) · ❌ bad implementation

First film: a station image and clip per scene, with a per-station caption and narration.

**What was wrong:**

- ❌ **Not a connected story.** Seven separate captions and facts, with no handoff between stations.
- ❌ **No subtitles** and no story structure.
- ❌ **Timing error.** Scene lengths came from MP3 file headers, which overstated the audio by about 15 s. Scenes were longer than their narration.
- ❌ **Composition structure.** Videos nested in timed wrappers caused lint errors, fixed by flattening.

### ✅ v0.5 · Flow prompt, crop fix, cube fix · done

- ✅ Flow prompt for the clay shot, in `memory-palace/clay/flow_prompt.md`.
- ✅ Walkthrough camera at 24 mm and 2.4 m, so "05 CHECK" and "Library Bridge" sit fully inside the frame.
- ✅ CHECK cube lowered from 2.1 m to 1.6 m, so it no longer covers the station name.

### ⚪ v0.4 · Skill-built clay shot · done, partly

- ✅ The clay shot runs the blender-director skill's `director.py` helpers, uses the `truck` camera move, checks frames 1, 120 and 240, and renders from the terminal.
- ⚠️ The coloured palace is still a custom script, and the MCP connector was not used (headless run).
- ❌ **Bad implementation, fixed:** `set_mp4_output()` was called after `save()`, so the file kept Blender's default output path and the first render went to `/tmp`. Fixed by setting the output first.

### 🔍 v0.3 · Sanity fix: mirrored labels · done

- ✅ Every label turns to face the walkthrough camera (Track To constraint), so text reads correctly.
- ❌ **Bad implementation, fixed:** the first walkthrough had mirrored labels that passed the file checks but failed a frame check. Lesson: check frames, not only file properties.

### 🎨 v0.2 · Generated media (DeepInfra) · done

- ✅ Seven images (FLUX-2-pro), seven 5-second videos (Wan 2.2), seven narrations (Kokoro-82M). Ledger $1.28 of $2.00.
- ❌ **Bad implementations, fixed:** the JPEG was saved as `.png`; the Pages artifact grew to 43 MB and the deploy failed three times (fixed by shrinking the repo copies of the videos to 640 px).

### 🏛️ v0.1 · Blender palace and Pages site · done

- ✅ Seven-station palace built headless in Blender 5.3, eight renders, GitHub Pages deploy with the Actions workflow.
- ❌ **Bad claim, corrected:** the first report said the palace used the blender-director skill. It did not. The report now says so.

---

## 🧾 Lessons

1. 🔗 **A memory story must link the items** (one handoff per station). Seven facts in a row do not work.
2. ✅ **Get approval before production.** Story and storyboard first, then voice, subtitles and render.
3. 🖼️ **Check frames, not just file properties.** Two bugs (mirrored labels, timing from headers) passed file checks.
4. 📦 **Keep deploy artifacts small.** Large media can fail the Pages deploy with "no artifacts found".
