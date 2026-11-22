"""
build_film.py - write the HyperFrames composition for the memory-palace film.

Reads story.json (chapter durations and text from the real voiceover) and writes
hyperframes-film/index.html:
  * nine timed scenes (Ken Burns station images, 5-second station clips, emoji captions)
  * animated word-by-word subtitles, timed to each chapter's duration
  * an opening card that shows the seven keywords in order
  * a closing card that shows them again and asks the viewer to remember them
  * the single voiceover track, its slot matched to the audio length

Word timings are estimated from word length within each chapter (no transcription model
is installed), so they line up with the narration's pacing rather than exact syllables.

Run:  python3 memory-palace/story/build_film.py
"""
import html
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FILM = os.path.join(ROOT, "hyperframes-film")
ASSETS = os.path.join(FILM, "assets")
ASSET_SRC = "/Volumes/Samsung/MemoryPalace/assets"     # full-size media (external drive)
REPO_ASSETS = os.path.join(ROOT, "assets")              # small repo copies (used for the site build)
CLAY = os.path.join(ROOT, "clay", "shot_clay.mp4")
OVERVIEW = os.path.join(ROOT, "renders", "Cam_00_Overview.png")

with open(os.path.join(HERE, "story.json")) as f:
    story = json.load(f)
chapters = story["chapters"]

# key: (emoji, keyword, place, station image, station clip)
META = {
    "open":  ("🏛️", "Opening", "Blender-built palace", None, None),
    "01": ("🧭", "PLAN", "Entrance Courtyard", "station_01.jpg", "station_01.mp4"),
    "02": ("🧱", "SETTING", "Colonnade", "station_02.jpg", "station_02.mp4"),
    "03": ("🎥", "MOVE", "Rotunda", "station_03.jpg", "station_03.mp4"),
    "04": ("⚪", "CLAY", "Sunken Garden", "station_04.jpg", "station_04.mp4"),
    "05": ("🔍", "CHECK", "Library Bridge", "station_05.jpg", "station_05.mp4"),
    "06": ("📝", "PROMPT", "Observatory", "station_06.jpg", "station_06.mp4"),
    "07": ("🎬", "RENDER", "Summit Altar", "station_07.jpg", "station_07.mp4"),
    "close": ("🚀", "Closing", "Your palace, your route", None, None),
}
KEYWORDS = [(k, META[k][1]) for k in ("01", "02", "03", "04", "05", "06", "07")]


def copy(src, name):
    os.makedirs(ASSETS, exist_ok=True)
    shutil.copy(src, os.path.join(ASSETS, name))
    return f"assets/{name}"


def pick(name):
    # Repo copies first: small, so the Pages artifact stays within size limits.
    for base in (REPO_ASSETS, ASSET_SRC):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    raise SystemExit(f"missing media: {name}")


def word_timeline(text, start, dur, prefix):
    """Split text into word spans with start times spread across the chapter's duration."""
    words = text.split()
    weights = [len(w) + 1 for w in words]
    total = float(sum(weights))
    spans, timings, t = [], [], start
    for i, (w, wt) in enumerate(zip(words, weights)):
        wid = f"{prefix}w{i}"
        spans.append(f'<span class="word" id="{wid}">{html.escape(w)}</span>')
        timings.append((wid, t))
        t += dur * wt / total
    return " ".join(spans), timings


# ---- scenes -------------------------------------------------------------
scenes, sub_html, word_tl = [], [], []
t = 0.0
for i, ch in enumerate(chapters):
    key, dur = ch["key"], float(ch["seconds"])
    emoji, title, place, img, vid = META[key]
    if key == "open":
        bg, clip = copy(OVERVIEW, "overview.png"), None
    elif key == "close":
        bg, clip = None, copy(CLAY, "shot_clay.mp4")
    else:
        bg = copy(pick(img), img)
        clip = copy(pick(vid), vid)
    scenes.append({"i": i, "key": key, "start": t, "dur": dur, "emoji": emoji, "title": title,
                   "place": place, "bg": bg, "clip": clip})

    spans, timings = word_timeline(ch["text"], t, dur, f"s{i}_")
    sub_html.append(f'<div class="clip subs" id="subs{i}" data-start="{t:.2f}" data-duration="{dur:.2f}" '
                    f'data-track-index="6"><div class="subline">{spans}</div></div>')
    for wid, at in timings:
        word_tl.append(f'tl.fromTo("#{wid}", {{ opacity: 0, y: 8 }}, {{ opacity: 1, y: 0, duration: 0.12, ease: "power1.out" }}, {at:.2f});')
    t += dur
