"""
build_site.py - writes ../index.html from the station data and the generated manifest.

Run:  python3 memory-palace/build_site.py
Reads the station list from generate_assets.py, and (if present) the
manifest and ledger written by generate_assets.py. Missing media are shown as
"not generated yet" so the page is always valid.
"""
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import generate_assets as ga  # noqa: E402

MANIFEST = os.path.join(HERE, "assets", "manifest.json")
LEDGER = os.path.join(ga.OUT, "ledger.json")  # external drive ledger (written by generate_assets.py)


def e(s):
    return html.escape(str(s), quote=True)


def media_exists(name):
    return os.path.exists(os.path.join(HERE, "assets", name))


def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def cost_rows(ledger):
    """Planned cost rows; actual costs are shown when a ledger exists."""
    s = ga.STATIONS
    rows = [
        ("Images", ga.IMAGE_MODEL, "$0.015 / image", len(s), ga.IMAGE_PRICE * len(s)),
        ("Videos", ga.VIDEO_MODEL, f"$0.033 / second, {ga.VIDEO_SECONDS} s each", len(s),
         ga.VIDEO_PRICE_PER_SEC * ga.VIDEO_SECONDS * len(s)),
        ("Narration", ga.TTS_MODEL, "priced per character (upper bound used)", len(s),
         sum(max(0.0005, len(x["say"]) * 0.000005) for x in s)),
    ]
    return rows


def cost_table(ledger):
    rows = cost_rows(ledger)
    planned = sum(r[4] for r in rows)
    body = []
    for kind, model, unit, qty, cost in rows:
        body.append(f"<tr><td>{e(kind)}</td><td><code>{e(model)}</code></td><td>{e(unit)}</td>"
                    f"<td>{qty}</td><td>${cost:.3f}</td></tr>")
    actual = ledger["total"] if ledger else None
    actual_txt = (f"${actual:.4f} actual (from the budget ledger)" if actual is not None
                  else "not spent yet (generation is pending)")
    return f"""
<table>
  <thead><tr><th>Type</th><th>Model</th><th>Unit price</th><th>Qty</th><th>Cost</th></tr></thead>
  <tbody>{''.join(body)}</tbody>
  <tfoot><tr><th colspan="4">Planned total</th><th>${planned:.3f}</th></tr>
  <tr><th colspan="4">Spent so far</th><th>{e(actual_txt)}</th></tr>
  <tr><th colspan="4">Hard budget</th><th>$2.00 limit, guard stops at ${ga.HARD_CAP:.2f}</th></tr></tfoot>
</table>"""


