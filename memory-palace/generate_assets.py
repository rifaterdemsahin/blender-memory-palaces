"""
generate_assets.py - make the memory palace "come alive" with DeepInfra models.

For each of the 7 palace stations it creates:
  * an image   (black-forest-labs/FLUX-2-pro)      $0.015 per image
  * a video    (Wan-AI/Wan2.2-T2V-A14B, 5 s, 720p) $0.033 per second
  * narration  (TTS model, see TTS_MODEL)          priced per character (tiny)

Every paid call is recorded in a budget ledger. The script refuses to make a
call that would push the running total past HARD_CAP, so the demo cannot
overspend the $2.00 limit.

Secrets: the API key is read ONLY from the environment variable
DEEPINFRA_API_KEY. It is never written to disk or to the repo.

Usage
  python3 generate_assets.py --dry-run     # plan + cost estimate, no network
  python3 generate_assets.py --test        # one image + one short narration (cents)
  python3 generate_assets.py --all         # all 7 stations (image, video, narration)

Outputs (external drive, large files): /Volumes/Samsung/MemoryPalace/assets/
Small copies for the site:             memory-palace/assets/
"""
import argparse
import base64
import datetime as dt
import json
import os
import shutil
import sys
import urllib.error
import urllib.request

API = "https://api.deepinfra.com"
IMAGE_MODEL = "black-forest-labs/FLUX-2-pro"
IMAGE_PRICE = 0.015                     # USD per image (DeepInfra listing)
VIDEO_MODEL = "Wan-AI/Wan2.2-T2V-A14B"
VIDEO_PRICE_PER_SEC = 0.033             # USD per second (DeepInfra listing)
VIDEO_SECONDS = 5
TTS_MODEL = "hexgrad/Kokoro-82M"        # UNVERIFIED on DeepInfra: confirmed by the test call
TTS_PRICE_PER_CHAR = 0.0                # set after the test call (listing price varies by model)
TTS_VOICE = "af_heart"

HARD_CAP = 1.90                         # stop before the $2.00 limit
BUDGET_CAP = 2.00

OUT = "/Volumes/Samsung/MemoryPalace/assets"
SITE_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LEDGER = os.path.join(OUT, "ledger.json")
MANIFEST = os.path.join(SITE_OUT, "manifest.json")