TOTAL = t
VOICE_S = float(story["voiceover_seconds"])
voice = copy(os.path.join(ASSET_SRC, "story", "voiceover.mp3"), "voiceover.mp3")

# ---- opening card: the seven words, in order ----------------------------
open_dur = scenes[0]["dur"]
kw_open = "".join(f'<span class="kwd" id="ko{k}"><b>{n}</b> {html.escape(name)}</span>'
                  for k, (n, name) in enumerate(KEYWORDS, start=1))
card_open = (f'<div class="clip card" id="card-open" data-start="0" data-duration="{open_dur:.2f}" data-track-index="5">'
             f'<div class="card-title">🧠 Seven words to remember</div><div class="kwlist">{kw_open}</div></div>')
CARD_OPEN_OUT = 10.0            # card holds the words for ~10 s, then fades
card_tl = []
for k in range(len(KEYWORDS)):
    card_tl.append(f'tl.fromTo("#ko{k + 1}", {{ opacity: 0, x: -36 }}, {{ opacity: 1, x: 0, duration: 0.45, ease: "power3.out" }}, {1.0 + k * 0.8:.2f});')
card_tl.append(f'tl.to("#card-open", {{ opacity: 0, duration: 0.7, ease: "power2.in" }}, {CARD_OPEN_OUT:.2f});')

# ---- closing card: the words again, then ask the viewer to remember them -------
close = scenes[-1]
close_dur = close["dur"]
kw_close = "".join(f'<span class="kwd" id="kc{k}"><b>{n}</b> {html.escape(name)}</span>'
                   for k, (n, name) in enumerate(KEYWORDS, start=1))
card_close = (f'<div class="clip card card-close" id="card-close" data-start="{close["start"]:.2f}" '
              f'data-duration="{close_dur:.2f}" data-track-index="5">'
              f'<div class="kwlist">{kw_close}</div>'
              f'<div class="ask" id="ask">🧠 Now remember them. Say them out loud, in order: '
              f'<b>PLAN · SETTING · MOVE · CLAY · CHECK · PROMPT · RENDER</b></div></div>')
cs = close["start"]
for k in range(len(KEYWORDS)):
    card_tl.append(f'tl.fromTo("#kc{k + 1}", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "power2.out" }}, {cs + 0.5 + k * 0.4:.2f});')
ask_at = cs + 0.5 + 7 * 0.4 + 0.6
card_tl.append(f'tl.fromTo("#ask", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }}, {ask_at:.2f});')

# ---- scene markup -------------------------------------------------------
parts = []
for s in scenes:
    i = s["i"]
    if s["bg"]:
        bg_el = (f'<img class="clip kb" id="bg{i}" src="{s["bg"]}" alt="{html.escape(s["title"])}" '
                 f'data-start="{s["start"]:.2f}" data-duration="{s["dur"]:.2f}" data-track-index="0">')
    else:
        bg_el = (f'<div class="clip kb" id="bg{i}" data-start="{s["start"]:.2f}" '
                 f'data-duration="{s["dur"]:.2f}" data-track-index="0"></div>')
    vid_el = ""
    if s["clip"]:
        clip_dur = min(10.0 if s["key"] == "close" else 5.0, s["dur"])
        # closing: small clip in the top-right, clear of the centred word card and the bottom subtitles
        side = (' style="left:auto;right:60px;top:56px;bottom:auto;width:400px;height:225px"'
                if s["key"] == "close" else "")
        vid_el = (f'<video class="clip scene-video" id="vid{i}" src="{s["clip"]}" muted playsinline{side} '
                  f'data-start="{s["start"]:.2f}" data-duration="{clip_dur:.2f}" data-media-start="0" '
                  f'data-track-index="1"></video>')
    parts.append(f"""
    <section class="scene" id="scene{i}">
      {bg_el}
      {vid_el}
      <div class="clip caption" id="cap{i}" data-start="{s['start'] + 0.4:.2f}" data-duration="{max(0.1, s['dur'] - 0.4):.2f}" data-track-index="4">
        <div class="kw">{s['emoji']} {html.escape(s['title'])}</div>
        <div class="place">{html.escape(s['place'])}</div>
      </div>
    </section>""")

