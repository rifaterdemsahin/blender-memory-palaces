# Memory Palace: build log and documentation

A 3D Method-of-Loci memory palace with 7 stations, built procedurally in Blender 5.3 by `build_palace.py`.

## 1. What was built

| Item | Value |
|---|---|
| Blender | 5.3.0 (hash 02f0899d78e3, built 2026-11-10), run headless |
| Blender install used | `/Volumes/Samsung/Apps/Blender.app`, reached through `/opt/homebrew/bin/blender` (a Homebrew wrapper that execs the app on the external drive) |
| Render engine | `BLENDER_EEVEE` (the 5.x identifier, looked up at runtime), 32 samples |
| Still resolution | 1280 x 720 |
| Walkthrough | frames 1 to 240 at 24 fps (10 s), 240 keyed camera frames |
| Scene file | `memory_palace.blend` (about 204 KB) |

### The 7 items (placeholders replaced)

The request template had placeholder items (`[Item 1 — e.g., ...]`). I used the 7 steps of the `blender-director` skill that is also in this repo, so the palace is useful and memorable. To use your own facts, edit the `ITEMS` list at the top of `build_palace.py` and rebuild.

| # | Keyword | Station | Meaning | Sculpture | Light colour |
|---|---|---|---|---|---|
| 1 | PLAN | Entrance Courtyard | Plan the shot: hero, setting, move, look | gold ring on a stem | warm gold |
| 2 | SETTING | Colonnade | Build the set: 3 to 6 background shapes | four white pillars and a lintel | cool white |
| 3 | MOVE | Rotunda | Pick one camera move | red arrow pointing sideways | red |
| 4 | CLAY | Sunken Garden | Build in grey clay at real scale | grey clay blocks and a ball | grey-green |
| 5 | CHECK | Library Bridge | Check frames 1, 120 and 240 | magenta tilted cube on a pillar | violet |
| 6 | PROMPT | Observatory | Write the Flow prompt | blue glass sphere on a stand | blue |
| 7 | RENDER | Summit Altar | Save the .blend and render the clip | glowing orange cone flame | orange |

Station positions (metres, ground plane): 1 (0,0), 2 (0,12), 3 (7,22), 4 (14,28), 5 (21,22), 6 (25,12), 7 (22,0). Each station has a 1.6 m stone pedestal, a point light 3 m in front of it, and two floating labels: `NN KEYWORD` and the station name.

### Cameras

| Name | Position | Lens | Purpose |
|---|---|---|---|
| `Cam_00_Overview` | (12, -30, 40) | 35 mm | bird's-eye view of the whole palace |
| `Cam_01` to `Cam_07` | 6 m in front of each station, at eye height 1.6 m | 28 mm | eye-level view facing that station's sculpture |
| `Cam_Walkthrough` | follows the Catmull-Rom spline through the station cameras | 28 mm | keyed on every frame, 1 to 240 |

`Walkthrough_Path` is a Bezier curve (auto handles) on the floor at z = 0.05 m, through the same 7 points. It is visible in the overview and does not sit in any camera's view.

## 2. Steps and results (in order)

1. **Environment check.** Blender 5.3.0 runs with `blender --version`. The external drive `/Volumes/Samsung` is mounted, with about 464 GB free. The internal disk was 78% full, so every large file was written to the external drive.
2. **Folder.** Created `/Volumes/Samsung/MemoryPalace/` and `renders/`, as the storage rule asks.
3. **Script.** Wrote `build_palace.py`. It starts from an empty factory scene, builds the stations, cameras and path, saves the `.blend`, then renders each camera to PNG.
4. **First run failed.** `TypeError: bad operand type for unary -: 'tuple'`. The Catmull-Rom path code received plain tuples instead of `Vector`s. Fix: store station points as `Vector`.
5. **Second run succeeded.** Saved `memory_palace.blend` and rendered 8 PNGs. Exit code 0.
6. **Review of the renders (visual).**
   - Overview: good, but the palace was small in frame. Moved the camera closer, from (12,-42,52) to (12,-30,40).
   - Path: the path tube was drawn at eye height and passed exactly through the station camera positions, so a white tube filled the right side of `Cam_03`. Fix: draw the path on the floor (z = 0.05).
   - MOVE arrow: pointed straight at the station camera, so it showed as a flat circle. Fix: turned it to point sideways (+X).
7. **Third run succeeded.** 8 PNGs, exit code 0. Renders reviewed again (see section 4 for what remains).
8. **Verification of the saved scene (headless).** Checked:
   - render engine `BLENDER_EEVEE`, frames 1 to 240, 1280 x 720;
   - 9 cameras with the expected positions and lenses;
   - `Cam_Walkthrough` has 240 keyframes;
   - `Walkthrough_Path` exists;
   - 14 text labels (7 `NN KEYWORD` and 7 station names).
9. **Cleanup.** Removed the stale `memory_palace.blend1` backup and the temporary verification script.
10. **Copied the deliverables into the repo** (`memory-palace/`) and created `index.html` at the repo root for GitHub Pages. Only small files are copied (about 7.6 MB in total). The large working copies stay on the external drive.

## 3. Where things are

| What | Location |
|---|---|
| Working build (external drive) | `/Volumes/Samsung/MemoryPalace/` |
| Build script | `/Volumes/Samsung/MemoryPalace/build_palace.py` (copy in `memory-palace/build_palace.py`) |
| Scene | `/Volumes/Samsung/MemoryPalace/memory_palace.blend` (copy in `memory-palace/memory_palace.blend`) |
| Renders | `/Volumes/Samsung/MemoryPalace/renders/` (copy in `memory-palace/renders/`) |
| Run log | `/Volumes/Samsung/MemoryPalace/build.log` (copy in `memory-palace/build.log`) |
| Web page | `index.html` at the repo root |

## 4. Known issues (not fixed)

- In `Cam_07` the RENDER flame covers the "05 CHECK" label, so only part of the label shows.
- In `Cam_05` the magenta cube covers part of the "Library Bridge" station name.
- The station cameras face the sculpture from 6 m, so the sculpture is small in frame. This is by design for a walkthrough view, but a closer lens would make details clearer.
- Lighting is point-light only and tuned by eye. Fine for a memory aid, but not photoreal.

## 5. How to reproduce

```sh
blender -b --python /Volumes/Samsung/MemoryPalace/build_palace.py
```

This rebuilds the scene, saves `memory_palace.blend` and rewrites all 8 renders. It takes a few minutes on this machine.

To open the scene in the Blender UI:

```sh
blender /Volumes/Samsung/MemoryPalace/memory_palace.blend
```

Then scrub the timeline (frames 1 to 240) to walk the palace.

## 6. Publishing

- The repo root `index.html` is the GitHub Pages entry point. It links the renders, the `.blend`, the build script and this log.
- The README links to `index.html`.
- See the commit history for the exact push.
