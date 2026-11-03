"""blender_kit — production helpers for photoreal explainer shots in headless Blender (bpy).

Import from a scene script:
    import sys; sys.path.insert(0, "<repo>/skills/create-video/scripts")
    from blender_kit import *

Encodes the craft rules from references/blender-craft.md so every scene gets them for free:
bevelled edges with hardened normals (the bright edge line that reads as "real"),
physically-plausible material presets, the premium studio rig, eased animation,
emission ramps, dust fields, screen-space anchor export for tracked 2D labels,
and a render+encode pipeline with motion-interpolation and bloom.
"""
import json
import math
import os
import random
import subprocess
import tempfile

import bpy  # must precede bmesh: the pip `bpy` build registers bmesh on import
import bmesh
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

# ----------------------------------------------------------------------------- scene


def reset(fps_render=12, duration_s=3.0, background="#050507"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.fps = fps_render
    s.frame_start = 1
    s.frame_end = max(2, round(duration_s * fps_render))
    world = bpy.data.worlds.new("world")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = hex_rgba(background)
    bg.inputs[1].default_value = 1.0
    s.world = world
    return s


def frame_at(t):
    """seconds -> frame number for the current scene"""
    s = bpy.context.scene
    return 1 + t * s.render.fps


def hex_rgba(h, a=1.0):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)


# ----------------------------------------------------------------------------- materials


def material(name, color="#808080", rough=0.5, metal=0.0, coat=0.0, coat_rough=0.05,
             transmission=0.0, ior=1.45, emission=None, emission_strength=0.0,
             aniso=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]

    def setin(key, val):
        if key in b.inputs:
            b.inputs[key].default_value = val

    setin("Base Color", hex_rgba(color))
    setin("Roughness", rough)
    setin("Metallic", metal)
    setin("Coat Weight", coat)
    setin("Coat Roughness", coat_rough)
    setin("Transmission Weight", transmission)
    setin("IOR", ior)
    setin("Anisotropic", aniso)
    setin("Alpha", alpha)
    if emission:
        setin("Emission Color", hex_rgba(emission))
        setin("Emission Strength", emission_strength)
    return m


def emission_socket(mat):
    return mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]


# Presets tuned for the dark-studio look. Colors are sRGB hex.
def M_glass_frosted():
    return material("glass_frosted", "#E8ECF2", rough=0.28, transmission=1.0, ior=1.5, coat=0.6)


def M_glass_clear():
    return material("glass_clear", "#FFFFFF", rough=0.02, transmission=1.0, ior=1.5)


def M_alu_space_gray():
    return material("alu_space_gray", "#5A5D63", rough=0.32, metal=1.0, aniso=0.4)


def M_alu_silver():
    return material("alu_silver", "#C9CCD1", rough=0.25, metal=1.0, aniso=0.5)


def M_pcb():
    return material("pcb", "#0D2B1F", rough=0.45, coat=0.8, coat_rough=0.15)


def M_copper():
    return material("copper", "#D98A5B", rough=0.25, metal=1.0)


def M_gold():
    return material("gold", "#E6B866", rough=0.2, metal=1.0)


def M_chip():
    return material("chip", "#121214", rough=0.55)


def M_rubber_black():
    return material("rubber_black", "#141416", rough=0.6)


def M_emissive(name, color="#E0A33E", strength=6.0):
    return material(name, color, rough=0.4, emission=color, emission_strength=strength)


def M_dust():
    return material("dust", "#FFFFFF", rough=1.0, emission="#FFF4E0", emission_strength=0.45)


# ----------------------------------------------------------------------------- geometry


def _finish(ob, mat=None, bevel=0.0, segments=3, smooth=True):
    if smooth:
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.shade_smooth()
    if bevel > 0:
        mod = ob.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(40)
        mod.harden_normals = True
        mod.miter_outer = "MITER_ARC"
    if mat:
        ob.data.materials.append(mat)
    ob.select_set(False)
    return ob


