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
     "Erdem had one talk to give. Seven ideas. One chance. And a memory that kept slipping through the cracks. "
     "So Erdem did the only sensible thing. Erdem built a palace inside the mind, and went in."),
    ("01", "PLAN",
     "Station one. Entrance Courtyard. A golden compass, the size of a house, slams down onto the stone and "
     "lightning rips from its needle. Every great film starts with a single question: who is the hero, "
     "where does it happen, how does the camera move, and what does it feel like."),
    ("02", "SETTING",
     "Station two. Colonnade. Forty white columns burst out of the ground. Each one holds up a whole world: "
     "a mountain, a city, a tree, a wave. Plain grey shapes, at real size. Build the world first, "
     "and the story has somewhere to stand."),
    ("03", "MOVE",
     "Station three. Rotunda. A red arrow, as long as a car, screams around the marble ring and leaves a trail "
     "of fire. Now the camera wakes up. One move, and only one. A dolly, an orbit, a chase, a crane, or a truck. "
     "Choose it like your life depends on it."),
    ("04", "CLAY",
     "Station four. Sunken Garden. Giant grey figures wrestle a boulder of clay into shape, fingerprints and all. "
     "No colour. No tricks. Just form. If the shape cannot tell the story alone, "
     "no paint in the world will save it."),
    ("05", "CHECK",
     "Station five. Library Bridge. Three neon numbers hang in the air like judges. Frame one. Frame one hundred "
     "and twenty. Frame two hundred and forty. Erdem leans in, spots the flaw, fixes it, "
     "and looks again. Nothing gets past these numbers."),
    ("06", "PROMPT",
     "Station six. Observatory. A glass sphere, bigger than a bus, throws your words into the night sky. "
     "Lock the camera first. Then paint the look, in two to four sentences. Short. Sharp. Unforgettable."),
    ("07", "RENDER",
     "Station seven. Summit Altar. The flame erupts. The film launches into the sky, a reel of light, "
     "ten seconds long, and it lands. Erdem walks back down the stairs, all seven stations in order, "
     "and never once looks at the notes."),
    ("close", "Closing",
     "And now it is your turn, watcher. Pick your own seven things. Build your own palace. "
     "Walk it until the route is burned into your bones. The memory is yours to keep."),
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
    """True duration: decode the whole file. MP3 headers can overstate length, so they are not used."""
    import re
    out = subprocess.run(["ffmpeg", "-i", path, "-f", "null", "-"], capture_output=True, text=True).stderr
    h, m, s = re.findall(r"time=(\d+):(\d+):(\d+\.\d+)", out)[-1]
    return int(h) * 3600 + int(m) * 60 + float(s)


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
