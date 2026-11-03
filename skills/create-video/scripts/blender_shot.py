#!/usr/bin/env python3
"""Photoreal 3D shot renderer — Blender (bpy) Cycles, fully headless.

Takes a declarative shot-spec JSON and renders an MP4. This is the "exact 3D"
tier: PBR materials, studio lighting, animated camera with eased keyframes, DOF.

Install: pip install bpy      (Blender as a Python module; CPU Cycles works headless)

Usage: python3 blender_shot.py <shot.json> <out.mp4>
       [--fps-render 15] [--samples 48] [--scale 0.5]

Rendering at 15fps / half resolution keeps CPU time sane; the script then
retimes to the spec fps with ffmpeg minterpolate (motion-interpolated) and
upscales, which looks close to a native render for slow cinematic moves.

shot.json schema (all sections optional except duration):
{
  "duration_s": 3.0, "fps": 30, "width": 1080, "height": 1920,
  "background": "#0C0C0E",
  "objects": [
    { "type": "torus|box|cylinder|sphere|plane|text",
      "name": "tire",
      "location": [0,0,1.4], "rotation_deg": [90,0,20], "scale": [1,1,1],
      "params": {"major_radius":1.0,"minor_radius":0.42},   // per type
      "text": "170 °C",                                      // type text only
      "material": {"color":"#141416","roughness":0.5,"metallic":0.05,
                    "emission":"#E0A33E","emission_strength":0},
      "spin_z_deg_per_s": 20                                 // optional animation
    }
  ],
  "lights": [
    { "type":"area|spot|sun|point", "location":[3,-2,5], "rotation_deg":[35,25,0],
      "energy":900, "size":6, "color":"#FFFFFF" }
  ],
  "camera": {
    "lens_mm": 60, "fstop": 1.8, "focus_object": "tire",
    "keys": [                                   // eased keyframes (BEZIER)
      { "t": 0.0, "location":[2.6,-3.4,1.1], "rotation_deg":[82,0,36] },
      { "t": 3.0, "location":[2.0,-2.6,1.3], "rotation_deg":[80,0,30] }
    ]
  }
}
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile


def hex_rgb(h, alpha=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, alpha)


def rad(deg3):
    return tuple(math.radians(d) for d in deg3)


def action_fcurves(action):
    """All fcurves of an action, across Blender 4.x (flat) and 5.x (layered) APIs."""
    if getattr(action, "fcurves", None) is not None:
        return list(action.fcurves)
    out = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                out.extend(cb.fcurves)
    return out


def build_and_render(spec, outdir, fps_render, samples, scale):
    import bpy  # heavy import; only inside blender path

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    fps = spec.get("fps", 30)
    dur = spec["duration_s"]
    scene.render.fps = fps_render
    scene.frame_start = 1
    scene.frame_end = max(2, int(dur * fps_render))

    # world background
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = hex_rgb(spec.get("background", "#0C0C0E"))
    bg.inputs[1].default_value = 1.0
    scene.world = world

    objs = {}
    for o in spec.get("objects", []):
        typ = o["type"]
        params = o.get("params", {})
        if typ == "torus":
            bpy.ops.mesh.primitive_torus_add(
                major_radius=params.get("major_radius", 1),
                minor_radius=params.get("minor_radius", 0.4),
                major_segments=96, minor_segments=48)
        elif typ == "box":
            bpy.ops.mesh.primitive_cube_add(size=params.get("size", 1))
        elif typ == "cylinder":
            bpy.ops.mesh.primitive_cylinder_add(
                radius=params.get("radius", 1), depth=params.get("depth", 1), vertices=64)
        elif typ == "sphere":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=params.get("radius", 1), segments=48)
        elif typ == "plane":
            bpy.ops.mesh.primitive_plane_add(size=params.get("size", 20))
        elif typ == "text":
            bpy.ops.object.text_add()
            ob = bpy.context.object
            ob.data.body = o.get("text", "")
            ob.data.extrude = params.get("extrude", 0.02)
            ob.data.align_x = "CENTER"
        else:
            continue
        ob = bpy.context.object
        ob.name = o.get("name", typ)
        ob.location = o.get("location", (0, 0, 0))
        ob.rotation_euler = rad(o.get("rotation_deg", (0, 0, 0)))
        ob.scale = o.get("scale", (1, 1, 1))
        if typ in ("torus", "sphere", "cylinder"):
            bpy.ops.object.shade_smooth()

        m = o.get("material", {})
        mat = bpy.data.materials.new(ob.name + "_mat")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = hex_rgb(m.get("color", "#888888"))
        bsdf.inputs["Roughness"].default_value = m.get("roughness", 0.5)
        bsdf.inputs["Metallic"].default_value = m.get("metallic", 0.0)
        if m.get("emission_strength", 0) > 0:
            bsdf.inputs["Emission Color"].default_value = hex_rgb(m.get("emission", "#FFFFFF"))
            bsdf.inputs["Emission Strength"].default_value = m["emission_strength"]
        ob.data.materials.append(mat)

        spin = o.get("spin_z_deg_per_s")
        if spin:
            ob.rotation_euler = rad(o.get("rotation_deg", (0, 0, 0)))
            ob.keyframe_insert("rotation_euler", frame=1)
            end_rot = list(o.get("rotation_deg", (0, 0, 0)))
            end_rot[2] += spin * dur
            ob.rotation_euler = rad(end_rot)
            ob.keyframe_insert("rotation_euler", frame=scene.frame_end)
            for fc in action_fcurves(ob.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
        objs[ob.name] = ob

    def aim(ob, target_loc):
        """Point an object at a world location via an empty + TRACK_TO."""
        bpy.ops.object.empty_add(location=target_loc)
        tgt = bpy.context.object
        c = ob.constraints.new("TRACK_TO")
        c.target = tgt
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"

    for li in spec.get("lights", []):
        bpy.ops.object.light_add(type=li.get("type", "area").upper(),
                                 location=li.get("location", (0, 0, 5)),
                                 rotation=rad(li.get("rotation_deg", (0, 0, 0))))
        L = bpy.context.object
        L.data.energy = li.get("energy", 500)
        L.data.color = hex_rgb(li.get("color", "#FFFFFF"))[:3]
        if hasattr(L.data, "size"):
            L.data.size = li.get("size", 4)
        if L.data.type == "SPOT":
            L.data.spot_blend = li.get("blend", 0.8)
        if "aim_at" in li:                       # aim beats hand-set rotation
            aim(L, li["aim_at"])

    cam_spec = spec.get("camera", {})
    keys = cam_spec.get("keys", [{"t": 0, "location": (0, -5, 2), "rotation_deg": (80, 0, 0)}])
    bpy.ops.object.camera_add(location=keys[0]["location"],
                              rotation=rad(keys[0]["rotation_deg"]))
    cam = bpy.context.object
    cam.data.lens = cam_spec.get("lens_mm", 50)
    focus = cam_spec.get("focus_object")
    if focus and focus in objs:
        cam.data.dof.use_dof = True
        cam.data.dof.focus_object = objs[focus]
        cam.data.dof.aperture_fstop = cam_spec.get("fstop", 2.0)
    scene.camera = cam
    for k in keys:
        frame = 1 + k["t"] * fps_render
        cam.location = k["location"]
        cam.rotation_euler = rad(k["rotation_deg"])
        cam.keyframe_insert("location", frame=frame)
        cam.keyframe_insert("rotation_euler", frame=frame)
    if cam.animation_data and cam.animation_data.action:
        for fc in action_fcurves(cam.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.easing = "EASE_IN_OUT"

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = int(spec.get("width", 1080) * scale)
    scene.render.resolution_y = int(spec.get("height", 1920) * scale)
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = os.path.join(outdir, "f_")
    bpy.ops.render.render(animation=True)
    return fps


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("shot")
    p.add_argument("out")
    p.add_argument("--fps-render", type=int, default=15)
    p.add_argument("--samples", type=int, default=48)
    p.add_argument("--scale", type=float, default=0.5)
    args = p.parse_args()
    with open(args.shot) as f:
        spec = json.load(f)
    fps = spec.get("fps", 30)
    w, h = spec.get("width", 1080), spec.get("height", 1920)

    with tempfile.TemporaryDirectory() as tmp:
        build_and_render(spec, tmp, args.fps_render, args.samples, args.scale)
        n_frames = len([f for f in os.listdir(tmp) if f.endswith(".png")])
        # retime + motion-interpolate to target fps, upscale to target res
        # (minterpolate needs a few frames of context; fall back to plain fps for stubs)
        retime = (f"minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc"
                  if n_frames >= 5 else f"fps={fps}")
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error",
             "-framerate", str(args.fps_render), "-pattern_type", "glob",
             "-i", os.path.join(tmp, "f_*.png"),
             "-vf", f"{retime},scale={w}:{h}:flags=lanczos,format=yuv420p",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-y", args.out],
            capture_output=True, text=True)
        if r.returncode != 0:
            print(f"ERROR encode: {r.stderr[-400:]}", file=sys.stderr)
            return 1
    print(f"OK: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
