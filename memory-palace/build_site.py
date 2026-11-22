"""
build_site.py - writes ../index.html from the station data, the cost ledger and the media files.

Run:  python3 memory-palace/build_site.py
Media is read from memory-palace/assets/ (copied there as backups). Missing media is shown as
a clear "not generated yet" placeholder, so the page is always valid.
Each station card opens a modal pop-up (native <dialog>) with its image, video and narration.
"""
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import generate_assets as ga  # noqa: E402

ASSETS = os.path.join(HERE, "assets")
LEDGER = os.path.join(ga.OUT, "ledger.json")
REPO_LEDGER = os.path.join(ASSETS, "ledger.json")  # backup copy kept in the project


def e(s):
    return html.escape(str(s), quote=True)


def have(name):
    return os.path.exists(os.path.join(ASSETS, name))


def load_ledger():
    for p in (LEDGER, REPO_LEDGER):
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return None


def cost_table(ledger):
    s = ga.STATIONS
    rows = [
        ("🖼️ Images", ga.IMAGE_MODEL, "$0.015 / image", len(s), ga.IMAGE_PRICE * len(s)),
        ("🎬 Videos", ga.VIDEO_MODEL, f"$0.033 / second, {ga.VIDEO_SECONDS} s each", len(s),
         ga.VIDEO_PRICE_PER_SEC * ga.VIDEO_SECONDS * len(s)),
        ("🎙️ Narration", ga.TTS_MODEL, "per character (upper bound used)", len(s),
         sum(max(0.0005, len(x["say"]) * 0.000005) for x in s)),
    ]
    planned = sum(r[4] for r in rows)
    body = "".join(
        f"<tr><td>{e(k)}</td><td><code>{e(m)}</code></td><td>{e(u)}</td><td>{q}</td><td>${c:.3f}</td></tr>"
        for k, m, u, q, c in rows)
    spent = f"${ledger['total']:.4f} (from the budget ledger)" if ledger else "not spent yet"
    return f"""
<div class="table-wrap"><table>
<thead><tr><th>Type</th><th>Model</th><th>Unit price</th><th>Qty</th><th>Planned</th></tr></thead>
<tbody>{body}</tbody>
<tfoot>
<tr><th colspan="4">📊 Planned total</th><th>${planned:.3f}</th></tr>
<tr><th colspan="4">💸 Spent so far</th><th>{e(spent)}</th></tr>
<tr><th colspan="4">🛡️ Budget guard</th><th>stops at ${ga.HARD_CAP:.2f} (limit $2.00)</th></tr>
</tfoot></table></div>"""


def media_block(s):
    n = s["n"]
    img, vid, aud = f"station_{n:02d}.jpg", f"station_{n:02d}.mp4", f"station_{n:02d}.mp3"
    out = []
    out.append(f'<img src="memory-palace/assets/{img}" alt="🖼️ {e(s["kw"])} at {e(s["place"])}">'
               if have(img) else '<div class="pending">🖼️ image not generated yet</div>')
    out.append(f'<video controls preload="metadata" src="memory-palace/assets/{vid}"></video>'
               if have(vid) else '<div class="pending">🎬 video not generated yet</div>')
    out.append(f'<audio controls preload="none" src="memory-palace/assets/{aud}"></audio>'
               if have(aud) else '<div class="pending">🎙️ narration not generated yet</div>')
    return "".join(out)


def station_card(s):
    n = s["n"]
    ready = all(have(x) for x in (f"station_{n:02d}.jpg", f"station_{n:02d}.mp4", f"station_{n:02d}.mp3"))
    badge = "✅ media ready" if ready else "⏳ media pending"
    return f"""
<button class="station" type="button" data-open="modal-{n}" aria-haspopup="dialog">
  <span class="num">{n:02d} · {e(s['kw'])}</span>
  <span class="place">{e(s['place'])}</span>
  <span class="badge">{badge}</span>
  <span class="cta">👉 Open station</span>
</button>"""


