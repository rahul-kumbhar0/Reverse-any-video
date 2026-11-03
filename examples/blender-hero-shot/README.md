# Example: photoreal Blender hero shot

A tire-style 2.5s hero shot rendered entirely headlessly from this declarative spec —
PBR materials, the premium-explainer light rig (soft key + aimed amber rim + cool fill),
eased camera push-in, DOF, AgX tone mapping.

```bash
pip install bpy
python3 ../../skills/create-video/scripts/blender_shot.py hero.json out/hero.mp4 --fps-render 12 --samples 32 --scale 0.5
python3 ../../skills/create-video/scripts/synth_sfx.py whoosh whoosh.wav
```

~6 min on 4 CPU cores. See skills/reverse-video/references/3d-motion-playbook.md for the
lighting grammar this implements.