def rounded_slab(name, w, d, h, corner_r=0.0, bevel=0.004, mat=None, loc=(0, 0, 0)):
    """Box w×d×h (z up, origin at center) with rounded plan-view corners + bevelled edges.
    This is the workhorse: phones, trackpads, PCBs, chips, glass layers."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (w, d, h)
    bpy.ops.object.transform_apply(scale=True)
    if corner_r > 0:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        vert_edges = [e for e in bm.edges
                      if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-6
                      and abs(e.verts[0].co.x - e.verts[1].co.x) < 1e-6]
        r = min(corner_r, w / 2 - 1e-4, d / 2 - 1e-4)
        bmesh.ops.bevel(bm, geom=vert_edges, offset=r, segments=10, affect="EDGES",
                        profile=0.5, clamp_overlap=True)
        bm.to_mesh(ob.data)
        bm.free()
    return _finish(ob, mat, bevel=bevel)


def cylinder(name, r, depth, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.003, verts=64):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc,
                                        rotation=tuple(math.radians(a) for a in rot))
    ob = bpy.context.object
    ob.name = name
    return _finish(ob, mat, bevel=bevel)


def torus(name, R, r, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=96,
                                     minor_segments=24, location=loc,
                                     rotation=tuple(math.radians(a) for a in rot))
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    return _finish(ob, mat, bevel=0)


def bar_array(name, length, thick, height, count, pitch, axis="x", mat=None, loc=(0, 0, 0)):
    """Evenly spaced thin bars (electrode grids, traces, pins). One object, array modifier.
    axis='x': bars run along X, repeat along Y. axis='y': run along Y, repeat along X."""
    if axis == "x":
        size, rep = (length, thick, height), (0, 1, 0)
    else:
        size, rep = (thick, length, height), (1, 0, 0)
    span = (count - 1) * pitch
    start = tuple(l - (span / 2 if rep[i] else 0) for i, l in enumerate(loc))
    bpy.ops.mesh.primitive_cube_add(size=1, location=start)
    ob = bpy.context.object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    arr = ob.modifiers.new("array", "ARRAY")
    arr.count = count
    arr.use_relative_offset = False
    arr.use_constant_offset = True
    arr.constant_offset_displace = tuple(pitch * c for c in rep)
    return _finish(ob, mat, bevel=0, smooth=False)


def dust_field(count=110, bounds=((-2, 2), (-2, 2), (-0.5, 3)), radius=(0.0015, 0.004), seed=3):
    """Single object of tiny emissive specks floating in the light (depth cue)."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    for _ in range(count):
        r = rnd.uniform(*radius)
        m = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
        c = Vector(tuple(rnd.uniform(*b) for b in bounds))
        bmesh.ops.translate(bm, verts=m["verts"], vec=c)
    me = bpy.data.meshes.new("dust")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("dust", me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(M_dust())
    ob.visible_shadow = False
    return ob


def parent(children, parent_ob):
    for c in children:
        c.parent = parent_ob
        c.matrix_parent_inverse = parent_ob.matrix_world.inverted()


def group(name, loc=(0, 0, 0)):
    """An empty used as an animatable group root (move a whole layer by moving this)."""
    bpy.ops.object.empty_add(location=loc)
    e = bpy.context.object
    e.name = name
    return e


def anchor(name, parent_ob, offset=(0, 0, 0)):
    """An empty that marks where a 2D label should point; follows its parent."""
    bpy.ops.object.empty_add(location=parent_ob.matrix_world @ Vector(offset))
    e = bpy.context.object
    e.name = "anchor:" + name
    e.parent = parent_ob
    e.matrix_parent_inverse = parent_ob.matrix_world.inverted()
    return e


# ----------------------------------------------------------------------------- animation


def _ease_all(ob_or_id):
    ad = getattr(ob_or_id, "animation_data", None)
    if not ad or not ad.action:
        return
    for fc in action_fcurves(ad.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.easing = "AUTO"
            kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"


def action_fcurves(action):
    """fcurves across Blender 4.x (flat) and 5.x (layered actions)."""
    if getattr(action, "fcurves", None) is not None:
        return list(action.fcurves)
    out = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                out.extend(cb.fcurves)
    return out


def key_loc(ob, keys):
    """keys: [(t_seconds, (x,y,z)), ...] — eased (clamped bezier: no overshoot)."""
    for t, loc in keys:
        ob.location = loc
        ob.keyframe_insert("location", frame=frame_at(t))
    _ease_all(ob)


def key_rot(ob, keys):
    for t, rot in keys:
        ob.rotation_euler = tuple(math.radians(a) for a in rot)
        ob.keyframe_insert("rotation_euler", frame=frame_at(t))
    _ease_all(ob)


def key_value(socket, keys):
    """Animate any node input (e.g. emission strength ramp)."""
    for t, v in keys:
        socket.default_value = v
        socket.keyframe_insert("default_value", frame=frame_at(t))


# ----------------------------------------------------------------------------- lighting & camera


def light(kind, loc, energy, color="#FFFFFF", size=2.0, aim_at=None, spot_deg=55, blend=0.8):
    bpy.ops.object.light_add(type=kind.upper(), location=loc)
    L = bpy.context.object
    L.data.energy = energy
    L.data.color = hex_rgba(color)[:3]
    if hasattr(L.data, "size"):
        L.data.size = size
    if L.data.type == "SPOT":
        L.data.spot_size = math.radians(spot_deg)
        L.data.spot_blend = blend
    if aim_at is not None:
        track(L, aim_at)
    return L


def track(ob, target):
    """target: an object or a (x,y,z) point."""
    if not hasattr(target, "location"):
        bpy.ops.object.empty_add(location=target)
        target = bpy.context.object
    c = ob.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return target


def studio_rig(target=(0, 0, 0), scale=1.0, rim="#E0A33E", fill="#6FA8FF",
               key_energy=320, rim_energy=1800, fill_energy=500, top_softbox=True,
               key_color="#F1F4FF"):
    """The premium dark-explainer rig (3d-motion-playbook §1): large soft key high-left,
    warm rim behind grazing the silhouette, cool fill opposite, plus a soft overhead strip
    that gives glass/metal a long clean reflection."""
    s = scale
    rig = [
        light("area", (-3.0 * s, -2.6 * s, 4.2 * s), key_energy, color=key_color,
              size=4.5 * s, aim_at=target),
        light("spot", (-2.4 * s, 3.8 * s, 2.2 * s), rim_energy, color=rim, aim_at=target, spot_deg=40),
        light("spot", (3.4 * s, 2.8 * s, 1.0 * s), fill_energy, color=fill, aim_at=target, spot_deg=50),
    ]
    if top_softbox:
        L = light("area", (0.6 * s, -0.5 * s, 5.5 * s), key_energy * 0.45, size=1.2 * s, aim_at=target)
        L.data.shape = "RECTANGLE"
        L.data.size_y = 6.0 * s
        rig.append(L)
    return rig


def camera(lens=50, fstop=2.8, focus=None, keys=None, target=None, sensor=36):
    """Camera with eased location keys; aims at `target` (object/point) if given."""
    bpy.ops.object.camera_add(location=keys[0][1] if keys else (0, -6, 2))
    cam = bpy.context.object
    cam.data.lens = lens
    cam.data.sensor_width = sensor
    if focus is not None:
        cam.data.dof.use_dof = True
        cam.data.dof.focus_object = focus
        cam.data.dof.aperture_fstop = fstop
    if target is not None:
        track(cam, target)
    if keys:
        key_loc(cam, keys)
    bpy.context.scene.camera = cam
    return cam


# ----------------------------------------------------------------------------- export & render


def export_anchors(path, width=1080, height=1920):
    """Per-frame normalized screen positions (x right, y down, 0..1) of every 'anchor:*'
    empty, for 2D labels/annotation lines in the compositor that track the 3D motion.
    width/height must match the final render: projection depends on the aspect ratio."""
    s = bpy.context.scene
    s.render.resolution_x, s.render.resolution_y = width, height
    s.render.pixel_aspect_x = s.render.pixel_aspect_y = 1.0
    cam = s.camera
    anchors = [o for o in s.objects if o.name.startswith("anchor:")]
    data = {"fps": s.render.fps, "frames": s.frame_end - s.frame_start + 1, "anchors": {}}
    for a in anchors:
        data["anchors"][a.name[7:]] = []
    for f in range(s.frame_start, s.frame_end + 1):
        s.frame_set(f)
        for a in anchors:
            p = world_to_camera_view(s, cam, a.matrix_world.translation)
            data["anchors"][a.name[7:]].append([round(p.x, 4), round(1 - p.y, 4)])
    s.frame_set(s.frame_start)
    with open(path, "w") as fh:
        json.dump(data, fh)
    return data


def render(out_mp4, width=1080, height=1920, fps_out=30, samples=48, scale=0.5,
           still_at=None, bloom=True, motion_blur=True):
    """Cycles CPU render -> MP4 (motion-interpolated to fps_out, upscaled, optional bloom).
    still_at=<seconds> renders a single verification PNG instead (out_mp4 -> .png)."""
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = samples
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.02
    s.cycles.use_denoising = True
    s.cycles.max_bounces = 8
    s.cycles.transmission_bounces = 8
    s.cycles.glossy_bounces = 4
    s.cycles.diffuse_bounces = 2
    s.cycles.caustics_reflective = False
    s.cycles.caustics_refractive = False
    s.render.use_persistent_data = True
    s.render.use_motion_blur = motion_blur
    s.render.motion_blur_shutter = 0.5
    s.render.resolution_x = int(width * scale)
    s.render.resolution_y = int(height * scale)
    s.view_settings.view_transform = "AgX"
    try:
        s.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    s.render.image_settings.file_format = "PNG"

    if still_at is not None:
        s.frame_set(round(frame_at(still_at)))
        png = os.path.splitext(out_mp4)[0] + ".png"
        s.render.filepath = png
        bpy.ops.render.render(write_still=True)
        if bloom:
            _bloom_png(png)
        return png

    with tempfile.TemporaryDirectory() as tmp:
        s.render.filepath = os.path.join(tmp, "f_")
        bpy.ops.render.render(animation=True)
        n = len([f for f in os.listdir(tmp) if f.endswith(".png")])
        retime = (f"minterpolate=fps={fps_out}:mi_mode=mci:mc_mode=aobmc:vsbmc=1"
                  if n >= 5 else f"fps={fps_out}")
        vf = f"{retime},scale={width}:{height}:flags=lanczos"
        if bloom:
            vf += "," + BLOOM_FILTER
        vf += ",format=yuv420p"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                        "-framerate", str(s.render.fps), "-pattern_type", "glob",
                        "-i", os.path.join(tmp, "f_*.png"), "-vf", vf,
                        "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-y", out_mp4],
                       check=True)
    return out_mp4


# Highlights-only blur screened back over the image: the soft glow on emissive parts and
# specular edges that Cycles alone doesn't produce (AE/Blender compositor "glare" equivalent).
BLOOM_FILTER = ("split[base][hl];[hl]curves=all='0/0 0.74/0 1/1',gblur=sigma=16[g];"
                "[base][g]blend=all_mode=screen:all_opacity=0.4")


def _bloom_png(png):
    tmp = png + ".bloom.png"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", png,
                    "-vf", BLOOM_FILTER, "-y", tmp], check=True)
    os.replace(tmp, png)
