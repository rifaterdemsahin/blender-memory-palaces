"""
build_palace.py - procedural 3D Memory Palace (Method of Loci) for Blender 5.3.

Run headless from a terminal:
    blender -b --python /Volumes/Samsung/MemoryPalace/build_palace.py

What it does
  1. Starts from an empty factory scene (no default cube).
  2. Builds a 7-station promenade. Each station = stone pedestal + one
     high-contrast mnemonic sculpture + its own coloured point light +
     floating markers "NN KEYWORD" and the station name.
  3. Adds Cam_00_Overview (bird's-eye), Cam_01..Cam_07 (eye level, 6 m in
     front of each station, facing its sculpture) and Cam_Walkthrough, which
     is keyframed along the Walkthrough_Path curve over frames 1-240.
  4. Saves memory_palace.blend and renders every named camera to PNG.

Blender 5.x API notes: Principled BSDF socket names are the 4.x+ ones
("Base Color", "Emission Color", "Emission Strength", "Transmission Weight").
The EEVEE engine id is looked up at runtime so the script works whichever
EEVEE identifier the build exposes.
"""
import bisect
import math
import os

import bpy
from mathutils import Vector

# ---------------------------------------------------------------- settings
OUT = "/Volumes/Samsung/MemoryPalace"
RENDER_DIR = os.path.join(OUT, "renders")
BLEND_PATH = os.path.join(OUT, "memory_palace.blend")
RES_X, RES_Y = 1280, 720
SAMPLES = 32          # EEVEE samples for the still renders
FRAMES = 240          # walkthrough length (10 s at 24 fps)
EYE = 1.6             # eye height in metres
WALK_H = 2.4          # walkthrough camera height (raised so the labels stay in frame)
STATION_DIST = 6.0    # how far in front of a station the station camera stands

# The 7 items to memorise, in order. Station i = ITEMS[i].
# (keyword, station name, what the item means, station position on the ground)
ITEMS = [
    ("PLAN",    "Entrance Courtyard", "Plan the shot: hero, setting, move, look", (0, 0)),
    ("SETTING", "Colonnade",          "Build the set: 3-6 background shapes",    (0, 12)),
    ("MOVE",    "Rotunda",            "Pick one camera move",                    (7, 22)),
    ("CLAY",    "Sunken Garden",      "Build in grey clay at real scale",        (14, 28)),
    ("CHECK",   "Library Bridge",     "Check frames 1, 120 and 240",             (21, 22)),
    ("PROMPT",  "Observatory",        "Write the Flow prompt",                   (25, 12)),
    ("RENDER",  "Summit Altar",       "Save the .blend and render the clip",     (22, 0)),
]

# Each station gets its own light colour so the stations are easy to tell apart.
STATION_LIGHT = [
    (1.00, 0.80, 0.40),   # 1 gold
    (0.75, 0.90, 1.00),   # 2 cool white
    (1.00, 0.15, 0.10),   # 3 red
    (0.55, 0.85, 0.55),   # 4 grey-green
    (0.70, 0.35, 1.00),   # 5 violet
    (0.30, 0.65, 1.00),   # 6 blue
    (1.00, 0.45, 0.10),   # 7 orange
]