# Extreme, absurd, sensory scenes make each item easier to remember.
# Each station: item keyword, image prompt, video prompt, narration.
STATIONS = [
    {
        "n": 1, "kw": "PLAN", "place": "Entrance Courtyard",
        "image": "A colossal golden compass the size of a house draws a movie frame on a courtyard floor, "
                 "lightning cracks from its needle, a 10-metre gold ring floats above, hyper-saturated, "
                 "cinematic, dramatic low angle",
        "video": "A colossal golden compass draws a film frame on the courtyard floor, lightning cracks from "
                 "its needle, gold ring spins slowly, slow push-in camera",
        "say": "Station one. Entrance Courtyard. PLAN. A giant golden compass is drawing your shot on the floor, "
               "and lightning strikes the needle. Plan the hero, the setting, the move and the look.",
    },
    {
        "n": 2, "kw": "SETTING", "place": "Colonnade",
        "image": "Forty colossal white marble columns rise out of the ground, each one carrying a giant painted "
                 "background shape: a mountain, a city, a tree, a wave, glowing, surreal, high contrast",
        "video": "Forty colossal white marble columns rise from the ground, each carrying a giant painted "
                 "background, slow orbit camera through the colonnade",
        "say": "Station two. Colonnade. SETTING. Forty white columns hold up a mountain, a city, a tree and a wave. "
               "Build three to six background shapes, and fill the whole horizon.",
    },
    {
        "n": 3, "kw": "MOVE", "place": "Rotunda",
        "image": "A red comet-arrow the size of a car blasts around a round marble rotunda, trailing fire, "
                 "a tiny camera on a crane follows it, hyper-saturated red and black, epic",
        "video": "A red comet-arrow the size of a car blasts around a marble rotunda, leaving a trail of fire, "
                 "fast tracking camera",
        "say": "Station three. Rotunda. MOVE. A red arrow the size of a car circles the rotunda. Pick one camera move: "
               "dolly, orbit, chase, crane or truck.",
    },
    {
        "n": 4, "kw": "CLAY", "place": "Sunken Garden",
        "image": "Giant grey clay figures sculpt a huge grey clay ball in a sunken garden, fingerprints in the clay, "
                 "a rolling clay boulder, matte grey, dramatic side light, surreal",
        "video": "Giant grey clay figures sculpt a huge grey clay ball in a sunken garden, the ball rolls slowly, "
                 "static camera",
        "say": "Station four. Sunken Garden. CLAY. Giant grey clay figures sculpt the scene, one block at a time. "
               "Build at real scale, in metres.",
    },
    {
        "n": 5, "kw": "CHECK", "place": "Library Bridge",
        "image": "A giant magenta crystal cube hangs over a stone library bridge, three neon numbers 1, 120 and 240 "
                 "glow in the air, a giant magnifying glass, cinematic, neon magenta",
        "video": "A giant magenta crystal cube hangs over a stone bridge, neon numbers 1, 120 and 240 glow in the "
                 "air, camera slowly pans across the glowing numbers",
        "say": "Station five. Library Bridge. CHECK. A giant magenta crystal checks three frames glowing in the air: "
               "one, one twenty, and two forty. Fix it, then look again.",
    },
    {
        "n": 6, "kw": "PROMPT", "place": "Observatory",
        "image": "A giant blue glass sphere sits on top of a telescope, light beams project words into the night sky "
                 "saying 'locked camera, golden hour', lens flare, cinematic",
        "video": "A giant blue glass sphere on a telescope projects glowing words into the night sky, "
                 "lens flare, slow zoom in",
        "say": "Station six. Observatory. PROMPT. A giant glass sphere projects your Flow prompt into the night sky. "
               "Keep the first line that locks the camera. Two to four sentences.",
    },
    {
        "n": 7, "kw": "RENDER", "place": "Summit Altar",
        "image": "An orange flame cone erupts from a stone altar and shoots a glowing film reel of light into the sky, "
                 "a clip appears as a film strip, epic, warm orange glow",
        "video": "An orange flame erupts from a stone altar and shoots a glowing film reel into the sky, "
                 "camera tilts up to follow the reel",
        "say": "Station seven. Summit Altar. RENDER. An orange flame launches the film into the sky. Save the blend file, "
               "render the ten second clip, and make it real.",
    },
]


# ---------------------------------------------------------------- budget
def load_ledger():
    if os.path.exists(LEDGER):
        with open(LEDGER) as f:
            return json.load(f)
    return {"entries": [], "total": 0.0}


def save_ledger(led):
    os.makedirs(OUT, exist_ok=True)
    with open(LEDGER, "w") as f:
        json.dump(led, f, indent=2)


def charge(led, kind, model, est, detail):
    """Refuse the call if it would push the running total past HARD_CAP."""
    if led["total"] + est > HARD_CAP:
        raise RuntimeError(
            f"budget guard: {kind} would bring total to ${led['total'] + est:.3f} (> ${HARD_CAP:.2f} cap)"
        )
    led["entries"].append({
        "time": dt.datetime.now().isoformat(timespec="seconds"),
        "kind": kind, "model": model, "estimate_usd": round(est, 4), "detail": detail,
    })
    led["total"] = round(led["total"] + est, 4)
    save_ledger(led)


def fix_actual(led, actual):
    """Replace the last estimate with the cost DeepInfra reported, when it reported one."""
    if actual is None:
        return
    last = led["entries"][-1]
    led["total"] = round(led["total"] - last["estimate_usd"] + actual, 4)
    last["actual_usd"] = actual
    save_ledger(led)


# ---------------------------------------------------------------- http
def _key():
    k = os.environ.get("DEEPINFRA_API_KEY", "").strip()
    if not k:
        sys.exit("DEEPINFRA_API_KEY is not set in this shell. Set it, then rerun.")
    return k


def post_json(path, body, timeout=600):
    req = urllib.request.Request(
        API + path, data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} from {path}: {e.read().decode()[:300]}")


def download(url, dest):
    if url.startswith("/"):
        url = API + url
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {_key()}"})
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)
    return dest


