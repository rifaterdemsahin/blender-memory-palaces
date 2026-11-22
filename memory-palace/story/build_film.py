"""
build_film.py - write the HyperFrames composition for the memory-palace film.

Reads story.json (chapter durations from the real voiceover) and writes
hyperframes-film/index.html: nine timed scenes, each with a Ken Burns station image,
a 5-second station video, an emoji caption, and the single voiceover track.
Copies the media it uses into hyperframes-film/assets/.

Run:  python3 memory-palace/story/build_film.py
Then: cd memory-palace/hyperframes-film && npx hyperframes@0.9.81 render
"""
import html
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FILM = os.path.join(ROOT, "hyperframes-film")
ASSETS = os.path.join(FILM, "assets")
ASSET_SRC = "/Volumes/Samsung/MemoryPalace/assets"          # full-size media (external drive)
REPO_ASSETS = os.path.join(ROOT, "assets")                   # repo copies (small videos)
CLAY = os.path.join(ROOT, "clay", "shot_clay.mp4")
OVERVIEW = os.path.join(ROOT, "..", "memory-palace", "renders", "Cam_00_Overview.png")

with open(os.path.join(HERE, "story.json")) as f:
    story = json.load(f)
chapters = story["chapters"]

# Scene meta: (chapter key, emoji, caption title, image, video)
META = {
    "open": ("🏛️", "Opening", "Blender-built palace", None, None),
    "01": ("🧭", "PLAN", "Entrance Courtyard", "station_01.jpg", "station_01.mp4"),
    "02": ("🧱", "SETTING", "Colonnade", "station_02.jpg", "station_02.mp4"),
    "03": ("🎥", "MOVE", "Rotunda", "station_03.jpg", "station_03.mp4"),
    "04": ("⚪", "CLAY", "Sunken Garden", "station_04.jpg", "station_04.mp4"),
    "05": ("🔍", "CHECK", "Library Bridge", "station_05.jpg", "station_05.mp4"),
    "06": ("📝", "PROMPT", "Observatory", "station_06.jpg", "station_06.mp4"),
    "07": ("🎬", "RENDER", "Summit Altar", "station_07.jpg", "station_07.mp4"),
    "close": ("🚀", "Closing", "Your palace, your route", None, None),
}


def copy(src, name):
    os.makedirs(ASSETS, exist_ok=True)
    dest = os.path.join(ASSETS, name)
    shutil.copy(src, dest)
    return f"assets/{name}"


def pick(name):
    # Repo copies first: they are small, so the Pages artifact stays within size limits.
    # The full-size render used ASSET_SRC; re-render from ASSET_SRC for maximum quality.
    for base in (REPO_ASSETS, ASSET_SRC):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    raise SystemExit(f"missing media: {name}")


scenes = []
t = 0.0
for ch in chapters:
    key = ch["key"]
    dur = float(ch["seconds"])
    emoji, title, place, img, vid = META[key]
    if key == "open":
        bg = copy(OVERVIEW, "overview.png")
        clip = None
    elif key == "close":
        bg = None
        clip = copy(CLAY, "shot_clay.mp4")
    else:
        bg = copy(pick(img), img)
        clip = copy(pick(vid), vid)
    scenes.append({"key": key, "start": t, "dur": dur, "emoji": emoji, "title": title,
                   "place": place, "bg": bg, "clip": clip})
    t += dur
TOTAL = t

voice = copy(os.path.join(ASSET_SRC, "story", "voiceover.mp3"), "voiceover.mp3")
VOICE_S = float(story["voiceover_seconds"])   # the audio slot matches the audio length

parts = []
for i, s in enumerate(scenes):
    if s["bg"]:
        bg_el = (f'<img class="clip kb" id="bg{i}" src="{s["bg"]}" alt="{html.escape(s["title"])}" '
                 f'data-start="{s["start"]:.2f}" data-duration="{s["dur"]:.2f}" data-track-index="0">')
    else:
        bg_el = f'<div class="clip kb" id="bg{i}" data-start="{s["start"]:.2f}" data-duration="{s["dur"]:.2f}" data-track-index="0"></div>'
    vid_el = ""
    if s["clip"]:
        clip_dur = min(5.0 if s["key"] not in ("close",) else 10.0, s["dur"])
        vid_el = (f'<video class="clip scene-video" id="vid{i}" src="{s["clip"]}" muted playsinline '
                  f'data-start="{s["start"]:.2f}" data-duration="{clip_dur:.2f}" data-media-start="0" '
                  f'data-track-index="1"></video>')
    parts.append(f"""
    <section class="scene" id="scene{i}">
      {bg_el}
      {vid_el}
      <div class="clip caption" id="cap{i}" data-start="{s['start'] + 0.4:.2f}" data-duration="{s['dur'] - 0.4:.2f}" data-track-index="4">
        <div class="kw">{s['emoji']} {html.escape(s['title'])}</div>
        <div class="place">{html.escape(s['place'])}</div>
      </div>
    </section>""")

TL = []
for i, s in enumerate(scenes):
    a = s["start"]
    if i == 0:   # the opening is already on screen at 0 s (thumbnail and first frame)
        TL.append('tl.set("#scene0", { opacity: 1 }, 0);')
    else:
        TL.append(f'tl.fromTo("#scene{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6, ease: "power2.out" }}, {a:.2f});')
    TL.append(f'tl.fromTo("#bg{i}", {{ scale: 1.0 }}, {{ scale: 1.08, duration: {s["dur"]:.2f}, ease: "none" }}, {a:.2f});')
    cap_at = 0.0 if i == 0 else a + 0.4
    TL.append(f'tl.fromTo("#cap{i}", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }}, {cap_at:.2f});')

doc = f"""<!doctype html>
<html lang="en" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      :root {{ --ground: #05060a; --ink: #ffffff; --accent: #7fd6ff; --font-display: system-ui, -apple-system, "Segoe UI", sans-serif; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: var(--ground); }}
      #root {{ position: relative; width: 1920px; height: 1080px; font-family: var(--font-display); color: var(--ink); }}
      .scene {{ position: absolute; inset: 0; overflow: hidden; opacity: 0; }}
      .kb {{ position: absolute; inset: 0; width: 1920px; height: 1080px; object-fit: cover; transform-origin: 50% 50%; }}
      .scene-video {{ position: absolute; left: 60px; bottom: 150px; width: 720px; height: 405px; object-fit: cover; border-radius: 18px; box-shadow: 0 18px 60px rgba(0,0,0,.6); }}
      .caption {{ position: absolute; left: 60px; top: 56px; background: rgba(5,6,10,.62); padding: 18px 26px; border-radius: 16px; }}
      .caption .kw {{ font-size: 56px; font-weight: 700; letter-spacing: -0.02em; }}
      .caption .place {{ font-size: 30px; color: var(--accent); margin-top: 4px; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.2f}" data-width="1920" data-height="1080">
{''.join(parts)}
      <audio id="voice" src="{voice}" data-start="0" data-duration="{VOICE_S:.2f}" data-volume="1" data-track-index="3"></audio>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join('      ' + x for x in TL)}
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""

with open(os.path.join(FILM, "index.html"), "w") as f:
    f.write(doc)
print(f"wrote {FILM}/index.html: {len(scenes)} scenes, {TOTAL:.2f}s, media in {ASSETS}")