TL = []
for s in scenes:
    i, a = s["i"], s["start"]
    if i == 0:
        TL.append('tl.set("#scene0", { opacity: 1 }, 0);')
    else:
        TL.append(f'tl.fromTo("#scene{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6, ease: "power2.out" }}, {a:.2f});')
    TL.append(f'tl.fromTo("#bg{i}", {{ scale: 1.0 }}, {{ scale: 1.08, duration: {s["dur"]:.2f}, ease: "none" }}, {a:.2f});')
    cap_at = 0.0 if i == 0 else a + 0.4
    TL.append(f'tl.fromTo("#cap{i}", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }}, {cap_at:.2f});')

ALL_TL = TL + card_tl + word_tl
tl_lines = "\n      ".join(ALL_TL)

doc = f"""<!doctype html>
<html lang="en" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      :root {{ --ground: #05060a; --ink: #ffffff; --accent: #7fd6ff; --gold: #ffd479; --font-display: system-ui, -apple-system, "Segoe UI", sans-serif; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: var(--ground); }}
      #root {{ position: relative; width: 1920px; height: 1080px; font-family: var(--font-display); color: var(--ink); }}
      .scene {{ position: absolute; inset: 0; overflow: hidden; opacity: 0; }}
      .kb {{ position: absolute; inset: 0; width: 1920px; height: 1080px; object-fit: cover; transform-origin: 50% 50%; }}
      .scene-video {{ position: absolute; left: 60px; bottom: 170px; width: 720px; height: 405px; object-fit: cover; border-radius: 18px; box-shadow: 0 18px 60px rgba(0,0,0,.6); }}
      .caption {{ position: absolute; left: 60px; top: 56px; background: rgba(5,6,10,.62); padding: 18px 26px; border-radius: 16px; }}
      .caption .kw {{ font-size: 56px; font-weight: 700; letter-spacing: -0.02em; }}
      .caption .place {{ font-size: 30px; color: var(--accent); margin-top: 4px; }}
      .subs {{ position: absolute; left: 60px; right: 60px; bottom: 36px; text-align: center; z-index: 20; }}
      .subline {{ display: inline-block; background: rgba(5,6,10,.68); padding: 12px 22px; border-radius: 14px; font-size: 38px; line-height: 1.35; font-weight: 600; }}
      .word {{ display: inline-block; opacity: 0; margin: 0 .12em; }}
      .card {{ position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: 1280px; padding: 40px 48px; background: rgba(5,6,10,.82); border: 1px solid rgba(127,214,255,.35); border-radius: 26px; z-index: 30; text-align: center; box-shadow: 0 30px 90px rgba(0,0,0,.6); }}
      .card-title {{ font-size: 54px; font-weight: 700; color: var(--gold); margin-bottom: 22px; }}
      .kwlist {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 14px 18px; }}
      .kwd {{ display: inline-block; font-size: 40px; padding: 10px 20px; border-radius: 12px; background: rgba(127,214,255,.12); border: 1px solid rgba(127,214,255,.45); opacity: 0; }}
      .kwd b {{ color: var(--gold); font-weight: 800; margin-right: 6px; }}
      .card-close .ask {{ margin-top: 30px; font-size: 40px; line-height: 1.4; opacity: 0; color: var(--ink); }}
      .card-close .ask b {{ color: var(--accent); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.2f}" data-width="1920" data-height="1080">
{''.join(parts)}
{''.join(sub_html)}
      {card_open}
      {card_close}
      <audio id="voice" src="{voice}" data-start="0" data-duration="{VOICE_S:.2f}" data-volume="1" data-track-index="3"></audio>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {tl_lines}
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""

with open(os.path.join(FILM, "index.html"), "w") as f:
    f.write(doc)
print(f"wrote {FILM}/index.html: {len(scenes)} scenes, {TOTAL:.2f}s, {sum(len(c['text'].split()) for c in chapters)} subtitle words")