# ---------------------------------------------------------------- helpers
def new_mat(name, rgb, metallic=0.0, rough=0.5, emit=None, emit_power=0.0, glass=0.0):
    """Principled BSDF material with the options each sculpture needs."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1.0)
        b.inputs["Emission Strength"].default_value = emit_power
    if glass:
        b.inputs["Transmission Weight"].default_value = glass
        b.inputs["IOR"].default_value = 1.45
    return m


def put(kind, name, loc, scale=(1, 1, 1), rot=(0, 0, 0), mat=None, **kw):
    """Add a primitive at loc (its centre), set scale/rotation and material."""
    if kind == "cube":
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    elif kind == "cyl":
        bpy.ops.mesh.primitive_cylinder_add(radius=kw.get("r", 0.5), depth=kw.get("d", 1.0), location=loc)
    elif kind == "cone":
        bpy.ops.mesh.primitive_cone_add(radius1=kw.get("r", 0.5), radius2=0.0, depth=kw.get("d", 1.0), location=loc)
    elif kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=kw.get("r", 0.5), location=loc)
    elif kind == "torus":
        bpy.ops.mesh.primitive_torus_add(major_radius=kw.get("R", 0.9), minor_radius=kw.get("r", 0.12), location=loc)
    else:
        raise ValueError(kind)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.rotation_euler = rot
    if mat is not None:
        o.data.materials.append(mat)
    return o


def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def aim(ob, target):
    """Point a camera (or any -Z-forward object) at a world-space target."""
    d = Vector(target) - Vector(ob.location)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def make_camera(name, loc, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start, cd.clip_end = 0.1, 500
    ob = link(bpy.data.objects.new(name, cd))
    ob.location = loc
    return ob


def label(text, loc, mat, size):
    """Flat text that stands up and faces the -Y side (where the cameras are)."""
    cd = bpy.data.curves.new(name=f"Txt_{text}", type="FONT")
    cd.body = text
    cd.size = size
    cd.align_x = "CENTER"
    cd.extrude = 0.02
    ob = link(bpy.data.objects.new(f"Label_{text}", cd))
    ob.location = loc
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.data.materials.append(mat)
    return ob


def catmull(p0, p1, p2, p3, t):
    """Uniform Catmull-Rom point between p1 and p2."""
    t2, t3 = t * t, t * t * t
    return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def sample_path(pts, per_seg=80):
    ext = [pts[0]] + pts + [pts[-1]]
    samples = []
    for i in range(len(pts) - 1):
        for k in range(per_seg):
            samples.append(catmull(ext[i], ext[i + 1], ext[i + 2], ext[i + 3], k / per_seg))
    samples.append(pts[-1])
    cum = [0.0]
    for a, b in zip(samples, samples[1:]):
        cum.append(cum[-1] + (b - a).length)
    return samples, cum


def point_at(samples, cum, s):
    i = bisect.bisect_right(cum, s) - 1
    i = max(0, min(i, len(samples) - 2))
    seg = cum[i + 1] - cum[i]
    f = 0.0 if seg == 0 else (s - cum[i]) / seg
    return samples[i].lerp(samples[i + 1], f)


# ---------------------------------------------------------------- sculptures
# Each takes (x, y, z0, materials) where z0 is the top of the pedestal and
# returns nothing. Sculptures stay under ~3.3 m so the markers above them read.
def sculpt_plan(x, y, z0, M):            # 1 gold ring = a circled plan
    put("cyl", "PLAN_Stem", (x, y, z0 + 0.6), d=1.2, r=0.05, mat=M["stone"])
    put("torus", "PLAN_Ring", (x, y, z0 + 1.6), rot=(math.radians(90), 0, 0), R=0.85, r=0.12, mat=M["gold"])
    put("sphere", "PLAN_Core", (x, y, z0 + 1.6), r=0.22, mat=M["gold"])


def sculpt_setting(x, y, z0, M):         # 2 colonnade = a set built from columns
    for dx, dy in [(-0.6, -0.6), (0.6, -0.6), (-0.6, 0.6), (0.6, 0.6)]:
        put("cyl", "SET_Pillar", (x + dx, y + dy, z0 + 1.0), d=2.0, r=0.14, mat=M["white"])
    put("cube", "SET_Lintel", (x, y, z0 + 2.1), scale=(1.9, 1.9, 0.25), mat=M["white"])


def sculpt_move(x, y, z0, M):            # 3 red arrow = a sideways camera move (+X), visible from the front
    put("cyl", "MOVE_Shaft", (x, y, z0 + 1.2), rot=(0, math.radians(90), 0), d=1.4, r=0.12, mat=M["red"])
    put("cone", "MOVE_Head", (x + 1.2, y, z0 + 1.2), rot=(0, math.radians(90), 0), d=0.9, r=0.4, mat=M["red"])


def sculpt_clay(x, y, z0, M):            # 4 grey clay blocks = the clay build stage
    put("cube", "CLAY_Base", (x, y, z0 + 0.35), scale=(1.2, 1.0, 0.7), mat=M["clay"])
    put("sphere", "CLAY_Ball", (x + 0.1, y, z0 + 1.0), r=0.35, mat=M["clay"])
    put("cube", "CLAY_Block", (x - 0.5, y + 0.3, z0 + 0.2), scale=(0.5, 0.5, 0.4), mat=M["clay"])


def sculpt_check(x, y, z0, M):           # 5 magenta tilted cube on a thin pillar = check it
    put("cyl", "CHECK_Pillar", (x, y, z0 + 0.9), d=1.8, r=0.05, mat=M["stone"])
    put("cube", "CHECK_Cube", (x, y, z0 + 2.1), scale=(0.9, 0.9, 0.9),
        rot=(math.radians(30), 0, math.radians(45)), mat=M["magenta"])


def sculpt_prompt(x, y, z0, M):          # 6 glass sphere on a stand = the prompt lens
    put("cyl", "PROMPT_Stand", (x, y, z0 + 0.4), d=0.8, r=0.12, mat=M["stone"])
    put("sphere", "PROMPT_Glass", (x, y, z0 + 1.5), r=0.6, mat=M["glass"])


def sculpt_render(x, y, z0, M):          # 7 glowing flame = the final render
    put("cone", "RENDER_Flame", (x, y, z0 + 1.2), d=2.4, r=0.7, mat=M["flame"])
    put("sphere", "RENDER_Core", (x, y, z0 + 0.5), r=0.3, mat=M["core"])


SCULPTORS = {
    "PLAN": sculpt_plan, "SETTING": sculpt_setting, "MOVE": sculpt_move,
    "CLAY": sculpt_clay, "CHECK": sculpt_check, "PROMPT": sculpt_prompt,
    "RENDER": sculpt_render,
}


# ---------------------------------------------------------------- build
def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    os.makedirs(RENDER_DIR, exist_ok=True)

    # render settings (Blender 5.x engine id is looked up, not hard-coded)
    engines = bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys()
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x, scene.render.resolution_y = RES_X, RES_Y
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.frame_start, scene.frame_end = 1, FRAMES
    try:
        scene.eevee.taa_render_samples = SAMPLES
    except AttributeError:
        pass

    # dark world so the lit sculptures pop
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.012, 0.014, 0.022, 1.0)
        bg.inputs["Strength"].default_value = 1.0

    # shared materials
    M = {
        "stone": new_mat("Stone", (0.22, 0.21, 0.20), rough=0.8),
        "floor": new_mat("Floor", (0.05, 0.05, 0.06), rough=0.9),
        "white": new_mat("StoneWhite", (0.85, 0.85, 0.82), rough=0.7),
        "gold": new_mat("Gold", (1.0, 0.76, 0.34), metallic=1.0, rough=0.22),
        "red": new_mat("RedGlossy", (0.8, 0.04, 0.03), rough=0.3),
        "clay": new_mat("GreyClay", (0.55, 0.55, 0.55), rough=0.95),
        "magenta": new_mat("MagentaMetal", (0.9, 0.1, 0.7), metallic=0.9, rough=0.25),
        "glass": new_mat("BlueGlass", (0.5, 0.75, 1.0), rough=0.05, glass=1.0),
        "flame": new_mat("Flame", (1.0, 0.4, 0.05), rough=0.5, emit=(1.0, 0.45, 0.1), emit_power=6.0),
        "core": new_mat("Core", (1, 1, 1), rough=0.5, emit=(1.0, 0.95, 0.8), emit_power=12.0),
        "path": new_mat("PathGlow", (0.3, 0.9, 1.0), rough=0.5, emit=(0.3, 0.9, 1.0), emit_power=4.0),
    }
    text_mat = {}
    for i, (kw, *_rest) in enumerate(ITEMS):
        c = STATION_LIGHT[i]
        text_mat[kw] = new_mat(f"Text_{kw}", c, rough=0.5, emit=c, emit_power=5.0)

    # ground
    bpy.ops.mesh.primitive_plane_add(size=120, location=(12, 14, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor.data.materials.append(M["floor"])

    # stations
    station_pts = []
    for i, (kw, name, desc, (x, y)) in enumerate(ITEMS, start=1):
        ped_h = 0.9
        put("cube", f"Pedestal_{i:02d}", (x, y, ped_h / 2), scale=(1.6, 1.6, ped_h), mat=M["stone"])
        SCULPTORS[kw](x, y, ped_h, M)

        # coloured light for this station (in front, above, so it lights the sculpture)
        ld = bpy.data.lights.new(f"Light_{i:02d}", "POINT")
        ld.color = STATION_LIGHT[i - 1]
        ld.energy = 700
        ld.shadow_soft_size = 1.0
        lob = link(bpy.data.objects.new(ld.name, ld))
        lob.location = (x, y - 3.0, 3.5)

        # markers: "NN KEYWORD" and the station name, both facing the cameras
        label(f"{i:02d} {kw}", (x, y, 4.1), text_mat[kw], 0.6)
        label(name, (x, y, 3.55), text_mat[kw], 0.38)

        station_pts.append(Vector((x, y - STATION_DIST, EYE)))

    # walkthrough curve (visible path through the eye-level stations)
    cd = bpy.data.curves.new("Walkthrough_Path", "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = 0.04
    spline = cd.splines.new("BEZIER")
    spline.bezier_points.add(len(station_pts) - 1)
    for bp, p in zip(spline.bezier_points, station_pts):
        bp.co = (p.x, p.y, 0.05)   # drawn on the floor so it never sits in a camera's view
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    path_ob = link(bpy.data.objects.new("Walkthrough_Path", cd))
    path_ob.data.materials.append(M["path"])

    # overview camera
    ov = make_camera("Cam_00_Overview", (12, -30, 40), lens=35)
    aim(ov, (12, 12, 0))

    # eye-level station cameras, STATION_DIST in front of each station
    station_cams = []
    for i, (kw, name, desc, (x, y)) in enumerate(ITEMS, start=1):
        cam = make_camera(f"Cam_{i:02d}", (x, y - STATION_DIST, EYE), lens=28)
        aim(cam, (x, y, 2.4))
        station_cams.append(cam)

    # walkthrough camera keyed along the Catmull-Rom path, one key per frame
    wt = make_camera("Cam_Walkthrough", station_pts[0], lens=24)   # wider than 28 mm so labels stay inside the frame

    # Fix for the mirrored-label defect: every label turns to face the walkthrough camera,
    # so text reads correctly from any side the walk approaches it from.
    for ob in bpy.data.objects:
        if ob.type == "FONT":
            c = ob.constraints.new("TRACK_TO")
            c.target = wt
            c.track_axis = "TRACK_Z"   # the text's front (+Z) points at the camera
            c.up_axis = "UP_Y"
    samples, cum = sample_path(station_pts)
    total = cum[-1]
    for f in range(1, FRAMES + 1):
        s = (f - 1) / (FRAMES - 1) * total
        pos = point_at(samples, cum, s)
        look = point_at(samples, cum, min(total, s + 4.0))
        pos.z = WALK_H      # raised so the labels above each station stay inside the frame
        look.z = WALK_H
        wt.location = pos
        aim(wt, look)
        wt.keyframe_insert("location", frame=f)
        wt.keyframe_insert("rotation_euler", frame=f)

    scene.camera = ov
    return scene, ov, station_cams, wt


def render_all(scene, cams):
    for cam in cams:
        scene.camera = cam
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = os.path.join(RENDER_DIR, f"{cam.name}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", scene.render.filepath, flush=True)


if __name__ == "__main__":
    scene, ov, station_cams, wt = build()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("SAVED", BLEND_PATH, flush=True)
    render_all(scene, [ov] + station_cams)
    print("DONE", flush=True)