def station_modal(s, idx):
    n = s["n"]
    nxt = ""
    if idx + 1 < len(ga.STATIONS):
        n2 = ga.STATIONS[idx + 1]
        nxt = f'<button class="next" type="button" data-open="modal-{n2["n"]}">➡️ Next: {n2["n"]:02d} {e(n2["kw"])}</button>'
    return f"""
<dialog id="modal-{n}" class="modal" aria-labelledby="title-{n}">
  <div class="modal-head">
    <h3 id="title-{n}">🏛️ {n:02d} · {e(s['kw'])} <small>{e(s['place'])}</small></h3>
    <button class="close" type="button" data-close aria-label="Close">✖️</button>
  </div>
  <div class="media">{media_block(s)}</div>
  <p>🎙️ <strong>Narration:</strong> {e(s['say'])}</p>
  <p>🎨 <strong>Image prompt:</strong> {e(s['image'])}</p>
  <p>🎬 <strong>Video prompt:</strong> {e(s['video'])}</p>
  <div class="modal-foot">{nxt}</div>
</dialog>"""


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🏛️ Memory Palace Live</title>
<meta name="description" content="A 7-station memory palace: Blender 3D, DeepInfra image, video and narration, with costs shown.">
<style>
:root{--bg:#0b0d12;--panel:#151923;--text:#e8ebf2;--muted:#9aa3b5;--accent:#7fd6ff;--ok:#7be38b;--warn:#ffcc66}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--bg:#f4f5f8;--panel:#fff;--text:#151923;--muted:#55607a;--accent:#1565c0;--ok:#1b7f32;--warn:#8a5a00}}
:root[data-theme="light"]{--bg:#f4f5f8;--panel:#fff;--text:#151923;--muted:#55607a;--accent:#1565c0;--ok:#1b7f32;--warn:#8a5a00}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1100px;margin:0 auto;padding:20px 16px 64px}
h1{font-size:clamp(1.9rem,4.5vw,2.8rem);margin:12px 0 8px}
h2{font-size:1.45rem;margin:40px 0 12px;border-bottom:1px solid var(--panel);padding-bottom:6px;scroll-margin-top:16px}
p{margin:0 0 12px}
a{color:var(--accent)}
code{background:var(--panel);padding:1px 6px;border-radius:4px;font-size:.9em;word-break:break-all}
.lede{color:var(--muted);max-width:72ch}
.panel{background:var(--panel);border-radius:12px;padding:16px;margin:12px 0}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.95rem;min-width:520px}
th,td{padding:8px;border-bottom:1px solid var(--bg);text-align:left;vertical-align:top}
tfoot th{color:var(--ok)}
.menu{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:8px}
.menu a,.menu summary{color:var(--accent);text-decoration:none;padding:7px 11px;border-radius:8px;background:var(--panel);cursor:pointer;list-style:none}
.menu details{position:relative}
.menu details div{position:absolute;top:110%;left:0;background:var(--panel);border-radius:10px;padding:8px;display:flex;flex-direction:column;gap:4px;min-width:260px;z-index:5;box-shadow:0 8px 24px rgba(0,0,0,.4)}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(230px,1fr))}
button.station{all:unset;cursor:pointer;display:flex;flex-direction:column;gap:4px;background:var(--panel);border-radius:12px;padding:14px;transition:transform .15s}
button.station:hover,button.station:focus-visible{transform:translateY(-3px);outline:2px solid var(--accent)}
.station .num{color:var(--accent);font-weight:700;letter-spacing:.04em}
.station .place{font-size:1.1rem}
.station .badge{color:var(--muted);font-size:.85rem}
.station .cta{color:var(--ok);font-size:.9rem;margin-top:4px}
dialog.modal{background:var(--panel);color:var(--text);border:none;border-radius:14px;padding:18px;width:min(720px,94vw);box-shadow:0 20px 60px rgba(0,0,0,.6)}
dialog.modal::backdrop{background:rgba(0,0,0,.65)}
.modal-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.modal-head h3{margin:0 0 8px}
.modal-head small{color:var(--muted);font-weight:400}
.close{all:unset;cursor:pointer;font-size:1.2rem;padding:4px}
.modal img,.modal video{display:block;width:100%;border-radius:10px;margin:8px 0}
.modal audio{width:100%;margin:6px 0}
.modal .media{margin:4px 0 10px}
.modal p{font-size:.95rem}
.pending{background:var(--bg);color:var(--warn);border-radius:10px;padding:26px 12px;text-align:center;margin:8px 0;font-size:.95rem}
.next{all:unset;cursor:pointer;color:var(--accent);background:var(--bg);padding:8px 12px;border-radius:8px}
.cards{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}
.card{background:var(--panel);border-radius:12px;padding:14px;text-decoration:none;color:var(--text);display:block}
.card b{color:var(--accent)}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;background:var(--panel);color:var(--muted);font-size:.85rem;margin:2px}
footer{margin-top:48px;color:var(--muted);font-size:.9rem}
</style>
</head>
<body>
<main>
<nav class="menu" aria-label="Site menu">
  <a href="index.html">🏠 Home</a>
  <a href="memory-palace/why.html">🧠 Why it works</a>
  <a href="memory-palace/leverage.html">🚀 Leverage it</a>
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
  <a href="https://github.com/rifaterdemsahin/blender-memory-palaces/tree/main">📚 README on GitHub</a>
