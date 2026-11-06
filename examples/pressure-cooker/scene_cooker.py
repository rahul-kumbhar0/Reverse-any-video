"""Why does a pressure cooker whistle? — photoreal hero shots (Blender/Cycles via blender_kit).

One generic (unbranded) Indian-style pressure cooker on a gas burner. Shots:
  hero      0-5.9s   closed cooker on the flame, low push-in
  cutaway   7.0s     sliced in half: water heating, bubbles, steam, gasket glows at ~3.6s
  weight    9.4s     macro on the weight valve: lifts at ~5.1s, steam jet, jiggle
  safety    4.5s     macro on the fusible safety plug: glows, melts, puff escapes
  pullback  3.8s     wide pull-back: weight jiggling, steam puffs

python3 scene_cooker.py --shot cutaway --out out/cutaway.mp4 [--still 3.8] [--samples 28 --scale 0.45 --fps-render 8]
"""
import argparse
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "create-video", "scripts"))
from blender_kit import *  # noqa: E402,F401,F403
from blender_kit import _finish  # noqa: E402
import bmesh  # noqa: E402

DUR = {"hero": 5.9, "cutaway": 7.0, "weight": 9.4, "safety": 4.5, "pullback": 3.8}

p = argparse.ArgumentParser()
p.add_argument("--shot", required=True, choices=list(DUR))
p.add_argument("--out", required=True)
p.add_argument("--still", type=float, default=None)
p.add_argument("--samples", type=int, default=28)
p.add_argument("--scale", type=float, default=0.45)
p.add_argument("--fps-render", type=int, default=8)
p.add_argument("--anchors-only", action="store_true")
args = p.parse_args()
SHOT, D = args.shot, DUR[args.shot]
CUT = SHOT == "cutaway"

reset(fps_render=args.fps_render, duration_s=D, background="#050507")

# ------------------------------------------------------------------ materials
ALU = brushed(micro_surface(material("alu_body", "#DADDE2", rough=0.22, metal=1.0, aniso=0.6), scale=90, bump=0.03, rough_var=0.06), axis="x")
ALU_LID = micro_surface(material("alu_lid", "#BFC2C8", rough=0.18, metal=1.0), scale=120, bump=0.02, rough_var=0.05)
BAKELITE = micro_surface(material("bakelite", "#121214", rough=0.38, coat=0.4), scale=200, bump=0.04, rough_var=0.08)
RUBBER = material("gasket", "#1A1A1C", rough=0.7, emission="#E0A33E", emission_strength=0.0)
WEIGHT = brushed(material("weight", "#2B2C30", rough=0.3, metal=1.0), axis="y", streak=300)
CHROME = material("chrome", "#E4E6EA", rough=0.08, metal=1.0)
PLUG = material("plug", "#B9BCC2", rough=0.3, metal=1.0, emission="#FF6A1A", emission_strength=0.0)
IRON = micro_surface(material("iron", "#1B1B1E", rough=0.55, metal=1.0), scale=60, bump=0.15, rough_var=0.12)
STONE = micro_surface(material("stone", "#0D0D10", rough=0.4, coat=0.3), scale=8, bump=0.05, rough_var=0.15)
WATER = material("water", "#9CC9E8", rough=0.05, transmission=0.92, ior=1.33)
HEAT = M_emissive("heat_glow", "#FF7A1A", 0.0)
FLAME = M_emissive("flame", "#3E7BFF", 9.0)
FLAME_CORE = M_emissive("flame_core", "#9FC2FF", 6.0)
STEAM = material("steam", "#FFFFFF", rough=1.0, emission="#F4F1EA", emission_strength=0.45, alpha=0.13)
BUBBLE = material("bubble", "#DDEEFF", rough=0.02, transmission=1.0, ior=1.1)

# ------------------------------------------------------------------ helpers
def open_pot(name, r, h, wall, mat, loc):
    """Cylinder with the top face removed + solidify = real wall thickness (shows in cutaway)."""
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=96, location=loc)
    ob = bpy.context.object
    ob.name = name
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    top = [f for f in bm.faces if f.normal.z > 0.9]
    bmesh.ops.delete(bm, geom=top, context="FACES")
    bm.to_mesh(ob.data)
    bm.free()
    sol = ob.modifiers.new("wall", "SOLIDIFY")
    sol.thickness = wall
    sol.offset = -1
    return _finish(ob, mat, bevel=0.008)


CUTTER = None


