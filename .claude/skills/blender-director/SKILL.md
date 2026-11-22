---
name: blender-director
description: Turn a one-line video idea into a 10-second grey "clay" Blender clip with a named camera move (dolly, orbit, chase, crane or truck), ready to restyle into a cinematic shot with Google Flow's free video-to-video. Use when someone gives a shot idea and wants a Blender scene, a camera move, a clay render, or a Flow prompt for it. Needs Blender open with the MCP for Blender add-on running.
---

# Blender Director

You get a one-line idea ("a sports car racing through a desert at sunset"). You build a simple 3D scene in Blender, add one clean camera move, check it, save it and set it to render a 10-second clip. Then you write the Flow prompt.

The scene stays plain grey clay on purpose. Blender's only jobs are the shapes, the layout and the camera path. The video model adds the look later, so time spent on materials is wasted.

## 0. Before you start
- Blender must be open with the MCP for Blender add-on running (N panel > MCP for Blender > Start MCP Server). Call `get_scene_info` once to check the connection.
- The helper lives next to this file: `scripts/director.py`. Load it at the top of every `execute_blender_code` call:
  `exec(open("<this skill's folder>/scripts/director.py").read())`

## 1. Plan the shot (write it out in 4 lines before building)
- **Hero:** the one thing the shot is about (a car, a creature, a building, a product).
- **Setting:** 3 to 6 kinds of background shapes that say where we are (rock pillars, buildings, trees, waves).
- **Move:** pick one from the table. If the idea names a move, use it.
- **Look for Flow:** one line of what it should look like in the end (light, weather, time of day, style).

| Move | Use it when | Feels like |
|---|---|---|
| dolly | a reveal, a hero standing still, a product | pushing in, building tension |
| orbit | showing off one object from all sides | a trailer hero shot |
| chase | anything that moves (cars, animals, runners) | action, speed |
| crane | big places, endings, a city or a landscape | epic, opening or closing shot |
| truck | walking past a scene, a lineup, a street | documentary, sideways travel |

## 2. Build
In one `execute_blender_code` call:
```python
exec(open("<skill>/scripts/director.py").read())
reset_scene()
light_and_sky(sun_elevation=30)          # one sun, soft shadows, flat grey sky
ground()                                  # big ground plane
body = clay("Hero", 0.82); world = clay("Set", 0.68); dark = clay("Dark", 0.45)
# hero from boxes / cylinders / spheres at real scale (metres), e.g. a car is about 4.5 x 1.9 x 1.3
# setting: fill the background out to the horizon, both sides
```
Rules that make Flow's result better:
- **Real scale, in metres.** A door is 2 m, a car 4.5 m, a person 1.8 m. Flow judges how big things are from the shapes.
- **Silhouette first.** The hero must read from its outline alone: a car needs a cabin and 4 wheels, a dragon needs wings and a tail. Blocky is fine; ambiguous isn't.
- **Use 2 or 3 shades of grey** so the hero stands out from the set and the ground.
- **No empty void.** Fill the frame to the horizon. Empty grey space becomes random stuff in the final.
- **No look-alikes.** Two similar objects side by side can swap in the final. Make them different sizes or shapes.
- **Whatever is wrong here gets copied.** A bent leg or a floating box shows up in the final too. Fix it now, not in the prompt.
- Moving things: `move(obj, start, end)` gives a constant speed for the whole 10 s.

## 3. Camera move
```python
camera_move("chase", (car, 0.7), distance=8, height=1.2, lens=32)   # follows the car, swings to its side
camera_move("orbit", (0, 0, 2), distance=12, height=3, amount=120)   # 120 degrees round a point
camera_move("dolly", hero, distance=10, height=1.7)                  # push in
camera_move("crane", (0, 0, 0), distance=25, height=2, amount=15)    # rise 15 m
camera_move("truck", (0, 0, 1.5), distance=9, amount=14)             # slide 14 m sideways
```
One camera move per clip, eased in and out, the hero framed the whole time. Lens 28-35 for wide and action, 50-85 for close and product.

## 4. Check, then fix
Use the `look` tool from the camera at frames 1, 120 and 240 (material view). Check:
- the hero is in frame and not cut off at every one of the 3 frames;
- the background fills the frame (no void, no edge of the ground plane);
- the hero's outline reads in a second;
- nothing floats or clips through the ground.
Fix and look again. Two or three passes is normal.

## 5. Write the Flow prompt (before the render)
Open `flow-prompts.md`, pick the closest template and fill in the look line from step 1. Keep it short: 2 to 4 sentences. Long prompts get ignored. Always keep the first sentence that locks the camera.

After the render, tell the user what to do in Flow (see `README.md`, "In Flow"): upload `shot_clay.mp4`, pick Omni Flash, paste the prompt, test at 360p first (about 10 credits for 10 s), and only make the 720p version when the test looks right (`credit-planner.md`).

## 6. Save and render
```python
save("<project folder>/shot.blend")
set_mp4_output("<project folder>/shot_clay.mp4")
```
Never render the animation through `execute_blender_code`: it freezes Blender for minutes and the connector times out. Render the 10 s clip from a terminal instead (run it yourself if you can run shell commands, otherwise give the user the line):
- Mac: `/Applications/Blender.app/Contents/MacOS/Blender -b shot.blend -a`
- Windows: `"C:\Program Files\Blender Foundation\Blender 4.x\blender.exe" -b shot.blend -a`
- Linux: `blender -b shot.blend -a`
Or in Blender: Render > Render Animation (Ctrl+F12). A 10 s 720p clip needs a few minutes on a laptop.

## Done means
`shot.blend` and `shot_clay.mp4` (10 s, 24 fps, 1280x720), 3 check frames, the shot plan, and a filled-in Flow prompt.