</nav>

<h1>🏛️ Memory Palace, Live</h1>
<p class="lede">🧭 A 7-station walk through a 3D memory palace. Each station holds one item. Each item is turned into an exaggerated image 🖼️, a 5-second video 🎬 and a spoken narration 🎙️. Tap a station to open it.</p>
<p>
  <span class="badge">🧱 Blender 5.3</span>
  <span class="badge">🎨 FLUX-2-pro</span>
  <span class="badge">🎬 Wan 2.2</span>
  <span class="badge">🎙️ Kokoro</span>
  <span class="badge">⚡ DeepInfra</span>
  <span class="badge">🧩 blender-director skill</span>
</p>

<h2>🧩 1. Components on this page</h2>
<div class="cards">
  <a class="card" href="#stations">🏛️ <b>7 Stations</b><br>Tap each one for a pop-up with its media.</a>
  <a class="card" href="#palace">🧱 <b>3D palace</b><br>Blender scene, walkthrough video, renders.</a>
  <a class="card" href="#clay">⚪ <b>Clay shot</b><br>Grey clay version built with the blender-director skill.</a>
  <a class="card" href="#cost">💰 <b>Costs</b><br>Every paid call, planned and spent.</a>
  <a class="card" href="memory-palace/why.html">🧠 <b>Why it works</b><br>The memory science behind it.</a>
  <a class="card" href="memory-palace/leverage.html">🚀 <b>Leverage it</b><br>How Erdem can use it.</a>
  <a class="card" href="memory-palace/report.html">📋 <b>Reports</b><br>Sanity check and skill review.</a>
</div>

<h2 id="stations">🏛️ 2. The seven stations</h2>
<div class="grid">
__STATIONS__
</div>

<h2 id="palace">🧱 3. The 3D palace (Blender)</h2>
<div class="panel">
  <p>🎞️ <strong>Walkthrough video</strong> (10 s, 240 frames, rendered in Blender):</p>
  <video controls preload="metadata" src="memory-palace/renders/walkthrough.mp4" style="width:100%;border-radius:10px"></video>
  <p style="margin-top:12px">🛰️ <strong>Overview render:</strong></p>
  <img src="memory-palace/renders/Cam_00_Overview.png" alt="🧱 Overview of the 7-station palace" loading="lazy" style="width:100%;border-radius:10px">
  <p style="margin-top:12px">📄 Files: <a href="memory-palace/memory_palace.blend">💾 memory_palace.blend</a> · <a href="memory-palace/build_palace.py">🐍 build_palace.py</a> · <a href="memory-palace/BUILD_LOG.md">📝 BUILD_LOG.md</a></p>
</div>

