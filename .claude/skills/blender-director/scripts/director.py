"""
Blender Director helper.
Run inside Blender (the AI runs it through the Blender connector):
    exec(open("/path/to/blender-director/scripts/director.py").read())
Then call the functions below. Works on Blender 4.2 and newer (tested on 5.2).

Everything is plain clay on purpose: the video model adds the look later.
Blender's job is only shapes, layout and the camera path.
"""
import bpy, math
from mathutils import Vector

FPS = 24
SECONDS = 10
LAST = FPS * SECONDS  # frame 240


# ---------- scene ----------
def reset_scene():
    """Empty the scene and set 10 s at 24 fps, 1280x720, Eevee."""
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.curves):
        for item in list(block):
            if item.users == 0:
                block.remove(item)
    s = bpy.context.scene
    s.render.fps = FPS
    s.frame_start, s.frame_end = 1, LAST
    s.render.engine = "BLENDER_EEVEE"
    s.render.resolution_x, s.render.resolution_y = 1280, 720
    s.render.resolution_percentage = 100
    try:
        s.view_settings.view_transform = "Standard"
        s.view_settings.look = "None"
    except Exception:
        pass
    try:
        s.eevee.taa_render_samples = 64
        s.eevee.use_shadows = True
    except Exception:
        pass
    return s


def clay(name="Clay", shade=0.72, rough=0.85):
    """A plain grey clay material. shade 0 = black, 1 = white. Use 2 or 3 shades for separation."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = (shade, shade, shade, 1)
        b.inputs["Roughness"].default_value = rough
    m.diffuse_color = (shade, shade, shade, 1)
    return m


def give(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def light_and_sky(sun_elevation=35, sun_azimuth=40, sun_strength=3.5, sky=0.55, soft=6):
    """One sun with soft shadows and a flat light-grey sky."""
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (sky, sky, sky, 1)
        bg.inputs["Strength"].default_value = 1.0
    ld = bpy.data.lights.new("Sun", "SUN")
    ld.energy = sun_strength
    ld.angle = math.radians(soft)
    sun = bpy.data.objects.new("Sun", ld)
    bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(90 - sun_elevation), 0, math.radians(sun_azimuth))
    return sun


def box(name, size, loc, mat, rot_z=0.0):
    """size = (x, y, z) in metres, loc = centre of the base on the ground."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(loc[0], loc[1], loc[2] + size[2] / 2))
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.rotation_euler[2] = math.radians(rot_z)
    bpy.ops.object.transform_apply(scale=True)
    return give(o, mat)


def ground(size=2000, mat=None):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    g = bpy.context.active_object
    g.name = "Ground"
    return give(g, mat or clay("Ground", 0.62))


def move(obj, start, end, f0=1, f1=LAST):
    """Move an object in a straight line at constant speed (no ease), e.g. a car driving."""
    obj.location = start
    obj.keyframe_insert("location", frame=f0)
    obj.location = end
    obj.keyframe_insert("location", frame=f1)
    _linear(obj)


# ---------- camera moves ----------
def _ease(t):
    return t * t * (3 - 2 * t)  # smooth start and stop


def _linear(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    # Blender 4.4+ layered actions keep fcurves in channelbags; older ones on the action
    curves = []
    if hasattr(ad.action, "fcurves"):
        try:
            curves = list(ad.action.fcurves)
        except Exception:
            curves = []
    if not curves and hasattr(ad.action, "layers"):
        for layer in ad.action.layers:
            for strip in layer.strips:
                for bag in getattr(strip, "channelbags", []):
                    curves += list(bag.fcurves)
    for fc in curves:
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"


def _camera(lens=35):
    cd = bpy.data.cameras.new("DirectorCam")
    cd.lens = lens
    cd.clip_start, cd.clip_end = 0.1, 5000
    cam = bpy.data.objects.new("DirectorCam", cd)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def _aim(cam, target):
    d = Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def _target_at(target, f):
    """target is a point (x, y, z) or an object (followed as it moves) plus optional height offset."""
    if isinstance(target, tuple) and len(target) == 2 and hasattr(target[0], "matrix_world"):
        obj, dz = target
    elif hasattr(target, "matrix_world"):
        obj, dz = target, 0.0
    else:
        return Vector(target)
    bpy.context.scene.frame_set(f)
    return obj.matrix_world.translation + Vector((0, 0, dz))


def camera_move(kind, target, distance=8.0, height=1.6, lens=35, angle=0.0, amount=None):
    """
    Key a 10 s camera move on every frame. kind:
      "dolly"  push in toward the target (amount = metres travelled, default 45% of distance)
      "orbit"  circle around the target (amount = degrees, default 90)
      "chase"  follow a moving object from behind, swinging round to its side (amount = degrees, default 75)
      "crane"  rise up and tilt down onto the target (amount = metres of rise, default 6)
      "truck"  slide sideways past the target, always looking at it (amount = metres, default 10)
    target: a point (x, y, z), an object, or (object, height_offset).
    angle: where the camera starts, in degrees around the target (0 = behind, looking along +Y).
    """
    s = bpy.context.scene
    cam = _camera(lens)
    a0 = math.radians(angle)
    for f in range(1, LAST + 1):
        t = (f - 1) / (LAST - 1)
        e = _ease(t)
        tgt = _target_at(target, f)
        if kind == "dolly":
            amt = amount if amount is not None else distance * 0.45
            r, a, h = distance - amt * e, a0, height
        elif kind == "orbit":
            amt = math.radians(amount if amount is not None else 90)
            r, a, h = distance, a0 + amt * e, height
        elif kind == "chase":
            amt = math.radians(amount if amount is not None else 75)
            r, a, h = distance * (1 + 0.15 * e), a0 + amt * e, height + 0.3 * e
        elif kind == "crane":
            amt = amount if amount is not None else 6.0
            r, a, h = distance, a0, height + amt * e
        elif kind == "truck":
            amt = amount if amount is not None else 10.0
            side = Vector((math.cos(a0), math.sin(a0), 0))
            back = Vector((math.sin(a0), -math.cos(a0), 0))
            cam.location = tgt + back * distance + side * (amt * (e - 0.5)) + Vector((0, 0, height - tgt.z))
            _aim(cam, tgt)
            cam.keyframe_insert("location", frame=f)
            cam.keyframe_insert("rotation_euler", frame=f)
            continue
        else:
            raise ValueError("kind must be dolly, orbit, chase, crane or truck")
        cam.location = (tgt.x + r * math.sin(a), tgt.y - r * math.cos(a), h)
        _aim(cam, tgt)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
    _linear(cam)
    s.frame_set(1)
    return cam


# ---------- output ----------
def save(path):
    bpy.ops.wm.save_as_mainfile(filepath=path)
    return path


def set_mp4_output(path):
    """Point the render at an H.264 MP4 (render it with: blender -b scene.blend -a)."""
    s = bpy.context.scene
    im = s.render.image_settings
    try:
        im.media_type = "VIDEO"
    except Exception:
        pass
    im.file_format = "FFMPEG"
    s.render.ffmpeg.format = "MPEG4"
    s.render.ffmpeg.codec = "H264"
    s.render.ffmpeg.constant_rate_factor = "HIGH"
    s.render.filepath = path
    return path


def report():
    s = bpy.context.scene
    return {
        "objects": len(bpy.data.objects),
        "frames": (s.frame_start, s.frame_end),
        "fps": s.render.fps,
        "size": (s.render.resolution_x, s.render.resolution_y),
        "camera": s.camera.name if s.camera else None,
        "output": s.render.filepath,
    }
