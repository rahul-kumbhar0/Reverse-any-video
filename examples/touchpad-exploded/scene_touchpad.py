"""Exploded view of a laptop force-touch trackpad — 3s hero shot.

Layers (top→bottom): etched glass · capacitive electrode grid · controller PCB ·
force sensors + haptic engine · aluminium stiffener frame.

python3 scene_touchpad.py --out out/touchpad.mp4                # full animation
python3 scene_touchpad.py --out out/check.mp4 --still 2.6       # one verification frame
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "create-video", "scripts"))
from blender_kit import *  # noqa: E402,F401

p = argparse.ArgumentParser()
p.add_argument("--out", required=True)
p.add_argument("--still", type=float, default=None)
p.add_argument("--samples", type=int, default=48)
p.add_argument("--scale", type=float, default=0.5)
p.add_argument("--fps-render", type=int, default=12)
p.add_argument("--anchors-only", action="store_true", help="export label tracks, skip render")
args = p.parse_args()

DUR = 3.0
reset(fps_render=args.fps_render, duration_s=DUR, background="#050507")

W, D = 1.6, 1.0          # trackpad footprint
R = 0.09                 # plan-view corner radius
GAP = 0.44               # exploded spacing between layers

# ---------------------------------------------------------------- layers (built at origin, grouped)
layers = []              # (group_empty, assembled_z, exploded_z, label, anchor_offset)

# 1 · aluminium stiffener frame
g_frame = group("L_frame")
frame = rounded_slab("frame", W + 0.06, D + 0.06, 0.035, corner_r=R + 0.03, bevel=0.006,
                     mat=brushed(M_alu_space_gray(), axis="x"))
frame_screws = []
for i, (sx, sy) in enumerate([(-0.74, -0.45), (0.74, -0.45), (-0.74, 0.45), (0.74, 0.45)]):
    frame_screws += screw(f"fscrew{i}", (sx, sy, 0.024), r=0.024)
ribs = bar_array("frame_ribs", W - 0.2, 0.025, 0.02, 3, 0.28, axis="x",
                 mat=M_alu_space_gray(), loc=(0, 0, 0.026))
parent([frame, ribs] + frame_screws, g_frame)
layers.append((g_frame, 0.0, 0.0, "frame", (W / 2 + 0.03, 0, 0)))

# 2 · haptic engine + 4 force sensors
g_haptic = group("L_haptic")
engine = rounded_slab("engine", 0.62, 0.17, 0.09, corner_r=0.03, bevel=0.006,
                      mat=brushed(M_alu_silver(), axis="x"), loc=(0, -0.05, 0))
eng_screws = screw("escrew_l", (-0.27, -0.05, 0.05), r=0.016) + screw("escrew_r", (0.27, -0.05, 0.05), r=0.016)
coil = torus("coil", 0.11, 0.035, mat=M_copper(), loc=(0, -0.05, 0.05), scale=(1.9, 0.62, 0.6))
magnet = rounded_slab("magnet", 0.5, 0.05, 0.02, corner_r=0.01, bevel=0.003,
                      mat=M_chip(), loc=(0, -0.05, 0.055))
sensors = []
for i, (sx, sy) in enumerate([(-0.66, -0.38), (0.66, -0.38), (-0.66, 0.38), (0.66, 0.38)]):
    base = rounded_slab(f"force{i}", 0.13, 0.13, 0.03, corner_r=0.02, bevel=0.004,
                        mat=M_alu_silver(), loc=(sx, sy, 0))
    gauge = rounded_slab(f"gauge{i}", 0.08, 0.08, 0.01, corner_r=0.012, bevel=0.002,
                         mat=M_emissive(f"gauge_glow{i}", "#E0A33E", 0.0), loc=(sx, sy, 0.02))
    sensors += [base, gauge]
parent([engine, coil, magnet] + eng_screws + sensors, g_haptic)
layers.append((g_haptic, 0.06, 0.06 + GAP, "haptic", (0.33, -0.05, 0.04)))

# 3 · controller PCB
g_pcb = group("L_pcb")
pcb = rounded_slab("pcb", W - 0.04, D - 0.04, 0.022, corner_r=R - 0.01, bevel=0.003,
                   mat=micro_surface(M_pcb(), scale=220, bump=0.05, rough_var=0.08))
traces_x = bar_array("traces_x", W - 0.3, 0.006, 0.003, 9, 0.085, axis="x",
                     mat=M_copper(), loc=(0, 0.04, 0.0125))
chip = rounded_slab("chip", 0.24, 0.24, 0.03, corner_r=0.012, bevel=0.004,
                    mat=M_chip(), loc=(0.42, -0.16, 0.025))
pins_l = bar_array("pins_l", 0.04, 0.012, 0.008, 9, 0.024, axis="x",
                   mat=M_gold(), loc=(0.29, -0.16, 0.014))
pins_r = bar_array("pins_r", 0.04, 0.012, 0.008, 9, 0.024, axis="x",
                   mat=M_gold(), loc=(0.55, -0.16, 0.014))
connector = rounded_slab("connector", 0.2, 0.07, 0.025, corner_r=0.01, bevel=0.003,
                         mat=M_rubber_black(), loc=(-0.45, 0.4, 0.022))
smds = smd_scatter("smd", ((-0.7, 0.1), (-0.05, 0.4)), 26, 0.011, seed=7)
smds += smd_scatter("smdb", ((0.15, 0.7), (0.12, 0.42)), 14, 0.011, seed=11)
vias = via_grid("vias", ((-0.7, 0.62), (-0.42, -0.12)), 0.05, 0.0115)
mark = text_label("chip_mark", "TPC-2A\n4417 X9", 0.035, (0.42, -0.16, 0.0405))
flex = flex_cable("flex", [(-0.45, 0.4, 0.03), (-0.45, 0.52, 0.05), (-0.45, 0.64, 0.0), (-0.45, 0.74, -0.1)],
                  width=0.14)
parent([pcb, traces_x, chip, pins_l, pins_r, connector, vias, mark, flex] + smds, g_pcb)
layers.append((g_pcb, 0.15, 0.15 + 2 * GAP, "pcb", (0.42, -0.16, 0.05)))

# 4 · capacitive sensor: thin clear film with crossing X/Y electrode grids
g_sense = group("L_sense")
film = rounded_slab("film", W - 0.02, D - 0.02, 0.008, corner_r=R - 0.005, bevel=0.0015,
                    mat=material("film", "#9FB4C8", rough=0.15, transmission=0.85, ior=1.4))
GRID = M_emissive("grid_glow", "#E0A33E", 0.3)
rows = bar_array("rows", W - 0.12, 0.006, 0.003, 11, 0.082, axis="x", mat=GRID, loc=(0, 0, 0.006))
cols = bar_array("cols", D - 0.12, 0.006, 0.003, 18, 0.082, axis="y", mat=GRID, loc=(0, 0, 0.011))
parent([film, rows, cols], g_sense)
layers.append((g_sense, 0.185, 0.185 + 3 * GAP, "sense", (W / 2 - 0.06, 0.1, 0.01)))

# 5 · etched glass top
g_glass = group("L_glass")
glass = rounded_slab("glass", W, D, 0.03, corner_r=R, bevel=0.007,
                     mat=micro_surface(M_glass_frosted(), scale=60, bump=0.03, rough_var=0.1))
parent([glass], g_glass)
layers.append((g_glass, 0.215, 0.215 + 4 * GAP, "glass", (W / 2, -0.15, 0.015)))

# ---------------------------------------------------------------- animation
# Explode top-first with a 0.12s stagger; clamped-bezier easing (no overshoot).
for i, (g, z0, z1, name, off) in enumerate(reversed(layers)):
    if z0 == z1:
        anchor(name, g, off)
        continue
    t0 = 0.35 + i * 0.12
    t1 = t0 + 1.25
    key_loc(g, [(0.0, (0, 0, z0)), (t0, (0, 0, z0)), (t1, (0, 0, z1)), (DUR, (0, 0, z1 + 0.03))])
    anchor(name, g, off)

# The sensor grid "comes alive" once separated; force gauges follow.
key_value(emission_socket(GRID), [(0.0, 0.3), (1.3, 0.3), (2.0, 3.2), (DUR, 3.2)])
for i in range(4):
    sock = emission_socket(bpy.data.materials[f"gauge_glow{i}"])
    key_value(sock, [(0.0, 0.0), (1.6, 0.0), (2.2, 3.0), (DUR, 3.0)])

# ---------------------------------------------------------------- world dressing
dust = dust_field(count=110, bounds=((-1.6, 1.6), (-1.0, 1.6), (-0.2, 2.6)))
key_loc(dust, [(0.0, (0, 0, 0)), (DUR, (0.05, 0.02, 0.08))])

floor = rounded_slab("floor", 30, 30, 0.01, mat=material("floor", "#0B0B0E", rough=0.35, metal=0.1),
                     loc=(0, 0, -0.06))

# ---------------------------------------------------------------- light & camera
aim = group("aim", (0, 0, 0.1))
key_loc(aim, [(0.0, (0, 0, 0.12)), (0.35, (0, 0, 0.12)), (2.0, (0, 0.05, 0.95)), (DUR, (0, 0.05, 0.98))])
studio_environment()                       # HDRI via $RAV_HDRI, else gradient studio world
reflection_strips(target=(0, 0, 0.6), radius=3.2, height=3.4, count=3, strength=5.0)
studio_rig(target=(0, 0, 0.6), scale=1.0, key_energy=480, rim_energy=850, fill_energy=420)


def _far(p, a=(0, 0, 0.12), k=2.0):          # same framing at 2x lens: double the distance
    return tuple(a[i] + (p[i] - a[i]) * k for i in range(3))


camera(lens=70, fstop=5.6, focus=aim, target=aim,
       keys=[(0.0, _far((2.55, -3.7, 1.75))), (DUR, _far((2.3, -3.95, 2.55)))])

# ---------------------------------------------------------------- go
os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
export_anchors(os.path.splitext(args.out)[0] + ".anchors.json")
if args.anchors_only:
    print("OK: anchors")
    sys.exit(0)
res = render(args.out, samples=args.samples, scale=args.scale, still_at=args.still, exposure=0.35)
print("OK:", res)
