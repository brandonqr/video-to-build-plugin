#!/usr/bin/env python3
"""Normalize scale/origin, optionally rotate around Z, downscale textures to 2K WebP, and audit a GLB in Blender."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Optimize and normalize a GLB inside headless Blender.")
    parser.add_argument("--input", required=True, help="Input .glb/.gltf path")
    parser.add_argument("--output", required=True, help="Output normalized .glb path")
    parser.add_argument("--size", type=float, default=26.0, help="Target max bounding-box dimension")
    parser.add_argument("--max-tex", type=int, default=2048, help="Max texture width/height")
    parser.add_argument("--rotate-z", type=float, default=0.0, help="Degrees to rotate around Blender Z axis")
    parser.add_argument("--quality", type=int, default=86, help="WebP image quality (1-100)")
    parser.add_argument("--preview", help="Optional PNG render path for visual audit")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    in_path = Path(args.input).resolve()
    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(in_path))

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if not meshes:
        print(json.dumps({"error": "No mesh objects found in GLB"}))
        return 1

    min_v = Vector((1e9, 1e9, 1e9))
    max_v = Vector((-1e9, -1e9, -1e9))
    for m in meshes:
        mw = m.matrix_world
        for v in m.data.vertices:
            wv = mw @ v.co
            min_v.x = min(min_v.x, wv.x)
            min_v.y = min(min_v.y, wv.y)
            min_v.z = min(min_v.z, wv.z)
            max_v.x = max(max_v.x, wv.x)
            max_v.y = max(max_v.y, wv.y)
            max_v.z = max(max_v.z, wv.z)

    raw_size = max_v - min_v
    scale = args.size / max(raw_size.x, raw_size.y, raw_size.z, 0.001)
    cx = (min_v.x + max_v.x) * 0.5
    cy = (min_v.y + max_v.y) * 0.5

    rad = math.radians(args.rotate_z)
    cos_r = math.cos(rad)
    sin_r = math.sin(rad)

    for m in meshes:
        mw = m.matrix_world.copy()
        for v in m.data.vertices:
            wv = mw @ v.co
            tx = (wv.x - cx) * scale
            ty = (wv.y - cy) * scale
            tz = (wv.z - min_v.z) * scale
            rx = tx * cos_r - ty * sin_r
            ry = tx * sin_r + ty * cos_r
            v.co = Vector((rx, ry, tz))
        m.parent = None
        m.location = (0.0, 0.0, 0.0)
        m.rotation_euler = (0.0, 0.0, 0.0)
        m.scale = (1.0, 1.0, 1.0)
        m.data.update()

    bpy.context.view_layer.update()

    for img in bpy.data.images:
        w, h = img.size[0], img.size[1]
        if w > args.max_tex or h > args.max_tex:
            img.scale(min(w, args.max_tex), min(h, args.max_tex))

    bpy.ops.export_scene.gltf(
        filepath=str(out_path),
        export_format="GLB",
        export_yup=True,
        export_image_format="WEBP",
        export_image_quality=args.quality,
        export_materials="EXPORT",
    )

    verts = sum(len(m.data.vertices) for m in meshes)
    tris = sum(sum(len(p.vertices) - 2 for p in m.data.polygons) for m in meshes)
    open_edges = 0
    nmin = Vector((1e9, 1e9, 1e9))
    nmax = Vector((-1e9, -1e9, -1e9))
    for m in meshes:
        efc: dict[tuple[int, int], int] = {}
        for p in m.data.polygons:
            for ek in p.edge_keys:
                efc[ek] = efc.get(ek, 0) + 1
        open_edges += sum(1 for c in efc.values() if c == 1)
        for v in m.data.vertices:
            nmin.x = min(nmin.x, v.co.x)
            nmin.y = min(nmin.y, v.co.y)
            nmin.z = min(nmin.z, v.co.z)
            nmax.x = max(nmax.x, v.co.x)
            nmax.y = max(nmax.y, v.co.y)
            nmax.z = max(nmax.z, v.co.z)

    nsize = nmax - nmin
    ncenter = (nmin + nmax) * 0.5

    if args.preview:
        prev_path = Path(args.preview).resolve()
        prev_path.parent.mkdir(parents=True, exist_ok=True)
        scene = bpy.context.scene
        scene.render.engine = "CYCLES"
        scene.cycles.samples = 12
        scene.render.resolution_x = 960
        scene.render.resolution_y = 540
        world = bpy.data.worlds.new("AuditWorld")
        scene.world = world
        world.use_nodes = True
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs[0].default_value = (0.043, 0.047, 0.039, 1.0)
            bg.inputs[1].default_value = 1.6
        sun = bpy.data.lights.new("Sun", type="SUN")
        sun.energy = 2.8
        sun_obj = bpy.data.objects.new("Sun", sun)
        scene.collection.objects.link(sun_obj)
        sun_obj.rotation_euler = (math.radians(45), 0.0, math.radians(-35))
        cam_data = bpy.data.cameras.new("Cam")
        cam_obj = bpy.data.objects.new("Cam", cam_data)
        scene.collection.objects.link(cam_obj)
        scene.camera = cam_obj
        max_dim = max(nsize.x, nsize.y, nsize.z, 1.0)
        cam_obj.location = ncenter + Vector((-max_dim * 0.48, -max_dim * 1.02, max_dim * 0.45))
        cam_obj.rotation_euler = (ncenter - cam_obj.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(prev_path)
        bpy.ops.render.render(write_still=True)

    report = {
        "raw_size_bytes": in_path.stat().st_size,
        "optimized_size_bytes": out_path.stat().st_size,
        "mesh_count": len(meshes),
        "vertices": verts,
        "triangles": tris,
        "open_boundary_edges": open_edges,
        "bbox_min": [round(v, 3) for v in nmin],
        "bbox_max": [round(v, 3) for v in nmax],
        "size": [round(v, 3) for v in nsize],
        "images": [{"name": img.name, "size": list(img.size)} for img in bpy.data.images],
    }
    print("OPTIMIZE_GLB_REPORT:", json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
