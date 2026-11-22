"""
render_walkthrough.py - render the palace walkthrough (Cam_Walkthrough, frames 1-240) to MP4.

Run headless:
    blender -b /Volumes/Samsung/MemoryPalace/memory_palace.blend --python memory-palace/render_walkthrough.py

Writes /Volumes/Samsung/MemoryPalace/renders/walkthrough.mp4 (H.264, 24 fps, 1280x720).
Uses EEVEE with a low sample count so the 10-second animation finishes in minutes.
"""
import os

import bpy

OUT_DIR = "/Volumes/Samsung/MemoryPalace/renders"
OUT_FILE = os.path.join(OUT_DIR, "walkthrough.mp4")

os.makedirs(OUT_DIR, exist_ok=True)
scene = bpy.context.scene
scene.camera = bpy.data.objects["Cam_Walkthrough"]
scene.frame_start, scene.frame_end = 1, 240
scene.render.fps = 24
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.render.resolution_percentage = 100
try:
    scene.eevee.taa_render_samples = 16
except AttributeError:
    pass

scene.render.image_settings.media_type = "VIDEO"   # Blender 5.x: set media type before the FFMPEG format
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
scene.render.filepath = OUT_FILE

bpy.ops.render.render(animation=True)
print("WALKTHROUGH_DONE", OUT_FILE, flush=True)