def cut(ob):
    """Cutaway: boolean away the half facing the camera (y < 0)."""
    global CUTTER
    if not CUT:
        return ob
    if CUTTER is None:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -2.0, 0.8))
        CUTTER = bpy.context.object
        CUTTER.name = "cutter"
        CUTTER.scale = (6, 4, 6)
        CUTTER.hide_render = True
        CUTTER.display_type = "WIRE"
    m = ob.modifiers.new("cut", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.solver = "EXACT"
    m.object = CUTTER
    return ob


# ------------------------------------------------------------------ stove + counter
counter = rounded_slab("counter", 14, 14, 0.1, mat=STONE, loc=(0, 0, -0.05))
burner = cylinder("burner", 0.42, 0.08, mat=IRON, loc=(0, 0, 0.04), bevel=0.01)
cap = cylinder("burner_cap", 0.2, 0.05, mat=IRON, loc=(0, 0, 0.1), bevel=0.01)
# grate: 4 arms + ring
for i in range(4):
    a = math.radians(45 + i * 90)
    arm = rounded_slab(f"grate{i}", 0.62, 0.05, 0.05, mat=IRON, loc=(0.42 * math.cos(a), 0.42 * math.sin(a), 0.17), bevel=0.008)
    arm.rotation_euler = (0, 0, a)
torus("grate_ring", 0.8, 0.025, mat=IRON, loc=(0, 0, 0.12))
# flame tips: ring of small emissive cones
for i in range(28):
    a = 2 * math.pi * i / 28
    x, y = 0.26 * math.cos(a), 0.26 * math.sin(a)
    bpy.ops.mesh.primitive_cone_add(radius1=0.025, radius2=0.0, depth=0.09, vertices=12, location=(x, y, 0.15))
    f = bpy.context.object
    f.rotation_euler = (math.radians(25) * -math.sin(a), math.radians(25) * math.cos(a), 0)
    f.data.materials.append(FLAME if i % 2 else FLAME_CORE)
    f.visible_shadow = False

# ------------------------------------------------------------------ cooker
BASE_Z = 0.2                    # sits on the grate
H, R = 0.9, 0.72
body = cut(open_pot("body", R, H, 0.035, ALU, (0, 0, BASE_Z + H / 2)))
rim = cut(torus("rim", R - 0.005, 0.022, mat=ALU, loc=(0, 0, BASE_Z + H)))
base_disc = cut(cylinder("base", R * 0.92, 0.03, mat=IRON, loc=(0, 0, BASE_Z + 0.012), bevel=0.006))
# lid (slightly domed) + gasket
LID_Z = BASE_Z + H + 0.03
lid = cut(cylinder("lid", R - 0.02, 0.05, mat=ALU_LID, loc=(0, 0, LID_Z), bevel=0.012))
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=96, ring_count=48, location=(0, 0, LID_Z - 0.02))
dome = bpy.context.object
dome.name = "dome"
dome.scale = (R - 0.04, R - 0.04, 0.14)
_finish(dome, ALU_LID, bevel=0)
bpy.ops.object.select_all(action="DESELECT")
cut(dome)
gasket = cut(torus("gasket", R - 0.045, 0.026, mat=RUBBER, loc=(0, 0, LID_Z - 0.035)))
# handles: body handle + lid handle (two-piece, black bakelite)
h_body = rounded_slab("handle_body", 0.85, 0.12, 0.09, corner_r=0.05, bevel=0.012, mat=BAKELITE, loc=(R + 0.42, 0, BASE_Z + H - 0.06))
h_lid = rounded_slab("handle_lid", 0.8, 0.11, 0.07, corner_r=0.05, bevel=0.012, mat=BAKELITE, loc=(R + 0.4, 0, BASE_Z + H + 0.05))
bracket = rounded_slab("bracket", 0.16, 0.14, 0.1, corner_r=0.02, bevel=0.008, mat=ALU, loc=(R + 0.02, 0, BASE_Z + H - 0.05))
for k, xo in enumerate((0.25, 0.6)):
    screw(f"hscrew{k}", (R + xo, 0, BASE_Z + H + 0.088), r=0.016)