<h2 id="clay">⚪ 4. Clay shot (blender-director skill)</h2>
<div class="panel">
  <p>📝 <a href="flow_prompt.md">Flow prompt</a> for this clip is in the project.</p>
  <p>🧩 Built with the repo's <code>blender-director</code> skill and its <code>director.py</code> helpers. One <code>truck</code> camera move past seven clay plinths, 10 s at 24 fps.</p>
  <video controls preload="metadata" src="memory-palace/clay/shot_clay.mp4" style="width:100%;border-radius:10px"></video>
  <p style="margin-top:12px">📂 <a href="https://github.com/rifaterdemsahin/blender-memory-palaces/tree/main/.claude/skills/blender-director">📂 Skill folder on GitHub</a> · <a href="memory-palace/report.html#skill">🧩 Skill-usage report</a></p>
</div>

<h2 id="cost">💰 5. Cost</h2>
<div class="panel">
  <p>🛡️ Every paid call is in a budget ledger, and generation stops before the hard limit. All figures are USD at DeepInfra's listed prices.</p>
__COST_TABLE__
</div>

<h2>🔗 6. Everything used</h2>
<ul>
<li>🎨 <strong>Image:</strong> <code>black-forest-labs/FLUX-2-pro</code> via DeepInfra's OpenAI-compatible images endpoint.</li>
<li>🎬 <strong>Video:</strong> <code>Wan-AI/Wan2.2-T2V-A14B</code> via DeepInfra, 5 s, 720p.</li>
<li>🎙️ <strong>Narration:</strong> <code>hexgrad/Kokoro-82M</code> via DeepInfra's OpenAI-compatible speech endpoint.</li>
<li>🧱 <strong>3D:</strong> Blender 5.3.0 (headless, EEVEE).</li>
<li>🧩 <strong>Skill:</strong> <code>blender-director</code> (see the report for how far it was followed).</li>
<li>🎞️ <strong>Video coordination:</strong> the HyperFrames CLI (npm <code>hyperframes</code> 0.9.81) runs on demand via <code>npx</code>; the video composition is ⏳ pending.</li>
<li>📜 <strong>Process:</strong> <a href="master.spec">📜 master.spec</a> · <a href="README.md">📚 README</a></li>
</ul>
<p class="lede">🔐 The API key is never stored in the repo or on this page.</p>

<footer>🏛️ Source: <a href="https://github.com/rifaterdemsahin/blender-memory-palaces">github.com/rifaterdemsahin/blender-memory-palaces</a></footer>
</main>

__MODALS__
<script>
// 🪟 Modal pop-ups for stations: open with data-open, close with data-close or a backdrop click.
document.querySelectorAll('[data-open]').forEach(function (b) {
  b.addEventListener('click', function () {
    var d = document.getElementById(b.getAttribute('data-open'));
    if (!d) return;
    document.querySelectorAll('dialog[open]').forEach(function (o) { o.close(); });
    if (d.showModal) d.showModal(); else d.setAttribute('open', '');
  });
});
document.querySelectorAll('dialog.modal').forEach(function (d) {
  d.querySelectorAll('[data-close]').forEach(function (c) { c.addEventListener('click', function () { d.close(); }); });
  d.addEventListener('click', function (ev) { if (ev.target === d) d.close(); });
  d.addEventListener('close', function () { d.querySelectorAll('video,audio').forEach(function (m) { m.pause(); }); });
});
</script>
</body>
</html>
"""


def main():
    ledger = load_ledger()
    stations = "\n".join(station_card(s) for s in ga.STATIONS)
    modals = "\n".join(station_modal(s, i) for i, s in enumerate(ga.STATIONS))
    out = (PAGE.replace("__COST_TABLE__", cost_table(ledger))
           .replace("__STATIONS__", stations)
           .replace("__MODALS__", modals))
    with open(os.path.join(ROOT, "index.html"), "w") as f:
        f.write(out)
    ready = sum(1 for s in ga.STATIONS if all(have(x) for x in (
        f"station_{s['n']:02d}.jpg", f"station_{s['n']:02d}.mp4", f"station_{s['n']:02d}.mp3")))
    print(f"wrote index.html | stations with full media: {ready}/{len(ga.STATIONS)}")


if __name__ == "__main__":
    main()
