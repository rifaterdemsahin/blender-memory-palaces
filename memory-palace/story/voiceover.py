"""
voiceover.py - the memory-palace story, read aloud with DeepInfra TTS (Kokoro-82M).

One chapter per station, plus an opening and a closing that speak to Erdem directly
(pronouns not stated, so they/them). Writes one MP3 per chapter and a joined voiceover.mp3.
Every paid call goes into the same budget ledger as generate_assets.py.

Key: read only from the environment variable DEEPINFRA_API_KEY (never stored).

Run:  DEEPINFRA_API_KEY=... python3 memory-palace/story/voiceover.py
"""
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import generate_assets as ga  # noqa: E402  (shared ledger, model and key handling)

OUT = os.path.join(ga.OUT, "story")          # large working files on the external drive
SITE = os.path.join(HERE)                    # small copies for the repo / site

CHAPTERS = [
    ("open", "Opening",
     "Once upon a shot, Erdem had one important talk to give, and seven things to remember. "
     "So Erdem built a palace in the mind, and walked it, one room at a time."),
    ("01", "PLAN",
     "Station one. Entrance Courtyard. A giant golden compass draws the shot on the floor. "
     "Erdem starts with the question every director asks: who is the hero, what is the setting, "
     "what is the move, and what is the look."),
    ("02", "SETTING",
     "Station two. Colonnade. Forty white columns hold up a mountain, a city, a tree and a wave. "
     "Erdem builds the set in plain grey shapes, at real size, so nothing surprises them later."),
    ("03", "MOVE",
     "Station three. Rotunda. A red arrow circles the marble ring. Erdem chooses one camera move "
     "with care: a dolly, an orbit, a chase, a crane or a truck."),
    ("04", "CLAY",
     "Station four. Sunken Garden. Giant clay figures sculpt the world in grey. No colour yet. "
     "The shape has to carry the story alone."),
    ("05", "CHECK",
     "Station five. Library Bridge. Three numbers glow in the air: frame one, frame one hundred and twenty, "
     "frame two hundred and forty. Erdem looks through the camera, fixes what is wrong, and looks again."),
    ("06", "PROMPT",
     "Station six. Observatory. A glass sphere projects words into the night sky. Lock the camera first, "
     "then describe the look, in two to four sentences."),
    ("07", "RENDER",
     "Station seven. Summit Altar. A flame launches the film into the sky. Ten seconds, rendered and ready. "
     "Erdem remembers all seven, in order, and walks back down the stairs knowing the way."),
    ("close", "Closing",
     "And you, watching this, Erdem: pick your own seven things, and build your own palace. "
     "The route is yours, and so is the memory."),
]


def speak(text, dest):
    body = json.dumps({"model": ga.TTS_MODEL, "input": text, "voice": ga.TTS_VOICE,
                       "response_format": "mp3"}).encode()
    req = urllib.request.Request(
        ga.API + "/v1/openai/audio/speech", data=body, method="POST",
        headers={"Authorization": f"Bearer {ga._key()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SITE, exist_ok=True)
    led = ga.load_ledger()
    chars = sum(len(t) for _, _, t in CHAPTERS)
    est_total = max(0.001, chars * 0.000005)
    if led["total"] + est_total > ga.HARD_CAP:
        sys.exit(f"budget guard: narration would exceed ${ga.HARD_CAP:.2f}")

    manifest = []
    for key, title, text in CHAPTERS:
        dest = os.path.join(OUT, f"voice_{key}.mp3")
        ga.charge(led, "tts", ga.TTS_MODEL, max(0.0005, len(text) * 0.000005), f"story {key} {len(text)} chars")
        speak(text, dest)
        ga.fix_actual(led, None)
        d = duration(dest)
        manifest.append({"key": key, "title": title, "text": text, "seconds": round(d, 2),
                         "file": f"voice_{key}.mp3"})
        print(f"OK {key} {title} {d:.2f}s", flush=True)

    # join all chapters into one voiceover track
    listfile = os.path.join(OUT, "voice_list.txt")
    with open(listfile, "w") as f:
        for m in manifest:
            f.write(f"file '{os.path.join(OUT, m['file'])}'\n")
    joined = os.path.join(OUT, "voiceover.mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
                    "-c", "copy", joined], check=True)
    total = duration(joined)

    # small copies for the repo (site and HyperFrames project)
    import shutil
    for m in manifest:
        shutil.copy(os.path.join(OUT, m["file"]), os.path.join(SITE, m["file"]))
    shutil.copy(joined, os.path.join(SITE, "voiceover.mp3"))
    shutil.copy(ga.LEDGER, os.path.join(SITE, "ledger.json"))
    with open(os.path.join(SITE, "story.json"), "w") as f:
        json.dump({"voiceover_seconds": round(total, 2), "chapters": manifest,
                   "ledger_total_usd": led["total"]}, f, indent=2)
    print(f"VOICEOVER done: {total:.2f}s total, ledger ${led['total']:.4f}", flush=True)


if __name__ == "__main__":
    main()