# vent pipe + weight (whistle)
TOP = LID_Z + 0.12
vent = cylinder("vent", 0.028, 0.12, mat=CHROME, loc=(0, 0, TOP - 0.02), bevel=0.004)
w_grp = group("weight_grp", (0, 0, TOP + 0.05))
w_body = cylinder("weight_body", 0.075, 0.09, mat=WEIGHT, loc=(0, 0, TOP + 0.05), bevel=0.012)
w_cap = cylinder("weight_cap", 0.045, 0.05, mat=WEIGHT, loc=(0, 0, TOP + 0.115), bevel=0.01)
w_knob = cylinder("weight_knob", 0.022, 0.05, mat=CHROME, loc=(0, 0, TOP + 0.16), bevel=0.008)
parent([w_body, w_cap, w_knob], w_grp)
# fusible safety plug, offset on the lid
PLUG_LOC = (-0.3, 0.12, LID_Z + 0.075)
plug_base = cylinder("plug_base", 0.045, 0.03, mat=CHROME, loc=PLUG_LOC, bevel=0.006)
plug = cylinder("plug", 0.03, 0.035, mat=PLUG, loc=(PLUG_LOC[0], PLUG_LOC[1], PLUG_LOC[2] + 0.03), bevel=0.008)

# ------------------------------------------------------------------ inside (cutaway only)
if CUT:
    water = cut(cylinder("water", R - 0.04, 0.48, mat=WATER, loc=(0, 0, BASE_Z + 0.27), bevel=0.0))
    heat = cylinder("heat", R - 0.05, 0.01, mat=HEAT, loc=(0, 0, BASE_Z + 0.045), bevel=0)
    cut(heat)
    key_value(emission_socket(HEAT), [(0, 0.0), (1.2, 4.0), (D, 6.0)])
    key_value(emission_socket(RUBBER), [(0, 0.0), (3.4, 0.0), (3.9, 6.0), (D, 6.0)])   # "gasket" line
    rnd = random.Random(4)
    for i in range(46):                        # bubbles rising through the water (back half only)
        x, y = rnd.uniform(-0.55, 0.55), rnd.uniform(0.05, 0.55)
        r = rnd.uniform(0.007, 0.018)
        t0 = rnd.uniform(0.3, D - 1.2)
        b = bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=16, ring_count=8, location=(x, y, BASE_Z + 0.06))
        bub = bpy.context.object
        bub.data.materials.append(BUBBLE)
        key_loc(bub, [(0, (x, y, BASE_Z + 0.06)), (t0, (x, y, BASE_Z + 0.06)),
                      (t0 + 1.1, (x + rnd.uniform(-0.03, 0.03), y, BASE_Z + 0.5))])
        bub.scale = (0, 0, 0)
        bub.keyframe_insert("scale", frame=frame_at(max(0, t0 - 0.05)))
        bub.scale = (1, 1, 1)
        bub.keyframe_insert("scale", frame=frame_at(t0))
        bub.keyframe_insert("scale", frame=frame_at(t0 + 1.05))
        bub.scale = (0, 0, 0)
        bub.keyframe_insert("scale", frame=frame_at(t0 + 1.12))
    for i in range(30):                        # steam swirling above the water
        x, y = rnd.uniform(-0.5, 0.5), rnd.uniform(0.05, 0.5)
        z0 = BASE_Z + 0.55
        bpy.ops.mesh.primitive_uv_sphere_add(radius=rnd.uniform(0.03, 0.06), segments=16, ring_count=8, location=(x, y, z0))
        puff = bpy.context.object
        puff.data.materials.append(STEAM)
        puff.visible_shadow = False
        key_loc(puff, [(0, (x, y, z0)), (D, (x + rnd.uniform(-0.1, 0.1), y, z0 + rnd.uniform(0.15, 0.3)))])


def steam_jet(origin, t_start, t_end, n=26, seed=9, height=0.9, spread=0.12, size=1.0):
    """Puffs shooting up from a vent between t_start and t_end, growing as they rise."""
    rnd = random.Random(seed)
    for i in range(n):
        t0 = t_start + (t_end - t_start) * i / n + rnd.uniform(0, 0.08)
        life = rnd.uniform(0.7, 1.1)
        x0, y0, z0 = origin
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022 * size, segments=16, ring_count=8, location=origin)
        puff = bpy.context.object
        puff.data.materials.append(STEAM)
        puff.visible_shadow = False
        dx, dy = rnd.uniform(-spread, spread), rnd.uniform(-spread, spread)
        key_loc(puff, [(0, origin), (t0, origin), (t0 + life, (x0 + dx, y0 + dy, z0 + height * rnd.uniform(0.7, 1.1)))])
        for t, s in ((0, 0.0), (max(0, t0 - 0.02), 0.0), (t0, 0.5), (t0 + life * 0.75, 2.2), (t0 + life, 0.0)):
            puff.scale = (s, s, s)
            puff.keyframe_insert("scale", frame=frame_at(min(D, t)))


