"""
build_clay_shot.py - the memory palace as a grey CLAY shot, built with the blender-director skill.

Uses the skill's own helper module (.claude/skills/blender-director/scripts/director.py):
reset_scene, light_and_sky, ground, clay, box, camera_move, save, set_mp4_output.

Plan (SKILL.md step 1):
  Hero:    the tallest clay piece, station 7 (RENDER altar), the one that reads from far away.
  Setting: 7 clay plinths in a straight promenade, each with a different silhouette.
  Move:    truck (camera slides sideways past the row, always looking at the centre).
  Look:    grey clay. The Flow prompt is written from flow-prompts.md (see the report page).

Run (headless, the skill's render path):
    blender -b --python memory-palace/clay/build_clay_shot.py
    blender -b /Volumes/Samsung/MemoryPalace/clay/shot.blend -a      # 10 s clip -> shot_clay.mp4
"""
import math
import os

import bpy

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DIRECTOR = os.path.join(REPO, ".claude", "skills", "blender-director", "scripts", "director.py")
OUT = "/Volumes/Samsung/MemoryPalace/clay"
os.makedirs(OUT, exist_ok=True)

exec(open(DIRECTOR).read())  # the skill's helpers, as SKILL.md step 0 says

reset_scene()
light_and_sky(sun_elevation=30)
ground(size=400)
hero = clay("Hero", 0.82)
setting = clay("Set", 0.68)
dark = clay("Dark", 0.45)

SPACING = 6.0
STATIONS = 7


def cyl(name, x, y, z, r, h, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=(x, y, z + h / 2))
    o = bpy.context.active_object
    o.name, o.rotation_euler = name, rot
    return give(o, mat)


def sph(name, x, y, z, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(x, y, z + r))
    o = bpy.context.active_object
    o.name = name
    return give(o, mat)


def cone(name, x, y, z, r, h, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=0, depth=h, location=(x, y, z + h / 2))
    o = bpy.context.active_object
    o.name, o.rotation_euler = name, rot
    return give(o, mat)


for i in range(STATIONS):
    x = i * SPACING
    base = 0.9
    box(f"Plinth_{i + 1:02d}", (1.6, 1.6, base), (x, 0, 0), setting)

    if i == 0:      # 01 PLAN: tall thin pillar
        cyl("PLAN_Pillar", x, 0, base, 0.18, 2.4, dark)
    elif i == 1:    # 02 SETTING: four columns and a lintel
        for dx, dy in [(-0.55, -0.55), (0.55, -0.55), (-0.55, 0.55), (0.55, 0.55)]:
            cyl("SET_Column", x + dx, dy, base, 0.14, 2.0, setting)
        box("SET_Lintel", (1.8, 1.8, 0.25), (x, 0, base + 2.0), setting)
    elif i == 2:    # 03 MOVE: a sideways cone, the arrow of motion
        cone("MOVE_Arrow", x, 0, base + 1.0, 0.45, 1.8, hero, rot=(0, math.radians(90), 0))
    elif i == 3:    # 04 CLAY: a big ball on a block
        box("CLAY_Block", (1.2, 1.2, 1.0), (x, 0, base), dark)
        sph("CLAY_Ball", x, 0, base + 1.0, 0.6, setting)
    elif i == 4:    # 05 CHECK: a tilted cube on a thin stem
        cyl("CHECK_Stem", x, 0, base, 0.05, 1.8, dark)
        bpy.ops.mesh.primitive_cube_add(size=0.9, location=(x, 0, base + 2.1))
        o = bpy.context.active_object
        o.name, o.rotation_euler = "CHECK_Cube", (math.radians(30), 0, math.radians(45))
        give(o, dark)
    elif i == 5:    # 06 PROMPT: a sphere on a stand
        cyl("PROMPT_Stand", x, 0, base, 0.12, 0.8, dark)
        sph("PROMPT_Sphere", x, 0, base + 0.8, 0.5, setting)
    else:           # 07 RENDER: the tallest piece = the hero of the row
        cone("RENDER_Altar", x, 0, base, 0.8, 2.8, hero)

# The skill's one camera move: truck sideways past the row, looking at its centre.
centre = (SPACING * (STATIONS - 1) / 2, 0, 1.5)
camera_move("truck", centre, distance=12, height=1.6, lens=35, amount=28)

set_mp4_output(os.path.join(OUT, "shot_clay.mp4"))   # set the output BEFORE saving, so the .blend keeps it
save(os.path.join(OUT, "shot.blend"))
print("CLAY_SCENE_SAVED", report(), flush=True)