# ---------------------------------------------------------------- calls
def make_image(led, station):
    est = IMAGE_PRICE
    charge(led, "image", IMAGE_MODEL, est, f"station {station['n']} {station['kw']}")
    data = post_json("/v1/openai/images/generations", {
        "model": IMAGE_MODEL, "prompt": station["image"], "size": "1024x1024", "n": 1,
    })
    b64 = data["data"][0]["b64_json"]
    dest = os.path.join(OUT, f"station_{station['n']:02d}.png")
    with open(dest, "wb") as f:
        f.write(base64.b64decode(b64))
    fix_actual(led, None)
    return dest


def make_video(led, station):
    est = VIDEO_PRICE_PER_SEC * VIDEO_SECONDS
    charge(led, "video", VIDEO_MODEL, est, f"station {station['n']} {station['kw']} {VIDEO_SECONDS}s")
    data = post_json(f"/v1/inference/{VIDEO_MODEL}", {
        "prompt": station["video"], "seconds": VIDEO_SECONDS, "resolution": "720p", "orientation": "landscape",
    })
    actual = None
    st = data.get("inference_status") or {}
    if isinstance(st.get("cost"), (int, float)) and st.get("cost") > 0:
        actual = float(st["cost"])
    dest = download(data["video_url"], os.path.join(OUT, f"station_{station['n']:02d}.mp4"))
    fix_actual(led, actual)
    return dest


def make_narration(led, station):
    # Priced per character; the charge is an upper bound so the guard stays safe.
    chars = len(station["say"])
    est = max(0.0005, chars * 0.000005)
    charge(led, "tts", TTS_MODEL, est, f"station {station['n']} {chars} chars")
    req = urllib.request.Request(
        API + "/v1/openai/audio/speech", method="POST",
        data=json.dumps({"model": TTS_MODEL, "input": station["say"], "voice": TTS_VOICE,
                         "response_format": "mp3"}).encode(),
        headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        audio = r.read()
    dest = os.path.join(OUT, f"station_{station['n']:02d}.mp3")
    with open(dest, "wb") as f:
        f.write(audio)
    fix_actual(led, None)
    return dest


# ---------------------------------------------------------------- main
def plan(stations):
    img = IMAGE_PRICE * len(stations)
    vid = VIDEO_PRICE_PER_SEC * VIDEO_SECONDS * len(stations)
    tts = sum(max(0.0005, len(s["say"]) * 0.000005) for s in stations)
    total = img + vid + tts
    print(f"Plan for {len(stations)} stations")
    print(f"  images     {IMAGE_MODEL:<28} ${img:.3f}")
    print(f"  videos     {VIDEO_MODEL:<28} ${vid:.3f}  ({VIDEO_SECONDS}s each)")
    print(f"  narration  {TTS_MODEL:<28} ${tts:.4f}  (upper bound)")
    print(f"  TOTAL estimate ${total:.3f}  | hard cap ${HARD_CAP:.2f} | budget ${BUDGET_CAP:.2f}")
    return total


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--test", action="store_true")
    g.add_argument("--all", action="store_true")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SITE_OUT, exist_ok=True)

    if args.dry_run:
        plan(STATIONS)
        return

    stations = STATIONS[:1] if args.test else STATIONS
    led = load_ledger()
    if args.test:
        make_image(led, STATIONS[0])
        make_narration(led, STATIONS[0])
        print(f"TEST done. ledger total ${led['total']:.4f}")
        return

    results = []
    for s in stations:
        rec = {"n": s["n"], "kw": s["kw"], "place": s["place"]}
        rec["image"] = os.path.basename(make_image(led, s))
        rec["video"] = os.path.basename(make_video(led, s))
        rec["audio"] = os.path.basename(make_narration(led, s))
        results.append(rec)
        print("OK station", s["n"], rec, flush=True)
    with open(MANIFEST, "w") as f:
        json.dump({"generated": dt.datetime.now().isoformat(timespec="seconds"),
                   "ledger_total_usd": led["total"], "stations": results}, f, indent=2)
    print(f"ALL done. ledger total ${led['total']:.4f}")


if __name__ == "__main__":
    main()