wz = TOP + 0.05
if SHOT == "weight":
    # weight rests, lifts on "lifts the weight" (~5.1s), jiggles, steam rushes out
    keys = [(0, (0, 0, wz)), (5.0, (0, 0, wz))]
    t = 5.2
    while t < D - 0.2:
        keys += [(t, (0, 0, wz + 0.04)), (t + 0.12, (0, 0, wz + 0.015))]
        t += 0.24
    key_loc(w_grp, keys)
    steam_jet((0, 0, TOP + 0.19), 5.1, D - 0.3, n=110, height=0.7, spread=0.06)
if SHOT == "pullback":
    keys, t = [(0, (0, 0, wz))], 0.4
    while t < D - 0.2:
        keys += [(t, (0, 0, wz + 0.035)), (t + 0.12, (0, 0, wz + 0.01))]
        t += 0.24
    key_loc(w_grp, keys)
    steam_jet((0, 0, TOP + 0.19), 0.3, D - 0.2, n=70, height=1.1, spread=0.08, size=1.6)
if SHOT == "safety":
    key_value(emission_socket(PLUG), [(0, 0.0), (0.8, 0.0), (2.0, 7.0), (D, 7.0)])
    plug.keyframe_insert("scale", frame=frame_at(2.2))
    plug.scale = (1.15, 1.15, 0.15)            # melts and slumps
    plug.keyframe_insert("scale", frame=frame_at(3.0))
    steam_jet((PLUG_LOC[0], PLUG_LOC[1], PLUG_LOC[2] + 0.04), 2.9, D - 0.1, n=50, seed=3, height=0.45, spread=0.05)

# ------------------------------------------------------------------ dressing, light, camera
dust = dust_field(count=90, bounds=((-2.5, 2.5), (-1.5, 2.5), (0.1, 3.0)))
key_loc(dust, [(0, (0, 0, 0)), (D, (0.04, 0.02, 0.06))])
gradient_world(top="#6A707A", bottom="#0A0A0E", strength=0.7)
reflection_strips(target=(0, 0, 0.9), radius=3.6, height=3.6, count=3, strength=5.0, length=7.0)
studio_rig(target=(0, 0, 0.8), scale=1.3, key_energy=700, rim_energy=1300, fill_energy=520)
# warm under-glow from the flame onto the pot bottom
light("point", (0, 0, 0.18), 60, color="#3E7BFF")

aim = group("aim", (0, 0, 0.9))
CAMS = {
    "hero":     dict(lens=70, f=5.6, aim=[(0, (0, 0, 0.75)), (D, (0, 0, 0.85))],
                     cam=[(0, (3.0, -5.6, 1.05)), (D, (2.5, -4.7, 1.2))]),
    "cutaway":  dict(lens=60, f=6.3, aim=[(0, (0, 0.1, 0.7)), (D, (0, 0.1, 0.75))],
                     cam=[(0, (1.4, -5.6, 1.6)), (D, (-0.6, -5.4, 1.8))]),
    "weight":   dict(lens=100, f=4.0, aim=[(0, (0, 0, TOP + 0.05)), (D, (0, 0, TOP + 0.2))],
                     cam=[(0, (0.9, -2.2, TOP + 0.25)), (D, (0.75, -1.95, TOP + 0.45))]),
    "safety":   dict(lens=100, f=4.0, aim=[(0, PLUG_LOC), (D, (PLUG_LOC[0], PLUG_LOC[1], PLUG_LOC[2] + 0.1))],
                     cam=[(0, (-0.1, -1.7, PLUG_LOC[2] + 0.5)), (D, (-0.2, -1.5, PLUG_LOC[2] + 0.42))]),
    "pullback": dict(lens=60, f=5.6, aim=[(0, (0, 0, 1.1)), (D, (0, 0, 0.95))],
                     cam=[(0, (2.6, -4.6, 1.6)), (D, (4.2, -7.4, 1.9))]),
}
c = CAMS[SHOT]
key_loc(aim, c["aim"])
camera(lens=c["lens"], fstop=c["f"], focus=aim, target=aim, keys=c["cam"])

# label anchors for the compositor
anchor("gasket", gasket, (-(R - 0.045), 0.0, 0))
anchor("vent", vent, (0, 0, 0.05))
anchor("weight", w_grp, (0.075, 0, 0.03))
anchor("plug", plug, (0, 0, 0.02))
anchor("water", bpy.data.objects.get("water") or body, (0.3, 0.2, 0.0))

os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
export_anchors(os.path.splitext(args.out)[0] + ".anchors.json")
if args.anchors_only:
    print("OK: anchors")
    sys.exit(0)
print("OK:", render(args.out, samples=args.samples, scale=args.scale, still_at=args.still, exposure=0.3))
