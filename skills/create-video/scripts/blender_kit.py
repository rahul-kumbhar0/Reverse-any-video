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
        mod.use_clamp_overlap = True
        wn = ob.modifiers.new("weighted_normal", "WEIGHTED_NORMAL")   # flat faces stay flat
        wn.mode = "FACE_AREA"
        wn.weight = 50
        wn.keep_sharp = True
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
        L.data.shadow_soft_size = 0.6        # point-source spots cast hard, distracting shadows
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
           still_at=None, bloom=True, motion_blur=True, exposure=0.0):
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
    s.cycles.sample_clamp_indirect = 8.0        # kills fireflies (blender-rendering skill)
    s.cycles.blur_glossy = 0.5
    try:
        s.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    except (AttributeError, TypeError):
        pass
    s.render.use_persistent_data = True
    s.render.use_motion_blur = motion_blur
    s.render.motion_blur_shutter = 0.5
    s.render.resolution_x = int(width * scale)
    s.render.resolution_y = int(height * scale)
    s.view_settings.view_transform = "AgX"
    s.view_settings.exposure = exposure
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


# ----------------------------------------------------------------------------- detailing
# The reference's "top detailing" is mostly surface response, not polygons: brushed metal
# streaks, roughness that varies (smudges/wear), tiny bumps, plus small hardware (screws,
# SMD parts, vias, markings, flex cables). These helpers add that layer.


def _nodes(mat):
    nt = mat.node_tree
    return nt, nt.nodes, nt.links, nt.nodes["Principled BSDF"]