def station_card(s, idx):
    img, vid, aud = f"station_{s['n']:02d}.png", f"station_{s['n']:02d}.mp4", f"station_{s['n']:02d}.mp3"
    parts = []
    parts.append(f'<img src="memory-palace/assets/{img}" alt="{e(s["kw"])} at {e(s["place"])}" loading="lazy">'
                 if media_exists(img) else '<div class="pending">image not generated yet</div>')
    parts.append(f'<video controls preload="none" src="memory-palace/assets/{vid}"></video>'
                 if media_exists(vid) else '<div class="pending">video not generated yet</div>')
    parts.append(f'<audio controls preload="none" src="memory-palace/assets/{aud}"></audio>'
                 if media_exists(aud) else '<div class="pending">narration not generated yet</div>')
    nxt = ""
    if idx + 1 < len(ga.STATIONS):
        n2 = ga.STATIONS[idx + 1]
        nxt = f'<a class="next" href="#station-{n2["n"]}">Next: {s["n"] + 1:02d} {e(n2["kw"])} →</a>'
    return f"""
<article class="station" id="station-{s['n']}">
  <div class="num">{s['n']:02d} · {e(s['kw'])}</div>
  <h3>{e(s['place'])}</h3>
  <div class="media">{''.join(parts)}</div>
  <p class="say"><strong>Narration:</strong> {e(s['say'])}</p>
  <p class="image-prompt"><strong>Image prompt:</strong> {e(s['image'])}</p>
  <p class="image-prompt"><strong>Video prompt:</strong> {e(s['video'])}</p>
  {nxt}
</article>"""


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Memory Palace Live</title>
<meta name="description" content="A 7-station memory palace: Blender 3D, DeepInfra image, video and narration. Cost shown.">
<style>
:root{--bg:#0b0d12;--panel:#151923;--text:#e8ebf2;--muted:#9aa3b5;--accent:#7fd6ff;--ok:#7be38b;--warn:#ffcc66}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--bg:#f4f5f8;--panel:#fff;--text:#151923;--muted:#55607a;--accent:#1565c0;--ok:#1b7f32;--warn:#8a5a00}}
:root[data-theme="light"]{--bg:#f4f5f8;--panel:#fff;--text:#151923;--muted:#55607a;--accent:#1565c0;--ok:#1b7f32;--warn:#8a5a00}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1100px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:clamp(1.9rem,4.5vw,2.8rem);margin:0 0 8px}
h2{font-size:1.45rem;margin:44px 0 12px;border-bottom:1px solid var(--panel);padding-bottom:6px}
h3{margin:4px 0 6px}
p{margin:0 0 12px}
a{color:var(--accent)}
code{background:var(--panel);padding:1px 6px;border-radius:4px;font-size:.9em;word-break:break-all}
.lede{color:var(--muted);max-width:72ch}
.panel{background:var(--panel);border-radius:12px;padding:16px;margin:12px 0}
table{width:100%;border-collapse:collapse;font-size:.95rem}
th,td{padding:8px;border-bottom:1px solid var(--bg);text-align:left;vertical-align:top}
tfoot th{color:var(--ok)}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.station{background:var(--panel);border-radius:12px;padding:14px;scroll-margin-top:12px}
.station .num{color:var(--accent);font-weight:700;letter-spacing:.04em}
.station img,.station video{display:block;width:100%;border-radius:8px;margin:8px 0}
.station audio{width:100%;margin:6px 0}
.say{color:var(--text)}
.image-prompt{color:var(--muted);font-size:.88rem}
.pending{background:var(--bg);color:var(--warn);border-radius:8px;padding:24px 12px;text-align:center;margin:8px 0;font-size:.9rem}
.next{display:inline-block;margin-top:6px}
ol li{margin-bottom:8px}
.badge{display:inline-block;padding:2px 8px;border-radius:999px;background:var(--bg);color:var(--muted);font-size:.8rem}
footer{margin-top:48px;color:var(--muted);font-size:.9rem}
.menu{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:12px}
.menu a,.menu summary{color:var(--accent);text-decoration:none;padding:6px 10px;border-radius:8px;background:var(--panel);cursor:pointer;list-style:none}
.menu details{position:relative}
.menu details div{position:absolute;top:110%;left:0;background:var(--panel);border-radius:10px;padding:8px;display:flex;flex-direction:column;gap:4px;min-width:250px;z-index:5;box-shadow:0 8px 24px rgba(0,0,0,.4)}
</style>
</head>
<body>
<main>
<nav class="menu" aria-label="Site menu">
  <a href="index.html">🏠 Home</a>
  <details>
    <summary>📋 Report ▾</summary>
    <div>
      <a href="memory-palace/report.html">📑 Report hub</a>
      <a href="memory-palace/report.html#sanity">🔍 Sanity check</a>
      <a href="memory-palace/report.html#skill">🧩 Skill usage</a>
      <a href="memory-palace/sanity-check.html">🧪 Full sanity-check page</a>
      <a href="https://github.com/rifaterdemsahin/blender-memory-palaces/tree/main/.claude/skills/blender-director">📂 blender-director skill (GitHub)</a>
    </div>
  </details>
</nav>
<h1>🏛️ Memory Palace, Live</h1>
<p class="lede">A 7-station walk through a 3D memory palace. Each station is one item to remember. Each item is turned into an exaggerated image, a 5-second video and a spoken narration, so you can watch it, hear it, and link it to its place.</p>
<p><span class="badge">Blender 5.3 (3D palace)</span> <span class="badge">FLUX-2-pro (image)</span> <span class="badge">Wan 2.2 (video)</span> <span class="badge">Kokoro (narration)</span> <span class="badge">DeepInfra (inference)</span></p>

<h2>1. How the memory technique works</h2>
<p><strong>The Method of Loci</strong> (memory palace) is over 2,000 years old. You picture a place you know well, put each item at a fixed spot along a route, and later you walk the route in your head. Each spot cues the item, so you recall the items in order.</p>
<ol>
<li><strong>Choose a route.</strong> Here: 7 stations, from the Entrance Courtyard to the Summit Altar. The route never changes.</li>
<li><strong>Place one item at each station.</strong> The item is the keyword: PLAN, SETTING, MOVE, CLAY, CHECK, PROMPT, RENDER.</li>
<li><strong>Make the image absurd.</strong> The brain remembers bizarre, huge, glowing and emotional things far better than ordinary ones. A giant golden compass drawing on the floor sticks better than "a plan".</li>
<li><strong>Add sound and motion.</strong> The narration says the keyword and the idea out loud, and the video shows the scene moving. Two senses plus motion means more ways to find the memory again.</li>
<li><strong>Link each station to the next.</strong> Each station ends with a link to the next one, so the story flows from one place to the next.</li>
<li><strong>Walk it, then test yourself.</strong> Read the station number, close your eyes, and say the keyword before you look. Then check. Repeat until you get all seven in order.</li>
</ol>
<p class="lede">Why this works: the palace gives order (the route), each image gives meaning (the absurd scene), the narration and video give a second channel (sound and motion), and the links give the chain. This is the same method used by memory champions, adapted to a 3D world.</p>

<h2>2. Cost</h2>
<div class="panel">
<p>Every paid call is in a budget ledger, and the generator stops before the hard limit. All figures are USD from DeepInfra's published prices.</p>
__COST_TABLE__
</div>

<h2>3. The seven stations</h2>
<div class="grid">
__STATIONS__
</div>

<h2>4. The 3D palace (Blender)</h2>
<p>The same seven stations, built in Blender 5.3 with <code>memory-palace/build_palace.py</code>. Overview:</p>
<div class="panel"><img src="memory-palace/renders/Cam_00_Overview.png" alt="Blender overview of the 7-station palace" loading="lazy" style="width:100%;border-radius:8px"></div>
<p>Full build notes: <a href="memory-palace/BUILD_LOG.md">BUILD_LOG.md</a>. Scene: <a href="memory-palace/memory_palace.blend">memory_palace.blend</a>.</p>

<h2>5. Everything used</h2>
<ul>
<li><strong>Image model:</strong> <code>black-forest-labs/FLUX-2-pro</code>, DeepInfra OpenAI-compatible <code>/v1/openai/images/generations</code>.</li>
<li><strong>Video model:</strong> <code>Wan-AI/Wan2.2-T2V-A14B</code>, DeepInfra <code>/v1/inference/</code>, 5 s, 720p, landscape.</li>
<li><strong>Narration model:</strong> <code>hexgrad/Kokoro-82M</code> via the OpenAI-compatible speech endpoint. Status: endpoint and price not yet confirmed; the one-call test (see <a href="master.spec">master.spec</a>) is what confirms them.</li>
<li><strong>3D:</strong> Blender 5.3.0 (headless), EEVEE renders.</li>
<li><strong>Scripts:</strong> <code>memory-palace/build_palace.py</code> (Blender), <code>memory-palace/generate_assets.py</code> (DeepInfra, budget guard), <code>memory-palace/build_site.py</code> (this page).</li>
<li><strong>Process and spec:</strong> <a href="master.spec">master.spec</a>.</li>
</ul>
<p class="lede">The API key is never stored in the repo or on this page. It was read only from the environment.</p>

<footer>Source: <a href="https://github.com/rifaterdemsahin/blender-memory-palaces">github.com/rifaterdemsahin/blender-memory-palaces</a></footer>
</main>
</body>
</html>
"""


def main():
    manifest = load_json(MANIFEST)
    ledger = load_json(LEDGER)
    out = (PAGE.replace("__COST_TABLE__", cost_table(ledger))
           .replace("__STATIONS__", "\n".join(station_card(s, i) for i, s in enumerate(ga.STATIONS))))
    with open(os.path.join(ROOT, "index.html"), "w") as f:
        f.write(out)
    print("wrote index.html", "with manifest" if manifest else "(no manifest yet)")


if __name__ == "__main__":
    main()
