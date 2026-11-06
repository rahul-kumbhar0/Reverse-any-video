---
description: Create any video — in a cloned style, from a built-in archetype, or by editing raw footage
argument-hint: [style-or-archetype] "<content brief>" [duration] [aspect]
---

Create a video per $ARGUMENTS: if the first token matches a folder under
`skills/generated/` use that style; if it matches a built-in archetype
(explainer-reel, tutorial-screencast, talking-head, product-ad, kinetic-typography,
slideshow-montage, documentary-chapter, music-beat-edit, trailer-teaser, data-story,
ugc-style, whiteboard-sketch) synthesize a spec from it; otherwise treat everything
as the brief and pick the best-fitting archetype yourself.

Use the `create-video` skill from this plugin: resolve style + format (aspect preset),
write the script to the style's formula and show it for approval, build timeline.json to
the style's pacing numbers, render (Remotion preferred, FFmpeg assembler fallback),
verify against the fidelity checklist by looking at extracted frames, and deliver the
MP4 + script + timeline.

If the brief includes the user's own footage, start in Mode B
(`scripts/edit_footage.py scan/cut/beatcut`) before building the timeline.
For long renders, delegate to the `video-director` agent.