def micro_surface(mat, scale=180.0, bump=0.08, rough_var=0.12, seed=0.0):
    """Roughness variation + micro bump from noise: kills the 'perfect CG' sheen."""
    nt, N, L, b = _nodes(mat)
    tc = N.new("ShaderNodeTexCoord")
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 6.0
    if "W" in noise.inputs:
        noise.noise_dimensions = "4D"
        noise.inputs["W"].default_value = seed
    L.new(tc.outputs["Object"], noise.inputs["Vector"])
    base_r = b.inputs["Roughness"].default_value
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = max(0.0, base_r - rough_var)
    mr.inputs["To Max"].default_value = min(1.0, base_r + rough_var)
    L.new(noise.outputs["Fac"], mr.inputs["Value"])
    L.new(mr.outputs["Result"], b.inputs["Roughness"])
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.002
    L.new(noise.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return mat


def brushed(mat, axis="x", streak=600.0, bump=0.12):
    """Brushed-metal streaks: noise stretched along one axis drives bump + anisotropy."""
    nt, N, L, b = _nodes(mat)
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    sx, sy = (2.0, streak) if axis == "x" else (streak, 2.0)
    mp.inputs["Scale"].default_value = (sx, sy, 2.0)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 8.0
    L.new(mp.outputs["Vector"], noise.inputs["Vector"])
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.001
    L.new(noise.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    if "Anisotropic" in b.inputs:
        b.inputs["Anisotropic"].default_value = 0.7
        if "Anisotropic Rotation" in b.inputs:
            b.inputs["Anisotropic Rotation"].default_value = 0.0 if axis == "x" else 0.25
    return mat


def screw(name, loc, r=0.022, mat=None):
    """Phillips pan-head screw: domed head + cross recess."""
    head = cylinder(name, r, r * 0.55, mat=mat or M_alu_silver(), loc=loc, bevel=r * 0.35, verts=32)
    slot = M_chip()
    z = loc[2] + r * 0.28
    a = rounded_slab(name + "_x", r * 1.3, r * 0.22, r * 0.12, mat=slot, loc=(loc[0], loc[1], z), bevel=0)
    b_ = rounded_slab(name + "_y", r * 0.22, r * 1.3, r * 0.12, mat=slot, loc=(loc[0], loc[1], z), bevel=0)
    return [head, a, b_]


def smd_scatter(prefix, region, count, z, seed=5, sizes=((0.03, 0.016), (0.022, 0.012), (0.05, 0.03))):
    """Scatter surface-mount parts (resistor/capacitor bodies with metal end caps)."""
    rnd = random.Random(seed)
    body_mats = [material("smd_tan", "#B08A5A", rough=0.5), material("smd_black", "#1A1A1C", rough=0.4),
                 material("smd_gray", "#6F7176", rough=0.45)]
    cap = M_alu_silver()
    out = []
    (x0, x1), (y0, y1) = region
    for i in range(count):
        w, d = rnd.choice(sizes)
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        rot = rnd.random() < 0.5
        if rot:
            w, d = d, w
        out.append(rounded_slab(f"{prefix}{i}", w, d, d * 0.6, mat=rnd.choice(body_mats),
                                loc=(x, y, z + d * 0.3), bevel=0.0015))
        ex = (w / 2 - min(w, d) * 0.12) if not rot else 0
        ey = (d / 2 - min(w, d) * 0.12) if rot else 0
        for sgn in (-1, 1):
            out.append(rounded_slab(f"{prefix}{i}c{sgn}", min(w, d) * 0.25 if not rot else w * 1.02,
                                    d * 1.02 if not rot else min(w, d) * 0.25, d * 0.62, mat=cap,
                                    loc=(x + sgn * ex, y + sgn * ey, z + d * 0.3), bevel=0.001))
    return out


def via_grid(name, region, pitch, z, r=0.006, mat=None):
    """Plated vias: tiny gold dots in a grid (array modifier on both axes)."""
    (x0, x1), (y0, y1) = region
    nx, ny = max(1, int((x1 - x0) / pitch)), max(1, int((y1 - y0) / pitch))
    ob = cylinder(name, r, 0.002, mat=mat or M_gold(), loc=(x0, y0, z), bevel=0, verts=12)
    for axis, n in ((0, nx), (1, ny)):
        arr = ob.modifiers.new(f"arr{axis}", "ARRAY")
        arr.count = n
        arr.use_relative_offset = False
        arr.use_constant_offset = True
        off = [0, 0, 0]
        off[axis] = pitch
        arr.constant_offset_displace = off
    return ob


def text_label(name, body, size, loc, mat=None, rot=(0, 0, 0)):
    """Flat printed marking (chip part numbers, silkscreen)."""
    bpy.ops.object.text_add(location=loc, rotation=tuple(math.radians(a) for a in rot))
    ob = bpy.context.object
    ob.name = name
    ob.data.body = body
    ob.data.size = size
    ob.data.align_x = "CENTER"
    ob.data.align_y = "CENTER"
    ob.data.extrude = 0.0004
    ob.data.materials.append(mat or material("ink", "#8E9096", rough=0.6))
    return ob


def flex_cable(name, points, width=0.08, thickness=0.004, mat=None):
    """Ribbon flex cable (amber polyimide) along a smooth path of (x,y,z) points."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp_, p in zip(sp.bezier_points, points):
        bp_.co = p
        bp_.handle_left_type = bp_.handle_right_type = "AUTO"
    cu.extrude = width / 2
    cu.offset = 0
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    sol = ob.modifiers.new("solid", "SOLIDIFY")
    sol.thickness = thickness
    ob.data.materials.append(mat or material("kapton", "#C9781E", rough=0.3, coat=0.6,
                                             transmission=0.25))
    return ob


# ----------------------------------------------------------------------------- environments
# "Shape the reflections, not the illumination" (EL4CTEO/blender-skills lighting-lookdev):
# glossy products read as premium when long soft strips are *reflected* in them. These
# emitters are invisible to the camera, so the background stays near-black.


def reflection_strips(target=(0, 0, 0.6), radius=4.0, height=3.0, count=3, strength=6.0,
                      color="#FFFFFF", length=6.0, width=0.6):
    """Camera-invisible emissive strips arranged around the subject, for clean highlights."""
    out = []
    mat = material("strip_emit", color, emission=color, emission_strength=strength)
    for i in range(count):
        ang = math.radians(-150 + i * (120 / max(1, count - 1)))
        loc = (target[0] + radius * math.cos(ang), target[1] + radius * math.sin(ang), height)
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
        ob = bpy.context.object
        ob.name = f"refl_strip{i}"
        ob.scale = (width, length, 1)
        ob.data.materials.append(mat)
        track(ob, target)
        ob.visible_camera = False
        ob.visible_shadow = False
        out.append(ob)
    return out


def gradient_world(top="#2A2D33", bottom="#050507", strength=0.35, camera_color="#050507"):
    """Studio gradient environment used for reflections/IBL, while the camera sees camera_color.
    Stand-in for a studio HDRI when none is available."""
    w = bpy.context.scene.world
    nt = w.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        if n.type != "OUTPUT_WORLD":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_WORLD")
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = hex_rgba(bottom)
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = hex_rgba(top)
    L.new(sep.outputs["Z"], ramp.inputs["Fac"])
    env_bg = N.new("ShaderNodeBackground")
    env_bg.inputs["Strength"].default_value = strength
    L.new(ramp.outputs["Color"], env_bg.inputs["Color"])
    cam_bg = N.new("ShaderNodeBackground")
    cam_bg.inputs["Color"].default_value = hex_rgba(camera_color)
    lp = N.new("ShaderNodeLightPath")
    mix = N.new("ShaderNodeMixShader")
    L.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    L.new(env_bg.outputs["Background"], mix.inputs[1])
    L.new(cam_bg.outputs["Background"], mix.inputs[2])
    L.new(mix.outputs["Shader"], out.inputs["Surface"])
    return w


def hdri_world(path, strength=0.8, rotation_deg=0.0, camera_color="#050507"):
    """Image-based lighting from an HDRI (e.g. Poly Haven CC0 'studio_small_09'), camera sees
    camera_color. Fetch with scripts/fetch_assets.py when the network allows."""
    w = bpy.context.scene.world
    nt = w.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        if n.type != "OUTPUT_WORLD":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_WORLD")
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(rotation_deg))
    env = N.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(path)
    L.new(tc.outputs["Generated"], mp.inputs["Vector"])
    L.new(mp.outputs["Vector"], env.inputs["Vector"])
    bg = N.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    L.new(env.outputs["Color"], bg.inputs["Color"])
    cam_bg = N.new("ShaderNodeBackground")
    cam_bg.inputs["Color"].default_value = hex_rgba(camera_color)
    lp = N.new("ShaderNodeLightPath")
    mix = N.new("ShaderNodeMixShader")
    L.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    L.new(bg.outputs["Background"], mix.inputs[1])
    L.new(cam_bg.outputs["Background"], mix.inputs[2])
    L.new(mix.outputs["Shader"], out.inputs["Surface"])
    return w


def studio_environment(hdri=None, **kw):
    """HDRI if a file is given/available (env RAV_HDRI), else the gradient studio world."""
    path = hdri or os.environ.get("RAV_HDRI")
    if path and os.path.exists(path):
        return hdri_world(path, **kw)
    return gradient_world()
