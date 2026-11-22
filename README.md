# blender-memory-palaces

**Live page (GitHub Pages): [index.html](https://rifaterdemsahin.github.io/blender-memory-palaces/)**

A 7-station 3D memory palace, built procedurally in Blender 5.3 with a Python script (Method of Loci).

- Page: [`index.html`](index.html) (renders, walkthrough description and downloads)
- Scene: [`memory-palace/memory_palace.blend`](memory-palace/memory_palace.blend)
- Build script: [`memory-palace/build_palace.py`](memory-palace/build_palace.py)
- Full build log and documentation: [`memory-palace/BUILD_LOG.md`](memory-palace/BUILD_LOG.md)

Rebuild it:

```sh
blender -b --python memory-palace/build_palace.py
```

The script writes to `/Volumes/Samsung/MemoryPalace/` (see `OUT` at the top of the script).

## Skills

- [`.claude/skills/blender-director`](.claude/skills/blender-director/SKILL.md): turns a one-line shot idea into a 10-second clay Blender clip with a camera move, plus a Google Flow prompt.
